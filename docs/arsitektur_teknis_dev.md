# 🛠️ Arsitektur Teknis Lengkap Sistem OCR (Developer Documentation)

Dokumen ini berisi spesifikasi arsitektur teknis lengkap, diagram komponen, diagram alur data, model konkurensi, dan skema database untuk tim pengembang (*Software Engineers / Developers*).

---

## 1. Topologi Sistem & Arsitektur Tingkat Tinggi (Context - Level 1)

Sistem ini mengadopsi pola **Modular Monolith** dengan eksekusi *asynchronous* berbasis *Daemon Thread* dan *Multiprocessing Worker Pool* untuk menangani beban komputasi OCR yang intensif (*CPU-bound*).

```mermaid
flowchart TD
    devUser["👤 Web Client / User<br/>(Mengakses antarmuka web, mengatur berkas, monitor proses)"]
    ocrSystem["🚀 OCR Management System - Flask<br/>(Routing, Autentikasi, Antrean, Orkestrator OCR)"]
    tesseract["⚙️ Tesseract OCR Engine - Binary C++<br/>(Ekstraksi Teks Gambar)"]
    dbMySQL[("🗄️ MySQL Database<br/>(Users, Metadata, Log Riwayat)")]
    fileStorage[("📂 Local File System<br/>(input_pdf, output_pdf, logs, state JSON)")]

    devUser -->|"HTTP / AJAX Requests"| ocrSystem
    ocrSystem -->|"SQL Queries (PyMySQL/SQLAlchemy)"| dbMySQL
    ocrSystem -->|"File I/O & State Persistence"| fileStorage
    ocrSystem -->|"Subprocess Wrapper (pytesseract)"| tesseract
```

---

## 2. Diagram Kontainer & Aliran Komponen (Container - Level 2)

Diagram ini menggambarkan pembagian 4 lapisan utama sistem secara terstruktur dan terisolasi:

```mermaid
graph TD
    Client["🌐 1. Presentation Layer<br/>(Jinja2 Web UI & AJAX Polling)"]
    
    subgraph WebServer["🚀 2. Flask Application Server (MVC Layer)"]
        Routes["Routes / Blueprints<br/>(auth, dashboard, ocr, folder, export)"]
        Services["Business Services<br/>(progress, metadata, settings, log)"]
        Models["Data Models & ORM<br/>(User & Riwayat Model)"]
        
        Routes --> Services
        Routes --> Models
    end

    subgraph AsyncCore["⚡ 3. OCR Background Processing Engine"]
        Orchestrator["Daemon Thread & Task Dispatcher<br/>(core_engine.jalankan_sistem_ocr)"]
        Workers["Multiprocessing OCR Workers<br/>(PyMuPDF + Pillow Preprocess + Tesseract)"]
        
        Orchestrator --> Workers
    end

    subgraph Persistence["💾 4. Storage & Database Layer"]
        MySQL[("MySQL Database<br/>(Users, Riwayat, Metadata)")]
        FileStorage[("File System Storage<br/>(input_pdf / output_pdf)")]
        RuntimeState["IPC State & Signals<br/>(ocr_runtime_state.json / ocr_stop.signal)"]
    end

    %% Aliran Antar-Lapisan
    Client -->|"HTTP Request & Live Progress Polling"| Routes
    Routes -->|"Trigger OCR / Send Stop Signal"| Orchestrator
    Services <-->|"Read / Write State"| RuntimeState
    Models <-->|"Database Queries"| MySQL
    Workers -->|"Read Raw & Write Searchable PDF"| FileStorage
    Workers -->|"Persist OCR Result Log"| Models
```

### 📌 Ringkasan Peran 4 Kontainer Utama:
1. **Presentation Layer (Browser):** Antarmuka web pengguna untuk memicu pengerjaan, mengatur folder, dan melakukan *live progress polling* via AJAX.
2. **Flask Application Server (MVC):** Mengatur otentikasi sesi, memvalidasi input, menyediakan endpoint REST/AJAX, dan memisahkan logika bisnis (*Services*) dari akses data (*Models*).
3. **OCR Processing Engine:** Bekerja di latar belakang (*background daemon thread*) dan mendistribusikan berkas ke *worker pool multiprocessing* untuk eksekusi OCR tanpa memblokir server web.
4. **Storage & Persistence Layer:** Menyimpan relasi data di MySQL, berkas fisik PDF/gambar di *file system*, serta status runtime untuk koordinasi antar-proses (IPC).

---

## 3. Alur Kerja Pemrosesan Dokumen & Konkurensi

### A. Sequence Diagram: Eksekusi OCR Asinkronus

