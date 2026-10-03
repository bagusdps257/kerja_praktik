import os
import io
import time
import hashlib
import threading
import concurrent.futures
import multiprocessing
from contextlib import nullcontext

# ==============================================================================
# 1. KONFIGURASI ENVIRONMENT & DEPENDENSI
# ==============================================================================
# Batasi thread internal Tesseract menjadi 1 per proses agar tidak terjadi perebutan
# resource CPU (contention) dengan multiprocessing Python (ProcessPoolExecutor).
os.environ['OMP_THREAD_LIMIT'] = '1'

import fitz  # PyMuPDF: library berkinerja tinggi untuk membaca, merender, dan memodifikasi PDF
import pytesseract  # Wrapper Python untuk engine Tesseract OCR
from PIL import Image  # Pillow: manipulasi dan pre-processing gambar

from models import OCRDashboardModel
from services.log_service import catat_log
from services.metadata_service import sedot_metadata
from services.progress_service import (
    ambil_progress,
    mulai,
    update_file,
    update_progress,
    update_file_and_progress,
    selesai,
    berhenti,
    error,
    is_queue_paused,
    is_stop_requested
)
from services.settings_service import load_settings, resolve_tesseract_cmd

from config.settings import TESSERACT_CMD
pytesseract.pytesseract.tesseract_cmd = resolve_tesseract_cmd(TESSERACT_CMD)

# Format ekstensi file yang didukung oleh sistem OCR
SUPPORTED_EXTENSIONS = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp')
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp')


# ==============================================================================
# 2. PRE-PROCESSING GAMBAR (OPTIMASI AKURASI OCR)
# ==============================================================================
def _preprocess_image(img, auto_upscale=False):
    """
    [ALUR PRE-PROCESSING]
    Mempersiapkan gambar sebelum dikirim ke Tesseract OCR agar akurasi pembacaan karakter meningkat:
    1. Smart Upscaling (Lanczos): Jika gambar beresolusi rendah (<1400px), perbesar resolusi secara tajam.
    2. Mengubah gambar menjadi Grayscale (1-channel L, 8-bit per piksel untuk efisiensi penyimpanan).
    3. Meningkatkan kontras sebesar 1.5x agar teks lebih kontras terhadap latar belakang.
    4. Menerapkan filter penajaman (SHARPEN) untuk memperjelas tepi huruf/karakter.
    """
    from PIL import ImageEnhance, ImageFilter
    
    # 0. Smart Upscaling untuk diagram/skema/gambar beresolusi rendah
    if auto_upscale and (img.width < 1400 or img.height < 1400):
        scale = min(2.5, 1800.0 / max(img.width, img.height))
        if scale > 1.1:
            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                resample_filter = Image.LANCZOS
            img = img.resize((int(img.width * scale), int(img.height * scale)), resample=resample_filter)

    # 1. Konversi ke Grayscale (L = Luminance)
    img_gray = img.convert("L") if img.mode != "L" else img
    
    # 2. Peningkatan Kontras (Enhance Contrast 1.5x)
    enhancer = ImageEnhance.Contrast(img_gray)
    img_enhanced = enhancer.enhance(1.5)
    
    # 3. Filter Penajaman Karakter
    img_enhanced = img_enhanced.filter(ImageFilter.SHARPEN)
    
    return img_enhanced


# ==============================================================================
# 3. KONTROL STATUS & VALIDASI SISTEM
# ==============================================================================
def hentikan_proses_ocr():
    """
    [ALUR PENGHENTIAN]
    Mengirimkan sinyal stop dengan membuat file trigger sinyal (ocr_stop.signal).
    Loop pemrosesan OCR akan mendeteksi sinyal ini dan segera menghentikan antrean.
    """
    from services.progress_service import hentikan_proses_ocr as service_stop
    service_stop()
    catat_log("⏹️ Sinyal penghentian OCR dikirim oleh pengguna.")


def ambil_progress_ocr():
    """Mengembalikan status runtime progress OCR saat ini (persentase, file aktif, status)."""
    return ambil_progress()


