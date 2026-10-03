import os
import sys
import subprocess

from flask import Blueprint, jsonify, request, redirect, url_for, send_from_directory
from flask_login import login_required

from models.model_provider import db_model

folder_bp = Blueprint("folder", __name__)

from services.settings_service import load_settings, save_settings

@folder_bp.route("/update_folder", methods=["POST"])
@login_required
def update_folder():
    field = request.form.get("field")
    value = request.form.get("value", "").strip()
    
    print(f"DEBUG update_folder: Received POST. field='{field}', value='{value}'")

    # Support direct form submission (e.g. user hits Enter in the text input)
    if not field:
        input_dir = request.form.get("input_dir", "").strip()
        output_dir = request.form.get("output_dir", "").strip()
        if input_dir or output_dir:
            settings = load_settings()
            if input_dir:
                if not os.path.isdir(input_dir):
                    return "Folder input tidak ditemukan", 400
                settings["input_dir"] = input_dir
            if output_dir:
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    return f"Error creating directory: {e}", 500
                settings["output_dir"] = output_dir
            db_model.update_folder(settings.get("input_dir", db_model.input_dir), settings.get("output_dir", db_model.output_dir))
            save_settings(settings)
            return redirect(url_for("dashboard.index"))
        return "Bad Request", 400

    if field not in allowed_fields or not value:
        print(f"DEBUG update_folder: Validation failed! field='{field}', value='{value}'")
        return "Bad Request", 400

    if field == "input_dir":
        if not os.path.isdir(value):
            print(f"DEBUG update_folder: Input directory does not exist! '{value}'")
            return "Folder input tidak ditemukan", 400
    else:
        try:
            os.makedirs(value, exist_ok=True)
        except Exception as e:
            print(f"DEBUG update_folder: Error creating directory! {e}")
            return "Internal Server Error", 500

    # Load existing settings to preserve the other field
    settings = load_settings()
    
    if field == "input_dir":
        input_dir = value
        output_dir = settings.get("output_dir", db_model.output_dir)
    else:
        input_dir = settings.get("input_dir", db_model.input_dir)
        output_dir = value

    # Update running engine's memory
    db_model.update_folder(input_dir, output_dir)
    
    # Save to user_settings.json for persistence
    settings["input_dir"] = input_dir
    settings["output_dir"] = output_dir
    save_settings(settings)
    print(f"DEBUG update_folder: Saved! input_dir='{input_dir}', output_dir='{output_dir}'")

    return redirect(url_for("dashboard.index"))



@folder_bp.route("/lihat_pdf/<path:filename>")
@login_required
def lihat_pdf(filename):
    folder_output = os.path.abspath(db_model.output_dir)
    clean_filename = filename.strip('/\\')
    target = os.path.abspath(os.path.join(folder_output, clean_filename))

    def is_safe_path(candidate):
        try:
            return os.path.commonpath([candidate, folder_output]) == folder_output
        except Exception:
            return False

    # 1. Cek langsung file sesuai nama yang diminta
    if is_safe_path(target) and os.path.isfile(target):
        return send_from_directory(os.path.dirname(target), os.path.basename(target))

    # 2. Cek apakah berkas merupakan hasil konversi gambar ke .pdf
    pdf_version = os.path.splitext(clean_filename)[0] + ".pdf"
    target_pdf = os.path.abspath(os.path.join(folder_output, pdf_version))
    if is_safe_path(target_pdf) and os.path.isfile(target_pdf):
        return send_from_directory(os.path.dirname(target_pdf), os.path.basename(target_pdf))

    # 3. Fallback: cari file berdasarkan basename di subfolder output
    file_basename = os.path.basename(clean_filename)
    pdf_basename = os.path.splitext(file_basename)[0] + ".pdf"
    for root, dirs, files in os.walk(folder_output):
        if file_basename in files:
            return send_from_directory(root, file_basename)
        if pdf_basename in files:
            return send_from_directory(root, pdf_basename)

    return "File tidak ditemukan", 404


@folder_bp.route("/api/folders")
@login_required
def api_folders():
    req_path = request.args.get("path", "").strip()
    from config.settings import BASE_DIR
    
    # Default to project BASE_DIR if empty
    if not req_path:
        req_path = BASE_DIR
            
    abs_path = os.path.abspath(req_path)

    # Block exploration of critical OS system directories
    forbidden_paths = [
        "/etc", "/proc", "/sys", "/root", "/boot", "/dev", "/run", "/var/log",
        r"C:\Windows", r"C:\Program Files", r"C:\Program Files (x86)", r"C:\ProgramData"
    ]
    for forbidden in forbidden_paths:
        try:
            if abs_path == os.path.abspath(forbidden) or os.path.commonpath([abs_path, os.path.abspath(forbidden)]) == os.path.abspath(forbidden):
                return jsonify({"error": "Akses ke direktori sistem dibatasi.", "current": BASE_DIR, "folders": []}), 403
        except Exception:
            pass

    if not os.path.isdir(abs_path):
        return jsonify({"error": "Direktori tidak ditemukan."}), 400
        
    parent = os.path.dirname(abs_path)
    if parent == abs_path:
        parent = None
        
    try:
        items = os.listdir(abs_path)
        folders = []
        for item in items:
            try:
                full_path = os.path.join(abs_path, item)
                if os.path.isdir(full_path) and not item.startswith('.'):
                    folders.append(item)
            except Exception:
                pass
        folders.sort()
        return jsonify({
            "current": abs_path,
            "parent": parent,
            "folders": folders
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@folder_bp.route("/api/check_folder")
@login_required
def api_check_folder():
    raw_path = request.args.get("path", "").strip()
    if not raw_path:
        return jsonify({"valid": False, "exists": False, "message": "Jalur folder kosong"})
    
    abs_path = os.path.abspath(raw_path)
    if not os.path.exists(abs_path):
        return jsonify({"valid": False, "exists": False, "message": "Folder belum ada di server"})
    
    if not os.path.isdir(abs_path):
        return jsonify({"valid": False, "exists": True, "message": "Jalur yang dimasukkan adalah file, bukan folder"})
    
    # Count files
    try:
        valid_exts = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp')
        matching_count = 0
        total_files = 0
        for root, dirs, files in os.walk(abs_path):
            for f in files:
                total_files += 1
                if f.lower().endswith(valid_exts):
                    matching_count += 1
        
        return jsonify({
            "valid": True,
            "exists": True,
            "abs_path": abs_path,
            "total_files": total_files,
            "matching_count": matching_count,
            "message": f"Folder valid ({matching_count} dokumen terdeteksi)"
        })
    except Exception as e:
        return jsonify({"valid": False, "exists": True, "message": f"Akses folder terbatas: {str(e)}"})


@folder_bp.route("/api/subfolders")
@login_required
def api_subfolders():
    from services.storage_service import get_subfolders_info
    req_input = request.args.get("input_dir", "").strip() or db_model.input_dir

    if not req_input or not os.path.isdir(req_input):
        return jsonify({
            "status": "error",
            "message": "Direktori input tidak valid atau belum diset.",
            "subfolders": []
        }), 400

    subfolders = get_subfolders_info(req_input)
    return jsonify({
        "status": "success",
        "input_dir": req_input,
        "subfolders": subfolders
    })


