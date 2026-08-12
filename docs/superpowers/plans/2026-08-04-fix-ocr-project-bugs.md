# Fix OCR Project Bugs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve all identified architectural, concurrency, input validation, state sync, and resource leak bugs across the OCR Project codebase.

**Architecture:** 
1. Synchronize `OCRDashboardModel` initial state with `user_settings.json` on startup.
2. Prevent concurrent OCR thread collisions in `routes/ocr.py`.
3. Add robust exception handling and retries around Windows file replaces in `services/progress_service.py`.
4. Ensure `PyMuPDF` objects are closed under all exception paths in `core_engine.py`.
5. Fix form input parsing safely in `routes/folder.py` and remove dead code in `models/dashboard_model.py`.

**Tech Stack:** Python 3, Flask, PyMuPDF (fitz), SQLite3, PyTesseract

## Global Constraints

- Preserve all existing public route definitions and signatures.
- All file edits must maintain clean, working Python code.
- Always handle Windows-specific file locks and paths gracefully.

---

### Task 1: Fix App Startup Settings Synchronization & Remove Dead Code in `models/dashboard_model.py`

**Files:**
- Modify: [`models/dashboard_model.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/models/dashboard_model.py)

**Interfaces:**
- Consumes: `services.settings_service.load_settings`
- Produces: Updated `OCRDashboardModel.__init__` loading user settings.

- [ ] **Step 1: Inspect `__init__` and `ambil_dokumen` in `models/dashboard_model.py`**

Confirm current lines in `__init__` and duplicate statements in `ambil_dokumen`.

- [ ] **Step 2: Update `__init__` to load settings from `user_settings.json`**

In `models/dashboard_model.py`:
```python
from services.settings_service import load_settings

class OCRDashboardModel:
    def __init__(self):
        settings = load_settings()
        self.input_dir = settings.get("input_dir", INPUT_DEFAULT)
        self.output_dir = settings.get("output_dir", OUTPUT_DEFAULT)
        self.log_path = LOG_PATH
        self.init_db()
```

- [ ] **Step 3: Remove duplicate dead code from `ambil_dokumen`**

Remove unreachable lines 461-463 in `models/dashboard_model.py`.

- [ ] **Step 4: Verify syntax and behavior**

Run `python -c "from models.dashboard_model import OCRDashboardModel; m = OCRDashboardModel(); print(m.input_dir, m.output_dir)"`

---

### Task 2: Prevent Concurrent OCR Thread Spawning in `routes/ocr.py`

**Files:**
- Modify: [`routes/ocr.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/routes/ocr.py)

**Interfaces:**
- Consumes: `services.progress_service.ambil_progress`
- Produces: Protected `/jalankan` route preventing duplicate active threads.

- [ ] **Step 1: Add running state check to `/jalankan`**

In `routes/ocr.py`:
```python
from services.progress_service import ambil_progress

@ocr_bp.route("/jalankan", methods=["POST"])
def jalankan():
    prog = ambil_progress()
    if prog.get("status") == "RUNNING":
        return jsonify({"status": "warning", "message": "OCR process is already running."}), 400

    input_baru = request.form.get("input_dir")
    output_baru = request.form.get("output_dir")

    if input_baru and output_baru:
        db_model.update_folder(input_baru, output_baru)

    thread = threading.Thread(
        target=core_engine.jalankan_sistem_ocr,
        args=(db_model.input_dir, db_model.output_dir)
    )
    thread.daemon = True
    thread.start()

    return redirect(url_for("dashboard.index"))
```

- [ ] **Step 2: Verify route handling**

Ensure non-blocking, safe execution when status is `RUNNING`.

---

### Task 3: Robust File Lock & Exception Handling in `services/progress_service.py`

**Files:**
- Modify: [`services/progress_service.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/services/progress_service.py)

- [ ] **Step 1: Wrap `_write_state` with retries for Windows file lock exceptions**

In `services/progress_service.py`:
```python
def _write_state(data):
    os.makedirs(os.path.dirname(STATE_FILE_PATH), exist_ok=True)
    tmp_path = STATE_FILE_PATH + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        for _ in range(3):
            try:
                os.replace(tmp_path, STATE_FILE_PATH)
                break
            except OSError:
                time.sleep(0.05)
    except Exception:
        pass
```

---

### Task 4: Fix Resource Leaks in `core_engine.py`

**Files:**
- Modify: [`core_engine.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/core_engine.py)

- [ ] **Step 1: Ensure `pdf_baru` document is closed in error paths**

In `ekstrak_teks_dan_pdf()`:
```python
def ekstrak_teks_dan_pdf(jalur_pdf):
    doc_asli = fitz.open(jalur_pdf)
    pdf_baru = fitz.open()
    confidences = []

    try:
        semua_teks = ""
        for page_num in range(len(doc_asli)):
            if is_stop_requested():
                pdf_baru.close()
                raise KeyboardInterrupt

            page = doc_asli[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            semua_teks += pytesseract.image_to_string(img, lang="ind+eng")

            try:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                confs = [float(c) for c in data['conf'] if c != '-1' and c != -1]
                if confs:
                    confidences.append(sum(confs) / len(confs))
            except Exception:
                pass

            pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang="ind+eng")
            pdf_temp = fitz.open("pdf", pdf_bytes)
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
    finally:
        doc_asli.close()
```

---

### Task 5: Safe Form Key Handling in `routes/folder.py`

**Files:**
- Modify: [`routes/folder.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/routes/folder.py)

- [ ] **Step 1: Use safe `.get()` in `/update_folder`**

In `routes/folder.py`:
```python
@folder_bp.route("/update_folder", methods=["POST"])
def update_folder():
    input_dir = request.form.get("input_dir")
    output_dir = request.form.get("output_dir")
    if input_dir and output_dir:
        db_model.update_folder(input_dir, output_dir)
    return redirect(url_for("dashboard.index"))
```
