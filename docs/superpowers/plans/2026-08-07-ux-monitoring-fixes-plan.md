# UX and Monitoring Bug Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the hanging folder browse button by replacing it with a web-based explorer, expand search to include author, and restore broken OCR monitoring data.

**Architecture:** We will implement an `/api/folders` route for the web explorer, update `_build_orm_query` for author search, and rewrite `ambil_data_monitoring` to return the complete JSON payload expected by the frontend.

**Tech Stack:** Python, Flask, SQLAlchemy, JavaScript, Bootstrap

## Global Constraints
- Target database engine: MySQL (via Flask-SQLAlchemy ORM)
- The web explorer API must return valid JSON.
- `ambil_data_monitoring` must return the exact keys: `engine_status`, `engine_health`, `processing_speed`, `cpu_usage`, `memory_usage`, `live_logs`, `queue_tasks`, `active_task_count`, `queue_paused`.

---

### Task 1: Expand Search Scope to Author

**Files:**
- Modify: `models/dashboard_model.py`
- Create: `scratch/test_search.py`

**Interfaces:**
- Consumes: User search query `q`
- Produces: Updated `Riwayat.query` inside `_build_orm_query`

- [ ] **Step 1: Write verification script**

Create `scratch/test_search.py`:
```python
from flask import Flask
from config.settings import Config
from models.extensions import db
from models.dashboard_model import OCRDashboardModel

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    model = OCRDashboardModel()
    query = model._build_orm_query(q="testauthor")
    sql = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
    assert "testauthor" in sql
    assert "riwayat.author" in sql.lower() or "author" in sql.lower()
    print("Search query building works!")
```

- [ ] **Step 2: Run script to verify it fails**

Run: `.\env\Scripts\python.exe scratch/test_search.py`
Expected: `AssertionError` because `author` is not in the SQL.

- [ ] **Step 3: Modify `_build_orm_query`**

In `models/dashboard_model.py`, locate `_build_orm_query` and update the `or_` clause:
```python
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    Riwayat.nama_file.ilike(search_term),
                    Riwayat.folder_path.ilike(search_term),
                    Riwayat.keterangan.ilike(search_term),
                    Riwayat.author.ilike(search_term)
                )
            )
```

- [ ] **Step 4: Run script to verify it passes**

Run: `.\env\Scripts\python.exe scratch/test_search.py`
Expected: `Search query building works!`

- [ ] **Step 5: Commit**

```bash
git add models/dashboard_model.py scratch/test_search.py
git commit -m "fix: include author in search scope"
```

---

### Task 2: Restore OCR Monitoring Payload

**Files:**
- Modify: `models/dashboard_model.py`
- Create: `scratch/test_monitoring.py`

**Interfaces:**
- Consumes: `services.progress_service`, `psutil`, `Riwayat.query`
- Produces: Complete JSON dictionary in `ambil_data_monitoring`

- [ ] **Step 1: Write verification script**

Create `scratch/test_monitoring.py`:
```python
from flask import Flask
from config.settings import Config
from models.extensions import db
from models.dashboard_model import OCRDashboardModel

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    model = OCRDashboardModel()
    data = model.ambil_data_monitoring()
    assert 'live_logs' in data
    assert 'queue_tasks' in data
    print("Monitoring payload complete!")
```

- [ ] **Step 2: Run script to verify it fails**

Run: `.\env\Scripts\python.exe scratch/test_monitoring.py`
Expected: `AssertionError` because `live_logs` is missing.

- [ ] **Step 3: Restore `ambil_data_monitoring`**

