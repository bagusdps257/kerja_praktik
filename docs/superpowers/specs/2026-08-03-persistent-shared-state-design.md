# Persistent Shared State & Multi-Process Deployment Design

## 1. Overview & Goal
Currently, telemetry progress (`progress_service.py`) and stop signals (`stop_flag`) are maintained in local Python process memory. When deployed in multi-process WSGI environments (e.g. Gunicorn with multiple workers or multi-process Flask setups), requests routed to different workers cannot access or modify the running process's progress or stop signal.

The goal of this design is to replace in-memory state with an **Atomic File-Based Shared State Engine**:
1. Progress telemetry (`status`, `persen`, `selesai`, `total`, `current_file`, `queue_paused`) persists to `logs/ocr_runtime_state.json` via atomic file swaps (`os.replace`).
2. Execution control signals use file-based flags (`logs/ocr_stop.signal`).
3. Ensures 100% process-safe state sharing across any number of WSGI worker processes without external server dependencies (e.g. Redis).

## 2. Architecture & System Scope
- **Module Affected**: `services/progress_service.py`
- **Engine Affected**: `core_engine.py` (Replace `stop_flag` with file signal checks)
- **Routes Affected**: `routes/dashboard.py`, `routes/ocr.py`

```
  +----------------------+      Atomic Swap      +------------------------------+
  |  WSGI Worker 1 (OCR) |  ------------------>  |  logs/ocr_runtime_state.json |
  +----------------------+                       +--------------+---------------+
                                                                ^
  +----------------------+      Reads Telemetry                 |
  |  WSGI Worker 2 (GET) |  ------------------------------------+
  +----------------------+

  +----------------------+      Creates Signal   +------------------------------+
  |  WSGI Worker 3 (POST)|  ------------------>  |    logs/ocr_stop.signal      |
  +----------------------+                       +------------------------------+
```

## 3. Detailed Component Specifications

### 3.1 Progress Service (`services/progress_service.py`)
- **State File**: `logs/ocr_runtime_state.json`
- **Signal File**: `logs/ocr_stop.signal`
- **Atomic Writer Helper (`_write_state(data)`)**:
  ```python
  def _write_state(data):
      tmp_file = STATE_FILE_PATH + ".tmp"
      with open(tmp_file, "w", encoding="utf-8") as f:
          json.dump(data, f, indent=2)
      os.replace(tmp_file, STATE_FILE_PATH)
  ```
- **State Functions**:
  - `ambil_progress()`: Reads `STATE_FILE_PATH`. Returns default dict if missing.
  - `reset_progress()` / `mulai(total_file)`: Writes initialized state dict to `STATE_FILE_PATH` and removes `SIGNAL_STOP_PATH` if present.
  - `update_file(nama_file)` / `update_progress(jumlah_selesai)`: Reads current state, updates values, and performs atomic `_write_state(data)`.
  - `selesai()` / `berhenti()` / `error()`: Updates `"status"` field in state JSON.
  - `set_queue_paused(state)` / `is_queue_paused()`: Persists and reads `"queue_paused"` boolean in state JSON.

### 3.2 Core Engine Stop Signal & Telemetry Integration (`core_engine.py`)
- **Stop Signal Creator (`hentikan_proses_ocr()`)**:
  - Creates file `logs/ocr_stop.signal`.
  - Sets state status to `"STOPPED"`.
- **Stop Signal Check (`is_stop_requested()`)**:
  - Returns `os.path.exists("logs/ocr_stop.signal")`.
  - In `jalankan_sistem_ocr()`, checked after each task execution loop. When True, cancels remaining tasks and calls `berhenti()`.

## 4. Verification & Testing Plan
1. **Multi-Process Concurrency Test**: Run `scratch/test_shared_state.py` to simulate separate Python processes reading and writing progress and stop signals simultaneously.
2. **Atomic Read Verification**: Perform 500 rapid concurrent reads on `ambil_progress()` while `update_progress()` writes atomically to confirm no `JSONDecodeError`.
3. **Flask Route Telemetry Test**: Verify GET `/progress`, POST `/api/queue/pause`, and POST `/hentikan_ocr` routes.
