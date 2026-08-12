# Remove Unused `ocr_confidence` Attribute

## Objective
Remove the `ocr_confidence` attribute entirely from the `OCR_Project` as it is not displayed anywhere in the UI or Analytics, reducing unnecessary database payload and OCR computational overhead.

## Architecture & Components
The removal touches three areas of the system:

1. **Database Schema & ORM (`models/dashboard_model.py`)**:
   - Remove `ocr_confidence = db.Column(db.Float, default=0.0)` from the `Riwayat` class.
   - Remove it from the arguments and logic inside `catat_ke_db()` and `tambah_riwayat()`.
   - Remove its usage in `ambil_data_analitik()` (e.g., if there's any orphaned code summing it up).

2. **Core Processing Engine (`core_engine.py`)**:
   - Remove any extraction logic that calculates `confidence`.
   - Remove `ocr_confidence` from the data dictionaries sent back to the main thread via IPC or passed to `simpan_riwayat`.

## Error Handling
- Removing a column from an existing SQLAlchemy model (`Riwayat`) might cause a mismatch with the existing database if it is already populated.
- For SQLite, dropping a column is not natively supported in a single command. The implementation plan will handle clearing or updating the local SQLite database `riwayat.db`.

## Testing
- Ensure the application starts without ORM mapping errors.
- Ensure a document can be processed completely without crashing due to the missing `ocr_confidence` key.
