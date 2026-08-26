import pytest
from models.dashboard_model import OCRDashboardModel, Riwayat
from models.extensions import db

def test_catat_ke_db_create_and_update(app):
    with app.app_context():
        model = OCRDashboardModel()
        
        # 1. First record insert
        success = model.catat_ke_db(
            document_key="folder/invoice_001.pdf",
            folder_path="folder",
            nama_file="invoice_001.pdf",
            status="SUKSES",
            keterangan="OCR selesai",
            file_size="1.2 MB",
            author="Finance Team",
            subject="Monthly Invoice",
            keywords="invoice, payment",
            page_count="3",
            creation_date="2026-08-01",
            processing_time=1.45,
            retry_count=0
        )
        assert success is True

        row = Riwayat.query.filter_by(document_key="folder/invoice_001.pdf").first()
        assert row is not None
        assert row.author == "Finance Team"
        assert row.subject == "Monthly Invoice"
        assert row.keywords == "invoice, payment"
        assert row.status == "SUKSES"

        # 2. Update existing record without creating duplicate ID
        model.catat_ke_db(
            document_key="folder/invoice_001.pdf",
            folder_path="folder",
            nama_file="invoice_001.pdf",
            status="SUKSES",
            keterangan="Diperbarui",
            author="Finance Team Senior",
            subject="Monthly Invoice Updated",
            keywords="invoice, approved",
            processing_time=1.10,
            retry_count=1
        )

        total_rows = Riwayat.query.filter_by(document_key="folder/invoice_001.pdf").count()
        assert total_rows == 1  # No duplicate rows!

        updated_row = Riwayat.query.filter_by(document_key="folder/invoice_001.pdf").first()
        assert updated_row.author == "Finance Team Senior"
        assert updated_row.subject == "Monthly Invoice Updated"
        assert updated_row.keywords == "invoice, approved"
        assert updated_row.retry_count == 1
