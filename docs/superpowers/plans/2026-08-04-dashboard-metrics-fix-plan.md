# Dashboard Metrics Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `ambil_statistik` in `models/dashboard_model.py` to compute `total_output_pages` and `output_size_bytes` strictly for active target output files corresponding to current `input_dir` files, eliminating orphan file distortions.

**Architecture:** 
1. `models/dashboard_model.py`: In `ambil_statistik`, accumulate `active_output_size_bytes` and `active_output_pages` during input scanning loop whenever target output file exists or is marked successful.
2. Replace global `hitung_total_halaman_folder(output_dir)` and `hitung_ukuran_folder(output_dir)` with active folder metrics.
3. Testing: Verify metric outputs against current dataset (295 input files: 200 success / 422 pages, 95 failed / 190 pages -> total input 612 pages, output 422 pages).

**Tech Stack:** Python 3, PyMuPDF (fitz), OS File System

## Global Constraints

- Preserve all return dictionary keys for `ambil_statistik()`.
- Enforce invariant `total_input == total_output + total_gagal + pending`.

---

### Task 1: Refactor `ambil_statistik` in `models/dashboard_model.py`

**Files:**
- Modify: [`models/dashboard_model.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/models/dashboard_model.py:536-685)

**Interfaces:**
- Consumes: `self.input_dir`, `self.output_dir`, `database.get_connection`
- Produces: Correct active folder metrics.

- [ ] **Step 1: Update active output size & page accumulation in `ambil_statistik`**

In `models/dashboard_model.py`:
```python
        active_output_size_bytes = 0
        active_output_pages = 0

        # Inside loop over input files when file is successful/output exists:
        if output_exists:
            active_output_size_bytes += os.path.getsize(target_output_file)
            active_output_pages += file_pages
        elif is_success and output_dir_has_files:
            active_output_pages += file_pages

        # In return dict:
        "output_size": self.format_size(active_output_size_bytes),
        "output_size_bytes": active_output_size_bytes,
        "total_output_pages": active_output_pages,
```

---

### Task 2: Verification & Test

**Files:** All modified files

- [ ] **Step 1: Run verification test checking dashboard metrics**

Verify `total_input_pages == 612`, `total_output_pages == 422`, `total_input == 295`, `total_output == 200`, `total_gagal == 95`, `pending == 0`.
