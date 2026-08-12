# Functional Settings Backend & Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Settings page fully functional by persisting user settings to JSON, activating database backup and CSV export downloads, detecting Tesseract version dynamically, and wiring all buttons and form controls end-to-end.

**Architecture:** Create `services/settings_service.py` to handle JSON settings I/O and Tesseract detection, update `routes/dashboard.py` with `/settings/save` and `/settings/backup-db` endpoints, and update `templates/settings.html` with field names, dynamic values, and functional action button links.

**Tech Stack:** Python 3.x, Flask, SQLite3, JSON I/O, Subprocess, HTML5/Jinja2

## Global Constraints

- Preserve default fallback paths in `config/settings.py`.
- Do not alter existing database schema.
- Ensure all form controls in `templates/settings.html` are bound to their respective configuration properties.

---

### Task 1: Create Settings Service Module (`services/settings_service.py`)

**Files:**
- Create: `services/settings_service.py`
- Modify: `config/settings.py:1-16`
- Test: `scratch/test_settings_service.py`

**Interfaces:**
- Consumes: `config/settings.py` default constants
- Produces: `load_settings()`, `save_settings(data)`, `get_tesseract_version(tesseract_cmd)`

- [ ] **Step 1: Write test script for settings service**

Create `scratch/test_settings_service.py`:
```python
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.settings_service import load_settings, save_settings, get_tesseract_version

# Test loading
settings = load_settings()
print("Loaded Settings Keys:", list(settings.keys()))

# Test version detection
version = get_tesseract_version(settings.get("tesseract_path", "tesseract"))
print("Tesseract Version:", version)

# Test save & load roundtrip
settings["dpi_render"] = 300
save_settings(settings)
reloaded = load_settings()
assert reloaded["dpi_render"] == 300
print("Roundtrip test PASSED")
```

- [ ] **Step 2: Create `services/settings_service.py`**

Create `services/settings_service.py` with `load_settings`, `save_settings`, and `get_tesseract_version` logic.

- [ ] **Step 3: Run test script to verify `services/settings_service.py`**

Run: `.\env\Scripts\python.exe scratch/test_settings_service.py`
Expected output:
- `Loaded Settings Keys: [...]`
- `Tesseract Version: tesseract v...` or `Tesseract Not Found`
- `Roundtrip test PASSED`

---

### Task 2: Implement Flask Backend Routes in `routes/dashboard.py`

**Files:**
- Modify: `routes/dashboard.py:169-224`
- Test: `scratch/test_settings_routes.py`

**Interfaces:**
- Consumes: `services/settings_service.py`
- Produces: `/settings` (GET), `/settings/save` (POST), `/settings/backup-db` (GET)

- [ ] **Step 1: Write test script for Flask settings routes**

Create `scratch/test_settings_routes.py`:
```python
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

client = app.test_client()

# Test GET /settings
res_get = client.get('/settings')
assert res_get.status_code == 200
print("GET /settings PASSED")

# Test GET /settings/backup-db
res_backup = client.get('/settings/backup-db')
assert res_backup.status_code == 200
assert 'attachment' in res_backup.headers.get('Content-Disposition', '')
print("GET /settings/backup-db PASSED")

# Test POST /settings/save
res_post = client.post('/settings/save', data={
    'tesseract_path': r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    'ocr_language': 'ind+eng',
    'dpi_render': '250',
    'max_retry': '5',
    'input_dir': r'D:\SEMESTER 7\KERJAPRAKTIK\OCR_Project\input_pdf',
    'output_dir': r'D:\SEMESTER 7\KERJAPRAKTIK\OCR_Project\output_pdf',
    'storage_warning': '85',
    'refresh_interval': '1',
    'generate_searchable_pdf': 'on',
    'auto_cleanup': 'on'
}, follow_redirects=True)
assert res_post.status_code == 200
print("POST /settings/save PASSED")
```

- [ ] **Step 2: Update `routes/dashboard.py`**

In `routes/dashboard.py`:
- Update `settings()` route to load settings and `tesseract_version`.
- Add `save_settings()` route handling POST requests to `/settings/save`.
- Add `backup_db()` route handling GET requests to `/settings/backup-db`.

- [ ] **Step 3: Run test script to verify settings routes**

Run: `.\env\Scripts\python.exe scratch/test_settings_routes.py`
Expected output:
- `GET /settings PASSED`
- `GET /settings/backup-db PASSED`
- `POST /settings/save PASSED`

---

### Task 3: Wire Frontend Inputs, Action Links, and Modals in `templates/settings.html`

**Files:**
- Modify: `templates/settings.html:1-434`

**Interfaces:**
- Consumes: Template context (`settings`, `stats`, `tesseract_version`)
- Produces: Fully wired settings form and action buttons.

- [ ] **Step 1: Update form attributes, input names, and dynamic values in `templates/settings.html`**

Update `templates/settings.html`:
- Set form `<form id="settingsForm" method="POST" action="{{ url_for('dashboard.save_settings') }}">`.
- Add `name="..."` attributes to all form controls and bind `value` / `checked` attributes to `settings`.
- Bind "Backup Database" button to `<a href="{{ url_for('dashboard.backup_db') }}">`.
- Bind "Export CSV" button to `<a href="{{ url_for('export.export_csv') }}">`.
- Display `{{ tesseract_version }}` in the About tab.
- Add JS helper for browse buttons and range slider label.

- [ ] **Step 2: Verify full Jinja template rendering**

Run: `.\env\Scripts\python.exe -c "from app import app; client = app.test_client(); res = client.get('/settings'); assert res.status_code == 200; print('Full settings rendering test PASSED')"`
Expected output: `Full settings rendering test PASSED`.
