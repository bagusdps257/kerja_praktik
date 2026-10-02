import os
import json
import subprocess
from config.settings import BASE_DIR, INPUT_DEFAULT, OUTPUT_DEFAULT, TESSERACT_CMD

SETTINGS_FILE_PATH = os.path.join(BASE_DIR, "config", "user_settings.json")

DEFAULT_SETTINGS = {
    "tesseract_path": TESSERACT_CMD,
    "ocr_language": "ind+eng",
    "dpi_render": 150,
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


def load_settings():
    """
    Reads user_settings.json.
    If missing, writes DEFAULT_SETTINGS and returns dict.
    Merges any missing keys from DEFAULT_SETTINGS.
    """
    if not os.path.exists(SETTINGS_FILE_PATH):
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    if not isinstance(data, dict):
        data = {}

    modified = False
    for key, val in DEFAULT_SETTINGS.items():
        if key not in data:
            data[key] = val
            modified = True

    if modified:
        save_settings(data)

    return data


def save_settings(data):
    """
    Accepts dict, validates numeric limits (dpi_render 72-600, max_retry 1-10, storage_warning 50-95),
    dumps to user_settings.json formatted with indent 2, returns updated dict.
    """
    if not isinstance(data, dict):
        data = load_settings()

    if "dpi_render" in data:
        try:
            dpi = int(data["dpi_render"])
            data["dpi_render"] = max(72, min(600, dpi))
        except (ValueError, TypeError):
            data["dpi_render"] = DEFAULT_SETTINGS["dpi_render"]

    if "max_retry" in data:
        try:
            retry = int(data["max_retry"])
            data["max_retry"] = max(1, min(10, retry))
        except (ValueError, TypeError):
            data["max_retry"] = DEFAULT_SETTINGS["max_retry"]

    if "storage_warning" in data:
        try:
            warning = int(data["storage_warning"])
            data["storage_warning"] = max(50, min(95, warning))
        except (ValueError, TypeError):
            data["storage_warning"] = DEFAULT_SETTINGS["storage_warning"]

    if "tesseract_path" in data and data["tesseract_path"]:
        tp = data["tesseract_path"].strip()
        if os.path.isdir(tp):
            exe_candidate = os.path.join(tp, "tesseract.exe")
            if os.path.exists(exe_candidate):
                data["tesseract_path"] = exe_candidate
        elif not tp.lower().endswith(".exe") and os.path.exists(tp + ".exe"):
            data["tesseract_path"] = tp + ".exe"

    os.makedirs(os.path.dirname(SETTINGS_FILE_PATH), exist_ok=True)
    with open(SETTINGS_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return data


def resolve_tesseract_cmd(tesseract_cmd):
    """Resolve tesseract_cmd string to a valid executable path if possible."""
    if not tesseract_cmd:
        tesseract_cmd = TESSERACT_CMD

    tesseract_cmd = tesseract_cmd.strip()

    import shutil
    # Check if command name is on system PATH (e.g. 'tesseract' -> 'C:\...\tesseract.exe')
    which_path = shutil.which(tesseract_cmd)
    if which_path:
        return which_path

    if os.path.isdir(tesseract_cmd):
        exe_candidate = os.path.join(tesseract_cmd, "tesseract.exe")
        if os.path.exists(exe_candidate):
            return exe_candidate

    if not tesseract_cmd.lower().endswith(".exe") and os.path.exists(tesseract_cmd + ".exe"):
        return tesseract_cmd + ".exe"

    if os.path.exists(tesseract_cmd):
        return tesseract_cmd

    if os.name == 'nt' and os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
        return r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    if os.path.exists(TESSERACT_CMD):
        return TESSERACT_CMD

    return tesseract_cmd


def get_tesseract_version(tesseract_cmd):
    """
    Runs subprocess.run([tesseract_cmd, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3).
    Reads first line of stdout (e.g. tesseract 5.3.3...).
    Returns fallback "Tesseract Not Found" on error or timeout.
    """
    resolved_cmd = resolve_tesseract_cmd(tesseract_cmd)
    
    if resolved_cmd and os.path.exists(resolved_cmd):
        try:
            res = subprocess.run(
                [resolved_cmd, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3
            )
            if res.returncode == 0 and res.stdout:
                first_line = res.stdout.strip().splitlines()[0]
                return first_line
        except Exception:
            pass

    # Fallback attempt via pytesseract
    try:
        import pytesseract
        if resolved_cmd and os.path.exists(resolved_cmd):
            pytesseract.pytesseract.tesseract_cmd = resolved_cmd
        elif os.path.exists(TESSERACT_CMD):
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
            
        ver = pytesseract.get_tesseract_version()
        if ver:
            return f"tesseract v{ver}"
    except Exception:
        pass

    return "Tesseract Not Found"

