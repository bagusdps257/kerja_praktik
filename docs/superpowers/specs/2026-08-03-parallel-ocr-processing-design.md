# Parallel OCR Processing Architecture Design

## 1. Overview & Goal
Currently, `core_engine.py` processes PDF documents sequentially in a single-threaded loop. For large directories or multi-page documents, this underutilizes multi-core CPUs and causes slow throughput.

The goal of this design is to implement a parallel OCR processing engine using Python's `concurrent.futures.ProcessPoolExecutor` to distribute CPU-bound tasks (PyMuPDF rendering + Tesseract OCR) across available CPU cores while retaining thread-safe SQLite database operations on the main process thread.

## 2. Architecture & Component Scope
- **File Affected**: `core_engine.py`
- **Module Dependency**: `concurrent.futures`, `multiprocessing`, `services/settings_service.py`
- **Architecture Pattern**: Producer-Consumer Worker Pool with Main Thread Aggregator

```
                     +----------------------------------------+
                     |         jalankan_sistem_ocr()          |
                     |         (Main Process Thread)          |
                     +-------------------+--------------------+
                                         |
                                         v
                         +---------------+---------------+
                         |   ProcessPoolExecutor Pool   |
                         |   (max_workers = cpu - 1)     |
                         +---------------+---------------+
                                         |
            +----------------------------+----------------------------+
            |                            |                            |
            v                            v                            v
  +-------------------+        +-------------------+        +-------------------+
  |  Worker Process 1 |        |  Worker Process 2 |        |  Worker Process N |
  | - PyMuPDF Render  |        | - PyMuPDF Render  |        | - PyMuPDF Render  |
  | - Tesseract OCR   |        | - Tesseract OCR   |        | - Tesseract OCR   |
  | - Write Output    |        | - Write Output    |        | - Write Output    |
  +---------+---------+        +---------+---------+        +---------+---------+
            |                            |                            |
            +----------------------------+----------------------------+
                                         |
                                         v
                     +-------------------+--------------------+
                     |  Main Thread Result Aggregator         |
                     | - Write SQLite `riwayat` records       |
                     | - Update Live Progress & System Logs   |
                     +----------------------------------------+
```

## 3. Detailed Component Specifications

### 3.1 Top-Level Worker Task (`_ocr_worker_task`)
- **Signature**: `_ocr_worker_task(task_args)`
- **Task Arguments**:
  ```python
  (jalur_awal, jalur_tujuan, document_key, folder_path, nama_file_only,
   tesseract_cmd, ocr_lang, dpi_render, generate_pdf)
  ```
- **Processing Steps**:
  1. Set `pytesseract.pytesseract.tesseract_cmd = tesseract_cmd`.
  2. Open source PDF with PyMuPDF (`fitz.open`).
  3. Render pages at DPI matrix and perform Tesseract OCR (`image_to_string` and `image_to_pdf_or_hocr`).
  4. Save output PDF to `jalur_tujuan`.
  5. Calculate execution metrics (`ocr_confidence`, `processing_time`, `file_hash`, `metadata`).
- **Return Payload**:
  ```python
  {
      "document_key": document_key,
      "folder_path": folder_path,
      "nama_file": nama_file_only,
      "status": "SUKSES" | "GAGAL",
      "keterangan": str,
      "metadata": metadata,
      "ocr_confidence": float,
      "processing_time": float,
      "retry_count": int,
      "relative_path": document_key,
      "file_hash": file_hash
  }
  ```

### 3.2 Main Process Coordinator (`jalankan_sistem_ocr`)
1. **Directory Scanning**:
   - Collects all input PDF files and skips files whose outputs already exist (recording `SKIP` on main thread).
2. **Worker Pool Submission**:
   - Reads configured `tesseract_path`, `ocr_language`, `dpi_render`, etc. from `load_settings()`.
   - Computes `max_workers = max(1, os.cpu_count() - 1)`.
   - Submits candidate task tuples to `ProcessPoolExecutor(max_workers=max_workers)`.
3. **Result Consumption & Database Writing**:
   - As futures complete (`as_completed`), main thread receives payload dictionary and calls `db.catat_ke_db(...)`.
   - Updates `update_progress()` and `catat_log()`.
4. **Cancellation & Pause Handling**:
   - Checks `stop_flag` or `is_queue_paused()`. On stop, cancels pending futures and calls `executor.shutdown(wait=False, cancel_futures=True)`.

## 4. Verification & Benchmark Plan
1. **Performance Benchmark**:
   - Create `scratch/benchmark_parallel_ocr.py` to compare sequential vs parallel OCR on sample PDFs.
   - Verify throughput improvement (target: >= 3x speedup on quad-core+ CPUs).
2. **Database Integrity & Concurrency Test**:
   - Ensure zero `sqlite3.OperationalError` during execution.
   - Verify all processed records are saved to `riwayat` table.
