# Dashboard Metrics Fix Design Spec

## Overview
Refactor `ambil_statistik` in `models/dashboard_model.py` to calculate `total_output_pages` and `output_size_bytes` strictly for output files corresponding to active input files in `self.input_dir`, eliminating orphan file distortion on the Dashboard page.

## Detailed Metrics Logic

### 1. Active File Iteration & Page/Size Accumulation
During the physical scan loop of `self.input_dir`:
- `total_input`: Count of supported input files in `self.input_dir`.
- `total_input_pages`: Sum of page counts of all supported input files in `self.input_dir`.
- For each input file, determine `target_output_file`:
  - If `os.path.isfile(target_output_file)`:
    - Increment `total_output += 1`.
    - Accumulate `active_output_size_bytes += os.path.getsize(target_output_file)`.
    - Inspect target PDF page count and accumulate `active_output_pages += page_count`.
  - Else if DB status is `SUKSES`/`SKIP` and `output_dir` contains files:
    - Increment `total_output += 1`.
    - Accumulate page count from DB record/input file into `active_output_pages`.
  - Else if DB status is `GAGAL`/`FAILED` and `output_dir` contains files:
    - Increment `total_gagal += 1`.
  - Else:
    - Increment `pending += 1`.

### 2. Metric Invariants
- `total_input == total_output + total_gagal + pending`
- `total_output_pages == active_output_pages` (strictly for active output files)
- `output_size_bytes == active_output_size_bytes` (strictly for active output files)
- For 295 active input files (200 success + 95 failed 2-page files):
  - `total_input` = 295
  - `total_output` = 200
  - `total_gagal` = 95
  - `pending` = 0
  - `total_input_pages` = 612
  - `total_output_pages` = 422
