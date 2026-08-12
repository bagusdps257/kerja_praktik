# Single-Pass OCR Engine Optimization Design Spec

## Overview
Optimize PDF page OCR processing in `core_engine.py` by eliminating redundant `tesseract.exe` CLI subprocess calls, consolidating text extraction, confidence calculation, and searchable PDF generation into a single-pass workflow per page.

## Problem Statement
Current `ekstrak_teks_dan_pdf()` implementation makes 3 separate external `tesseract.exe` subprocess calls for every PDF page:
1. `pytesseract.image_to_string`
2. `pytesseract.image_to_data`
3. `pytesseract.image_to_pdf_or_hocr`

This causes high CPU, memory, and OS process spawn overhead, slowing down batch PDF processing significantly.

## Proposed Optimization Architecture

### 1. Single-Pass OCR Data Extraction (`core_engine.py`)
Modify `ekstrak_teks_dan_pdf(jalur_pdf, ocr_lang="ind+eng", dpi_render=200, generate_searchable_pdf=True)`:
- Convert page to image at resolution calculated from `dpi_render` (e.g. `matrix = fitz.Matrix(dpi_render / 72.0, dpi_render / 72.0)`).
- Execute `pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang=ocr_lang)` **once** per page:
  - Reconstruct page text from non-empty items in `data['text']`.
  - Extract confidence values from valid entries in `data['conf']`.
- If `generate_searchable_pdf` is `True`, execute `pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang=ocr_lang)` **once** per page to append searchable PDF layer.
- If `generate_searchable_pdf` is `False`, directly copy the original PDF page without re-encoding to save additional CPU cycles.

### 2. Performance Improvement Goal
- Reduce Tesseract CLI process spawning by **66%+**.
- Dynamic DPI resolution scaling based on `user_settings.json` (`dpi_render`).
- Maintain exact backwards compatibility for return signature `(pdf_baru, avg_conf)`.