```mermaid
sequenceDiagram
    autonumber
    actor Client as Web Client
    participant Route as routes/ocr.py
    participant Thread as Daemon Thread
    participant Engine as core_engine.py
    participant Worker as Multiprocess Worker
    participant State as services/progress_service.py
    participant DB as models/dashboard_model.py

    Client->>Route: POST /jalankan (input_dir, output_dir)
    Route->>State: ambil_progress() (Cek status saat ini)
    Route->>Thread: Inisialisasi threading.Thread(target=jalankan_sistem_ocr)
    Route->>Thread: thread.start()
    Route-->>Client: 302 Redirect / Return JSON OK

    par Background Execution
        Thread->>Engine: jalankan_sistem_ocr(input_dir, output_dir)
        Engine->>State: mulai(total_dokumen) -> update status=RUNNING
        loop Iterasi File dalam Direktori
            Engine->>Engine: Cek is_stop_requested()
            Engine->>Worker: Dispatch _ocr_worker_task(file_args)
            Worker->>Worker: Validasi & Ekstraksi (Smart Skip / Tesseract)
            Worker->>Worker: Simpan Output File ke Disk
            Worker-->>Engine: Return Task Result (Status, Metadata, SHA256)
            Engine->>DB: simpan_riwayat() -> INSERT / UPDATE riwayat
            Engine->>State: update_progress(selesai, force=False)
        end
        Engine->>State: selesai() -> status=FINISHED (100%)
    and Client Polling
        loop Setiap 1-2 Detik
            Client->>Route: GET /progress / API Poll
            Route->>State: ambil_progress()
            State-->>Route: Return Progress JSON State
            Route-->>Client: 200 OK (Data Progress)
        end
    end
```

---

## 4. Pipeline Pemrosesan Dokumen (Smart Skip & Image Preprocessing)

Setiap halaman dokumen dievaluasi menggunakan hierarki pemrosesan berkecepatan tinggi sebelum dikirim ke Tesseract:

```mermaid
flowchart TD
    Start(["File Masuk"]) --> CheckType{"Tipe File?"}
    
    CheckType -- ".pdf" --> OpenPDF["Buka dengan PyMuPDF (fitz)"]
    CheckType -- "Image (.png, .jpg, dll)" --> OpenImg["Buka dengan Pillow (PIL)"]
    
    subgraph PDF_Loop["Loop Setiap Halaman PDF"]
        OpenPDF --> PageInspect["Inspeksi Halaman: get_text & get_images"]
        PageInspect --> SmartSkipCheck{"Teks > 100 char & Jml Gambar == 0?"}
        
        SmartSkipCheck -- "YA (Smart Skip)" --> DirectCopy["Sisipkan Halaman Asli ke PDF Baru<br/>(Bypass OCR Engine)"]
        SmartSkipCheck -- "TIDAK" --> RenderPix["Render Page ke Pixmap (DPI Setting)"]
        RenderPix --> PILConvert["Konversi ke PIL Image"]
    end
    
    subgraph Preprocess["Pipeline Preprocessing Gambar"]
        OpenImg --> PILConvert
        PILConvert --> Gray["1. Convert ke Grayscale ('L')"]
        Gray --> Contrast["2. Enhance Contrast (Factor 1.5)"]
        Contrast --> Sharpen["3. Apply ImageFilter.SHARPEN"]
    end
    
    Sharpen --> TesseractExec["pytesseract.image_to_pdf_or_hocr<br/>Config: --psm 3 --oem 1"]
    TesseractExec --> PDFMerge["Insert Halaman Hasil OCR ke Dokumen Akhir"]
    DirectCopy --> PDFMerge
    
    PDFMerge --> SavePDF["Simpan PDF Baru (garbage=4, deflate=True, clean=True)"]
    SavePDF --> HashCalc["Hitung SHA-256 Checksum"]
    HashCalc --> End(["Selesai"])

    style SmartSkipCheck fill:#fff1b8,stroke:#d48806,stroke-width:2px
    style DirectCopy fill:#d9f7be,stroke:#52c41a,stroke-width:2px
    style TesseractExec fill:#ffd6e7,stroke:#eb2f96,stroke-width:2px
```

---

## 5. Entity-Relationship Diagram (Database Schema)

Database menggunakan relasi tabel berbasis **Flask-SQLAlchemy**:

```mermaid
erDiagram
    USERS ||--o{ RIWAYAT : "dikelola_oleh / logs"
    
    USERS {
        int id PK "Auto Increment"
        string username UK "Unique, Max 100"
        string password_hash "Werkzeug Hashed, Max 255"
        string created_at "ISO 8601 Timestamp"
        string last_login "ISO 8601 Timestamp"
    }

    RIWAYAT {
        int id PK "Auto Increment"
        string document_key "Relative Path / Key Identik (Max 255)"
        string folder_path "Subfolder Relative Path (Max 500)"
        string nama_file "Nama Berkas Asli (Max 255)"
        string status "SUKSES | GAGAL | SKIP (Max 50)"
        string waktu "Waktu Eksekusi (YYYY-MM-DD HH:MM:SS)"
        string updated_waktu "Waktu Update Terakhir"
        text keterangan "Pesan Status / Error Log"
        string file_size "Ukuran Berkas (Formatted)"
        string author "Metadata Author PDF"
        string page_count "Jumlah Halaman"
        string creation_date "Metadata Creation Date"
        float processing_time "Durasi Proses (Detik)"
        int retry_count "Jumlah Percobaan Ulang"
        string relative_path "Path Relatif Berkas"
        string file_hash "SHA-256 Checksum Berkas"
    }
```

