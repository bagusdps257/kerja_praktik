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

    allowed_fields = ("input_dir", "output_dir")
    
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
    clean_filename = filename.strip('/')
    target = os.path.abspath(os.path.join(folder_output, clean_filename))

    # Direct check
    if target.startswith(folder_output) and os.path.isfile(target):
        return send_from_directory(os.path.dirname(target), os.path.basename(target))

    # Search by relative path or basename fallback
    file_basename = os.path.basename(clean_filename)
    for root, dirs, files in os.walk(folder_output):
        if file_basename in files:
            return send_from_directory(root, file_basename)

    return "File tidak ditemukan", 404


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
