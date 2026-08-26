import io
import pytest
import openpyxl
from models.dashboard_model import OCRDashboardModel, Riwayat

def test_export_excel_structure(app, test_user, client):
    with app.app_context():
        # Insert sample riwayat
        model = OCRDashboardModel()
        model.catat_ke_db(
            document_key="test_dir/report_2026.pdf",
            folder_path="test_dir",
            nama_file="report_2026.pdf",
            status="SUKSES",
            keterangan="Sukses",
            file_size="500 KB",
            author="PLTU Unit 1",
            subject="Turbine Status",
            keywords="turbine, maintenance",
            page_count="5",
            creation_date="2026-08-15",
            processing_time=2.1,
            retry_count=0
        )

    # Login first
    client.post("/login", data={
        "username": "admin_test",
        "password": "password123"
    })

    # Trigger export
    res = client.get("/export_excel")
    assert res.status_code == 200
    assert res.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    # Verify openpyxl can parse the generated binary workbook
    wb = openpyxl.load_workbook(io.BytesIO(res.data))
    assert "Ringkasan" in wb.sheetnames
    assert "Data Lengkap" in wb.sheetnames

    sheet_data = wb["Data Lengkap"]
    # Check headers and row content
    headers = [cell.value for cell in sheet_data[1]]
    assert "Nama File" in headers
    assert "Subject" in headers
    assert "Keywords" in headers
    assert "Author" in headers

    # Verify data row
    row_values = [cell.value for cell in sheet_data[2]]
    assert "report_2026.pdf" in row_values
    assert "PLTU Unit 1" in row_values
    assert "Turbine Status" in row_values
