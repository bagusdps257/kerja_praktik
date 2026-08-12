# Active Folder Statistics Synchronization Design Spec

## Overview
Synchronize dashboard KPI card metrics (`total_input`, `total_output`, `total_gagal`, `pending`) in `models/dashboard_model.py` with the physical files in the currently selected `input_dir` and `output_dir` paths, resolving historical database accumulation inflating input counts and preventing cross-directory metric mismatches.

## Technical Specifications

### 1. Active Folder Input File Inventory
Scan `self.input_dir` physically for all files matching `SUPPORTED_EXTENSIONS`:
- Compute `total_input` = exact count of physical supported files in `self.input_dir`.
- Collect mapping of each input file's relative document key (`rel_path`), expected output filename, and full expected output path in `self.output_dir`.

### 2. Status Classification Per Active Input File
For each physical file in `self.input_dir`:
- Determine target output file path in `self.output_dir` (e.g. `output_dir / rel_path` or mapped `.pdf` for images).
- Query SQLite `riwayat` table for the latest status record matching `document_key == rel_path` or `nama_file == file_name`.
- Classification rules:
  1. **Success (`total_output`)**: Target output file physically exists in `self.output_dir` OR (latest DB status is `SUKSES`/`SKIP` and target output exists).
  2. **Failed (`total_gagal`)**: Target output file does not exist in `self.output_dir` AND latest DB status is `GAGAL`/`FAILED`.
  3. **Pending (`pending`)**: Target output file does not exist in `self.output_dir` AND latest DB status is NOT `GAGAL`/`FAILED`.

### 3. Metric Invariants
- `total_input == total_output + total_gagal + pending`
- Switching `output_dir` to a fresh empty folder correctly yields `total_output = 0`, `pending = total_input`.
- Total pages for successful documents (`total_halaman`) calculated strictly for files counted in `total_output`.
