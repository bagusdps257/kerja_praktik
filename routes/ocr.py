import threading

from flask import Blueprint, request, redirect, url_for, jsonify, current_app
from flask_login import login_required

import core_engine

from models.model_provider import db_model

from core_engine import hentikan_proses_ocr

from services.progress_service import ambil_progress, reset_progress

ocr_bp = Blueprint("ocr", __name__)

active_ocr_thread = None

@ocr_bp.route("/jalankan", methods=["POST"])
@login_required
def jalankan():
    global active_ocr_thread
    prog = ambil_progress()

    # Self-healing: jika thread sudah mati, reset variabel thread
    if active_ocr_thread is not None and not active_ocr_thread.is_alive():
        active_ocr_thread = None

    # Jika file state RUNNING tetapi TIDAK ada thread aktif yang sedang berjalan, reset status
    if prog.get("status") == "RUNNING" and (active_ocr_thread is None or not active_ocr_thread.is_alive()):
        reset_progress()
        prog = ambil_progress()

    if prog.get("status") == "RUNNING" and active_ocr_thread is not None and active_ocr_thread.is_alive():
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "status": "warning",
                "message": "OCR process is already running."
            }), 400
        return redirect(url_for("dashboard.index"))

    input_baru = request.form.get("input_dir")
    output_baru = request.form.get("output_dir")

    if input_baru and output_baru:
        db_model.update_folder(input_baru, output_baru)

    app = current_app._get_current_object()

    active_ocr_thread = threading.Thread(
        target=core_engine.jalankan_sistem_ocr,
        args=(db_model.input_dir, db_model.output_dir),
        kwargs={"overwrite": False, "flask_app": app}
    )
    active_ocr_thread.daemon = True
    active_ocr_thread.start()

    return redirect(url_for("dashboard.index"))


@ocr_bp.route("/stop", methods=["POST"])
@login_required
def stop_ocr():
    """Send stop signal to OCR background thread."""
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