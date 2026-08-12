# Analytics Backend Data Sync Design

## 1. Overview
The current `analytics.html` frontend template requests a rich set of metrics (storage utilization, active users, daily volumes) that are not provided by the existing `ambil_data_analitik` backend function in `models/dashboard_model.py`. This design specifies how the backend will be updated to fetch and format the exact data required by the frontend template, resolving the `UndefinedError`.

## 2. Requirements & Data Mapping
The `ambil_data_analitik` function must return a dictionary containing the following keys matching the Jinja2 template expectations:

- **KPIs**:
  - `total_files`: Integer (count of all documents in the query period)
  - `success_files`: Integer (count of documents with status 'SUKSES' or 'SUCCESS')
  - `failed_files`: Integer (count of documents with status 'GAGAL' or 'FAILED')
  - `skipped_files`: Integer (count of documents with status 'SKIP')
  - `success_rate`: Float/Int representing percentage (e.g., 95.5)
  - `avg_processing_time`: Float rounded to 2 decimal places (average of `processing_time` column)

- **Charts**:
  - `daily_trend`: List of dicts `[{'tanggal': 'YYYY-MM-DD', 'success': int, 'failed': int}]`
  - `daily_volume`: List of dicts `[{'tanggal': 'YYYY-MM-DD', 'jumlah': int}]`

- **Storage Metrics**:
  - `storage_used_percent`: Float/Int representing percentage of disk space used
  - `storage_total_gb`: Float (Total disk capacity in GB)
  - `storage_used_gb`: Float (Used disk capacity in GB)
  - `storage_free_formatted`: String (e.g., "150.5 GB")
  - `output_size_formatted`: String (Size of the output/PDF folder)
  - `log_size_formatted`: String (Size of the application logs)

- **User Metrics**:
  - `most_active_users`: List of dicts `[{'author': str, 'docs': int}]` (Top 5 users descending by document count)

## 3. Architecture & Approach
- **Database Querying**: We will use SQLAlchemy ORM on the `Riwayat` model. To ensure compatibility with SQLite (which lacks advanced DATE/TIME grouping functions via ORM), we will fetch the records matching the time period and perform the daily grouping and aggregation in Python memory.
- **File System Scanning**: We will reuse existing `hitung_ukuran_folder` and `format_size` helper functions within `OCRDashboardModel`. For overall disk capacity, we will use Python's `shutil.disk_usage`.
- **Performance**: We will only process database records for the requested time period, reducing in-memory overhead.

## 4. Error Handling
- In case of missing attributes or errors during aggregation (e.g., file system permissions), safe default values (e.g., 0, '0 B', empty lists) will be returned to ensure the frontend template renders without raising `UndefinedError`.
