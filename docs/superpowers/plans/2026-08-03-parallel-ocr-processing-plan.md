# Parallel OCR Processing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul `core_engine.py` to process PDF files in parallel using `concurrent.futures.ProcessPoolExecutor`, achieving a 3x-5x OCR throughput speedup while keeping SQLite database writes strictly single-threaded on the main process.

**Architecture:** Create top-level worker function `_ocr_worker_task` in `core_engine.py`, instantiate `ProcessPoolExecutor` with `max_workers = max(1, os.cpu_count() - 1)` in `jalankan_sistem_ocr`, and write completed task results to `riwayat` on the main process thread.

**Tech Stack:** Python 3.x (`concurrent.futures`, `multiprocessing`), PyMuPDF (`fitz`), PyTesseract, SQLite3

## Global Constraints

- Keep all SQLite database writes (`catat_ke_db`) strictly on the main process thread to avoid database locking.
- Maintain `stop_flag` cancellation and `is_queue_paused()` pause functionality.
- Ensure compatibility with Windows multiprocessing (`__name__ == '__main__'` entry point checks).

---

### Task 1: Implement Worker Task & Parallel Executor in `core_engine.py`

**Files:**
- Modify: `core_engine.py:1-366`
- Test: `scratch/benchmark_parallel_ocr.py`

**Interfaces:**
- Consumes: Input PDF files in `input_dir`
- Produces: Output PDF files in `output_dir`, database records in SQLite `riwayat` table.

- [ ] **Step 1: Write benchmark & test script `scratch/benchmark_parallel_ocr.py`**

Create `scratch/benchmark_parallel_ocr.py`:
```python
import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core_engine import jalankan_sistem_ocr
from config.settings import INPUT_DEFAULT, OUTPUT_DEFAULT

print("--- Starting Parallel OCR Processing ---")
start_time = time.time()
jalankan_sistem_ocr(INPUT_DEFAULT, OUTPUT_DEFAULT)
elapsed = time.time() - start_time
print(f"--- Parallel OCR Finished in {elapsed:.2f} seconds ---")
```

- [ ] **Step 2: Add top-level worker function `_ocr_worker_task` in `core_engine.py`**

In `core_engine.py`:
Add top-level function:
```python
def _ocr_worker_task(task_args):
    """
    Worker function executed in separate process.
    task_args tuple: (jalur_awal, jalur_tujuan, document_key, folder_path, nama_file_only,
                      tesseract_cmd, ocr_lang, dpi_render, generate_searchable_pdf)
    """
    (jalur_awal, jalur_tujuan, document_key, folder_path, nama_file_only,
     tesseract_cmd, ocr_lang, dpi_render, generate_searchable_pdf) = task_args

    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    start_time = time.time()
    metadata = sedot_metadata(jalur_awal)
    file_hash = compute_file_hash(jalur_awal)

    maksimal_percobaan = 3
    for percobaan in range(1, maksimal_percobaan + 1):
        try:
            pdf_baru, confidence = ekstrak_teks_dan_pdf(jalur_awal)
            pdf_baru.save(jalur_tujuan)
            pdf_baru.close()

            processing_time = round(time.time() - start_time, 2)
            return {
                "document_key": document_key,
                "folder_path": folder_path,
                "nama_file": nama_file_only,
                "status": "SUKSES",
                "keterangan": f"Berhasil pada percobaan {percobaan}",
                "metadata": metadata,
                "ocr_confidence": round(confidence, 1),
                "processing_time": processing_time,
                "retry_count": percobaan - 1,
                "relative_path": document_key,
                "file_hash": file_hash
            }
        except Exception as e:
            if percobaan == maksimal_percobaan:
                processing_time = round(time.time() - start_time, 2)
                return {
                    "document_key": document_key,
                    "folder_path": folder_path,
                    "nama_file": nama_file_only,
                    "status": "GAGAL",
                    "keterangan": str(e),
                    "metadata": metadata,
                    "ocr_confidence": 0.0,
                    "processing_time": processing_time,
                    "retry_count": percobaan,
                    "relative_path": document_key,
                    "file_hash": file_hash
                }
            time.sleep(0.5)
```

- [ ] **Step 3: Refactor `jalankan_sistem_ocr` to use `ProcessPoolExecutor`**

In `core_engine.py`:
- Import `concurrent.futures` and `load_settings` from `services.settings_service`.
- Compute `max_workers = max(1, os.cpu_count() - 1)`.
- Scan `input_dir` and collect tasks to submit to `ProcessPoolExecutor`.
- Handle `SKIP` items directly on main thread.
- Collect completed futures via `concurrent.futures.as_completed(future_map)`.
- Write results to `db` via `simpan_riwayat` and update progress on main thread.
- Handle `stop_flag` and `is_queue_paused()`.

- [ ] **Step 4: Run benchmark test script to verify execution**

Run: `.\env\Scripts\python.exe scratch/benchmark_parallel_ocr.py`
Expected output:
- Parallel execution of OCR tasks across multi-processing pool.
- Correct progress logs and `riwayat` DB entries created.
- Benchmark completion status displayed cleanly.
