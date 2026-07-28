import os
import io
import time
import hashlib
import threading
import concurrent.futures
import multiprocessing
from contextlib import nullcontext

# Batasi penggunaan multi-threading bawaan Tesseract agar tidak bentrok dengan multiprocessing Python
os.environ['OMP_THREAD_LIMIT'] = '1'

import fitz
import pytesseract
from PIL import Image

from models import OCRDashboardModel
from services.log_service import catat_log
from services.metadata_service import sedot_metadata
from services.progress_service import (
    ambil_progress,
    mulai,
    update_file,
    update_progress,
    selesai,
    berhenti,
    error,
    is_queue_paused,
    is_stop_requested
)
from services.settings_service import load_settings, resolve_tesseract_cmd

from config.settings import TESSERACT_CMD
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

SUPPORTED_EXTENSIONS = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp')
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp')


def _preprocess_image(img):
    """Pre-process image for better OCR accuracy: convert to grayscale and enhance contrast."""
    from PIL import ImageEnhance, ImageFilter
    img_gray = img.convert("L")
    enhancer = ImageEnhance.Contrast(img_gray)
    img_enhanced = enhancer.enhance(1.5)
    img_enhanced = img_enhanced.filter(ImageFilter.SHARPEN)
    return img_enhanced.convert("RGB")


def hentikan_proses_ocr():
    """Mengirim sinyal penghentian proses OCR."""
    from services.progress_service import hentikan_proses_ocr as service_stop
    service_stop()
    catat_log("⏹️ Sinyal penghentian OCR dikirim oleh pengguna.")


def ambil_progress_ocr():
    """Mengembalikan data progress OCR."""
    return ambil_progress()

