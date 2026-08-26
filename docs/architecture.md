# Arsitektur Proyek OCR (Optical Character Recognition)

Dokumen ini menjelaskan arsitektur perangkat lunak dari proyek **OCR Project** secara lengkap. Dokumen ini dapat Anda jadikan acuan untuk memahami alur kerja, struktur direktori, dan teknologi yang digunakan dalam sistem ini.

---

## 1. Tinjauan Sistem (System Overview)

Proyek ini adalah aplikasi web berbasis **Python (Flask)** yang berfungsi untuk mengekstraksi teks dari dokumen gambar atau PDF menggunakan teknologi Optical Character Recognition (OCR). Sistem ini membaca file yang diunggah ke dalam direktori tertentu, memprosesnya dengan **Tesseract OCR**, dan menyimpan hasilnya (PDF *searchable* atau teks) ke dalam direktori *output*. Aplikasi juga memiliki dasbor web untuk memonitor proses, mengelola riwayat OCR, dan manajemen pengguna (otentikasi).

---

## 2. Tech Stack (Teknologi yang Digunakan)

*   **Backend Framework**: [Flask](https://flask.palletsprojects.com/) (Python)
*   **Database ORM**: Flask-SQLAlchemy
*   **Database Engine**: SQLite (`ocr_database.db`)
*   **Mesin OCR**: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) melalui *wrapper* `pytesseract`
*   **Pemrosesan PDF**: [PyMuPDF](https://pymupdf.readthedocs.io/) (`fitz`)
*   **Pemrosesan Gambar**: Pillow (PIL)
*   **Autentikasi**: Flask-Login, Werkzeug Security
*   **Ekspor Data**: openpyxl (untuk mengekspor laporan excel/spreadsheet)
*   **Frontend**: HTML, CSS, JavaScript (via Jinja2 Templates)

---

## 3. Struktur Direktori Utama

Proyek ini mengadopsi pola **Modular Monolith** dengan pemisahan *concern* (pemisahan tanggung jawab) menggunakan arsitektur MVC (Model-View-Controller) yang dimodifikasi.

```text
OCR_Project/
│
├── app.py                   # Entry point aplikasi Flask, inisialisasi konfigurasi, dan register Blueprint.
├── core_engine.py           # Mesin utama (Core Engine) untuk logika OCR (PyMuPDF & Tesseract).
├── requirements.txt         # Daftar pustaka (dependencies) Python.
│
├── config/                  # Konfigurasi aplikasi (seperti pengaturan secret key, path Tesseract, konfigurasi DB).
│
├── models/                  # (Model) Definisi skema tabel database dan interaksinya.
│   ├── dashboard_model.py   # Model untuk menyimpan riwayat/history hasil OCR.
│   ├── user_model.py        # Model untuk entitas Pengguna (Users) dan autentikasi.
│   └── extensions.py        # Objek SQLAlchemy dan dependensi ekstensi Flask lainnya.
│
├── routes/                  # (Controller) Blueprint Flask, menangani HTTP request dan response.
│   ├── auth.py              # Endpoint login, logout.
│   ├── dashboard.py         # Endpoint dasbor utama dan statistik.
│   ├── ocr.py               # Endpoint untuk memicu / mengatur proses OCR.
│   ├── folder.py            # Endpoint untuk pengaturan folder input/output.
│   └── export.py            # Endpoint untuk mengekspor data hasil OCR.
│
├── services/                # Layanan bisnis (Business Logic Layer), menjembatani Routes dan Core/Model.
│   ├── log_service.py       # Menangani pencatatan aktivitas / error (logging).
│   ├── progress_service.py  # Menangani pelacakan progress persentase saat OCR berjalan.
│   ├── metadata_service.py  # Mengekstrak metadata dari file sebelum diproses.
│   └── settings_service.py  # Mengelola layanan pengaturan aplikasi.
│
├── templates/               # (View) File HTML (Jinja2) untuk UI dasbor.
├── static/                  # (View) Aset statis seperti CSS, JS, dan gambar untuk UI web.
│
├── database/                # Direktori penyimpanan file database lokal (SQLite).
│   └── ocr_database.db
│
├── InputZ/, input_pdf/, inputX/, inputERORx/  # Direktori folder tempat meletakkan file mentah (PDF/Gambar) yang akan di-OCR.
└── output_pdf/              # Direktori folder hasil pemrosesan (Searchable PDF atau Teks).
```

---

## 4. Alur Kerja Sistem (System Workflow)

### A. Alur Pemrosesan OCR (Backend Processing)
1. **Inisialisasi**: Pengguna (melalui antarmuka web di `/routes/ocr.py`) memicu proses OCR pada sebuah folder (misal `InputZ`).
2. **Validasi**: `core_engine.py` melakukan validasi awal (apakah folder input ada, apakah *executable* Tesseract terdeteksi).
3. **Ekstraksi**: `core_engine.py` memproses dokumen satu per satu:
    * Jika **PDF**: Membaca halaman demi halaman menggunakan `fitz` (PyMuPDF). Bila halaman hanya berisi teks, lewati OCR (optimasi). Bila berupa *scanned* dokumen/gambar, lakukan _preprocessing_ (mengubah *grayscale*, meningkatkan kontras) menggunakan `Pillow`.
    * Jika **Gambar**: Langsung ke tahap _preprocessing_.
4. **Penerjemahan (OCR)**: Gambar yang sudah melalui _preprocessing_ dikirim ke `pytesseract` untuk diubah menjadi PDF *searchable* atau sekadar teks mentah.
5. **Pencatatan & Progress**: Selama iterasi, `core_engine.py` akan terus mengirim sinyal ke `services/progress_service.py` untuk mengabarkan *progress* ke UI pengguna.
6. **Simpan Hasil**: Dokumen PDF keluaran disimpan ke dalam folder `output_pdf/` (dengan struktur yang sama persis dengan folder sumbernya).
7. **Pencatatan ke Database**: Informasi riwayat pengerjaan dokumen, seperti metadata dan status sukses/gagal disimpan ke database lewat `models/dashboard_model.py`.

### B. Alur Web MVC (Frontend & HTTP Flow)
1. **Request**: Pengguna mengakses *browser* (misalnya halaman dasbor utama).
2. **Route Handling**: Permintaan diterima oleh `app.py` dan diteruskan ke *Blueprint* yang sesuai, contoh: `routes/dashboard.py`.
3. **Autentikasi (Opsional)**: `Flask-Login` mencegat _request_ apabila *route* diatur dengan `@login_required`. Pengguna tak berizin diarahkan ke halaman _login_ (`routes/auth.py`).
4. **Data Fetching**: *Route* memanggil `dashboard_model.py` atau `services` untuk mengambil rekapan data.
5. **Response Rendering**: Data yang didapat diinjeksi ke dalam file HTML Jinja2 di dalam direktori `templates/` kemudian dikembalikan sebagai response HTML untuk pengguna.

---

## 5. Fitur Kunci & Optimasi Arsitektur
1. **Smart Skip OCR**: Algoritma cerdas dalam `core_engine.py` (`ekstrak_teks_dan_pdf`) memeriksa apakah PDF bawaan sudah mengandung teks (bukan hasil scan). Jika iya dan jumlah gambarnya 0, maka proses OCR yang memakan waktu akan dilewati (Smart Skip).
2. **Context Manager (Memory Optimization)**: Manajemen `Pillow Image` sangat memperhatikan *memory leak* dengan memanfaatkan instruksi `with Image... as img:` serta `.close()`.
3. **Asynchronous/Thread Awareness**: *Core engine* OCR dimonitor dalam servis sehingga sinyal `stop` secara asinkronus (interrupt) dapat ditangkap (`is_stop_requested()`). Tesseract juga dipaksa untuk menjalankan limitasi internal `OMP_THREAD_LIMIT = '1'` agar tidak bertabrakan dengan manajemen _thread_ bawaan Python.
4. **Decoupled Architecture**: Logika pemrosesan OCR yang tebal dipisah di `core_engine.py` (Domain Core). Logika web dipisah ke dalam `routes/`. Ini memudahkan pemeliharaan kode (Maintenance).

---

## 6. Persyaratan Menjalankan Proyek
Berdasarkan file `requirements.txt` dan konfigurasi kode, server yang akan di-deploy perlu memiliki:
* Python 3.7+
* Library dependencies dari `requirements.txt` (`pip install -r requirements.txt`)
* Terinstall program eksternal **Tesseract OCR** pada sistem operasi (Windows/Linux) dan path dikonfigurasi ke dalam config Flask (`config/settings.py`).

---
*Dokumen ini dibuat secara otomatis dengan merujuk langsung kepada kode sumber (source code) OCR_Project yang bersangkutan.*
