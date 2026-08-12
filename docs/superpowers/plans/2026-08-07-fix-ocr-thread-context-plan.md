# Fix OCR Thread Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Inject the Flask application context into the background OCR thread so SQLAlchemy database writes succeed without crashing.

**Architecture:** We will modify `routes/ocr.py` to capture the real Flask application instance via `current_app._get_current_object()` and pass it to `core_engine.jalankan_sistem_ocr`. Then, `core_engine.py` will wrap its execution inside `with flask_app.app_context():`.

**Tech Stack:** Python, Flask, Flask-SQLAlchemy, threading

## Global Constraints

- Target database engine: MySQL (via Flask-SQLAlchemy ORM)
- Do not introduce breaking changes to `routes/dashboard.py`.
- Thread target signature updates must be completely backward compatible if `flask_app` is None.

---

### Task 1: Pass Context to Background Thread

**Files:**
- Modify: `routes/ocr.py`
- Modify: `core_engine.py`

**Interfaces:**
- Consumes: `flask.current_app`
- Produces: `core_engine.jalankan_sistem_ocr(input_dir, output_dir, overwrite=False, flask_app=None)`

- [ ] **Step 1: Modify `core_engine.py` to accept and use `flask_app`**
Modify `jalankan_sistem_ocr` in `core_engine.py`. Find the function signature and add the `flask_app` argument and the context manager. (Around line 375).

```python
from contextlib import nullcontext

def jalankan_sistem_ocr(input_dir, output_dir, overwrite=False, flask_app=None):
    with (flask_app.app_context() if flask_app else nullcontext()):
        db = OCRDashboardModel()

        if not validasi_awal(input_dir, output_dir):
            return
            
        # ... rest of the original jalankan_sistem_ocr logic remains identical ...
        # (Be very careful to maintain correct indentation for the entire function body below this `with` block).
```

- [ ] **Step 2: Modify `routes/ocr.py` to pass the `app` instance**
In `routes/ocr.py`, modify the `/jalankan` route.

```python
from flask import current_app

# ... inside def jalankan(): ...

    if input_baru and output_baru:
        db_model.update_folder(input_baru, output_baru)

    app = current_app._get_current_object()

    active_ocr_thread = threading.Thread(
        target=core_engine.jalankan_sistem_ocr,
        args=(db_model.input_dir, db_model.output_dir),
        kwargs={"overwrite": False, "flask_app": app}
    )
    active_ocr_thread.daemon = True
    active_ocr_thread.start()

    return redirect(url_for("dashboard.index"))
```

- [ ] **Step 3: Test the integration via dummy script**

Create `scratch/test_ocr_thread_context.py`:

```python
import threading
from flask import Flask
from config.settings import Config
from models.extensions import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

from core_engine import jalankan_sistem_ocr

def test_context_passed():
    # Pass the app instance
    thread = threading.Thread(
        target=jalankan_sistem_ocr,
        args=("invalid_input", "invalid_output"), # will trigger validasi_awal failure
        kwargs={"flask_app": app}
    )
    thread.start()
    thread.join()
    print("Test finished without RuntimeError!")

if __name__ == "__main__":
    test_context_passed()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.\env\Scripts\python.exe scratch/test_ocr_thread_context.py`
Expected: Output containing `[LOG] ERROR FATAL: Folder input invalid_input tidak ditemukan!` and `Test finished without RuntimeError!`.

- [ ] **Step 5: Commit**

```bash
git add routes/ocr.py core_engine.py scratch/test_ocr_thread_context.py
git commit -m "fix: pass Flask application context to OCR background thread"
```
