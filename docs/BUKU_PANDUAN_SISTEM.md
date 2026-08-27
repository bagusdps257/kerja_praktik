# 📘 BUKU PANDUAN PENGGUNA DAN TEKNIS SISTEM
## Intelligent OCR & Document Management System (DMS) Web
**PT Jawa Satu Power — PLTGU Jawa-1**

---

> **Tentang Buku Panduan Ini:**  
> Buku panduan ini disusun sebagai dokumen rujukan resmi pengoperasian dan pemeliharaan sistem digitalisasi arsip *Intelligent OCR & DMS*. Panduan ini dirancang dengan bahasa yang komunikatif, visual, dan terstruktur agar mudah dipahami baik oleh **pengguna umum (operator arsip/staf non-IT)** maupun oleh **mentor teknik dan pengembang perangkat lunak (IT Engineer/Developer)**.

---

## 📑 DAFTAR ISI

1. [BAGIAN 1: PENGENALAN SISTEM](#bagian-1-pengenalan-sistem)
   - 1.1 Apa itu Sistem Intelligent OCR DMS?
   - 1.2 Manfaat dan Keunggulan Utama
   - 1.3 Alur Kerja Dokumen (High-Level Workflow)
2. [BAGIAN 2: PANDUAN PENGOPERASIAN (UNTUK PENGGUNA UMUM)](#bagian-2-panduan-pengoperasian-untuk-pengguna-umum)
   - 2.1 Akses Sistem dan Login Akun
   - 2.2 Mempersiapkan Berkas Dokumen (Folder Input)
   - 2.3 Menjalankan dan Menghentikan Proses OCR
   - 2.4 Memantau Antrean dan Log Terminal (Menu Monitoring)
   - 2.5 Mencari, Memfilter, dan Membuka Searchable PDF (Menu Dokumen)
   - 2.6 Mengekspor Laporan ke Spreadsheet Excel (.xlsx)
   - 2.7 Membaca Analitik Kinerja dan Ekspor PDF (Menu Analytics)
   - 2.8 Mengubah Konfigurasi OCR dan Mencadangkan Data (Menu Settings)
3. [BAGIAN 3: PANDUAN ARSITEKTUR & TEKNIS (UNTUK MENTOR / TIM IT)](#bagian-3-panduan-arsitektur--teknis-untuk-mentor--tim-it)
   - 3.1 Ringkasan Tech Stack & Dependensi
   - 3.2 Pola Arsitektur Perangkat Lunak (MVC + Service Layer)
   - 3.3 Struktur Direktori Proyek Lengkap
   - 3.4 Mekanisme Kerja Core OCR Multiprocessing Engine
   - 3.5 Logika Optimasi: Smart Skip & Dual-Pass Lanczos Upscaling
   - 3.6 Skema Database MySQL (Users & Riwayat 16 Kolom)
   - 3.7 Aspek Keamanan Sistem (Security Measures)
4. [BAGIAN 4: PANDUAN DEPLOYMENT & PEMELIHARAAN SERVER](#bagian-4-panduan-deployment--pemeliharaan-server)
   - 4.1 Persyaratan Server (Hardware & Software)
   - 4.2 Langkah Instalasi di Linux Ubuntu Server
   - 4.3 Menjalankan Sistem di Latar Belakang (Gunicorn / Systemd)
   - 4.4 Prosedur Pencadangan (*Backup*) dan Pemulihan (*Restore*) Database
   - 4.5 Menjalankan Pengujian Otomatis (*Automated Unit Testing*)
5. [BAGIAN 5: PANDUAN PENYELESAIAN MASALAH (TROUBLESHOOTING & FAQ)](#bagian-5-panduan-penyelesaian-masalah-troubleshooting--faq)

---

# BAGIAN 1: PENGENALAN SISTEM

## 1.1 Apa itu Sistem Intelligent OCR DMS?
**Intelligent OCR & Document Management System (DMS)** adalah perangkat lunak terpadu berbasis web yang dirancang khusus untuk mengotomatisasi pengalihan dokumen arsip fisik (berkas kertas hasil *scan* atau gambar diagram teknik) menjadi **Searchable PDF** (dokumen PDF yang teksnya dapat dicari dengan `Ctrl + F`, disorot, dan disalin).

Sistem ini beroperasi secara **100% On-Premise** di server lokal PT Jawa Satu Power tanpa mengirimkan data keluar jaringan perusahaan, sehingga kerahasiaan diagram skema dan arsip pembangkit tetap terjamin aman.

```
┌─────────────────┐       ┌────────────────────────┐       ┌────────────────────────┐
│  Folder Input   │ ───►  │  Intelligent OCR Core  │ ───►  │     Folder Output      │
│  (PDF Scan/JPG) │       │  (Tesseract + PyMuPDF) │       │ (Searchable PDF + DB)  │
└─────────────────┘       └────────────────────────┘       └────────────────────────┘
```

---

## 1.2 Manfaat dan Keunggulan Utama
* ⚡ **Eksekusi Cepat dengan Multiprocessing:** Memanfaatkan seluruh *core* CPU server secara paralel untuk memproses ratusan berkas sekaligus.
* 🧠 **Smart Skip (Hemat Waktu):** Dokumen yang sudah mengandung teks digital asli tidak di-OCR ulang, menghemat waktu proses hingga 80%.
* 📐 **Lanczos Dual-Pass OCR:** Mampu membaca teks kecil dan diagram teknik pembangkit listrik (*Single Line Diagram*) dengan mode segmentasi adaptif.
* 📊 **Analitik & Pelaporan Terintegrasi:** Menyajikan statistik tingkat keberhasilan, grafik volume, pemantauan kapasitas penyimpanan harddisk, dan ekspor laporan resmi (.xlsx & .pdf).
* 🔒 **Keamanan Ketat Berstandar Industri:** Proteksi brute-force, hash password `scrypt`, perlindungan CSRF, dan validasi anti *Path Traversal*.

---

# BAGIAN 2: PANDUAN PENGOPERASIAN (UNTUK PENGGUNA UMUM)

## 2.1 Akses Sistem dan Login Akun
1. Buka peramban web (*Google Chrome, Microsoft Edge, atau Mozilla Firefox*).
2. Masukkan alamat URL server (misal: `http://192.168.1.100:5000` atau `http://localhost:5000`).
3. Pada halaman Login:
   * Masukkan **Username** dan **Password** administrator Anda.
   * Klik tombol **"Masuk ke Sistem"**.

> 💡 **Catatan Registrasi Akun:**  
> Untuk menjaga keamanan internal, registrasi akun publik akan **otomatis terkunci** begitu akun administrator utama telah dibuat di sistem.

---

## 2.2 Mempersiapkan Berkas Dokumen (Folder Input)
1. Salin berkas PDF pindaian atau citra gambar yang ingin di-OCR ke dalam folder input server (default: `input_pdf/`).
2. **Struktur Subfolder:** Anda bebas membuat subfolder di dalam folder input (misal: `input_pdf/Turbin_2026/Laporan_Inspeksi/`). Sistem akan secara otomatis mendeteksi hingga ke subfolder terdalam dan mereplikasi struktur folder yang sama persis di folder hasil (*mirror folder tree*).
3. **Format yang Didukung:** `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, `.webp`.

---

## 2.3 Menjalankan dan Menghentikan Proses OCR

### A. Memulai Proses OCR
1. Buka halaman **Dasbor Utama** (klik menu *Dashboard* di sidebar kiri).
2. Periksa kartu status: pastikan folder input telah mendeteksi jumlah berkas dokumen.
3. Klik tombol biru besar: **"Mulai OCR"**.
4. Sistem akan langsung mengalihkan Anda ke halaman **OCR Monitoring** dan memulai konversi di latar belakang.

### B. Menghentikan Proses OCR (Stop)
1. Jika sewaktu-waktu Anda perlu membatalkan proses yang sedang berjalan, kembali ke halaman **Dasbor Utama**.
2. Klik tombol merah **"Stop"**.
3. Dialog konfirmasi akan muncul; klik **"Hentikan Proses"**.
4. Mesin OCR akan segera menyelesaikan halaman aktif saat itu dan menghentikan antrean secara aman (*graceful stop*).

---

## 2.4 Memantau Antrean dan Log Terminal (Menu Monitoring)
Buka menu **OCR Monitoring** di sidebar untuk melihat progres kerja sistem secara langsung (*real-time*):

```
┌─────────────────────────────────────────────────────────────┐
│ 📺 Log Terminal Konsol (ocr_worker_node_alpha.log)          │
│ [INFO] Memproses: Turbin_Unit1_Manual.pdf (Halaman 3/12)   │
│ [SUCCESS] Halaman 3 selesai dalam 1.2 detik (Akurasi: 96%)  │
│                                           [Auto-scroll: ON] │
├─────────────────────────────────────────────────────────────┤
│ 📋 Antrean Aktif (Active Queue)                             │
│ • Diagram_Kelistrikan.pdf ── [PROCESSING] [████████░░] 65%  │
│ • Manual_Generator_2026.pdf ── [QUEUED] Tunggu giliran...    │
│                                                             │
│ ⏸️ [Tombol Jeda Antrean]                                    │
└─────────────────────────────────────────────────────────────┘
```

* **Terminal Log Live:** Menampilkan baris catatan proses terkini. Anda dapat mengklik tombol **Auto-scroll ON/OFF** di pojok kanan atas log untuk membaca log sebelumnya tanpa tergeser otomatis.
* **Kartu Antrean Aktif:** Menampilkan berkas mana yang sedang aktif diproses oleh *worker*, nomor halaman, dan progress bar.
* **Tombol Jeda Antrean (*Pause Queue*):** Klik tombol ini jika ingin menunda proses berkas berikutnya tanpa mematikan proses berkas yang sedang berjalan. Klik kembali untuk melanjutkan (*Resume*).

---

## 2.5 Mencari, Memfilter, dan Membuka Searchable PDF (Menu Dokumen)
Buka menu **Kelola Dokumen** di sidebar untuk mengelola seluruh arsip hasil konversi:

1. **Pencarian Cepat (*Instant Search*):** Ketik kata kunci pada kotak pencarian (bisa berupa nama berkas, subjek, nama penulis/author, atau kata kunci teks dokumen). Tekan *Enter* atau klik ikon cari.
2. **Filter Fleksibel:**
   * **Filter Status:** Pilih *Semua Status*, *Sukses*, *Gagal*, atau *Dilewati (Skip)*.
   * **Filter Rentang Waktu:** Pilih *Semua Waktu*, *Hari Ini*, *7 Hari Terakhir*, *Pilih Bulan*, atau *Pilih Tahun*.
   * **Pagination:** Pilih menampilkan 10, 25, 50, atau 100 dokumen per halaman.
3. **Membuka Dokumen Searchable PDF:**
   * Klik tombol **"Lihat PDF"** (ikon mata) di baris dokumen.
   * File PDF hasil OCR akan terbuka di tab baru peramban web. Anda dapat langsung menekan `Ctrl + F` untuk mencari kata di dalam dokumen dan menyalin teksnya!
4. **Mengunduh PDF:**
   * Klik tombol **"Unduh"** (ikon download) untuk menyimpan file PDF langsung ke komputer lokal Anda.

---

## 2.6 Mengekspor Laporan ke Spreadsheet Excel (.xlsx)
1. Buka menu **Kelola Dokumen**.
2. Anda dapat memfilter status atau periode data terlebih dahulu jika hanya ingin mengekspor laporan tertentu.
3. Klik tombol hijau **"Ekspor Excel"** di pojok kanan atas.
4. Peramban web akan otomatis mengunduh berkas spreadsheet `.xlsx` berisi lembar kerja **"Data Lengkap"** dengan 13 kolom metadata terformat rapi (Waktu, Nama Berkas, Status dengan warna badge, Durasi Proses, Retry Count, Ukuran, Jumlah Halaman, Author, Subject, Keywords, dan Tanggal Pembuatan).

---

## 2.7 Membaca Analitik Kinerja dan Ekspor PDF (Menu Analytics)
Buka menu **Analytics** di sidebar untuk memantau performa sistem dan pemakaian media simpan:

* **Ringkasan Kartu KPI:** Total Dokumen, Persentase Tingkat Keberhasilan (*Success Rate %*), Dokumen Gagal, Dokumen Dilewati, dan Rata-rata Waktu Proses per Dokumen.
* **Grafik Tren Harian (*Daily Trend Line Chart*):** Grafik perbandingan dokumen sukses vs gagal per hari.
* **Grafik Volume Dokumen (*Document Volume Bar Chart*):** Beban volume berkas per tanggal.
* **Top 5 Authors:** Pemeringkatan kontributor pembuat dokumen teraktif.
* **Penggunaan Penyimpanan (*Storage Breakdown*):** Diagram donat kapasitas harddisk server (persentase terpakai, jumlah GB terpakai vs total kapasitas disk, dan sisa ruang kosong).
* **Mencetak / Ekspor Laporan Analitik ke PDF:**  
  Klik tombol **"Ekspor PDF"** di pojok kanan atas untuk membuka jendela cetak (*print dialog*). Pilih tujuan *"Save as PDF"* untuk menyimpan laporan analitik grafis siap cetak.

---

## 2.8 Mengubah Konfigurasi OCR dan Mencadangkan Data (Menu Settings)
Buka menu **Settings** di sidebar untuk konfigurasi teknis:

1. **Pengaturan Mesin OCR:**
   * **Resolusi Rendering (DPI):** Rekomendasi 150 atau 200 DPI untuk kecepatan optimal, atau 300 DPI untuk cetakan buram.
   * **Bahasa OCR:** Pilih `ind` (Bahasa Indonesia), `eng` (Bahasa Inggris), atau `ind+eng` (Kombinasi bilingual).
   * **Batas Percobaan Ulang (*Max Retry*):** Jumlah toleransi percobaan ulang saat berkas mengalami kegagalan baca (default: 3 kali).
   * **Folder Path:** Mengubah lokasi folder input dan output server jika diperlukan.
2. **Pencadangan Database (*Backup SQL*):**
   * Klik tombol **"Cadangkan Data"** pada menu Dokumen atau Settings untuk mengunduh berkas `.sql` cadangan lengkap 16 kolom.
3. **Pembersihan Riwayat (*Reset Database*):**
   * Klik tombol **"Hapus Riwayat"**.
   * Masukkan **Password Akun Administrator** pada jendela konfirmasi.
   * Sistem akan otomatis membuat file snapshot cadangan JSON di folder server sebelum menghapus data dari MySQL.

---

# BAGIAN 3: PANDUAN ARSITEKTUR & TEKNIS (UNTUK MENTOR / TIM IT)

## 3.1 Ringkasan Tech Stack & Dependensi

| Layer / Komponen | Teknologi & Versi | Peran dalam Sistem |
|---|---|---|
| **Platform OS** | Ubuntu Server 22.04/24.04 LTS | Sistem operasi server produksi *on-premise* |
| **Runtime Language** | Python 3.12.x / 3.13.x | Bahasa pemrograman utama |
| **Web Framework** | Flask 3.0+ | Framework backend MVC |
| **WSGI Server** | Gunicorn 21.x+ | Production application server |
| **Database Server** | MySQL 8.0+ / MariaDB 10.5+ | Penyimpanan relasional tabel pengguna dan riwayat |
| **ORM & Driver** | SQLAlchemy & PyMySQL | Pemetaan objek database relasional |
| **Mesin OCR** | Tesseract OCR Engine v5.3.4 | Ekstraksi teks berbasis Neural Network LSTM |
| **PDF Rendering Core** | PyMuPDF (`fitz`) v1.23+ | Ekstraksi halaman, rasterisasi bitmap, dan *PDF injection* |
| **Image Processing** | Pillow (PIL) & OpenCV Headless | Pre-processing citra, konversi *grayscale*, Lanczos upscaling |
| **Spreadsheet Engine** | openpyxl v3.1+ | Generator berkas laporan Excel `.xlsx` multi-format |
| **Hardware Telemetry** | psutil v5.9+ | Pembacaan metrik kapasitas disk server |

---

## 3.2 Pola Arsitektur Perangkat Lunak (MVC + Service Layer)
Sistem menerapkan prinsip **Clean Architecture & SOLID** dengan memisahkan kode menjadi lapisan terisolasi:

```
[ View Layer: Jinja2 Templates + Vanilla CSS/JS ]
                     ▲
                     │ (HTTP Request / JSON API)
                     ▼
[ Controller Layer: Flask Blueprints (routes/) ]
  ├── routes/auth.py       --> Login, Register, Profile
  ├── routes/dashboard.py  --> Dasbor Utama, Monitoring, Analytics, Settings
  ├── routes/ocr.py        --> Trigger Mulai OCR & Sinyal Stop
  ├── routes/folder.py     --> Penampil PDF Terproteksi
  └── routes/export.py     --> Ekspor Spreadsheet Excel (.xlsx)
                     ▲
                     │ (Delegasi Logika Bisnis)
                     ▼
[ Service Layer: Independent Business Modules (services/) ]
  ├── services/ocr_service.py        --> Wrapper Pipeline OCR
  ├── services/progress_service.py   --> State Tracking & Queue Signal
  ├── services/analytics_service.py  --> Agregasi Statistik & Metrik KPI
  ├── services/system_service.py     --> Log Streaming & Disk Telemetry
  └── services/settings_service.py   --> Manajemen Konfigurasi JSON
                     ▲
                     │ (Eksekusi Komputasi / Database)
                     ▼
[ Engine & Data Layer ]
  ├── core_engine.py                 --> Multiprocessing Pool & Tesseract Engine
  ├── models/dashboard_model.py      --> Repository Pattern Database Riwayat
  └── models/user_model.py           --> Model Data Pengguna & Password Hashing
```

---

## 3.3 Struktur Direktori Proyek Lengkap

```text
OCR_Project_Ubuntu/
├── app.py                     # Entry point inisialisasi aplikasi Flask & Blueprints
├── core_engine.py             # Engine utama OCR multiprocessing & konversi PDF
├── pytest.ini                 # Konfigurasi automated unit testing
├── requirements.txt           # Daftar seluruh dependensi Python package
├── config/
│   ├── settings.py            # Konfigurasi variabel aplikasi dan database
│   └── user_settings.json     # Konfigurasi runtime dinamis (DPI, bahasa, path)
├── models/
│   ├── database.py            # Inisialisasi instance SQLAlchemy ORM
│   ├── dashboard_model.py     # Repository pattern untuk query tabel riwayat
│   ├── user_model.py          # Model entitas tabel users (Flask-Login & Hashing)
│   └── model_provider.py      # Provider instance singleton database
├── routes/
│   ├── auth.py                # Controller autentikasi (login, register, profile)
│   ├── dashboard.py           # Controller halaman utama, monitoring, settings
│   ├── folder.py              # Controller streaming penampil file PDF
│   ├── ocr.py                 # Controller endpoint trigger /jalankan dan /stop
│   └── export.py              # Controller generator laporan Excel
├── services/
│   ├── analytics_service.py   # Layanan kalkulasi statistik dan tren analitik
│   ├── ocr_service.py         # Layanan abstraksi worker OCR
│   ├── progress_service.py    # Layanan manajemen state antrean (pause/resume/stop)
│   ├── settings_service.py    # Layanan pembacaan & penyimpanan user_settings.json
│   └── system_service.py      # Layanan streaming log terminal dan disk storage
├── static/
│   ├── css/style.css          # Desain antarmuka modern (Dark-accent, Glassmorphism)
│   └── js/                    # Modul JavaScript frontend (polling, toast, chart)
├── templates/
│   ├── base.html              # Template induk layout, sidebar, dan header
│   ├── index.html             # Halaman dasbor utama
│   ├── monitoring.html        # Halaman antrean aktif dan live terminal log
│   ├── documents.html         # Halaman penelusuran riwayat berkas
│   ├── analytics.html         # Halaman dasbor analitik bisnis & storage
│   ├── settings.html          # Halaman pengaturan sistem & database
│   ├── login.html             # Halaman form login
│   └── profile.html           # Halaman manajemen profil pengguna
├── tests/                     # Suite pengujian otomatis (11 Unit Tests)
├── logs/                      # Direktori file log runtime dan auto-backup JSON
├── input_pdf/                 # Direktori sumber berkas input
└── output_pdf/                # Direktori hasil berkas Searchable PDF
```

---

## 3.4 Mekanisme Kerja Core OCR Multiprocessing Engine
Proses OCR dijalankan di latar belakang menggunakan `concurrent.futures.ProcessPoolExecutor` dengan alokasi worker sebanyak `(os.cpu_count() - 1)` worker:

1. **Scanning Rekursif:** Sistem memindai `input_pdf/` dan menyusun daftar seluruh berkas yang valid.
2. **Pengurutan Antrean (Smallest File First):** Berkas diurutkan berdasarkan ukuran terkecil terlebih dahulu untuk meminimalkan *latency* antrean.
3. **Penyebaran Task Paralel:** Setiap berkas didelegasikan ke worker proses terpisah sehingga komputasi rendering dan OCR terdistribusi merata di seluruh inti CPU.
4. **Thread-Safe Database Writing:** Pencatatan hasil ekstraksi ke database MySQL dilakukan secara terpusat oleh *main thread* dengan mekanisme *Exponential Backoff Retry* untuk menghindari konflik *row locking*.

---

## 3.5 Logika Optimasi: Smart Skip & Dual-Pass Lanczos Upscaling

### A. Algoritma Smart Skip (Deteksi Teks Digital Asli)
Sebelum menjalankan rendering bitmap dan memanggil engine Tesseract:
```python
# Pemeriksaan teks digital pada halaman PDF asli
page = doc[page_num]
text = page.get_text("text")
images = page.get_images()

if len(text.strip()) > 100 and len(images) == 0:
    # Dokumen adalah digital native (bukan hasil scan)
    # Halaman asli langsung disalin tanpa OCR (Smart Skip)
```

### B. Algoritma Lanczos Dual-Pass OCR (Diagram Pembangkit)
Untuk berkas gambar skema diagram teknik:
1. **Pass 1 (Segmentasi Standar):** Sistem menjalankan OCR dengan mode Tesseract `--psm 3`.
2. **Pass 2 Fallback (Sparse Text):** Jika hasil pembacaan Pass 1 menghasilkan $< 3$ karakter, sistem otomatis menerapkan pembesaran gambar **Lanczos Upscaling 2.5x**, filter kontras 1.5x, dan mengeksekusi ulang OCR dengan mode `--psm 11` (*Sparse Text Detection*) agar teks pada kotak simbol diagram kelistrikan dapat terekstraksi sempurna.

---

## 3.6 Skema Database MySQL (Users & Riwayat 16 Kolom)

### A. Tabel `users` (Tabel Akun Pengguna)
| Kolom | Tipe Data | Keterangan |
|---|---|---|
| `id` | `INT AUTO_INCREMENT PRIMARY KEY` | ID unik pengguna |
| `username` | `VARCHAR(80) UNIQUE NOT NULL` | Nama pengguna untuk login |
| `password` | `VARCHAR(255) NOT NULL` | Password ter-hash (`scrypt` / `pbkdf2`) |
| `created_at` | `DATETIME DEFAULT CURRENT_TIMESTAMP` | Waktu pembuatan akun |
| `last_login` | `DATETIME NULL` | Waktu terakhir berhasil login |

### B. Tabel `riwayat` (Tabel Riwayat Metadata OCR 16 Kolom)
| No | Kolom | Tipe Data | Keterangan |
|:---:|---|---|---|
| 1 | `id` | `INT AUTO_INCREMENT PRIMARY KEY` | Primary key rekaman |
| 2 | `nama_file` | `VARCHAR(255) NOT NULL` | Nama berkas dokumen |
| 3 | `waktu` | `DATETIME NOT NULL` | Waktu pertama kali diproses |
| 4 | `status` | `VARCHAR(50) NOT NULL` | Status (`SUKSES`, `GAGAL`, `SKIP`) |
| 5 | `folder_path` | `TEXT NULL` | Jalur subdirektori relatif berkas |
| 6 | `processing_time` | `FLOAT DEFAULT 0.0` | Durasi pemrosesan (detik) |
| 7 | `retry_count` | `INT DEFAULT 0` | Jumlah percobaan ulang |
| 8 | `keterangan` | `TEXT NULL` | Pesan log atau ringkasan hasil |
| 9 | `file_size` | `VARCHAR(50) NULL` | Ukuran berkas (misal: "2.4 MB") |
| 10 | `page_count` | `INT DEFAULT 1` | Jumlah halaman dokumen |
| 11 | `updated_waktu` | `DATETIME NULL` | Timestamp pemrosesan terakhir |
| 12 | `error_type` | `VARCHAR(100) NULL` | Klasifikasi error jika gagal |
| 13 | `author` | `VARCHAR(255) NULL` | Nama pembuat / penulis dokumen |
| 14 | `creation_date` | `VARCHAR(100) NULL` | Tanggal pembuatan asli dokumen |
| 15 | `subject` | `TEXT NULL` | Subjek / perihal isi dokumen |
| 16 | `keywords` | `TEXT NULL` | Kata kunci dokumen yang terindeks |

---

## 3.7 Aspek Keamanan Sistem (Security Measures)
* 🛡️ **Proteksi Path Traversal:** Rute penampil PDF `/lihat_pdf/<filename>` memvalidasi jalur berkas menggunakan fungsi bawaan Python `os.path.commonpath([target_path, output_dir]) == output_dir`. Percobaan manipulasi URL seperti `../../etc/passwd` akan langsung diblokir (*HTTP 403 Forbidden*).
* 🔑 **Password Hashing Modern:** Seluruh kata sandi diproteksi algoritma satu arah `scrypt` / `pbkdf2:sha256` dengan *salt* acak sehingga aman terhadap serangan *rainbow table*.
* 🛑 **Perlindungan CSRF:** Setiap form web dan pemanggilan API `POST` dilindungi oleh token CSRF unik (`flask_wtf.csrf.CSRFProtect`).
* 📦 **Isolasi Variabel Lingkungan:** Kredensial database dan kunci rahasia sesi diisolasi dalam berkas `.env` yang dikecualikan dari Git repository (`.gitignore`).

---

# BAGIAN 4: PANDUAN DEPLOYMENT & PEMELIHARAAN SERVER

## 4.1 Persyaratan Server (Hardware & Software)
* **Sistem Operasi:** Ubuntu Server 22.04 LTS atau 24.04 LTS (x86_64).
* **Processor (CPU):** Minimal 2 Core vCPU (Rekomendasi: 4–8 Core untuk efisiensi multiprocessing).
* **Memori (RAM):** Minimal 4 GB RAM.
* **Penyimpanan:** Minimal 20 GB SSD (disesuaikan dengan volume arsip PDF yang disimpan).
* **Database:** MySQL Server 8.0+ / MariaDB 10.5+.

---

## 4.2 Langkah Instalasi di Linux Ubuntu Server

Buka terminal SSH (PuTTY) ke server Ubuntu, lalu jalankan perintah berikut secara berurutan:

```bash
# 1. Update repository dan instal paket sistem yang dibutuhkan
sudo apt update && sudo apt install -y python3 python3-pip python3-venv \
    tesseract-ocr tesseract-ocr-ind tesseract-ocr-eng \
    libgl1-mesa-glx libglib2.0-0 mysql-server

# 2. Masuk ke direktori proyek
cd ~/OCR_Project

# 3. Buat dan aktifkan virtual environment Python
python3 -m venv env
source env/bin/activate

# 4. Instal seluruh library dependensi Python
pip install --upgrade pip
pip install -r requirements.txt

# 5. Konfigurasi file lingkungan (.env)
cp .env.example .env
nano .env
# Sesuaikan SECRET_KEY dan koneksi DATABASE_URI MySQL Anda
```

---

## 4.3 Menjalankan Sistem di Latar Belakang (Gunicorn / Systemd)

Untuk menjalankan sistem secara permanen di server produksi:

### Opsi A: Menjalankan via Gunicorn (Terminal)
```bash
source env/bin/activate
gunicorn -w 4 -b 0.0.0.0:5000 app:app --timeout 300
```

### Opsi B: Membuat Service Otomatis (Systemd Service)
Buat file service di `/etc/systemd/system/ocr.service`:
```ini
[Unit]
Description=Gunicorn instance to serve OCR DMS Web System
After=network.target mysql.service

[Service]
User=magang
WorkingDirectory=/home/magang/OCR_Project
Environment="PATH=/home/magang/OCR_Project/env/bin"
ExecStart=/home/magang/OCR_Project/env/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app --timeout 300
Restart=always

[Install]
WantedBy=multi-user.target
```

Aktifkan dan jalankan service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ocr
sudo systemctl start ocr
sudo systemctl status ocr
```

---

## 4.4 Prosedur Pencadangan (*Backup*) dan Pemulihan (*Restore*) Database

### A. Pencadangan (*Backup Database*)
* **Cara 1 (Melalui Web):** Klik tombol **"Cadangkan Data"** pada menu *Documents* atau *Settings* untuk mengunduh file `.sql` langsung.
* **Cara 2 (Melalui Terminal MySQL):**
  ```bash
  mysqldump -u root -p ocr_database > backup_ocr_$(date +%Y%m%d).sql
  ```

### B. Pemulihan (*Restore Database*)
Jika terjadi kegagalan server dan data perlu dikembalikan:
```bash
mysql -u root -p ocr_database < backup_ocr_20260826.sql
```

---

## 4.5 Menjalankan Pengujian Otomatis (*Automated Unit Testing*)
Sebelum melakukan pembaruan kode ke server produksi, jalankan seluruh suite pengujian otomatis untuk memastikan seluruh modul berfungsi 100%:

```bash
# Pastikan virtual environment aktif
source env/bin/activate

# Jalankan pengujian pytest
pytest tests/ -v
```

Hasil uji yang diharapkan: **11/11 tests PASSED (100% Berhasil)**:
```text
tests/test_analytics.py::test_system_service_metrics PASSED      [  9%]
tests/test_analytics.py::test_safe_float_helper PASSED           [ 18%]
tests/test_auth.py::test_user_password_hashing PASSED            [ 27%]
tests/test_auth.py::test_duplicate_username_rejected PASSED      [ 36%]
tests/test_auth.py::test_login_and_logout_flow PASSED            [ 45%]
tests/test_auth.py::test_registration_lockdown_when_user_exists PASSED [ 54%]
tests/test_database.py::test_catat_ke_db_create_and_update PASSED [ 63%]
tests/test_export.py::test_export_excel_structure PASSED         [ 72%]
tests/test_security.py::test_safe_path_traversal_logic PASSED    [ 81%]
tests/test_security.py::test_unauthenticated_access_blocked PASSED [ 90%]
tests/test_settings.py::test_settings_load_and_save PASSED       [100%]
============================== 11 passed in 1.15s ==============================
```

---

# BAGIAN 5: PANDUAN PENYELESAIAN MASALAH (TROUBLESHOOTING & FAQ)

### ❓ T: Mengapa dokumen PDF tertentu sangat cepat selesai (hanya 0.1 detik)?
> **Jawab:** Sistem menerapkan optimasi **Smart Skip**. Jika dokumen tersebut adalah dokumen PDF digital asli (bukan hasil scan gambar), sistem tidak perlu melakukan render OCR ulang, melainkan langsung menyalinnya ke folder output sehingga menghemat waktu proses.

---

### ❓ T: Bagaimana jika ada kata sandi admin yang lupa?
> **Jawab:** Administrator server dapat mereset kata sandi melalui terminal Python:
> ```bash
> source env/bin/activate
> python3 -c "from app import create_app; from models.database import db; from models.user_model import User; from werkzeug.security import generate_password_hash; app=create_app(); app.app_context().push(); u=User.query.filter_by(username='admin').first(); u.password=generate_password_hash('PasswordBaru123'); db.session.commit(); print('Password berhasil direset!')"
> ```

---

### ❓ T: Mengapa halaman registrasi akun baru tidak dapat dibuka?
> **Jawab:** Ini adalah fitur **Security Lockdown**. Sistem secara sengaja mengunci form pendaftaran jika sudah terdapat minimal 1 akun di database. Jika Anda ingin membuka kembali registrasi, ubah `ALLOW_REGISTRATION=true` di file `.env`.

---

### ❓ T: Mengapa teks pada diagram kelistrikan yang kecil tetap terbaca jelas?
> **Jawab:** Sistem mengimplementasikan algoritma **Dual-Pass OCR dengan Lanczos Smart Upscaling**. Saat teks standar tidak terbaca, sistem memperbesar piksel gambar skema hingga 2.5x dan menggunakan mode deteksi teks renggang (`--psm 11`).

---

<br>

**Disusun dan Diverifikasi oleh:**  
*Bagus Dwi Putra Setiawan* — Mahasiswa Kerja Praktik  
Departemen IT & Engineering — **PT Jawa Satu Power**  
*Agustus 2026*
