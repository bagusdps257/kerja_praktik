# Persistent Shared State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul `services/progress_service.py` and `core_engine.py` to use an atomic file-based shared state engine (`logs/ocr_runtime_state.json` and `logs/ocr_stop.signal`), guaranteeing 100% process-safe telemetry and stop signaling across multi-process WSGI deployments.

**Architecture:** Implement atomic JSON file swapping (`_write_state`) in `services/progress_service.py`, replace in-memory `stop_flag` with file signal checks (`logs/ocr_stop.signal`), and update `core_engine.py` execution loops to monitor signal files.

**Tech Stack:** Python 3.x, File I/O (`os.replace`), JSON

## Global Constraints

- Do not alter existing telemetry dictionary return signatures (`status`, `persen`, `selesai`, `total`, `current_file`).
- Ensure `os.replace` atomic swap is used for all state writes to prevent partial JSON reads.
- Ensure signal files are cleaned up on `mulai()` or `reset_progress()`.

---

### Task 1: Refactor `services/progress_service.py` for Atomic File State

**Files:**
- Modify: `services/progress_service.py:1-96`
- Test: `scratch/test_shared_state.py`

**Interfaces:**
- Consumes: `logs/ocr_runtime_state.json`
- Produces: `ambil_progress()`, `reset_progress()`, `mulai(total_file)`, `update_file(nama_file)`, `update_progress(jumlah_selesai)`, `selesai()`, `berhenti()`, `error()`, `set_queue_paused(state)`, `is_queue_paused()`, `hentikan_proses_ocr()`, `is_stop_requested()`.

- [ ] **Step 1: Write test script `scratch/test_shared_state.py`**

Create `scratch/test_shared_state.py`:
```python
import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.progress_service import (
    reset_progress,
    mulai,
    update_file,
    update_progress,
    ambil_progress,
    set_queue_paused,
    is_queue_paused,
    hentikan_proses_ocr,
    is_stop_requested
)

# Reset & start
reset_progress()
mulai(100)

prog = ambil_progress()
assert prog["status"] == "RUNNING"
assert prog["total"] == 100

# Update file & progress
update_file("test.pdf")
update_progress(50)

prog = ambil_progress()
assert prog["current_file"] == "test.pdf"
assert prog["selesai"] == 50
assert prog["persen"] == 50

# Pause state
set_queue_paused(True)
assert is_queue_paused() == True
set_queue_paused(False)

# Stop signal
assert not is_stop_requested()
hentikan_proses_ocr()
assert is_stop_requested()

# Cleanup
reset_progress()
assert not is_stop_requested()

print("Shared state atomic tests PASSED!")
```

- [ ] **Step 2: Refactor `services/progress_service.py`**

In `services/progress_service.py`:
- Define `STATE_FILE_PATH` and `SIGNAL_STOP_PATH` under `logs/`.
- Implement `_read_state()` and `_write_state(data)` using `os.replace`.
- Implement state functions reading/writing JSON.
- Implement `hentikan_proses_ocr()` creating `SIGNAL_STOP_PATH` and `is_stop_requested()` checking `os.path.exists(SIGNAL_STOP_PATH)`.

- [ ] **Step 3: Run test script to verify `services/progress_service.py`**

Run: `.\env\Scripts\python.exe scratch/test_shared_state.py`
Expected output: `Shared state atomic tests PASSED!`

---

### Task 2: Integrate File Stop Signal & Shared State in `core_engine.py`

**Files:**
- Modify: `core_engine.py:25-35`, `core_engine.py:185-366`

**Interfaces:**
- Consumes: `services/progress_service.py` (`is_stop_requested`, `hentikan_proses_ocr`, `berhenti`)
- Produces: Process-safe OCR execution loop in `jalankan_sistem_ocr()`.

- [ ] **Step 1: Update `core_engine.py`**

In `core_engine.py`:
- Remove in-memory `threading.Event()` `stop_flag`.
- Import `hentikan_proses_ocr` and `is_stop_requested` from `services.progress_service`.
- In `jalankan_sistem_ocr()`:
  - Check `is_stop_requested()` instead of `stop_flag.is_set()`.
  - When `is_stop_requested()` is True, cancel pending futures, shutdown executor, call `berhenti()`, and log `"OCR stopped by user"`.

- [ ] **Step 2: Verify execution with Flask API routes**

Run test script `scratch/test_settings_routes.py` or HTTP client test to confirm `/progress`, `/api/status`, `/api/queue/pause` routes return 200 OK.
