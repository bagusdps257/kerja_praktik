# Functional Settings Backend & Frontend Integration Design

## 1. Overview & Goal
The Settings page (`templates/settings.html`) currently contains inactive database action buttons (*Backup Database*, *Export CSV*), hardcoded system information (*Tesseract 5.x*), and dummy form inputs that do not persist changes when submitted.

The goal of this design is to make the Settings page 100% functional end-to-end by:
1. Creating a JSON-based settings persistence module (`services/settings_service.py` & `config/user_settings.json`).
2. Implementing Flask routes for `/settings/save` (POST), `/settings/backup-db` (GET), and wiring `/settings/export-csv` (GET).
3. Implementing dynamic Tesseract binary version detection via `subprocess.run()` and rendering it in the "About System" tab.
4. Auditing and wiring all form controls and action buttons (*Save Settings*, *Reset*, *Reset History* confirmation modal, *Backup Database*, *Export CSV*).

## 2. Architecture & File Scope
- **Config**: `config/user_settings.json` (Stores persistent JSON configuration).
- **Service**: `services/settings_service.py` (Handles loading, saving settings, and detecting Tesseract version).
- **Routes**: `routes/dashboard.py` (Adds `/settings/save` POST and `/settings/backup-db` GET routes).
- **Templates**: `templates/settings.html` (Binds form inputs with `name` attributes and dynamic values, activates button links, wires modal submission).

## 3. Component & Logic Specifications

### 3.1 Settings Service (`services/settings_service.py`)
- **JSON File Location**: `config/user_settings.json`
- **Default Structure**:
  ```python
  DEFAULT_SETTINGS = {
      "tesseract_path": r"C:\Program Files\Tesseract-OCR\tesseract.exe",
      "ocr_language": "ind+eng",
      "dpi_render": 200,
      "max_retry": 5,
      "generate_searchable_pdf": True,
      "input_dir": INPUT_DEFAULT,
      "output_dir": OUTPUT_DEFAULT,
      "storage_warning": 85,
      "auto_cleanup": True,
      "refresh_interval": 1,
      "enable_auto_refresh": True,
      "remember_scroll": True,
      "pause_refresh": True,
      "notify_success": True,
      "notify_failed": True,
      "sound_notify": False
  }
  ```
- **Functions**:
  - `load_settings()`: Reads `user_settings.json`. If file does not exist, writes `DEFAULT_SETTINGS` and returns dict.
  - `save_settings(data)`: Validates numeric ranges (`dpi_render`: 72–600, `max_retry`: 1–10) and writes dict to `user_settings.json`.
  - `get_tesseract_version(tesseract_cmd)`: Runs `subprocess.run([tesseract_cmd, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)`. Extracts the first line of stdout (e.g., `tesseract 5.3.3...`). Returns `"Tesseract Not Found"` on error.

### 3.2 Backend Route Handlers (`routes/dashboard.py`)
- `GET /settings`:
  - Calls `load_settings()` and `get_tesseract_version(settings['tesseract_path'])`.
  - Renders `settings.html` with `stats`, `settings`, `tesseract_version`, and `available_years`.
- `POST /settings/save`:
  - Extracts form values:
    - Text/select: `tesseract_path`, `ocr_language`, `input_dir`, `output_dir`.
    - Numeric: `dpi_render` (int), `max_retry` (int), `storage_warning` (int), `refresh_interval` (int).
    - Checkboxes (booleans): `generate_searchable_pdf`, `auto_cleanup`, `enable_auto_refresh`, `remember_scroll`, `pause_refresh`, `notify_success`, `notify_failed`, `sound_notify`.
  - Calls `save_settings(new_data)`.
  - Updates `db_model.update_folder(input_dir, output_dir)` and `pytesseract.pytesseract.tesseract_cmd = tesseract_path`.
  - Redirects to `/settings` with Flask flash message.
- `GET /settings/backup-db`:
  - Checks if `DB_PATH` file exists.
  - Returns `send_file(DB_PATH, as_attachment=True, download_name=f"ocr_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")`.

### 3.3 Frontend Binding (`templates/settings.html`)
- Form Element: `<form id="settingsForm" method="POST" action="{{ url_for('dashboard.save_settings') }}">`
- Field Bindings:
  - `tesseract_path`: `name="tesseract_path" value="{{ settings.tesseract_path }}"`
  - `ocr_language`: `name="ocr_language"` with dynamic `<option>` selection.
  - `dpi_render`: `name="dpi_render" value="{{ settings.dpi_render }}"`
  - `max_retry`: `name="max_retry" value="{{ settings.max_retry }}"`
  - `generate_searchable_pdf`: `name="generate_searchable_pdf"` (`checked` if True)
  - `input_dir`: `name="input_dir" value="{{ settings.input_dir }}"`
  - `output_dir`: `name="output_dir" value="{{ settings.output_dir }}"`
  - `storage_warning`: `name="storage_warning" value="{{ settings.storage_warning }}"`
  - `auto_cleanup`: `name="auto_cleanup"` (`checked` if True)
  - `refresh_interval`: `name="refresh_interval"` with dynamic selection.
  - `enable_auto_refresh`, `remember_scroll`, `pause_refresh`: Checkboxes with `name="..."`
  - `notify_success`, `notify_failed`, `sound_notify`: Checkboxes with `name="..."`
- Action Buttons:
  - Backup Database: `<a href="{{ url_for('dashboard.backup_db') }}" class="btn btn-primary btn-sm px-3"><i class="bi bi-download me-1"></i> Backup Database</a>`
  - Export CSV: `<a href="{{ url_for('export.export_csv') }}" class="btn btn-outline-success btn-sm px-3"><i class="bi bi-filetype-csv me-1"></i> Export CSV</a>`
  - Save Settings: `<button type="submit" ...>` inside sticky footer.
  - Reset: `<button type="reset" ...>` inside form.
  - Reset History: Modal confirmation form posting to `{{ url_for('dashboard.reset_db') }}`.
- About System: Displays `{{ tesseract_version }} + PyMuPDF`.

## 4. Verification & Testing Plan
1. **Settings Persistence Test**: Change settings on `/settings` page, submit form, verify `config/user_settings.json` is updated and values reload on page refresh.
2. **Database Backup Download Test**: Click "Backup Database", verify HTTP 200 and attachment filename `ocr_backup_YYYYMMDD_HHMMSS.db`.
3. **CSV Export Download Test**: Click "Export CSV", verify HTTP 200 and CSV file download.
4. **Dynamic Tesseract Version Test**: Verify "About System" tab displays real Tesseract version output.
5. **Database Reset Test**: Confirm `#resetHistoryModal` triggers POST to `/reset_db` and empties `riwayat` table.
