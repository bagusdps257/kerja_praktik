# Analytics and Recent Files Bug Fix Design

## Purpose
Address three bugs:
1. **Recent Processed Files Not Updating**: Files that are re-processed (or skipped) do not appear at the top of the Recent Processed Files list.
2. **Success Rate is 0**: The Success Rate metric on the analytics dashboard shows 0% even though there are successfully processed (or skipped) files.
3. **Avg Processing Time Skewed**: The average processing time includes `SKIP` files (which take 0 seconds), making the average artificially low and unrepresentative of the actual OCR engine speed.

## Approach

### 1. Recent Processed Files (Ordering)
- **Problem**: Queries for recent files (`ambil_riwayat_db`, `ambil_semua_dokumen`, etc.) sort by `desc(Riwayat.id)`. When an existing file is updated (re-processed/skipped), its `id` does not change, keeping it buried.
- **Solution**: Change the sorting logic from `desc(Riwayat.id)` to `desc(Riwayat.waktu)`.

### 2. Success Rate Calculation (Analytics)
- **Problem**: `success_files` only counts `'SUKSES'` or `'SUCCESS'`, ignoring `'SKIP'`.
- **Solution**: Include `'SKIP'` in the successful statuses list.
```python
success_files = sum(1 for r in results if r.status in ('SUKSES', 'SUCCESS', 'SKIP'))
```

### 3. Average Processing Time Calculation
- **Problem**: `avg_processing_time = total_time / total_files`. If 250 files are skipped (0s) and 10 are processed (5s each), the average shows ~0.19s instead of 5s.
- **Solution**: Filter out `SKIP` files when calculating the average processing time so it only reflects documents that genuinely went through the OCR engine.
```python
processed_results = [r for r in results if r.status != 'SKIP']
total_time = sum(_safe_float(getattr(r, 'processing_time', 0)) for r in processed_results)
avg_processing_time = round(total_time / len(processed_results), 2) if len(processed_results) > 0 else 0.0
```

## Constraints
- No database migration is required.