def validasi_awal(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not os.path.exists(input_dir):
        catat_log(f"ERROR FATAL: Folder input {input_dir} tidak ditemukan!")
        error()
        return False

    if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
        catat_log("ERROR FATAL: Aplikasi Tesseract tidak ditemukan!")
        error()
        return False

    return True


def hitung_total_dokumen(input_dir):
    total = 0

    for root, _, files in os.walk(input_dir):
        total += sum(
            1 for f in files if f.lower().endswith(SUPPORTED_EXTENSIONS)
        )

    return total


hitung_total_pdf = hitung_total_dokumen


def buat_output_dir(root, input_dir, output_dir):
    relative_path = os.path.relpath(root, input_dir)

    if relative_path == ".":
        target = output_dir
    else:
        target = os.path.join(output_dir, relative_path)

    os.makedirs(target, exist_ok=True)

    return target


def ekstrak_teks_dan_pdf(jalur_pdf, ocr_lang="ind+eng", dpi_render=200, generate_searchable_pdf=True):
    doc_asli = fitz.open(jalur_pdf)
    pdf_baru = fitz.open()

    try:
        semua_teks = ""
        zoom = max(1.0, float(dpi_render) / 72.0)
        matrix = fitz.Matrix(zoom, zoom)

        for page_num in range(len(doc_asli)):

            if is_stop_requested():
                pdf_baru.close()
                raise KeyboardInterrupt

            page = doc_asli[page_num]

            # --- OPTIMASI 1 (Smart Skip PDF dengan deteksi Gambar) ---
            teks_asli = page.get_text().strip()
            daftar_gambar = page.get_images()
            
            # Jika teks cukup banyak dan tidak ada elemen gambar sama sekali, lompati OCR (sangat menghemat waktu)
            if len(teks_asli) > 50 and len(daftar_gambar) == 0:
                semua_teks += teks_asli + "\n"
                pdf_baru.insert_pdf(doc_asli, from_page=page_num, to_page=page_num)
                continue
            # --------------------------------------------------------

            pix = page.get_pixmap(
                matrix=matrix
            )

            # Optimasi 3: Menggunakan context manager untuk memori
            with Image.frombytes("RGB", [pix.width, pix.height], pix.samples) as img_raw:
                img = _preprocess_image(img_raw)

                # Searchable PDF generation
                if generate_searchable_pdf:
                    # --- OPTIMASI 2 (Hindari I/O BytesIO berlebih, serahkan objek PIL secara langsung) ---
                    pdf_bytes = pytesseract.image_to_pdf_or_hocr(
                        img,
                        extension="pdf",
                        lang=ocr_lang
                    )
                    
                    with fitz.open("pdf", pdf_bytes) as pdf_temp:
                        teks_halaman = pdf_temp[0].get_text()
                        if teks_halaman:
                            semua_teks += teks_halaman + "\n"
                        pdf_baru.insert_pdf(pdf_temp)
                else:
                    # If not generating searchable PDF, just use image_to_string to check text
                    teks_halaman = pytesseract.image_to_string(img, lang=ocr_lang)
                    if teks_halaman:
                        semua_teks += teks_halaman + "\n"
                    pdf_baru.insert_pdf(doc_asli, from_page=page_num, to_page=page_num)
                
                img.close()

        karakter_valid = [
            c for c in semua_teks if c.isalnum()
        ]

        if len(karakter_valid) < 3:
            pdf_baru.close()
            raise Exception("Tidak ada teks.")

        return pdf_baru

    except Exception:
        if pdf_baru:
            try:
                pdf_baru.close()
            except Exception:
                pass
        raise
    finally:
        doc_asli.close()


def ekstrak_teks_dari_gambar(jalur_gambar, ocr_lang="ind+eng", dpi_render=200, generate_searchable_pdf=True):
    pdf_baru = None
    img_processed = None
    
    try:
        if is_stop_requested():
            raise KeyboardInterrupt

        # Optimasi 3: Menggunakan context manager untuk manajemen memori otomatis
        with Image.open(jalur_gambar) as img_raw:
            img = img_raw.convert("RGB")
            img_processed = _preprocess_image(img)
            img.close()

        # Generate Searchable PDF layer or image to PDF
        if generate_searchable_pdf:
            # Optimasi 2: Passing Pillow objek secara langsung tanpa buffer I/O berlebih
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(
                img_processed,
                extension="pdf",
                lang=ocr_lang
            )
            pdf_baru = fitz.open("pdf", pdf_bytes)
            semua_teks = pdf_baru[0].get_text()
        else:
            img_bytes = io.BytesIO()
            img_processed.save(img_bytes, format="PDF")
            pdf_bytes = img_bytes.getvalue()
            pdf_baru = fitz.open("pdf", pdf_bytes)
            semua_teks = pytesseract.image_to_string(img_processed, lang=ocr_lang)
            img_bytes.close()

        karakter_valid = [c for c in semua_teks if c.isalnum()]
        if len(karakter_valid) < 3:
            raise Exception("Tidak ada teks.")

        return pdf_baru

    except Exception:
        if pdf_baru:
            try:
                pdf_baru.close()
            except Exception:
                pass
        raise
    finally:
        if img_processed:
            try: img_processed.close()
            except: pass


def ekstrak_dokumen(jalur_awal, ocr_lang="ind+eng", dpi_render=200, generate_searchable_pdf=True):
    ext = os.path.splitext(jalur_awal)[1].lower()
    if ext == ".pdf":
        return ekstrak_teks_dan_pdf(
            jalur_awal,
            ocr_lang=ocr_lang,
            dpi_render=dpi_render,
            generate_searchable_pdf=generate_searchable_pdf
        )
    elif ext in IMAGE_EXTENSIONS:
        return ekstrak_teks_dari_gambar(
            jalur_awal,
            ocr_lang=ocr_lang,
            dpi_render=dpi_render,
            generate_searchable_pdf=generate_searchable_pdf
        )
    else:
        raise ValueError(f"Ekstensi file tidak didukung: {ext}")


def compute_file_hash(filepath):
    """Compute SHA256 hash of a file's contents."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return ''


def simpan_riwayat(
    db,
    document_key,
    folder_path,
    nama_file,
    status,
    keterangan,
    metadata,
    processing_time=0.0,
    retry_count=0,
    relative_path="",
    file_hash=""
):
    file_size, page_count, author, creation_date = metadata

    db.catat_ke_db(
        document_key=document_key,
        folder_path=folder_path,
        nama_file=nama_file,
        status=status,
        keterangan=keterangan,
        file_size=file_size,
        author=author,
        page_count=page_count,
        creation_date=creation_date,
        processing_time=processing_time,
        retry_count=retry_count,
        relative_path=relative_path,
        file_hash=file_hash
    )


def _ocr_worker_task(task_args):
    """
    Worker function executed in separate process.
    task_args tuple: (jalur_awal, jalur_tujuan, document_key, folder_path, nama_file_only,
                      tesseract_cmd, ocr_lang, dpi_render, generate_searchable_pdf)
    """
    (jalur_awal, jalur_tujuan, document_key, folder_path, nama_file_only,
     tesseract_cmd, ocr_lang, dpi_render, generate_searchable_pdf) = task_args

    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    start_time = time.time()
    metadata = sedot_metadata(jalur_awal)
    file_hash = compute_file_hash(jalur_awal)

    maksimal_percobaan = 3
    for percobaan in range(1, maksimal_percobaan + 1):
        try:
            pdf_baru = ekstrak_dokumen(
                jalur_awal,
                ocr_lang=ocr_lang,
                dpi_render=dpi_render,
                generate_searchable_pdf=generate_searchable_pdf
            )
            pdf_baru.save(jalur_tujuan, garbage=4, deflate=True, clean=True)
            pdf_baru.close()

            processing_time = round(time.time() - start_time, 2)
            return {
                "document_key": document_key,
                "folder_path": folder_path,
                "nama_file": nama_file_only,
                "status": "SUKSES",
                "keterangan": "File berhasil diekstrak dan disimpan.",
                "metadata": metadata,
                "processing_time": processing_time,
                "retry_count": percobaan - 1,
                "relative_path": document_key,
                "file_hash": file_hash
            }
        except Exception as e:
            if percobaan == maksimal_percobaan:
                processing_time = round(time.time() - start_time, 2)
                return {
                    "document_key": document_key,
                    "folder_path": folder_path,
                    "nama_file": nama_file_only,
                    "status": "GAGAL",
                    "keterangan": "File tidak memiliki gambar yang memuat teks.",
                    "metadata": metadata,
                    "processing_time": processing_time,
                    "retry_count": percobaan,
                    "relative_path": document_key,
                    "file_hash": file_hash
                }
            time.sleep(0.5)


from flask import has_app_context


def jalankan_sistem_ocr(input_dir, output_dir, overwrite=False, flask_app=None):
    if flask_app:
        ctx_mgr = flask_app.app_context()
    elif has_app_context():
        ctx_mgr = nullcontext()
    else:
        try:
            from app import app as fallback_app
            ctx_mgr = fallback_app.app_context()
        except Exception:
            ctx_mgr = nullcontext()

    with ctx_mgr:
        db = OCRDashboardModel()

        if not validasi_awal(input_dir, output_dir):
            return

        settings = load_settings()
        tesseract_cmd = resolve_tesseract_cmd(settings.get("tesseract_path"))
        ocr_lang = settings.get("ocr_language", "ind+eng")
        dpi_render = settings.get("dpi_render", 200)
        generate_searchable_pdf = True

        total_dokumen = hitung_total_dokumen(input_dir)

        mulai(total_dokumen)

        catat_log("--- Memulai pemrosesan Searchable PDF ---")

        file_diproses = 0
        dihentikan_paksa = False

        max_workers = max(1, (os.cpu_count() or 2) - 1)

        tasks_to_run = []

        for root, _, files in os.walk(input_dir):
            if is_stop_requested():
                dihentikan_paksa = True
                break

            target_output_dir = buat_output_dir(
                root,
                input_dir,
                output_dir
            )

            for file_name in files:
                if is_stop_requested():
                    dihentikan_paksa = True
                    break

                if not file_name.lower().endswith(SUPPORTED_EXTENSIONS):
                    continue

                jalur_awal = os.path.join(root, file_name)
                relative_path = os.path.relpath(jalur_awal, input_dir)
                document_key = relative_path.replace('\\', '/')
                folder_path = os.path.dirname(document_key)
                nama_file_only = os.path.basename(document_key)

                if file_name.lower().endswith(IMAGE_EXTENSIONS):
                    output_file_name = os.path.splitext(file_name)[0] + ".pdf"
                else:
                    output_file_name = file_name

                jalur_tujuan = os.path.join(
                    target_output_dir,
                    output_file_name
                )

                # SKIP if output exists already and overwrite is False
                if os.path.exists(jalur_tujuan) and not overwrite:
                    update_file(nama_file_only)
                    catat_log(f"SKIP: {document_key}")

                    metadata = sedot_metadata(jalur_awal)
                    file_hash = compute_file_hash(jalur_awal)

                    simpan_riwayat(
                        db,
                        document_key,
                        folder_path,
                        nama_file_only,
                        "SKIP",
                        "File sudah pernah diproses sebelumnya.",
                        metadata,
                        relative_path=document_key,
                        file_hash=file_hash
                    )

                    file_diproses += 1
                    update_progress(file_diproses)
                    continue

                tasks_to_run.append((
                    jalur_awal,
                    jalur_tujuan,
                    document_key,
                    folder_path,
                    nama_file_only,
                    tesseract_cmd,
                    ocr_lang,
                    dpi_render,
                    generate_searchable_pdf
                ))

        if tasks_to_run and not dihentikan_paksa:
            with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                future_map = {
                    executor.submit(_ocr_worker_task, task): task
                    for task in tasks_to_run
                }

                for future in concurrent.futures.as_completed(future_map):
                    if is_stop_requested():
                        catat_log("⏹️ Proses OCR dihentikan oleh pengguna.")
                        executor.shutdown(wait=False, cancel_futures=True)
                        dihentikan_paksa = True
                        berhenti()
                        break

                    if is_queue_paused():
                        catat_log("PAUSE: Queue dihentikan sementara. Menunggu resume...")
                        while is_queue_paused():
                            if is_stop_requested():
                                dihentikan_paksa = True
                                break
                            time.sleep(0.5)

                        if dihentikan_paksa or is_stop_requested():
                            executor.shutdown(wait=False, cancel_futures=True)
                            break

                    try:
                        res = future.result()
                        if res:
                            update_file(res["nama_file"])
                            simpan_riwayat(
                                db,
                                res["document_key"],
                                res["folder_path"],
                                res["nama_file"],
                                res["status"],
                                res["keterangan"],
                                res["metadata"],
                                processing_time=res["processing_time"],
                                retry_count=res["retry_count"],
                                relative_path=res["relative_path"],
                                file_hash=res["file_hash"]
                            )
                            catat_log(f"{res['status']}: {res['document_key']}")
                            file_diproses += 1
                            update_progress(file_diproses)
                    except Exception as exc:
                        task_info = future_map[future]
                        catat_log(f"ERROR: {task_info[2]} - {exc}")
                        
                        try:
                            jalur_awal = task_info[0]
                            document_key = task_info[2]
                            folder_path = task_info[3]
                            nama_file_only = task_info[4]
                            
                            # Wrap metadata extraction individually so DB save
                            # always happens even if these fail
                            try:
                                metadata = sedot_metadata(jalur_awal)
                            except Exception:
                                metadata = ("-", "-", "-", "-")
                            
                            try:
                                file_hash = compute_file_hash(jalur_awal)
                            except Exception:
                                file_hash = ""
                            
                            simpan_riwayat(
                                db,
                                document_key,
                                folder_path,
                                nama_file_only,
                                "GAGAL",
                                f"Fatal Error: {exc}",
                                metadata,
                                processing_time=0.0,
                                retry_count=0,
                                relative_path=document_key,
                                file_hash=file_hash
                            )
                        except Exception as inner_exc:
                            catat_log(f"Failed to log fatal error to DB: {inner_exc}")
                            
                        file_diproses += 1
                        update_progress(file_diproses)

        if dihentikan_paksa:
            berhenti()
            catat_log("OCR stopped by user.")
        else:
            selesai()
            catat_log(f"FINISHED: {file_diproses} files processed.")
