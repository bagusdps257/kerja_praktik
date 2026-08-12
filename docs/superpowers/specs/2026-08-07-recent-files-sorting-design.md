# OCR Recent Processed Files Sorting Fix

## Objective
Fix a bug where the "Recent Processed Files" list and the main Documents table fail to bring recently skipped files (or re-processed files) to the top of the table. The tables currently sort by the initial creation ID (`Riwayat.id`) rather than the time they were last processed or updated (`waktu`).

## Architecture & Data Flow
- The OCR engine updates an existing `Riwayat` row's `waktu` column whenever a document is successfully processed, failed, or skipped.
- Both the dashboard and the documents page query the database via the `OCRDashboardModel`.
- By changing the `ORDER BY` clause from `desc(Riwayat.id)` to `desc(Riwayat.waktu), desc(Riwayat.id)`, any file that is touched (whether processed or skipped) will immediately bubble to the top of the feed.

## Components to Modify

### `models/dashboard_model.py`
- In `ambil_riwayat_db`:
  - Change `query.order_by(desc(Riwayat.id))` to `query.order_by(desc(Riwayat.waktu), desc(Riwayat.id))`.
- In `ambil_dokumen`:
  - Change `query.order_by(desc(Riwayat.id))` to `query.order_by(desc(Riwayat.waktu), desc(Riwayat.id))`.

## Error Handling & Edge Cases
- **Missing `waktu` Field**: In case old data has an empty `waktu` field, the fallback sorting `desc(Riwayat.id)` ensures that records still have a deterministic order.

## Testing Strategy
- Ensure that after running a batch of files for the second time, the skipped files appear at the top of the "Recent Processed Files" table on the Dashboard.
- Ensure the main "Documents" page also reflects the chronological ordering based on last modification.
