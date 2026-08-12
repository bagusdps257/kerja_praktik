# Daily Processing Performance & Success Rate Analytics Design

## 1. Overview & Goal
In the OCR & DMS Analytics page, the **Daily Processing Performance** line chart and overall **Success Rate** currently report a 0% success rate on previous days (e.g., July 29–31, 2026). Analysis revealed that documents processed on those days were assigned the status `SKIP` because their output searchable PDFs already existed in the output directory.

The goal of this design is to refine the analytics calculations in `models/dashboard_model.py` so that documents with status `SKIP` (which represent successfully generated OCR output files from prior runs) are counted towards the **Success Count** and **Success Rate** metrics in both overall KPIs and daily breakdown charts.

## 2. Architecture & System Scope
This is a target analytical query adjustment in the backend model layer:
- **File affected**: `models/dashboard_model.py`
- **Method affected**: `ambil_data_analitik(self, period=None, month=None, year=None)`
- **Database Schema**: Unchanged (`riwayat` table retains raw status `'SKIP'` for auditability).

## 3. Detailed Query Changes

### 3.1 Total Successful Files & Overall Success Rate
Update `success_files` query to include both `'SUKSES'` and `'SKIP'` statuses:
```sql
SELECT COUNT(*) FROM riwayat 
WHERE status IN ('SUKSES', 'SKIP') {p_sql}
```
`success_rate` calculation remains:
$$\text{Success Rate} = \text{Round}\left(\frac{\text{success\_files}}{\text{total\_files}} \times 100, 1\right)$$

### 3.2 Daily Trend Performance (`daily_trend`)
Update `success_count` aggregation in daily performance grouping:
```sql
SELECT {date_group} AS label_tgl,
       SUM(CASE WHEN UPPER(status) IN ('SUKSES', 'SUCCESS', 'SKIP') THEN 1 ELSE 0 END) AS success_count,
       SUM(CASE WHEN UPPER(status) IN ('GAGAL', 'FAILED') THEN 1 ELSE 0 END) AS failed_count
FROM riwayat
WHERE {dt_col} IS NOT NULL AND {dt_col} != '' {p_sql}
GROUP BY label_tgl
ORDER BY label_tgl ASC
```

### 3.3 Daily Success Rate (`daily_success_rate`)
Update daily success rate query:
```sql
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
```

## 4. Verification & Testing Plan
1. **Automated / Empirical Verification**:
   - Run a test script against `models/dashboard_model.py` (`ambil_data_analitik`) to verify `daily_trend` and `success_rate` output for dates 2026-07-29, 2026-07-30, 2026-07-31, and 2026-08-03.
   - Verify that 2026-07-29 displays 36 success docs (instead of 0), 2026-07-30 displays 8 success docs (instead of 0), and 2026-07-31 displays 88 success docs (instead of 0).
2. **Web Endpoint Test**:
   - Query `/analytics` route to confirm JSON data / template rendering functions cleanly without errors.
