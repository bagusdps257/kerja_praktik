# Single-Pass OCR Engine Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor OCR extraction in `core_engine.py` to single-pass per page, cutting Tesseract CLI subprocess spawns by 66%+ and implementing dynamic DPI scaling.

**Architecture:** 
1. `ekstrak_teks_dan_pdf`: Accept `ocr_lang`, `dpi_render`, `generate_searchable_pdf`. Calculate zoom matrix based on `dpi_render` (`dpi_render / 72.0`).
2. Single-pass extraction: Call `pytesseract.image_to_data` once per page for both text reconstruction and confidence score calculation.
3. Searchable PDF generation: Call `pytesseract.image_to_pdf_or_hocr` once per page if enabled, or copy original page if disabled.
4. Worker task: Update `_ocr_worker_task` to pass worker arguments directly into `ekstrak_teks_dan_pdf`.

**Tech Stack:** Python 3, PyMuPDF (fitz), PyTesseract, PIL

## Global Constraints

- Maintain return signature `(pdf_baru, avg_conf)` for `ekstrak_teks_dan_pdf`.
- Ensure all PyMuPDF document objects are safely closed under all exception/stop paths.

---

### Task 1: Refactor `ekstrak_teks_dan_pdf` in `core_engine.py`

**Files:**
- Modify: [`core_engine.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/core_engine.py:84-154)

**Interfaces:**
- Consumes: `pytesseract`, `fitz`, `PIL.Image`
- Produces: Optimized `ekstrak_teks_dan_pdf(jalur_pdf, ocr_lang="ind+eng", dpi_render=200, generate_searchable_pdf=True)`

- [ ] **Step 1: Update function signature & DPI scaling**

```python
def ekstrak_teks_dan_pdf(jalur_pdf, ocr_lang="ind+eng", dpi_render=200, generate_searchable_pdf=True):
    doc_asli = fitz.open(jalur_pdf)
    pdf_baru = fitz.open()
    confidences = []

    try:
        semua_teks = ""
        zoom = max(1.0, dpi_render / 72.0)
        matrix = fitz.Matrix(zoom, zoom)

        for page_num in range(len(doc_asli)):
            if is_stop_requested():
                pdf_baru.close()
                raise KeyboardInterrupt

            page = doc_asli[page_num]
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Single-pass OCR data extraction
            try:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang=ocr_lang)
                text_tokens = [w for w in data.get('text', []) if w.strip()]
                semua_teks += " ".join(text_tokens) + "\n"

                confs = [float(c) for c in data.get('conf', []) if c != '-1' and c != -1]
                if confs:
                    confidences.append(sum(confs) / len(confs))
            except Exception:
                pass

            if generate_searchable_pdf:
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang=ocr_lang)
                pdf_temp = fitz.open("pdf", pdf_bytes)
                pdf_baru.insert_pdf(pdf_temp)
                pdf_temp.close()
            else:
                pdf_baru.insert_pdf(doc_asli, from_page=page_num, to_page=page_num)

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
    finally:
        doc_asli.close()
```

---

### Task 2: Update Worker Call in `core_engine.py`

**Files:**
- Modify: [`core_engine.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/core_engine.py:200-225)

- [ ] **Step 1: Pass worker arguments to `ekstrak_teks_dan_pdf` in `_ocr_worker_task`**

In `_ocr_worker_task`:
```python
pdf_baru, confidence = ekstrak_teks_dan_pdf(
    jalur_awal,
    ocr_lang=ocr_lang,
    dpi_render=dpi_render,
    generate_searchable_pdf=generate_searchable_pdf
)
```

---

### Task 3: Verification & Benchmark Test

**Files:** All modified files

- [ ] **Step 1: Run benchmark test script comparing OCR execution**

Verify that `ekstrak_teks_dan_pdf` runs cleanly without errors and produces valid text and searchable PDF objects.
