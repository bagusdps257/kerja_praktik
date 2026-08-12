# Analytics Bug Fix (SKIP handling)

## Purpose
Fix the discrepancy between the Dashboard and Analytics pages where skipped files were not counted in the Analytics charts.

## Approach
- Modify `models/dashboard_model.py` specifically inside the `ambil_data_analitik` method.
- Update the status check for daily statistics to include `'SKIP'` in the list of successful statuses.
- Change `r.status in ('SUKSES', 'SUCCESS')` to `r.status in ('SUKSES', 'SUCCESS', 'SKIP')`.

## Constraints & Trade-offs
- By merging SKIP into success, the graph stays simple and perfectly matches the main dashboard's total success numbers.
- No frontend changes are required.