def validasi_awal(input_dir, output_dir, tesseract_cmd=None):
    """
    [ALUR VALIDASI AWAL]
    Memeriksa prasyarat sebelum proses OCR dimulai:
    1. Memastikan direktori output ada atau dibuatkan otomatis.
    2. Memastikan direktori input tersedia.
    3. Memastikan binary executable Tesseract OCR terpasang dan valid.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not os.path.exists(input_dir):
        catat_log(f"ERROR FATAL: Folder input {input_dir} tidak ditemukan!")
        error()
        return False

    cmd_to_check = resolve_tesseract_cmd(tesseract_cmd or pytesseract.pytesseract.tesseract_cmd)
    if not cmd_to_check or not os.path.exists(cmd_to_check):
        catat_log("ERROR FATAL: Aplikasi Tesseract tidak ditemukan!")
        error()
        return False

    pytesseract.pytesseract.tesseract_cmd = cmd_to_check
    return True


def hitung_total_dokumen(input_dir):
    """Menghitung total seluruh file dokumen yang valid di folder input (termasuk subfolder)."""
    total = 0
    for root, _, files in os.walk(input_dir):
        total += sum(
            1 for f in files if f.lower().endswith(SUPPORTED_EXTENSIONS)
        )
    return total


hitung_total_pdf = hitung_total_dokumen


def buat_output_dir(root, input_dir, output_dir):
    """
    [ALUR STRUKTUR DIREKTORI]
    Membuat struktur subfolder di folder output yang identik (mirror) dengan folder input.
    """
    relative_path = os.path.relpath(root, input_dir)

    if relative_path == ".":
        target = output_dir
    else:
        target = os.path.join(output_dir, relative_path)

    os.makedirs(target, exist_ok=True)
    return target


# ==============================================================================
# 4. EKSTRAKSI PDF & SMART SKIP OPTIMIZATION
# ==============================================================================
def ekstrak_teks_dan_pdf(jalur_pdf, ocr_lang="ind+eng", dpi_render=200, generate_searchable_pdf=True):
    """
    [ALUR EKSTRAKSI DOKUMEN PDF]
    1. Membuka PDF asli dan membuat objek dokumen PDF baru.
    2. Menghitung skala render berdasarkan resolusi DPI yang diinginkan.
    3. Memproses halaman demi halaman:
       a. Cek apakah ada interupsi/sinyal stop dari pengguna.
       b. [SMART SKIP]: Jika halaman sudah memiliki teks digital dan tidak ada gambar scan,
          langsung salin halaman asli tanpa membuang waktu menjalankan OCR.
       c. [OCR SCAN]: Jika halaman berupa scan, render ke gambar -> pre-process -> kirim ke Tesseract
          untuk menghasilkan halaman Searchable PDF (PDF berisi teks terindeks).
       d. Masukkan halaman hasil ke dokumen PDF baru.
    4. Validasi keberadaan karakter teks hasil ekstraksi.
    5. Mengembalikan objek PyMuPDF dokumen PDF baru.
    """
    doc_asli = fitz.open(jalur_pdf)
    pdf_baru = fitz.open()

    try:
        semua_teks = ""
        # Hitung faktor zoom matriks render dari DPI (default 72 DPI standar PDF)
        zoom = max(1.0, float(dpi_render) / 72.0)
        matrix = fitz.Matrix(zoom, zoom)

        # Iterasi setiap halaman di dalam dokumen PDF
        for page_num in range(len(doc_asli)):

            # Periksa apakah user meminta penghentian proses
            if is_stop_requested():
                pdf_baru.close()
                raise KeyboardInterrupt

            page = doc_asli[page_num]

            # ------------------------------------------------------------------
            # TAHAP A: SMART SKIP (Optimasi Halaman Teks Digital)
            # ------------------------------------------------------------------
            teks_asli = page.get_text().strip()
            daftar_gambar = page.get_images()
            
            # Jika halaman sudah kaya teks (>100 karakter) dan tidak memiliki gambar,
            # maka halaman ini BUKAN hasil scan. Lewati OCR dan salin langsung halamannya!
            if len(teks_asli) > 100 and len(daftar_gambar) == 0:
                semua_teks += teks_asli + "\n"
                pdf_baru.insert_pdf(doc_asli, from_page=page_num, to_page=page_num)
                continue

            # ------------------------------------------------------------------
            # TAHAP B: RENDER GAMBAR & PRE-PROCESSING UNTUK HALAMAN SCAN
            # ------------------------------------------------------------------
            # Render halaman PDF langsung ke grayscale (1-channel) beresolusi optimal
            pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csGRAY)

            # Buka pixmap ke objek Pillow Image Grayscale (mode "L") dengan context manager
            with Image.frombytes("L", [pix.width, pix.height], pix.samples) as img_raw:
                # Terapkan filter grayscale, contrast, dan sharpen
                img = _preprocess_image(img_raw)

                # --------------------------------------------------------------
                # TAHAP C: EKSEKUSI TESSERACT SEARCHABLE PDF
                # --------------------------------------------------------------
                if generate_searchable_pdf:
                    # Menghasilkan byte stream PDF 1 halaman yang memuat layer teks searchable
                    pdf_bytes = pytesseract.image_to_pdf_or_hocr(
                        img,
                        extension="pdf",
                        lang=ocr_lang,
                        config="--psm 3 --oem 1"
                    )
                    
                    # Buka byte PDF hasil OCR dan masukkan halamannya ke PDF output akhir
                    with fitz.open("pdf", pdf_bytes) as pdf_temp:
                        teks_halaman = pdf_temp[0].get_text()
                        if teks_halaman:
                            semua_teks += teks_halaman + "\n"
                        pdf_baru.insert_pdf(pdf_temp)
                else:
                    # Mode alternatif (jika hanya membaca teks mentah tanpa membuat layer PDF baru)
                    teks_halaman = pytesseract.image_to_string(img, lang=ocr_lang, config="--psm 3 --oem 1")
                    if teks_halaman:
                        semua_teks += teks_halaman + "\n"
                    pdf_baru.insert_pdf(doc_asli, from_page=page_num, to_page=page_num)
                
                img.close()

        # ----------------------------------------------------------------------
        # TAHAP D: VALIDASI HASIL TEKS & PRESERVASI METADATA
        # ----------------------------------------------------------------------
        # Pastikan setidaknya terdapat 3 karakter alfanumerik valid yang terbaca
        karakter_valid = [c for c in semua_teks if c.isalnum()]
        if len(karakter_valid) < 3:
            pdf_baru.close()
            raise Exception("Tidak ada teks.")

        # Preservasi metadata asli dokumen (Title, Author, Subject, Keywords, CreationDate)
        if hasattr(doc_asli, 'metadata') and doc_asli.metadata:
            meta = doc_asli.metadata.copy()
            pdf_baru.set_metadata(meta)

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


# ==============================================================================
# 5. EKSTRAKSI FILE GAMBAR KE SEARCHABLE PDF
# ==============================================================================
def ekstrak_teks_dari_gambar(jalur_gambar, ocr_lang="ind+eng", dpi_render=200, generate_searchable_pdf=True):
    """
    [ALUR EKSTRAKSI FILE GAMBAR (.PNG/.JPG/DLL)]
    1. Membuka file gambar dan melakukan pre-processing (Smart Upscaling Lanczos + Grayscale + Contrast + Sharpen).
    2. Pass 1: Eksekusi OCR dengan PSM 3 (Standar Dokumen).
    3. Pass 2 Fallback: Jika teks kurang dari 3 karakter (seperti diagram/alur flowchart/skema listrik),
       coba ulang dengan PSM 11 (Sparse Text Detection).
    4. Validasi teks dan mengembalikan objek dokumen Searchable PDF baru.
    """
    pdf_baru = None
    img_processed = None
    
    try:
        if is_stop_requested():
            raise KeyboardInterrupt

        # 1. Buka dan pre-process gambar dengan Smart Upscaling Lanczos
        with Image.open(jalur_gambar) as img_raw:
            img_processed = _preprocess_image(img_raw, auto_upscale=True)

        semua_teks = ""

        # 2. Pass 1: Eksekusi OCR Standar (--psm 3)
        if generate_searchable_pdf:
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(
                img_processed,
                extension="pdf",
                lang=ocr_lang,
                config="--psm 3 --oem 1"
            )
            pdf_baru = fitz.open("pdf", pdf_bytes)
            semua_teks = pdf_baru[0].get_text() if len(pdf_baru) > 0 else ""
        else:
            semua_teks = pytesseract.image_to_string(img_processed, lang=ocr_lang, config="--psm 3 --oem 1")

        # 3. Pass 2 Fallback: Jika PSM 3 tidak menemukan teks (kasus diagram/flowchart/skema), coba PSM 11
        karakter_valid = [c for c in semua_teks if c.isalnum()]
        if len(karakter_valid) < 3:
            if pdf_baru:
                try: pdf_baru.close()
                except: pass
                pdf_baru = None

            if generate_searchable_pdf:
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(
                    img_processed,
                    extension="pdf",
                    lang=ocr_lang,
                    config="--psm 11 --oem 1"
                )
                pdf_baru = fitz.open("pdf", pdf_bytes)
                semua_teks = pdf_baru[0].get_text() if len(pdf_baru) > 0 else ""
            else:
                semua_teks = pytesseract.image_to_string(img_processed, lang=ocr_lang, config="--psm 11 --oem 1")

        # 4. Validasi akhir keberadaan teks
        karakter_valid = [c for c in semua_teks if c.isalnum()]
        if len(karakter_valid) < 3:
            raise Exception("Tidak ada teks.")

        # Preservasi metadata default untuk konversi file gambar
        if not generate_searchable_pdf:
            img_bytes = io.BytesIO()
            img_processed.save(img_bytes, format="PDF")
            pdf_bytes = img_bytes.getvalue()
            pdf_baru = fitz.open("pdf", pdf_bytes)
            img_bytes.close()

        title = os.path.splitext(os.path.basename(jalur_gambar))[0]
        pdf_baru.set_metadata({
            "title": title,
            "author": "-",
            "subject": "-",
            "keywords": "-",
            "creator": "OCR Management System",
            "producer": "PyMuPDF + Tesseract OCR"
        })

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


# ==============================================================================
# 6. ROUTER EKSTRAKSI DOKUMEN
# ==============================================================================
def ekstrak_dokumen(jalur_awal, ocr_lang="ind+eng", dpi_render=200, generate_searchable_pdf=True):
    """
    [ROUTER EKSTRAKSI]
    Mengarahkan pemrosesan berdasarkan format ekstensi file:
    - Jika PDF -> diarahkan ke ekstrak_teks_dan_pdf()
    - Jika Gambar -> diarahkan ke ekstrak_teks_dari_gambar()
    """
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
    """Menghitung checksum hash SHA256 dari konten file untuk verifikasi keaslian & duplikasi."""
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
    """Mencatat informasi pengerjaan dokumen ke tabel riwayat di database."""
    if len(metadata) == 6:
        file_size, page_count, author, creation_date, subject, keywords = metadata
    elif len(metadata) == 4:
        file_size, page_count, author, creation_date = metadata
        subject = "-"
        keywords = "-"
    else:
        file_size, page_count, author, creation_date, subject, keywords = ("-", "-", "-", "-", "-", "-")

    db.catat_ke_db(
        document_key=document_key,
        folder_path=folder_path,
        nama_file=nama_file,
        status=status,
        keterangan=keterangan,
        file_size=file_size,
        author=author,
        subject=subject,
        keywords=keywords,
        page_count=page_count,
        creation_date=creation_date,
        processing_time=processing_time,
        retry_count=retry_count,
        relative_path=relative_path,
        file_hash=file_hash
    )


# ==============================================================================
# 7. WORKER TASK PER FILE DENGAN RETRY LOGIC (MULTIPROCESSING)
# ==============================================================================
def _ocr_worker_task(task_args):
    """
    [WORKER PROCESS TASK]
    Fungsi unit kerja yang dieksekusi di dalam child process terpisah secara paralel:
    1. Mengatur konfigurasi lokal Tesseract untuk worker ini.
    2. Menyedot metadata dokumen (ukuran, halaman, author, dll) dan hash SHA256.
    3. Menjalankan mekanisme Retry (mencoba ulang hingga max_retry jika gagal).
    4. Jika sukses: Menyimpan file PDF hasil ke folder tujuan dengan kompresi PyMuPDF.
    5. Mengembalikan dictionary hasil eksekusi lengkap dengan status 'SUKSES' atau 'GAGAL'.
    """
    (jalur_awal, jalur_tujuan, document_key, folder_path, nama_file_only,
     tesseract_cmd, ocr_lang, dpi_render, generate_searchable_pdf, max_retry) = task_args

    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    start_time = time.time()
    metadata = sedot_metadata(jalur_awal)
    file_hash = compute_file_hash(jalur_awal)

    maksimal_percobaan = max_retry if max_retry else 3
    
    # --------------------------------------------------------------------------
    # MEKANISME RETRY: Ulangi proses jika terjadi kegagalan/error
    # --------------------------------------------------------------------------
    for percobaan in range(1, maksimal_percobaan + 1):
        try:
            # Panggil proses ekstraksi OCR
            pdf_baru = ekstrak_dokumen(
                jalur_awal,
                ocr_lang=ocr_lang,
                dpi_render=dpi_render,
                generate_searchable_pdf=generate_searchable_pdf
            )
            # Simpan PDF output dengan kompresi tingkat tinggi (deflate objek, gambar, dan font)
            pdf_baru.save(
                jalur_tujuan,
                garbage=4,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
                clean=True
            )
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
            # Jika sudah mencapai batas maksimal percobaan, tandai sebagai GAGAL
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
            time.sleep(0.5)  # Jeda singkat sebelum retry berikutnya


from flask import has_app_context


# ==============================================================================
# 8. ORCHESTRATOR UTAMA SISTEM OCR (ENTRY POINT PEMROSESAN)
# ==============================================================================
def jalankan_sistem_ocr(input_dir, output_dir, overwrite=False, flask_app=None, target_subfolder=None):
    """
    [ORCHESTRATOR UTAMA SISTEM OCR]
    Alur eksekusi keseluruhan:
    LANGKAH 1: Inisialisasi context Flask & database.
    LANGKAH 2: Validasi folder & Tesseract OCR.
    LANGKAH 3: Membaca pengaturan konfigurasi (bahasa OCR, DPI, max retry, dll).
    LANGKAH 4: Menentukan direktori pemindaian (seluruh input atau subfolder spesifik).
    LANGKAH 5: Menghitung total dokumen dan menandai status runtime 'RUNNING'.
    LANGKAH 6: Memindai folder input (os.walk) & membuat folder output mirror.
    LANGKAH 7: Pengecekan file yang sudah ada (SKIP jika overwrite=False).
    LANGKAH 8: Eksekusi batch paralel menggunakan ProcessPoolExecutor.
    LANGKAH 9: Penanganan kontrol Stop (berhenti) atau Pause (jeda antrean).
    LANGKAH 10: Mencatat log, menyimpan riwayat ke DB, dan mengupdate progress UI per file.
    LANGKAH 11: Finalisasi status ('FINISHED' atau 'STOPPED').
    """
    # LANGKAH 1: Setup Flask App Context untuk akses database di background thread
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

        # LANGKAH 2 & 3: Muat konfigurasi pengguna & validasi awal
        settings = load_settings()
        tesseract_cmd = resolve_tesseract_cmd(settings.get("tesseract_path"))
        ocr_lang = settings.get("ocr_language", "ind+eng")
        dpi_render = settings.get("dpi_render", 200)
        generate_searchable_pdf = True
        max_retry = settings.get("max_retry", 3)

        if not validasi_awal(input_dir, output_dir, tesseract_cmd):
            return

        # LANGKAH 4: Tentukan direktori pemindaian (subfolder target vs seluruh input)
        target_subfolder = (target_subfolder or "").strip().strip('/\\')
        if target_subfolder:
            scan_dir = os.path.join(input_dir, target_subfolder)
            if not os.path.isdir(scan_dir):
                catat_log(f"❌ Error: Subfolder target '{target_subfolder}' tidak ditemukan di {input_dir}")
                error()
                return
            catat_log(f"🎯 Mode Target Aktif: Memproses khusus subfolder '{target_subfolder}'")
        else:
            scan_dir = input_dir

        # LANGKAH 5: Hitung total dokumen & mulai progress tracking
        total_dokumen = hitung_total_dokumen(scan_dir)
        mulai(total_dokumen, target_subfolder=target_subfolder)

        catat_log(f"--- Memulai pemrosesan Searchable PDF ({total_dokumen} berkas terdeteksi) ---")

        file_diproses = 0
        dihentikan_paksa = False

        # Tentukan jumlah worker paralel berdasarkan jumlah core CPU
        max_workers = max(1, (os.cpu_count() or 2) - 1)
        tasks_to_run = []

        # LANGKAH 6: Pindai file pada direktori yang ditargetkan
        for root, _, files in os.walk(scan_dir):
            if is_stop_requested():
                dihentikan_paksa = True
                break

            # Buat folder mirror di direktori output
            target_output_dir = buat_output_dir(root, input_dir, output_dir)

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

                jalur_tujuan = os.path.join(target_output_dir, output_file_name)

                # --------------------------------------------------------------
                # LANGKAH 6: CEK DUPLIKASI & PERUBAHAN FILE
                # --------------------------------------------------------------
                is_output_up_to_date = False
                if os.path.exists(jalur_tujuan):
                    try:
                        input_mtime = os.path.getmtime(jalur_awal)
                        output_mtime = os.path.getmtime(jalur_tujuan)
                        if input_mtime <= output_mtime:
                            is_output_up_to_date = True
                    except OSError:
                        is_output_up_to_date = False

                if is_output_up_to_date and not overwrite:
                    update_file(nama_file_only)
                    catat_log(f"SKIP: {document_key}")

                    metadata = sedot_metadata(jalur_awal)
                    file_hash = ""  # Skip hashing untuk mempercepat file yang di-skip

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

                # Kumpulkan task yang akan diproses oleh worker
                tasks_to_run.append((
                    jalur_awal,
                    jalur_tujuan,
                    document_key,
                    folder_path,
                    nama_file_only,
                    tesseract_cmd,
                    ocr_lang,
                    dpi_render,
                    generate_searchable_pdf,
                    max_retry
                ))

        # Update progress segera setelah loop skip selesai
        if file_diproses > 0:
            update_progress(file_diproses, force=True)

        # ----------------------------------------------------------------------
        # LANGKAH 7: EKSEKUSI BATCH MULTIPROCESSING PARALEL (SMALLEST FILE FIRST)
        # ----------------------------------------------------------------------
        if tasks_to_run and not dihentikan_paksa:
            # Urutkan task berdasarkan kapasitas file terkecil terlebih dahulu (Smallest File First)
            tasks_to_run.sort(key=lambda t: os.path.getsize(t[0]) if os.path.exists(t[0]) else 0)

            with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit seluruh task ke pool executor
                future_map = {
                    executor.submit(_ocr_worker_task, task): task
                    for task in tasks_to_run
                }

                # Ambil hasil pemrosesan secara asinkron saat masing-masing task selesai
                for future in concurrent.futures.as_completed(future_map):
                    # LANGKAH 8A: Deteksi Sinyal Stop (Penghentian oleh pengguna)
                    if is_stop_requested():
                        catat_log("⏹️ Proses OCR dihentikan oleh pengguna.")
                        executor.shutdown(wait=False, cancel_futures=True)
                        dihentikan_paksa = True
                        berhenti()
                        break

                    # LANGKAH 8B: Deteksi Sinyal Pause (Jeda antrean)
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

                    # LANGKAH 9: Ambil hasil worker dan simpan ke database & progress state
                    try:
                        res = future.result()
                        if res:
                            # Simpan histori pengerjaan dokumen ke database
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
                            update_file_and_progress(res["nama_file"], file_diproses, force=True)
                    except Exception as exc:
                        # Tangani error fatal jika worker mengalami crash
                        task_info = future_map[future]
                        catat_log(f"ERROR: {task_info[2]} - {exc}")
                        
                        try:
                            jalur_awal = task_info[0]
                            document_key = task_info[2]
                            folder_path = task_info[3]
                            nama_file_only = task_info[4]
                            
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
                        update_file_and_progress(nama_file_only, file_diproses, force=True)

        # ----------------------------------------------------------------------
        # LANGKAH 10: FINALISASI STATUS SISTEM
        # ----------------------------------------------------------------------
        if dihentikan_paksa:
            berhenti()
            catat_log("OCR stopped by user.")
        else:
            selesai()
            catat_log(f"FINISHED: {file_diproses} files processed.")