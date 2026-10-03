import threading

from flask import Blueprint, request, redirect, url_for, jsonify, current_app
from flask_login import login_required

import core_engine

from models.model_provider import db_model

from core_engine import hentikan_proses_ocr

from services.progress_service import ambil_progress, reset_progress

ocr_bp = Blueprint("ocr", __name__)

# Variabel global untuk menyimpan referensi thread OCR yang sedang aktif berjalan
active_ocr_thread = None


# ==============================================================================
# ENDPOINT: MULAI PEMROSESAN OCR (/jalankan)
# ==============================================================================
@ocr_bp.route("/jalankan", methods=["POST"])
@login_required
def jalankan():
    """
    [ALUR PEMICU OCR DARI WEB]
    1. Membaca status kemajuan saat ini dari file runtime state.
    2. Self-healing: Memeriksa apakah thread sebelumnya sudah selesai/mati.
    3. Mencegah eksekusi ganda jika sistem sudah berstatus 'RUNNING'.
    4. Memperbarui direktori input/output jika dikirimkan dari form.
    5. Menjalankan fungsi utama `core_engine.jalankan_sistem_ocr` di dalam
       Background Thread (threading.Thread) agar request HTTP tidak timeout.
    6. Mengarahkan kembali pengguna ke halaman dashboard utama.
    """
    global active_ocr_thread
    prog = ambil_progress()

    # 1. Self-healing: jika thread sudah mati, reset variabel thread ke None
    if active_ocr_thread is not None and not active_ocr_thread.is_alive():
        active_ocr_thread = None

    # 2. Jika file state 'RUNNING' tetapi thread fisiknya tidak ada, reset status
    if prog.get("status") == "RUNNING" and (active_ocr_thread is None or not active_ocr_thread.is_alive()):
        reset_progress()
        prog = ambil_progress()

    # 3. Validasi: Jangan izinkan memulai jika proses OCR sedang berjalan aktif
    if prog.get("status") == "RUNNING" and active_ocr_thread is not None and active_ocr_thread.is_alive():
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "status": "warning",
                "message": "OCR process is already running."
            }), 400
        return redirect(url_for("dashboard.index"))

    # 4. Ambil dan perbarui input/output path jika ada perubahan dari form UI
    input_baru = request.form.get("input_dir")
    output_baru = request.form.get("output_dir")
    target_subfolder = request.form.get("target_subfolder", "").strip()

    if input_baru and output_baru:
        db_model.update_folder(input_baru, output_baru)

    app = current_app._get_current_object()

    # 5. Jalankan engine OCR di background thread (daemon)
    active_ocr_thread = threading.Thread(
        target=core_engine.jalankan_sistem_ocr,
        args=(db_model.input_dir, db_model.output_dir),
        kwargs={
            "overwrite": False,
            "flask_app": app,
            "target_subfolder": target_subfolder if target_subfolder else None
        }
    )
    active_ocr_thread.daemon = True
    active_ocr_thread.start()

    # 6. Response: kembalikan JSON untuk request AJAX (agar tidak reload page) atau redirect jika submit form HTML standar
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "status": "success",
            "message": "Proses OCR berhasil dimulai.",
            "target_subfolder": target_subfolder
        })
    return redirect(url_for("dashboard.index"))


# ==============================================================================
# ENDPOINT: PENGHENTIAN OCR (/stop)
# ==============================================================================
@ocr_bp.route("/stop", methods=["POST"])
@login_required
def stop_ocr():
    """
    [ALUR PENGHENTIAN OCR]
    Mengirimkan sinyal stop secara asinkron ke background thread / child process
    agar proses OCR segera berhenti dengan aman.
    """
    try:
        hentikan_proses_ocr()
        return jsonify({
            "status": "success",
            "message": "OCR stopped by user."
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500