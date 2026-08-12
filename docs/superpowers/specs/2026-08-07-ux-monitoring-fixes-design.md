# UX and Monitoring Bug Fixes Design

## 1. Problem Statement
The application currently experiences three distinct issues reported by the user:
1. **Broken Browse Button:** The "Browse" folder selection relies on a server-side Python `tkinter` script triggered via AJAX. This frequently hangs or opens behind the browser in server environments, causing the UI to freeze. Furthermore, the input field is read-only, preventing manual path entry.
2. **Limited Search Scope:** The OCR document search currently filters only on filename, folder path, and remarks. It ignores the `author` column, making it hard to find documents by their creator.
3. **OCR Monitoring Broken:** Following a recent SQLAlchemy ORM migration, the `ambil_data_monitoring` function was accidentally replaced with a stub that does not emit the `live_logs` and `queue_tasks` required by the monitoring frontend. Consequently, the monitoring UI does not display active logs or queue data.

## 2. Approach

### 2.1. Web-Based Folder Browser (Option A + B)
- **UI Flexibility:** Remove the `readonly` attribute from `#input_dir` and `#output_dir` in `templates/partials/engine_control_section.html` so users can manually copy-paste paths.
- **Web File Explorer:** Replace the `tkinter` dependency completely. When "Browse" is clicked, open a Bootstrap modal containing a web-based file explorer.
- **Server Endpoint:** Introduce an `/api/folders` route (GET) in `routes/folder.py` that takes a `path` parameter. It will use Python's `os` module to list subdirectories of the requested path. If no path is provided, it returns a list of root drives (on Windows) or the root directory.
- **Client Logic:** Update `static/js/folder.js` to render the returned folders, handle click-to-navigate events, and a "Select This Folder" confirmation that updates the input box.

### 2.2. Expanding Search Columns
- **ORM Update:** In `models/dashboard_model.py`, locate `_build_orm_query`.
- **Search Clause:** Append `Riwayat.author.ilike(search_term)` to the existing SQLAlchemy `or_` clause.

### 2.3. Restoring the OCR Monitoring Payload
- **Rebuilding `ambil_data_monitoring`:** In `models/dashboard_model.py`, restore the comprehensive data assembly logic that was lost during migration.
- **Data Elements:** Ensure the returned dictionary includes:
  - `engine_status` and `engine_health` (derived from `progress_service`)
  - `cpu_usage` and `memory_usage` (via `psutil`)
  - `processing_speed` (calculated via SQLAlchemy count query for the last 1 hour)
  - `live_logs` (via `self.baca_log_terbaru(30)`)
  - `queue_tasks` (derived from `ambil_statistik` and `ambil_progress`)
  - `queue_paused` and `active_task_count`
- The existing `templates/monitoring.html` will automatically render these properties once the correct payload structure is restored.

## 3. Architecture & Interfaces
- **Web Explorer API:** `GET /api/folders?path=<encoded_path>`
  - Response: `{ "current": "C:\\", "parent": null, "folders": ["Windows", "Users", "Program Files"] }`
- **Frontend Changes:** Modal HTML injected into `engine_control_section.html` or loaded dynamically.
- **Safety:** The web explorer exposes server-side paths, but the application is designed as a local desktop-app equivalent running via Flask, so this is acceptable within the current security model.

## 4. Dependencies
- `psutil` (already used)
- `flask`, `SQLAlchemy`
