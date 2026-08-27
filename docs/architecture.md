# Arsitektur Proyek OCR & Document Management System (DMS)

Dokumen ini menjelaskan arsitektur perangkat lunak dari proyek **Intelligent OCR & DMS Project** secara lengkap. Dokumen ini dapat Anda jadikan acuan untuk memahami alur kerja, struktur direktori, dan teknologi yang digunakan dalam sistem ini.

---

## 1. Tinjauan Sistem (System Overview)

Proyek ini adalah aplikasi web berbasis **Python (Flask)** dengan pola arsitektur **MVC + Service Layer** yang berfungsi untuk mengekstraksi teks dari dokumen gambar atau PDF menggunakan teknologi Optical Character Recognition (OCR). Sistem ini membaca file yang diunggah ke dalam direktori tertentu secara rekursif, memprosesnya secara paralel dengan **ProcessPoolExecutor + Tesseract OCR Engine**, dan menyimpan hasilnya (Searchable PDF) ke dalam direktori *output*. Aplikasi juga memiliki dasbor web untuk memonitor proses secara live, mengelola riwayat OCR 16 kolom, analitik performa, pelaporan Excel/PDF, dan manajemen pengguna (otentikasi).

---

## 2. Tech Stack (Teknologi yang Digunakan)

*   **Backend Framework**: [Flask](https://flask.palletsprojects.com/) (Python 3.12+)
*   **Database ORM**: Flask-SQLAlchemy (SQLAlchemy 2.0+)
*   **Database Engine**: MySQL Server 8.0+ / MariaDB 10.5+ via PyMySQL
*   **Mesin OCR**: [Tesseract OCR v5.3.4](https://github.com/tesseract-ocr/tesseract) melalui *wrapper* `pytesseract`
*   **Pemrosesan PDF**: [PyMuPDF](https://pymupdf.readthedocs.io/) (`fitz` v1.23+)
*   **Pemrosesan Gambar**: Pillow (PIL v12+) & OpenCV Headless (v4.8+)
*   **Autentikasi & Keamanan**: Flask-Login, Werkzeug Security (`scrypt` / `pbkdf2:sha256`), Flask-WTF CSRFProtect
*   **Ekspor Data**: `openpyxl` (untuk mengekspor spreadsheet `.xlsx` 13 kolom) & CSS Media Print (untuk ekspor PDF analitik)
*   **Frontend**: HTML5, Vanilla CSS3 (Custom Dark-accent Design), JavaScript (AJAX Polling & Chart.js) via Jinja2 Templates

---

## 3. Struktur Direktori Utama

Proyek ini mengadopsi pola **Modular Monolith** dengan pemisahan *concern* (pemisahan tanggung jawab) menggunakan arsitektur **MVC + Service Layer & Repository Pattern**.

```text
OCR_Project_Ubuntu/
├── app.py                   # Entry point aplikasi Flask, inisialisasi konfigurasi, dan register Blueprint.
├── core_engine.py           # Mesin utama (Core Engine) untuk logika OCR Multiprocessing (PyMuPDF & Tesseract).
├── requirements.txt         # Daftar pustaka (dependencies) Python.
├── pytest.ini               # Konfigurasi automated unit testing.
│
├── config/                  # Konfigurasi aplikasi dan runtime dinamis.
│   ├── settings.py          # Konfigurasi secret key, database URI, dan environment.
│   └── user_settings.json   # Konfigurasi dinamis OCR (DPI, bahasa, retry, folder paths).
│
├── models/                  # (Model) Definisi skema tabel database dan interaksinya.
│   ├── database.py          # Objek SQLAlchemy ORM.
│   ├── dashboard_model.py   # Repository pattern untuk query tabel riwayat (16 kolom).
│   ├── user_model.py        # Model entitas tabel users (Flask-Login & hashing).
│   └── model_provider.py    # Singleton model provider.
│
├── routes/                  # (Controller) Blueprint Flask, menangani HTTP request dan response.
│   ├── auth.py              # Endpoint login, logout, register, dan profil.
│   ├── dashboard.py         # Endpoint dasbor utama, monitoring, analitik, dan pengaturan.
│   ├── ocr.py               # Endpoint trigger /jalankan dan /stop proses OCR.
│   ├── folder.py            # Endpoint streaming penampil PDF aman (anti path traversal).
│   └── export.py            # Endpoint generator ekspor spreadsheet Excel.
│
├── services/                # (Service Layer) Modul logika bisnis independen.
│   ├── analytics_service.py # Kalkulasi metrik KPI, grafik tren harian, dan volume dokumen.
│   ├── ocr_service.py       # Wrapper abstraksi pemanggilan worker OCR.
│   ├── progress_service.py  # State tracking antrean dan sinyal pause/resume/stop.
│   ├── settings_service.py  # Manajemen pembacaan & penyimpanan user_settings.json.
│   └── system_service.py    # Streaming log terminal dan pembacaan kapasitas harddisk.
│
├── templates/               # (View) Antarmuka web pengguna Jinja2 templates.
│   ├── base.html            # Layout induk (sidebar, header, notifikasi).
│   ├── index.html           # Dasbor utama.
│   ├── monitoring.html      # Antrean aktif dan live terminal log.
│   ├── documents.html       # Penelusuran arsip dokumen dan pencarian multi-kolom.
│   ├── analytics.html       # Visualisasi grafik analitik bisnis dan kapasitas storage.
│   ├── settings.html        # Pengaturan OCR dan pencadangan database.
│   ├── login.html           # Form login autentikasi.
│   └── profile.html         # Pengelolaan profil pengguna.
│
├── static/                  # Berkas aset statis (CSS, JS, ikon, gambar).
├── tests/                   # Automated unit test suite (pytest).
├── logs/                    # Direktori log runtime dan snapshot JSON cadangan.
├── input_pdf/               # Direktori sumber dokumen input.
└── output_pdf/              # Direktori target dokumen Searchable PDF hasil konversi.
```

---

## 4. Alur Kerja Sistem (Pipeline Workflow)

1. **Pemicuan Proses:** Pengguna menekan tombol "Mulai OCR" pada antarmuka web, yang memicu endpoint `POST /jalankan` di `routes/ocr.py`.
2. **Background Thread:** Request HTTP segera dijawab dan proses OCR dijalankan di latar belakang (*background daemon thread*) sehingga browser tidak pernah mengalami timeout.
3. **Multiprocessing Execution:** `core_engine.py` membuat `ProcessPoolExecutor` dengan worker paralel `os.cpu_count() - 1` untuk memproses antrean dokumen secara bersamaan.
4. **Optimasi Smart Skip & Lanczos:** Tiap halaman diperiksa apakah mengandung teks digital asli. Jika skema diagram buram, sistem menerapkan Lanczos 2.5x upscaling dan mode fallback `--psm 11`.
5. **Pencatatan Metadata:** Hasil OCR diinjeksikan menjadi Searchable PDF, disimpan di `output_pdf/`, dan metadata 16 kolom dicatat ke tabel `riwayat` di MySQL.
6. **Live Monitoring:** Frontend secara berkala melakukan polling asinkron (AJAX) ke `/api/monitoring` untuk menyajikan progres antrean dan baris terminal log secara real-time.
