import os
import json
import time
from config.settings import LOG_PATH, BASE_DIR

STATE_FILE_PATH = os.path.join(BASE_DIR, "logs", "ocr_runtime_state.json")
SIGNAL_STOP_PATH = os.path.join(BASE_DIR, "logs", "ocr_stop.signal")

DEFAULT_STATE = {
    "status": "IDLE",
    "persen": 0,
    "selesai": 0,
    "total": 0,
    "current_file": "-",
    "queue_paused": False
}


def _read_state():
    if not os.path.exists(STATE_FILE_PATH):
        return DEFAULT_STATE.copy()
    try:
        with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_STATE.copy()


_last_write_time = 0.0
_write_interval = 0.5  # Batasi penulisan ke disk maksimal setiap 0.5 detik

def _write_state(data, force=False):
    global _last_write_time
    sekarang = time.time()
    
    # Jika tidak force dan belum mencapai interval waktu, lewati penulisan (Optimasi I/O)
    if not force and (sekarang - _last_write_time) < _write_interval:
        return
        
    os.makedirs(os.path.dirname(STATE_FILE_PATH), exist_ok=True)
    tmp_path = STATE_FILE_PATH + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        for attempt in range(3):
            try:
                os.replace(tmp_path, STATE_FILE_PATH)
                _last_write_time = time.time()
                break
            except OSError:
                time.sleep(0.05)
    except Exception:
        pass


def melepaskan_signal_stop():
    if os.path.exists(SIGNAL_STOP_PATH):
        try:
            os.remove(SIGNAL_STOP_PATH)
        except OSError:
            pass


# =====================================================
# GETTER
# =====================================================

def ambil_progress():
    return _read_state()


# =====================================================
# RESET
# =====================================================

def reset_progress():
    _write_state(DEFAULT_STATE.copy(), force=True)
    melepaskan_signal_stop()


# =====================================================
# START
# =====================================================

def mulai(total_file):
    melepaskan_signal_stop()
    state = {
        "status": "RUNNING",
        "persen": 0,
        "selesai": 0,
        "total": total_file,
        "current_file": "-",
        "queue_paused": False
    }
    _write_state(state, force=True)


# =====================================================
# UPDATE
def update_file(nama_file, force=False):
    state = _read_state()
    state["current_file"] = nama_file
    _write_state(state, force=force)


def update_progress(jumlah_selesai, force=True):
    state = _read_state()
    state["selesai"] = jumlah_selesai
    total = state.get("total", 0)
    if total > 0:
        if jumlah_selesai < total:
            state["persen"] = min(99, int(jumlah_selesai / total * 100))
        else:
            state["persen"] = 100
    _write_state(state, force=force)


def update_file_and_progress(nama_file, jumlah_selesai, force=True):
    state = _read_state()
    state["current_file"] = nama_file
    state["selesai"] = jumlah_selesai
    total = state.get("total", 0)
    if total > 0:
        if jumlah_selesai < total:
            state["persen"] = min(99, int(jumlah_selesai / total * 100))
        else:
            state["persen"] = 100
    _write_state(state, force=force)


# =====================================================
# STATUS
# =====================================================

def selesai():
    state = _read_state()
    state["status"] = "FINISHED"
    state["persen"] = 100
    # Ensure selesai matches total so no phantom "remaining" files appear
    state["selesai"] = state.get("total", state.get("selesai", 0))
    _write_state(state, force=True)


def berhenti():
    state = _read_state()
    state["status"] = "STOPPED"
    _write_state(state, force=True)


def error():
    state = _read_state()
    state["status"] = "ERROR"
    _write_state(state, force=True)


# =====================================================
# QUEUE PAUSE STATE & STOP SIGNAL
# =====================================================

def set_queue_paused(state: bool):
    current = _read_state()
    current["queue_paused"] = bool(state)
    _write_state(current, force=True)
    return bool(state)


def is_queue_paused():
    state = _read_state()
    return bool(state.get("queue_paused", False))


def hentikan_proses_ocr():
    os.makedirs(os.path.dirname(SIGNAL_STOP_PATH), exist_ok=True)
    with open(SIGNAL_STOP_PATH, "w", encoding="utf-8") as f:
        pass
    berhenti()


def is_stop_requested():
    return os.path.exists(SIGNAL_STOP_PATH)
