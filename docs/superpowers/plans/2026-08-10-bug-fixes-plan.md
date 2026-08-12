# Bug Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement robust database backups, accurate CPU monitoring, and safe memory management for images.

**Architecture:** We will replace the SQLite backup logic with a `mysqldump` subprocess, add a 100ms interval to `psutil`, and wrap the image extraction in strict context managers and `finally` blocks.

**Tech Stack:** Python, Flask, subprocess, psutil, Pillow (PIL), PyMuPDF (fitz)

## Global Constraints

- Must work in a Laragon Windows environment (MySQL `root` without password by default).
- Do not introduce significant delays (CPU interval must be strictly 0.1s).
- Ensure no memory leaks when handling corrupted image files.

---

### Task 1: MySQL Database Backup Fix

**Files:**
- Modify: `routes/dashboard.py:243-251`

**Interfaces:**
- Consumes: User clicks "Backup Database" in Settings.
- Produces: Returns a `.sql` file attachment downloaded to the browser.

- [ ] **Step 1: Write the minimal implementation**

```python
import subprocess
import tempfile

@dashboard_bp.route('/settings/backup-db')
@login_required
def backup_db():
    from datetime import datetime
    backup_name = f"ocr_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    # Create a temporary file to store the dump
    temp_dir = tempfile.gettempdir()
    dump_path = os.path.join(temp_dir, backup_name)
    
    try:
        # Run mysqldump command for Laragon's default MySQL
        # Warning: Hardcoding for Laragon defaults as per project spec
        with open(dump_path, 'w') as f:
            subprocess.run(
                ["mysqldump", "-u", "root", "ocr_database"],
                stdout=f,
                stderr=subprocess.PIPE,
                check=True
            )
        
        return send_file(dump_path, as_attachment=True, download_name=backup_name)
    except Exception as e:
        import core_engine
        core_engine.catat_log(f"❌ Backup gagal: {str(e)}")
        flash("Gagal melakukan backup database MySQL. Pastikan mysqldump tersedia.", "danger")
        return redirect(url_for("dashboard.settings"))
```

- [ ] **Step 2: Commit**

```bash
git add routes/dashboard.py
git commit -m "fix: replace sqlite backup with mysqldump for laragon"
```

---

### Task 2: Accurate CPU Monitoring Fix

**Files:**
- Modify: `models/dashboard_model.py:702`

**Interfaces:**
- Consumes: OCR Monitoring page periodic fetch.
- Produces: Accurate CPU percentage integer.

- [ ] **Step 1: Write the minimal implementation**

```python
            try:
                # Add interval=0.1 to force an accurate reading window
                cpu_usage = int(psutil.cpu_percent(interval=0.1))
                memory_usage = int(psutil.virtual_memory().percent)
            except Exception:
                cpu_usage = 0
                memory_usage = 0
```

- [ ] **Step 2: Commit**

```bash
git add models/dashboard_model.py
git commit -m "fix: add 100ms interval to psutil cpu_percent for accurate monitoring"
```

---

### Task 3: Defensive Image Buffer Handling

**Files:**
- Modify: `core_engine.py:178-223`

**Interfaces:**
- Consumes: A file path `jalur_gambar` to process.
- Produces: A generated PDF or raises an exception for the worker to catch.

- [ ] **Step 1: Write the minimal implementation**

```python
def ekstrak_teks_dari_gambar(jalur_gambar, ocr_lang="ind+eng", dpi_render=200, generate_searchable_pdf=True):
    pdf_baru = None
    img_raw = None
    img = None
    img_buf = None
    img_jpg = None
    
    try:
        if is_stop_requested():
            raise KeyboardInterrupt

        img_raw = Image.open(jalur_gambar)
        img = img_raw.convert("RGB")
        img = _preprocess_image(img)

        # Generate Searchable PDF layer or image to PDF
        if generate_searchable_pdf:
            img_buf = io.BytesIO()
            img.save(img_buf, format="JPEG", quality=80)
            img_buf.seek(0)
            
            img_jpg = Image.open(img_buf)
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(
                img_jpg,
                extension="pdf",
                lang=ocr_lang
            )
            pdf_baru = fitz.open("pdf", pdf_bytes)
            semua_teks = pdf_baru[0].get_text()
        else:
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PDF")
            pdf_bytes = img_bytes.getvalue()
            pdf_baru = fitz.open("pdf", pdf_bytes)
            semua_teks = pytesseract.image_to_string(img, lang=ocr_lang)
            img_bytes.close()

        karakter_valid = [c for c in semua_teks if c.isalnum()]
        if len(karakter_valid) < 3:
            raise Exception("Tidak ada teks.")

        return pdf_baru

    except Exception:
        if pdf_baru:
            try:
                pdf_baru.close()
            except Exception:
                pass
        raise
    finally:
        # Strict cleanup of all image buffers
        if img_raw:
            try: img_raw.close()
            except: pass
        if img:
            try: img.close()
            except: pass
        if img_jpg:
            try: img_jpg.close()
            except: pass
        if img_buf:
            try: img_buf.close()
            except: pass
```

- [ ] **Step 2: Commit**

```bash
git add core_engine.py
git commit -m "fix: implement defensive try-finally blocks for image memory leaks"
```
