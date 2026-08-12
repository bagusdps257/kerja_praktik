# Fix OCR Background Thread Context Design

## 1. Problem Statement
The recent migration to Flask-SQLAlchemy (ORM) introduced a critical bug. The OCR worker runs in a background `threading.Thread` initiated by `routes/ocr.py`. Background threads in Flask do not inherit the request's application context by default. As a result, when the OCR engine attempts to log its state to the database via `OCRDashboardModel().tambah_riwayat()`, SQLAlchemy raises a `RuntimeError: Working outside of application context.`, causing the thread to silently crash. This breaks the start/stop mechanics, the "Recent Processed Files" table, and the real-time log monitoring.

## 2. Approach
The chosen approach (Option 1) is to explicitly pass the Flask application instance into the background thread and push an application context (`app.app_context()`) around the OCR processing logic. This is a lightweight, Flask-idiomatic way to allow background threads to interact with SQLAlchemy.

## 3. Architecture Changes

### 3.1. Thread Initialization (`routes/ocr.py`)
- Import `current_app` from `flask`.
- Capture the underlying application instance using `app = current_app._get_current_object()` inside the `/jalankan` route.
- Pass this `app` as a named argument `flask_app` to the `jalankan_sistem_ocr` target function when spawning the thread.

### 3.2. Worker Execution (`core_engine.py`)
- Update the signature of `jalankan_sistem_ocr(input_dir, output_dir, overwrite=False)` to include `flask_app=None`.
- Wrap the execution of the OCR process inside a context manager:
  ```python
  from contextlib import nullcontext
  
  def jalankan_sistem_ocr(input_dir, output_dir, overwrite=False, flask_app=None):
      with (flask_app.app_context() if flask_app else nullcontext()):
          # Existing OCR execution logic...
  ```
- This ensures that whenever the background thread attempts to initialize `OCRDashboardModel()` or call `db.session`, the thread possesses a valid SQLAlchemy context.

## 4. Considerations
- **ProcessPoolExecutor Integration:** The OCR tasks themselves are dispatched to separate processes via `ProcessPoolExecutor`. Since database writes are handled strictly by the main coordinator thread (which collects the futures), the processes do not need the Flask app context.
- **Log Service:** The monitoring logs rely on `services/log_service.py` writing to a physical text file. Restoring the thread's execution flow will naturally fix the log monitoring UI, which correctly reads the text file after our previous hotfix.
