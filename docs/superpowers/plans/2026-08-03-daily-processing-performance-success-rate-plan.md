# Daily Processing Performance & Success Rate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update analytical SQL queries in `models/dashboard_model.py` so that documents with status `'SKIP'` (representing existing successful OCR output files) are counted as successful operations in `Daily Processing Performance` trends and `Success Rate` calculations.

**Architecture:** Modify the `ambil_data_analitik()` method in `models/dashboard_model.py` to aggregate both `'SUKSES'` and `'SKIP'` statuses as successful OCR completions.

**Tech Stack:** Python 3.x, SQLite 3, Flask, Chart.js

## Global Constraints

- Do not alter the raw database schema or modify raw status values stored in the `riwayat` table.
- Maintain existing API contract and parameter structure of `ambil_data_analitik(self, period=None, month=None, year=None)`.
- Ensure compatibility with all time filters (`today`, `7d`, `30d`, `month`, `year`, `all time`).

---

### Task 1: Update Analytical Queries in `models/dashboard_model.py`

**Files:**
- Modify: `models/dashboard_model.py:604-740`
- Test: `scratch/test_analytics_query.py`

**Interfaces:**
- Consumes: SQLite `riwayat` table
- Produces: `ambil_data_analitik()` dictionary containing `success_files`, `success_rate`, `daily_trend`, and `daily_success_rate`.

- [ ] **Step 1: Write verification script to test current vs expected query output**

Create `scratch/test_analytics_query.py`:
```python
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.dashboard_model import OCRDashboardModel

model = OCRDashboardModel()
data = model.ambil_data_analitik()

print("Total Files:", data["total_files"])
print("Success Files:", data["success_files"])
print("Success Rate:", data["success_rate"])
print("Daily Trend:")
for item in data["daily_trend"]:
    print(f"  Date: {item['tanggal']} | Success: {item['success']} | Failed: {item['failed']}")
```

- [ ] **Step 2: Run verification script to observe initial behavior**

Run: `.\env\Scripts\python.exe scratch/test_analytics_query.py`
Expected output: Success count for 2026-07-29, 2026-07-30, 2026-07-31 are 0.

- [ ] **Step 3: Update `ambil_data_analitik` in `models/dashboard_model.py`**

In `models/dashboard_model.py`:
1. Change `success_files` query:
```python
cursor.execute(f"SELECT COUNT(*) FROM riwayat WHERE status IN ('SUKSES', 'SKIP') {p_sql}", tuple(p_params))
```
2. Change `daily_trend` query:
```python
cursor.execute(f"""
    SELECT {date_group} AS label_tgl,
           SUM(CASE WHEN UPPER(status) IN ('SUKSES', 'SUCCESS', 'SKIP') THEN 1 ELSE 0 END) AS success_count,
           SUM(CASE WHEN UPPER(status) IN ('GAGAL', 'FAILED') THEN 1 ELSE 0 END) AS failed_count
    FROM riwayat
    WHERE {dt_col} IS NOT NULL AND {dt_col} != '' {p_sql}
    GROUP BY label_tgl
    ORDER BY label_tgl ASC
""", tuple(p_params))
```
3. Change `daily_success_rate` query:
```python
cursor.execute(f"""
    SELECT {date_group} AS label_tgl,
        ROUND(
            CAST(SUM(CASE WHEN UPPER(status) IN ('SUKSES', 'SUCCESS', 'SKIP') THEN 1 ELSE 0 END) AS REAL)
            / CAST(COUNT(*) AS REAL) * 100,
            1
        ) AS rate
    FROM riwayat
    WHERE {dt_col} IS NOT NULL AND {dt_col} != '' {p_sql}
    GROUP BY label_tgl
    ORDER BY label_tgl ASC
""", tuple(p_params))
```

- [ ] **Step 4: Run verification script to confirm updated behavior**

Run: `.\env\Scripts\python.exe scratch/test_analytics_query.py`
Expected output:
- 2026-07-29 Success: 36 (36 skipped)
- 2026-07-30 Success: 8 (8 skipped)
- 2026-07-31 Success: 88 (88 skipped)
- 2026-08-03 Success: 44 (44 sukses)
- Total success_files includes both SUKSES and SKIP.

- [ ] **Step 5: Verify web app /analytics route**

Run flask or test request to ensure `/analytics` loads cleanly with new data structure.
