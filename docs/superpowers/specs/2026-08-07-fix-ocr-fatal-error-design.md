# Fix OCR Fatal Error Saving

## Purpose
When `core_engine.py` processes PDF or Image files in a separate worker process, the worker process might occasionally crash entirely (e.g. out of memory, PyMuPDF segfault, Tesseract crash) causing `future.result()` to raise an exception instead of returning a status dictionary. Currently, this causes the OCR engine to increment the progress tracker but fail to record the failure in the database, leading to a mismatch between files processed and files in the database, and resulting in persistent "Pending" files in the dashboard.

## Approach: Fallback Database Save on Fatal Error
When a fatal error is caught in the `future.result()` exception block, we will manually extract the file's metadata and save a "GAGAL" record to the database so that it properly registers as a failed file in both analytics and the document history.

## Technical Changes
Modify `core_engine.py` in the `jalankan_sistem_ocr` function:
1. Locate the `except Exception as exc:` block handling `future.result()`.
2. Unpack `task_info = future_map[future]` to get `jalur_awal`, `document_key`, `folder_path`, and `nama_file_only`.
3. Use `sedot_metadata(jalur_awal)` and `compute_file_hash(jalur_awal)` to safely get file information.
4. Call `simpan_riwayat(...)` with `status="GAGAL"` and `keterangan=f"Fatal Error: {exc}"`.
