import os
import pytest
from services.storage_service import get_subfolders_info
from models.extensions import db
import core_engine

def test_get_subfolders_info_service(tmp_path):
    input_dir = tmp_path / "input_pdf"
    input_dir.mkdir()

    sub1 = input_dir / "input 17"
    sub1.mkdir()
    (sub1 / "doc1.pdf").write_bytes(b"%PDF-1.4 dummy 1")
    (sub1 / "doc2.pdf").write_bytes(b"%PDF-1.4 dummy 2")
    (sub1 / "notes.txt").write_text("ignore non-image/pdf")

    sub2 = input_dir / "batch_other"
    sub2.mkdir()
    (sub2 / "sample.pdf").write_bytes(b"%PDF-1.4 dummy 3")

    info = get_subfolders_info(str(input_dir))
    assert len(info) == 2

    info_map = {item["name"]: item for item in info}
    assert "input 17" in info_map
    assert info_map["input 17"]["file_count"] == 2

    assert "batch_other" in info_map
    assert info_map["batch_other"]["file_count"] == 1

def test_api_subfolders_endpoint(client, test_user, tmp_path):
    client.post("/login", data={
        "username": "admin_test",
        "password": "password123"
    }, follow_redirects=True)

    input_dir = tmp_path / "test_input"
    input_dir.mkdir()
    sub = input_dir / "input 17"
    sub.mkdir()
    (sub / "report.pdf").write_bytes(b"%PDF-1.4 test")

    res = client.get(f"/api/subfolders?input_dir={str(input_dir)}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert len(data["subfolders"]) == 1
    assert data["subfolders"][0]["name"] == "input 17"
    assert data["subfolders"][0]["file_count"] == 1

def test_engine_control_section_contains_target_dropdown(client, test_user):
    client.post("/login", data={
        "username": "admin_test",
        "password": "password123"
    }, follow_redirects=True)

    res = client.get('/')
    assert res.status_code == 200
    html = res.data.decode('utf-8')

    assert 'id="target_subfolder"' in html
    assert 'name="target_subfolder"' in html
    assert 'id="btn-scan-subfolders"' in html
    assert 'Cakupan Pemrosesan (Target Subfolder)' in html

def test_core_engine_target_subfolder_invalid(tmp_path, app):
    input_dir = str(tmp_path / "input")
    output_dir = str(tmp_path / "output")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Subfolder does not exist
    core_engine.jalankan_sistem_ocr(
        input_dir,
        output_dir,
        flask_app=app,
        target_subfolder="non_existent_folder_xyz"
    )

    prog = core_engine.ambil_progress()
    assert prog["status"] == "ERROR"
