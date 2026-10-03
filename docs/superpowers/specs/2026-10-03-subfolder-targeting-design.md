# Technical Specification: Direct Subfolder Targeting in OCR Processing

## 1. Overview
Berdasarkan hasil bimbingan Kerja Praktik dengan Dosen Pembimbing, pemrosesan dokumen OCR harus dapat diarahkan secara spesifik ke subfolder tertentu (misalnya subfolder `input 17`), tanpa harus selalu memindai dan memeriksa seluruh berkas di folder induk.

Fitur ini memungkinkan pengguna (Operator & Staf) memilih cakupan pemrosesan (*Processing Scope*) langsung dari antarmuka dasbor:
1. **Seluruh Direktori Input (Semua Subfolder)** — Mode *default* untuk pemindaian menyeluruh.
2. **Subfolder Spesifik (Targeted Subfolder)** — Mode terarah untuk memproses hanya subfolder tertentu yang dipilih dari daftar dropdown dinamis.

---

## 2. Requirements & Business Rules

### Functional Requirements
* **FR-01 (Deteksi Subfolder Dinamis):** Sistem harus mampu memindai dan mendaftarkan seluruh subdirektori langsung (*immediate children*) di dalam direktori input yang aktif.
* **FR-02 (API Endpoint Subfolder):** Sistem harus menyediakan endpoint `GET /api/subfolders` yang mengembalikan daftar subfolder beserta estimasi jumlah berkas dokumen di dalamnya.
* **FR-03 (Seleksi UI di Dasbor):** Pada panel *Eksekusi Konversi OCR*, pengguna dapat memilih target subfolder melalui elemen `<select id="target_subfolder" name="target_subfolder">`.
* **FR-04 (Isolasi Pemrosesan Antrean):** Jika subfolder spesifik dipilih, `jalankan_sistem_ocr` hanya boleh menghitung, memindai, dan memasukkan berkas dari subfolder tersebut ke dalam antrean eksekusi `ProcessPoolExecutor`.
* **FR-05 (Preservasi Struktur Mirroring Output):** Berkas output Searchable PDF tetap harus disimpan dengan struktur hierarki folder yang sama persis di dalam `output_pdf/<subfolder_name>/`.
* **FR-06 (Penanganan Validasi):** Jika subfolder yang dipilih tidak ditemukan atau dihapus di luar aplikasi, sistem harus memvalidasi dan memunculkan notifikasi kesalahan yang jelas tanpa menyebabkan crash.

---

## 3. Architecture & Data Flow

```
[Web UI Dashboard]
   │
   ├─► 1. GET /api/subfolders ──► Pindai subfolder di input_dir
   │                               └─► Render dropdown: ["input 17", "batch_2026", ...]
   │
   └─► 2. POST /jalankan (input_dir, output_dir, target_subfolder="input 17")
         │
         ▼
   [routes/ocr.py: jalankan()]
         │
         ▼ (Spawn Background Thread)
   [core_engine.py: jalankan_sistem_ocr(..., target_subfolder="input 17")]
         │
         ├─► scan_dir = os.path.join(input_dir, target_subfolder)
         ├─► total_dokumen = hitung_total_dokumen(scan_dir)
         ├─► os.walk(scan_dir)  <-- HANYA MEMINDAI SUBFOLDER INI
         │     │
         │     └─► relative_path = os.path.relpath(jalur_awal, input_dir)
         │         jalur_tujuan = os.path.join(output_dir, relative_path)
         │
         └─► ProcessPoolExecutor: Hanya mengeksekusi berkas dari subfolder target!
```

---

## 4. Detailed Component Design

### 4.1 Subfolder Discovery Service (`services/storage_service.py`)
Fungsi pembantu untuk mendeteksi subfolder:
```python
def get_subfolders_info(input_dir):
    """
    Mengembalikan daftar dictionary subfolder di dalam input_dir:
    [
        {"name": "input 17", "file_count": 20, "path": "..."},
        ...
    ]
    """
```

### 4.2 Endpoint API (`routes/folder.py` / `routes/dashboard.py`)
* `GET /api/subfolders`:
  * Mengembalikan JSON format:
    ```json
    {
      "status": "success",
      "input_dir": "D:/.../input_pdf",
      "subfolders": [
        {"name": "input 17", "file_count": 20},
        {"name": "batch_revisi", "file_count": 5}
      ]
    }
    ```

### 4.3 Core Engine Modification (`core_engine.py`)
Perluasan signature fungsi:
```python
def jalankan_sistem_ocr(input_dir, output_dir, overwrite=False, flask_app=None, target_subfolder=None):
```
Logika penyesuaian:
```python
if target_subfolder:
    scan_dir = os.path.join(input_dir, target_subfolder)
    if not os.path.isdir(scan_dir):
        catat_log(f"ERROR: Subfolder target '{target_subfolder}' tidak ditemukan!")
        error()
        return
else:
    scan_dir = input_dir

total_dokumen = hitung_total_dokumen(scan_dir)
mulai(total_dokumen)

# os.walk dijalankan hanya pada scan_dir
for root, _, files in os.walk(scan_dir):
    # relative_path tetap dihitung terhadap input_dir induk
    # sehingga output tetap di output_dir/<target_subfolder>/<file>.pdf
    relative_path = os.path.relpath(jalur_awal, input_dir)
```

### 4.4 Web UI Enhancement (`templates/partials/engine_control_section.html`)
Di bawah input direktori input/output, ditambahkan dropdown cakupan:
```html
<div class="mb-3">
    <label class="form-label small text-uppercase text-muted fw-bold mb-1" style="letter-spacing:.04em; font-size:.76rem;">
        Cakupan Pemrosesan (Target Subfolder)
    </label>
    <div class="input-group">
        <span class="input-group-text"><i class="bi bi-diagram-3"></i></span>
        <select class="form-select" id="target_subfolder" name="target_subfolder">
            <option value="">Seluruh Direktori Input (Semua Subfolder)</option>
            <!-- Opsi subfolder dinamis terisi otomatis -->
        </select>
        <button class="btn btn-sm btn-outline-secondary" type="button" onclick="muatDaftarSubfolder()" title="Pindai Ulang Subfolder">
            <i class="bi bi-arrow-clockwise"></i>
        </button>
    </div>
    <div class="form-text small text-muted">
        Pilih subfolder tertentu (misal: <em>input 17</em>) untuk membatasi pemrosesan hanya pada berkas di folder tersebut.
    </div>
</div>
```

---

## 5. Verification & Testing Plan

### Automated Test Cases (`tests/test_subfolder_targeting.py`):
1. **`test_get_subfolders_api`**: Memastikan endpoint `GET /api/subfolders` mengembalikan daftar subfolder yang akurat.
2. **`test_subfolder_targeted_ocr_execution`**:
   - Buat direktori uji sementara: `test_input/` dengan subfolder `subfolder_17/` (3 berkas) dan `subfolder_lain/` (5 berkas).
   - Eksekusi `jalankan_sistem_ocr` dengan `target_subfolder="subfolder_17"`.
   - Verifikasi: Hanya 3 berkas dari `subfolder_17` yang diproses.
   - Verifikasi: Berkas di `subfolder_lain` sama sekali tidak disentuh.
   - Verifikasi: File output tersimpan di `test_output/subfolder_17/` (struktur mirror terjaga).
3. **`test_full_scope_execution_remains_intact`**:
   - Eksekusi dengan `target_subfolder=None` atau `""` memproses seluruh 8 berkas secara normal.

### Regression Testing:
- Menjalankan seluruh test suite pytest (`pytest -v`) untuk memastikan 21 pengujian yang ada tetap 100% passing.
