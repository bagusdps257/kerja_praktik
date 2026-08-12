# Image Format OCR Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend OCR engine, metadata extractor, and dashboard statistics to automatically scan, OCR, and convert image files (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`, `.bmp`, `.webp`) into Searchable PDFs.

**Architecture:** 
1. `services/metadata_service.py`: Update `sedot_metadata` to extract file size, 1 page count, and creation date for image formats.
2. `core_engine.py`: Add `ekstrak_teks_dari_gambar` and unified `ekstrak_dokumen` dispatcher. Update directory scanners to include image extensions and map image output files to `.pdf`.
3. `models/dashboard_model.py`: Update document scanners (`hitung_pdf` / `hitung_dokumen`, untracked count) to track image files.
4. Testing: Verify OCR processing for `.png`, `.jpg`, `.webp` sample files.

**Tech Stack:** Python 3, PyMuPDF (fitz), PyTesseract, PIL (Pillow)

## Global Constraints

- Supported extensions: `(".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp")`.
- Output for image files must be saved as Searchable PDFs in `output_dir`.
- Retain resource safety and exception handling for all file formats.

---

### Task 1: Image Metadata Support (`services/metadata_service.py`)

**Files:**
- Modify: [`services/metadata_service.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/services/metadata_service.py)

**Interfaces:**
- Consumes: `os`, `fitz`, `PIL.Image`
- Produces: Updated `sedot_metadata(file_path)` supporting both PDF and image formats.

- [ ] **Step 1: Update `sedot_metadata` for image files**

In `services/metadata_service.py`:
```python
from datetime import datetime
from PIL import Image

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp')

def sedot_metadata(file_path):
    size_str = "-"
    pages_str = "-"
    author_str = "-"
    date_str = "-"

    try:
        ukuran = os.path.getsize(file_path)
        if ukuran >= 1024 * 1024:
            size_str = f"{ukuran/(1024*1024):.2f} MB"
        else:
            size_str = f"{ukuran/1024:.2f} KB"

        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            doc = fitz.open(file_path)
            pages_str = str(doc.page_count)
            metadata = doc.metadata
            if metadata:
                author_str = metadata.get("author") or "-"
                creation = metadata.get("creationDate")
                if creation:
                    if creation.startswith("D:"):
                        try:
                            date_str = f"{creation[8:10]}-{creation[6:8]}-{creation[2:6]}"
                        except Exception:
                            date_str = creation
                    else:
                        date_str = creation
            doc.close()
        elif ext in IMAGE_EXTENSIONS:
            pages_str = "1"
            mtime = os.path.getmtime(file_path)
            date_str = datetime.fromtimestamp(mtime).strftime("%d-%m-%Y")
    except Exception:
        pass

    return (size_str, pages_str, author_str, date_str)
```

---

### Task 2: Core OCR Engine Image Integration (`core_engine.py`)

**Files:**
- Modify: [`core_engine.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/core_engine.py)

**Interfaces:**
- Consumes: `pytesseract`, `fitz`, `PIL.Image`, `services.metadata_service`
- Produces: `ekstrak_teks_dari_gambar`, `ekstrak_dokumen`, updated `jalankan_sistem_ocr` scanning image files.

- [ ] **Step 1: Define `SUPPORTED_EXTENSIONS` and `ekstrak_teks_dari_gambar`**

In `core_engine.py`:
```python
SUPPORTED_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp")

def ekstrak_teks_dari_gambar(jalur_gambar, ocr_lang="ind+eng", dpi_render=200, generate_searchable_pdf=True):
    pdf_baru = fitz.open()
    confidences = []
    semua_teks = ""

    try:
        with Image.open(jalur_gambar) as img_raw:
            img = img_raw.convert("RGB")

            try:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang=ocr_lang)
                words = [t for t in data.get('text', []) if t and str(t).strip()]
                if words:
                    semua_teks += " ".join(words) + "\n"

                for c in data.get('conf', []):
                    try:
                        val = float(c)
                        if val >= 0:
                            confidences.append(val)
                    except (ValueError, TypeError):
                        pass
            except Exception:
                pass

            if generate_searchable_pdf:
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang=ocr_lang)
                pdf_temp = fitz.open("pdf", pdf_bytes)
                pdf_baru.insert_pdf(pdf_temp)
                pdf_temp.close()
            else:
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PDF")
                pdf_temp = fitz.open("pdf", img_bytes.getvalue())
                pdf_baru.insert_pdf(pdf_temp)
                pdf_temp.close()

        karakter_valid = [c for c in semua_teks if c.isalnum()]
        if len(karakter_valid) < 3:
            pdf_baru.close()
            raise Exception("Tidak ada teks.")

        avg_conf = sum(confidences) / len(confidences) if confidences else 95.0
        return pdf_baru, avg_conf

    except Exception:
        if pdf_baru:
            try:
                pdf_baru.close()
            except Exception:
                pass
        raise

def ekstrak_dokumen(jalur_awal, ocr_lang="ind+eng", dpi_render=200, generate_searchable_pdf=True):
    ext = os.path.splitext(jalur_awal)[1].lower()
    if ext == ".pdf":
        return ekstrak_teks_dan_pdf(jalur_awal, ocr_lang, dpi_render, generate_searchable_pdf)
    else:
        return ekstrak_teks_dari_gambar(jalur_awal, ocr_lang, dpi_render, generate_searchable_pdf)
```

- [ ] **Step 2: Update `hitung_total_pdf` to `hitung_total_dokumen` and update file scanning**

Update `hitung_total_dokumen` to check `f.lower().endswith(SUPPORTED_EXTENSIONS)`.
Update `_ocr_worker_task` to call `ekstrak_dokumen`.
Update `jalankan_sistem_ocr` to check `SUPPORTED_EXTENSIONS` and output target name ending in `.pdf`.

---

### Task 3: Dashboard Model Support (`models/dashboard_model.py`)

**Files:**
- Modify: [`models/dashboard_model.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/models/dashboard_model.py)

- [ ] **Step 1: Update document scanning and untracked counting for image files**

Update `hitung_pdf` to check `SUPPORTED_EXTENSIONS`.
Update `ambil_statistik` untracked file count to check `SUPPORTED_EXTENSIONS`.

---

### Task 4: Verification & Integration Testing

**Files:** All modified files

- [ ] **Step 1: Run end-to-end verification script testing PNG, JPG, and WEBP image OCR**

Create test images and verify that `jalankan_sistem_ocr` processes images and creates Searchable PDFs in `output_dir`.
