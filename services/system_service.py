import os
import re
import shutil
import psutil
from config.settings import LOG_PATH

SUPPORTED_EXTENSIONS = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp')
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp')


def format_size(byte):
    """Format bytes into a human-readable string (B, KB, MB, GB, TB, PB)."""
    if byte is None:
        return "0 B"
    try:
        byte = float(byte)
    except (ValueError, TypeError):
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if byte < 1024:
            return f'{byte:.2f} {unit}'
        byte /= 1024
    return f'{byte:.2f} PB'


def hitung_ukuran_folder(direktori):
    """Calculate total size of all files in a directory (in bytes)."""
    total = 0
    if not direktori or not os.path.exists(direktori):
        return 0
    try:
        for root, _, files in os.walk(direktori):
            for file in files:
                path = os.path.join(root, file)
                if os.path.isfile(path) and not os.path.islink(path):
                    try:
                        total += os.path.getsize(path)
                    except OSError:
                        pass
    except Exception:
        pass
    return total


def hitung_total_halaman_folder(direktori, page_count_cache=None):
    """
    Count total PDF and image pages in a folder.
    Uses PyMuPDF with mtime caching dictionary for fast reads.
    """
    total_pages = 0
    if not direktori or not os.path.exists(direktori):
        return 0

    try:
        import fitz
    except ImportError:
        fitz = None

    if page_count_cache is None:
        page_count_cache = {}

    for root, _, files in os.walk(direktori):
        for file in files:
            file_lower = file.lower()
            if file_lower.endswith('.pdf') and fitz is not None:
                path = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(path)
                    cached = page_count_cache.get(path)
                    if cached and cached[0] == mtime:
                        total_pages += cached[1]
                    else:
                        doc = fitz.open(path)
                        pc = doc.page_count
                        doc.close()
                        page_count_cache[path] = (mtime, pc)
                        total_pages += pc
                except Exception:
                    pass
            elif file_lower.endswith(IMAGE_EXTENSIONS):
                total_pages += 1

    return total_pages


def baca_log_terbaru(log_path=None, batas=30):
    """
    Reads the last N lines from the system log file, stripping ANSI color codes.
    """
    target_log = log_path or LOG_PATH
    logs = []
    if target_log and os.path.exists(target_log):
        try:
            with open(target_log, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if any(x in line for x in ["Running on", "HTTP", "Press CTRL"]):
                        continue
                    clean_line = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
                    if clean_line:
                        logs.append(clean_line)
        except Exception:
            pass
    return logs[-batas:]


def get_hardware_metrics(output_dir='.'):
    """
    Reads CPU percentage, RAM percentage, and disk usage for the target folder.
    """
    try:
        cpu_usage = int(psutil.cpu_percent(interval=0.05))
        memory_usage = int(psutil.virtual_memory().percent)
    except Exception:
        cpu_usage = 0
        memory_usage = 0

    try:
        target_path = output_dir if (output_dir and os.path.exists(output_dir)) else '.'
        disk = shutil.disk_usage(target_path)
        total_gb = round(disk.total / (1024**3), 1)
        used_gb = round(disk.used / (1024**3), 1)
        used_percent = round((disk.used / disk.total) * 100, 1) if disk.total > 0 else 0
        free_bytes = disk.free
        free_formatted = format_size(free_bytes)
    except Exception:
        total_gb = 0
        used_gb = 0
        used_percent = 0
        free_bytes = 0
        free_formatted = "0 B"

    return {
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "disk_free_bytes": free_bytes,
        "disk_free_formatted": free_formatted,
        "disk_total_gb": total_gb,
        "disk_used_gb": used_gb,
        "disk_used_percent": used_percent
    }
