import os
import json
import time
import threading
from config.settings import LOG_PATH, BASE_DIR

STATE_FILE_PATH = os.path.join(BASE_DIR, "logs", "ocr_runtime_state.json")
SIGNAL_STOP_PATH = os.path.join(BASE_DIR, "logs", "ocr_stop.signal")

DEFAULT_STATE = {
    "status": "IDLE",
    "persen": 0,
    "selesai": 0,
    "total": 0,
    "current_file": "-",
    "queue_paused": False,
    "target_subfolder": ""
}

_state_lock = threading.RLock()
_current_state = None
_last_write_time = 0.0
_write_interval = 0.5  # Batasi penulisan ke disk maksimal setiap 0.5 detik


def _read_from_disk():
    if not os.path.exists(STATE_FILE_PATH):
        return DEFAULT_STATE.copy()
    for _ in range(5):
        try:
            with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        merged = DEFAULT_STATE.copy()
                        merged.update(data)
                        return merged
        except Exception:
            time.sleep(0.05)
    return DEFAULT_STATE.copy()


def _get_state_locked():
    global _current_state
    if _current_state is None:
        _current_state = _read_from_disk()
    return _current_state


def _write_to_disk(data, force=False):
    global _last_write_time
    sekarang = time.time()

    # Jika tidak force dan belum mencapai interval waktu, lewati penulisan (Optimasi I/O)
    if not force and (sekarang - _last_write_time) < _write_interval:
        return

    os.makedirs(os.path.dirname(STATE_FILE_PATH), exist_ok=True)
    tmp_path = f"{STATE_FILE_PATH}.{os.getpid()}.{threading.get_ident()}.tmp"
    try:
        payload = json.dumps(data, indent=2)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(payload)

        for _ in range(5):
            try:
                os.replace(tmp_path, STATE_FILE_PATH)
                _last_write_time = time.time()
                break
            except OSError:
                time.sleep(0.05)
        else:
            # Fallback on Windows if os.replace encounters file lock contention
            try:
                with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
                    f.write(payload)
                _last_write_time = time.time()
            except OSError:
                pass
    except Exception:
        pass
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
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
    with _state_lock:
        return _get_state_locked().copy()


# =====================================================
# RESET
# =====================================================

def reset_progress():
    melepaskan_signal_stop()
    with _state_lock:
        global _current_state
        _current_state = DEFAULT_STATE.copy()
        _write_to_disk(_current_state, force=True)


# =====================================================
# START
# =====================================================

def mulai(total_file, target_subfolder=""):
    melepaskan_signal_stop()
    with _state_lock:
        state = _get_state_locked()
        state["status"] = "RUNNING"
        state["persen"] = 0
        state["selesai"] = 0
        state["total"] = max(0, int(total_file or 0))
        state["current_file"] = "-"
        state["queue_paused"] = False
        state["target_subfolder"] = target_subfolder or ""
        _write_to_disk(state, force=True)


# =====================================================
# UPDATE
# =====================================================

def update_file(nama_file, force=False):
    with _state_lock:
        state = _get_state_locked()
        state["current_file"] = str(nama_file or "-")
        _write_to_disk(state, force=force)


def update_progress(jumlah_selesai, force=True):
    with _state_lock:
        state = _get_state_locked()
        state["selesai"] = max(0, int(jumlah_selesai or 0))
        total = state.get("total", 0)
        if total > 0:
            if state["selesai"] < total:
                state["persen"] = min(99, int(state["selesai"] / total * 100))
            else:
                state["persen"] = 100
        _write_to_disk(state, force=force)


def update_file_and_progress(nama_file, jumlah_selesai, force=True):
    with _state_lock:
        state = _get_state_locked()
        state["current_file"] = str(nama_file or "-")
        state["selesai"] = max(0, int(jumlah_selesai or 0))
        total = state.get("total", 0)
        if total > 0:
            if state["selesai"] < total:
                state["persen"] = min(99, int(state["selesai"] / total * 100))
            else:
                state["persen"] = 100
        _write_to_disk(state, force=force)


# =====================================================
# STATUS
# =====================================================

def selesai(jumlah_selesai=None):
    with _state_lock:
        state = _get_state_locked()
        state["status"] = "FINISHED"
        state["persen"] = 100

        if jumlah_selesai is not None:
            state["selesai"] = max(0, int(jumlah_selesai))
            if state.get("total", 0) < state["selesai"]:
                state["total"] = state["selesai"]
        else:
            total = state.get("total", 0)
            cur_selesai = state.get("selesai", 0)
            if total > 0:
                state["selesai"] = total
            elif cur_selesai > 0:
                state["total"] = cur_selesai

        _write_to_disk(state, force=True)


def berhenti():
    with _state_lock:
        state = _get_state_locked()
        state["status"] = "STOPPED"
        _write_to_disk(state, force=True)


def error():
    with _state_lock:
        state = _get_state_locked()
        state["status"] = "ERROR"
        _write_to_disk(state, force=True)


# =====================================================
# QUEUE PAUSE STATE & STOP SIGNAL
# =====================================================

def set_queue_paused(state: bool):
    with _state_lock:
        cur = _get_state_locked()
        cur["queue_paused"] = bool(state)
        _write_to_disk(cur, force=True)
        return bool(state)


def is_queue_paused():
    with _state_lock:
        cur = _get_state_locked()
        return bool(cur.get("queue_paused", False))


def hentikan_proses_ocr():
    os.makedirs(os.path.dirname(SIGNAL_STOP_PATH), exist_ok=True)
    with open(SIGNAL_STOP_PATH, "w", encoding="utf-8") as f:
        pass
    berhenti()


def is_stop_requested():
    return os.path.exists(SIGNAL_STOP_PATH)