Replace `ambil_data_monitoring` in `models/dashboard_model.py` with:
```python
    def ambil_data_monitoring(self):
        from services.progress_service import ambil_progress, is_queue_paused
        import psutil
        from datetime import datetime, timedelta

        try:
            progress = ambil_progress()
            queue_paused = is_queue_paused()
            status_ocr = progress.get("status", "IDLE")

            if queue_paused:
                engine_status = "PAUSED"
                engine_health = "Paused"
            elif status_ocr == "RUNNING":
                engine_status = "ONLINE"
                engine_health = "Processing"
            else:
                engine_status = "IDLE"
                engine_health = "Optimal"

            try:
                cpu_usage = int(psutil.cpu_percent(interval=None))
                memory_usage = int(psutil.virtual_memory().percent)
            except Exception:
                cpu_usage = 0
                memory_usage = 0

            # Processing Speed (docs/hr in last 1 hour)
            one_hour_ago = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            speed_count = Riwayat.query.filter(
                Riwayat.status == 'SUKSES',
                Riwayat.last_processed_at >= one_hour_ago
            ).count()
            
            processing_speed = speed_count

            live_logs = self.baca_log_terbaru(30)

            queue_tasks = []
            stats = self.ambil_statistik()
            pending_count = stats.get("pending", 0)

            if status_ocr == "RUNNING":
                curr_file = progress.get("current_file", "-")
                selesai = progress.get("selesai", 0)
                total = progress.get("total", 0)
                persen = progress.get("persen", 0)

                queue_tasks.append({
                    'file_name': curr_file if curr_file != "-" else "Processing PDF Batch",
                    'worker': 'Worker Alpha',
                    'status': 'PROCESSING',
                    'current_page': selesai + 1 if (total > 0 and selesai < total) else max(1, selesai),
                    'total_pages': max(1, total),
                    'progress': persen
                })

                rem = max(0, total - selesai - 1)
                if rem > 0:
                    queue_tasks.append({
                        'file_name': f'Pending Batch ({rem} files)',
                        'worker': 'Pending Assignment',
                        'status': 'QUEUED',
                        'pending_files': rem
                    })
            else:
                if pending_count > 0:
                    queue_tasks.append({
                        'file_name': f'Pending Batch ({pending_count} files)',
                        'worker': 'Pending Assignment',
                        'status': 'QUEUED',
                        'pending_files': pending_count
                    })

            active_task_count = len(queue_tasks)

            return {
                'engine_status': engine_status,
                'engine_health': engine_health,
                'processing_speed': processing_speed,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'live_logs': live_logs,
                'queue_tasks': queue_tasks,
                'active_task_count': active_task_count,
                'queue_paused': queue_paused
            }
        except Exception as e:
            print(f"Error in ambil_data_monitoring: {e}")
            return {
                'engine_status': 'IDLE',
                'engine_health': 'Error',
                'processing_speed': 0,
                'cpu_usage': 0,
                'memory_usage': 0,
                'live_logs': [],
                'queue_tasks': [],
                'active_task_count': 0,
                'queue_paused': False
            }
```

- [ ] **Step 4: Run script to verify it passes**

Run: `.\env\Scripts\python.exe scratch/test_monitoring.py`
Expected: `Monitoring payload complete!`

- [ ] **Step 5: Commit**

```bash
git add models/dashboard_model.py scratch/test_monitoring.py
git commit -m "fix: restore OCR monitoring payload structure"
```

---

### Task 3: Backend Web-Based Folder Browser

**Files:**
- Modify: `routes/folder.py`
- Create: `scratch/test_folder_api.py`

**Interfaces:**
- Consumes: `GET /api/folders?path=`
- Produces: JSON `{ "current": "...", "parent": "...", "folders": ["..."] }`

- [ ] **Step 1: Write verification script**

Create `scratch/test_folder_api.py`:
```python
from flask import Flask
from routes.folder import folder_bp

app = Flask(__name__)
app.register_blueprint(folder_bp)
# Mock flask_login
app.config['LOGIN_DISABLED'] = True

with app.test_client() as client:
    res = client.get('/api/folders')
    assert res.status_code == 200
    data = res.get_json()
    assert "current" in data
    assert "folders" in data
    print("Folder API works!")
```

- [ ] **Step 2: Run script to verify it fails**

Run: `.\env\Scripts\python.exe scratch/test_folder_api.py`
Expected: `404 Not Found`

- [ ] **Step 3: Implement `/api/folders` route**