---

## 6. Desain Konkurensi & Mekanisme Ketahanan (Resilience Patterns)

| Mekanisme | Implementasi Teknis | Tujuan Arsitektur |
| :--- | :--- | :--- |
| **Thread Isolation** | `os.environ['OMP_THREAD_LIMIT'] = '1'` | Mencegah *thread contention* dan *deadlock* antara C++ OpenMP (Tesseract) dan Python Threading/Multiprocessing. |
| **I/O Debouncing** | `_write_interval = 0.5s` pada `progress_service.py` | Mengurangi beban *disk thrashing* akibat penulisan file `ocr_runtime_state.json` yang terlalu sering. |
| **Atomic State Write** | Menulis ke `state.json.tmp` lalu `os.replace()` | Menghindari *race condition* atau *partial JSON read* saat klien melakukan polling bersamaan dengan update worker. |
| **Graceful Interruption** | `ocr_stop.signal` + `is_stop_requested()` polling | Memungkinkan penghentian proses OCR secara aman tanpa merusak berkas PDF yang sedang disimpan (*atomic file write*). |
| **Memory Management** | `with Image... as img:` + `.close()` & explicit garbage collection | Mencegah kebocoran memori RAM (*memory leaks*) saat memproses ratusan berkas gambar beresolusi tinggi. |
| **Retry Policy** | `maksimal_percobaan = max_retry (default 3)` | Otomatis mencoba ulang pemrosesan jika terjadi galat sesaat (*transient failure*) sebelum menandai status `GAGAL`. |
| **Self-Healing State** | Reset status otomatis di `routes/ocr.py` jika thread mati | Mencegah antarmuka web terkunci dalam status `RUNNING` abadi jika terjadi *unhandled crash*. |

---

## 7. Pemetaan Modul & Struktur Direktori

```text
OCR_Project/
├── app.py                      # Application Entry Point & Blueprint Registration
├── core_engine.py              # Core OCR Processing Engine (PyMuPDF, Pillow, Tesseract)
├── requirements.txt            # Python Dependencies Manifest
│
├── config/
│   └── settings.py             # Global Config (DB URI, Secret Key, Binary Paths)
│
├── models/                     # Data Layer (SQLAlchemy Models)
│   ├── extensions.py           # SQLAlchemy Instance Provider
│   ├── user_model.py           # User Authentication Model & Methods
│   ├── dashboard_model.py      # Riwayat Model & CRUD/Aggregation Queries
│   └── model_provider.py       # Singleton OCRDashboardModel Provider
│
├── routes/                     # Presentation/Controller Layer (Flask Blueprints)
│   ├── auth.py                 # Login, Logout, User Session Management
│   ├── dashboard.py            # Main Dashboard Metrics, Filter, Pagination
│   ├── ocr.py                  # Trigger Background OCR (/jalankan, /stop)
│   ├── folder.py               # Input/Output Path Config & Tree Browsing
│   └── export.py               # Excel (.xlsx) Report Generator (openpyxl)
│
├── services/                   # Business Logic & Infrastructure Layer
│   ├── progress_service.py     # Runtime State, Progress Tracker, Stop Signal
│   ├── metadata_service.py     # File Metadata Extraction (PyMuPDF/PIL)
│   ├── log_service.py          # Rotating File Logger
│   ├── settings_service.py     # Dynamic Settings Management & Path Resolution
│   └── storage_service.py      # Directory Traversal & Path Normalization
│
├── templates/                  # Jinja2 HTML Views
├── static/                     # Assets (CSS, JS, Fonts, Images)
└── logs/                       # Runtime Artifacts (state JSON, signals, log files)
```

---

## 8. Panduan Environment & Eksekusi

### Kebutuhan Dependensi:
* **Python Runtime:** Python 3.8+
* **Dependencies:** `Flask`, `Flask-SQLAlchemy`, `Flask-Login`, `Flask-WTF`, `PyMySQL`, `pytesseract`, `PyMuPDF (fitz)`, `Pillow`, `openpyxl`, `opencv-python-headless`.
* **System Binary:** `tesseract-ocr` dengan data bahasa `tessdata` untuk `ind` (Bahasa Indonesia) dan `eng` (Bahasa Inggris).

### Menjalankan Server:
```bash
# 1. Pastikan virtual environment aktif
source env/bin/activate  # Linux/macOS
# atau
.\env\Scripts\activate   # Windows

# 2. Install dependensi
pip install -r requirements.txt

# 3. Jalankan aplikasi Flask
python app.py
```

---
*Dokumen ini diperbarui secara berkala sesuai dengan evolusi codebase OCR_Project.*
