# Bug Fixes Design Spec (2026-08-10)

## Overview
This specification details the solutions for three critical bugs identified during the project code audit. The goal is to ensure data safety, accurate monitoring, and robust resource management during OCR processing.

## 1. MySQL Database Backup Fix
### Current Problem
The `backup_db` route in `routes/dashboard.py` relies on a hardcoded `DB_PATH` intended for SQLite. Because the application uses MySQL via Laragon, this results in a 404 error or an empty file, placing the user at risk of permanent data loss if a reset is triggered.

### Proposed Architecture
- **Tooling**: Utilize `mysqldump` (which comes bundled with Laragon's MySQL) to extract the database.
- **Execution**: The `backup_db` route will parse the `SQLALCHEMY_DATABASE_URI` (or use the known `root:@localhost/ocr_database` credentials) and spawn a `subprocess.run` command to execute `mysqldump`.
- **Output**: The output will be piped to a temporary `.sql` file (e.g., in a `temp` or `scratch` folder) and sent to the user via `send_file`.
- **Error Handling**: If `mysqldump` fails (e.g., not found in PATH), the route will elegantly catch the exception, log it, and return a flashed error message to the user instead of crashing.

## 2. Accurate CPU Monitoring
### Current Problem
In `models/dashboard_model.py`, `psutil.cpu_percent(interval=None)` is called. In a web request context, this returns 0.0 because `psutil` requires a time delta to calculate CPU usage, which it cannot do across isolated web requests without a blocking interval.

### Proposed Architecture
- **Fix**: Change the parameter to `psutil.cpu_percent(interval=0.1)`. 
- **Impact**: This introduces a microscopic 100ms delay to the monitoring API call, but guarantees a highly accurate CPU reading. This is an optimal trade-off for a dashboard.

## 3. Defensive Image Buffer Handling
### Current Problem
In `core_engine.py` (`ekstrak_teks_dari_gambar`), corrupted files disguised as images (e.g., a `.txt` renamed to `.jpg`) can cause `Image.open` to throw catastrophic exceptions. Without a rigid cleanup mechanism, these open bytes can lead to memory leaks in the background workers.

### Proposed Architecture
- **Fix**: Restructure the image extraction block.
- **Implementation**: 
  - Wrap the `img_raw` buffer and `img_buf` in strict `try...except...finally` blocks.
  - In the `finally` clause, ensure that all `BytesIO` buffers and `Image` objects are explicitly closed `.close()` if they exist.
  - Return gracefully or raise a standard exception so the worker captures it and updates the database status to `GAGAL`.
