import os
import pytest

def test_safe_path_traversal_logic():
    base_folder = os.path.abspath(r"/var/ocr/output_pdf")
    
    # 1. Normal valid path
    valid_file = os.path.abspath(r"/var/ocr/output_pdf/subfolder/document.pdf")
    assert os.path.commonpath([valid_file, base_folder]) == base_folder

    # 2. Directory prefix confusion (e.g. output_pdf_secret)
    prefix_trap = os.path.abspath(r"/var/ocr/output_pdf_secret/document.pdf")
    assert os.path.commonpath([prefix_trap, base_folder]) != base_folder

    # 3. Directory traversal attempt with ..
    traversal = os.path.abspath(r"/var/ocr/output_pdf/../../etc/passwd")
    assert os.path.commonpath([traversal, base_folder]) != base_folder

def test_unauthenticated_access_blocked(client):
    # Protected endpoints must redirect to login
    protected_urls = ["/", "/documents", "/monitoring", "/analytics", "/settings"]
    for url in protected_urls:
        res = client.get(url, follow_redirects=False)
        assert res.status_code == 302
        assert "/login" in res.headers["Location"]
