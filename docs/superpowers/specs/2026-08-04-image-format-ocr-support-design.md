# Image Format OCR Support Design Spec

## Overview
Extend the OCR Project scanning and extraction pipeline to automatically detect, process, and convert image files (`.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`, `.bmp`, `.webp`) into Searchable PDFs in the output directory.

## Data Model & Metadata Updates

### 1. Supported File Extensions
Define global tuple `SUPPORTED_EXTENSIONS`:
`(".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp")`

### 2. Metadata Service (`services/metadata_service.py`)
Update `sedot_metadata(file_path)`:
- If file is PDF: process via PyMuPDF `fitz.open(file_path)`.
- If file is Image: process via PIL/fitz, setting `page_count = "1"`, extracting size formatted in KB/MB, and reading modification date or EXIF creation date.

## OCR Engine Integration (`core_engine.py`)

### 1. Image OCR Extraction (`ekstrak_teks_dari_gambar`)
Implement `ekstrak_teks_dari_gambar(jalur_gambar, ocr_lang="ind+eng", dpi_render=200, generate_searchable_pdf=True)`:
- Open image via `PIL.Image.open(jalur_gambar)` and ensure RGB mode.
- Single-pass OCR call using `pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang=ocr_lang)`.
- Reconstruct text and calculate confidence score.
- Convert image to searchable PDF via `pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang=ocr_lang)`.
- Return PyMuPDF document `(pdf_baru, avg_conf)`.

### 2. General Document Extraction Dispatcher (`ekstrak_dokumen`)
Create dispatcher function `ekstrak_dokumen(jalur_awal, ocr_lang, dpi_render, generate_searchable_pdf)`:
- If `jalur_awal` ends with `.pdf`: delegate to `ekstrak_teks_dan_pdf`.
- Else (image file): delegate to `ekstrak_teks_dari_gambar`.

### 3. File Scanner & Dashboard Statistics (`models/dashboard_model.py`)
- Update `hitung_total_pdf` / `hitung_dokumen` and untracked file count scanner to match all extensions in `SUPPORTED_EXTENSIONS`.
- Output filename for images mapped to `.pdf` extension (e.g. `invoice.png` -> `invoice.pdf`).