In `routes/folder.py`, add this new route:
```python
@folder_bp.route("/api/folders")
@login_required
def api_folders():
    req_path = request.args.get("path", "").strip()
    
    # If empty, return drives on Windows or root on Linux
    if not req_path:
        import string
        if os.name == 'nt':
            drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
            return jsonify({"current": "", "parent": None, "folders": drives})
        else:
            req_path = "/"
            
    if not os.path.isdir(req_path):
        return jsonify({"error": "Invalid path"}), 400
        
    parent = os.path.dirname(req_path)
    if parent == req_path:
        parent = None # Reached root
        
    try:
        items = os.listdir(req_path)
        folders = []
        for item in items:
            try:
                full_path = os.path.join(req_path, item)
                if os.path.isdir(full_path) and not item.startswith('.'):
                    folders.append(item)
            except Exception:
                pass
        folders.sort()
        return jsonify({
            "current": req_path,
            "parent": parent,
            "folders": folders
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

- [ ] **Step 4: Run script to verify it passes**

Run: `.\env\Scripts\python.exe scratch/test_folder_api.py`
Expected: `Folder API works!`

- [ ] **Step 5: Commit**

```bash
git add routes/folder.py scratch/test_folder_api.py
git commit -m "feat: add api/folders endpoint for web explorer"
```

---

### Task 4: Frontend Web-Based Folder Browser & Input Unlocking

**Files:**
- Modify: `templates/partials/engine_control_section.html`
- Modify: `static/js/folder.js`

**Interfaces:**
- Consumes: `/api/folders`
- Produces: Updates `#input_dir` or `#output_dir` and saves via `/update_folder`

- [ ] **Step 1: Remove `readonly` attribute**

In `templates/partials/engine_control_section.html`:
Remove the `readonly` word from the `<input>` tags for both `input_dir` and `output_dir`.

- [ ] **Step 2: Add Modal HTML**

At the bottom of `templates/partials/engine_control_section.html`, add:
```html
<!-- Folder Explorer Modal -->
<div class="modal fade" id="folderExplorerModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Select Folder</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <div class="input-group mb-3">
                    <button class="btn btn-outline-secondary" type="button" id="explorerBtnUp"><i class="bi bi-arrow-up"></i> Up</button>
                    <input type="text" class="form-control" id="explorerCurrentPath" readonly>
                </div>
                <div class="list-group" id="explorerFolderList" style="max-height: 400px; overflow-y: auto;">
                    <!-- Folders injected here -->
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" id="explorerBtnSelect">Select This Folder</button>
            </div>
        </div>
    </div>
</div>
```

- [ ] **Step 3: Update `static/js/folder.js` logic**

Replace the contents of `static/js/folder.js` with:
```javascript
let currentExplorerTarget = null;
let currentExplorerPath = "";

function pilihFolder(idInput) {
    currentExplorerTarget = idInput;
    const modal = new bootstrap.Modal(document.getElementById('folderExplorerModal'));
    loadFolderExplorer("");
    modal.show();
}

function loadFolderExplorer(path) {
    fetch(`/api/folders?path=${encodeURIComponent(path)}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            currentExplorerPath = data.current;
            document.getElementById('explorerCurrentPath').value = data.current || "Drives";
            
            const btnUp = document.getElementById('explorerBtnUp');
            if (data.parent !== null && data.current !== "") {
                btnUp.onclick = () => loadFolderExplorer(data.parent);
                btnUp.disabled = false;
            } else {
                btnUp.onclick = () => loadFolderExplorer("");
                btnUp.disabled = (data.current === "");
            }
            
            const list = document.getElementById('explorerFolderList');
            list.innerHTML = "";
            data.folders.forEach(f => {
                const a = document.createElement('a');
                a.className = "list-group-item list-group-item-action d-flex align-items-center";
                a.href = "javascript:void(0)";
                a.innerHTML = `<i class="bi bi-folder-fill text-warning me-2"></i> ${f}`;
                a.onclick = () => {
                    const separator = data.current.endsWith('\\') || data.current.endsWith('/') || data.current === "" ? "" : "/";
                    loadFolderExplorer(data.current + separator + f);
                };
                list.appendChild(a);
            });
        });
}

document.getElementById('explorerBtnSelect')?.addEventListener('click', () => {
    if (!currentExplorerPath) {
        alert("Pilih direktori spesifik.");
        return;
    }
    document.getElementById(currentExplorerTarget).value = currentExplorerPath;
    
    // Save to server
    const formData = new FormData();
    formData.append('csrf_token', document.querySelector('input[name="csrf_token"]').value);
    formData.append('field', currentExplorerTarget);
    formData.append('value', currentExplorerPath);
    
    fetch('/update_folder', {
        method: 'POST',
        body: formData
    })
    .then(res => {
        if(res.ok) window.location.reload();
        else alert("Gagal mengupdate folder.");
    });
});
```

- [ ] **Step 4: Commit**

```bash
git add templates/partials/engine_control_section.html static/js/folder.js
git commit -m "feat: implement web-based folder explorer and unlock inputs"
```
