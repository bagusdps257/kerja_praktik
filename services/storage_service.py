import os
import shutil


def cek_kapasitas_penyimpanan(folder_path):
    """
    Membaca kapasitas drive tempat folder output berada.
    """

    try:
        abs_path = os.path.abspath(folder_path)

        if not os.path.exists(abs_path):
            abs_path = os.path.dirname(abs_path) or "."

        total, used, free = shutil.disk_usage(abs_path)

        gb = 1024 ** 3

        return {
            "total_gb": f"{total / gb:.0f}",
            "used_gb": f"{used / gb:.0f}",
            "free_gb": f"{free / gb:.0f}",
            "persentase": f"{(used / total) * 100:.1f}" if total else "0"
        }

    except Exception as e:
        print(f"Gagal membaca penyimpanan : {e}")

        return {
            "total_gb": "0",
            "used_gb": "0",
            "free_gb": "0",
            "persentase": "0"
        }


def hitung_total_ukuran_folder(folder_path):
    """
    Menghitung total ukuran seluruh file pada folder beserta subfolder.
    """

    total_size = 0

    if os.path.exists(folder_path):

        for root, dirs, files in os.walk(folder_path):

            for file in files:

                file_path = os.path.join(root, file)

                if not os.path.islink(file_path):
                    total_size += os.path.getsize(file_path)

    if total_size >= 1024 ** 3:
        return f"{total_size / (1024 ** 3):.2f} GB"

    elif total_size >= 1024 ** 2:
        return f"{total_size / (1024 ** 2):.2f} MB"

    else:
        return f"{total_size / 1024:.2f} KB"


def get_subfolders_info(input_dir):
    """
    Memindai seluruh subfolder langsung (immediate subdirectories) di dalam input_dir
    beserta jumlah dokumen valid (.pdf, .png, .jpg, dll) di dalamnya.
    """
    subfolders = []
    if not input_dir or not os.path.isdir(input_dir):
        return subfolders

    valid_exts = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp')

    try:
        for item in os.listdir(input_dir):
            item_path = os.path.join(input_dir, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                doc_count = 0
                for root, _, files in os.walk(item_path):
                    for f in files:
                        if f.lower().endswith(valid_exts):
                            doc_count += 1
                subfolders.append({
                    "name": item,
                    "path": item_path,
                    "file_count": doc_count
                })
        subfolders.sort(key=lambda x: x["name"].lower())
    except Exception as e:
        print(f"Error scanning subfolders: {e}")

    return subfolders