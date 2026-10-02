import pytest
import os
import fitz
from services.accuracy_service import calculate_cer_wer, extract_pdf_text


def test_cer_identical_text():
    ref = "PT JAWA SATU POWER"
    hyp = "PT JAWA SATU POWER"
    result = calculate_cer_wer(ref, hyp)

    assert result["cer"] == 0.0
    assert result["character_accuracy"] == 100.0
    assert result["wer"] == 0.0
    assert result["word_accuracy"] == 100.0
    assert result["substitutions"] == 0
    assert result["deletions"] == 0
    assert result["insertions"] == 0
    assert result["total_reference_chars"] == len(ref)


def test_cer_substitution_and_diff():
    # Case: lecturer's example where 'Indonesia' is misspelled
    ref = "Indonesia"
    hyp = "Ind0nesia"  # 'o' replaced with '0'
    result = calculate_cer_wer(ref, hyp)

    assert result["substitutions"] == 1
    assert result["deletions"] == 0
    assert result["insertions"] == 0
    assert result["total_reference_chars"] == 9
    assert round(result["cer"], 2) == round((1 / 9) * 100, 2)
    assert round(result["character_accuracy"], 2) == round(100.0 - (1 / 9) * 100, 2)
    assert "diff_tokens" in result


def test_cer_deletion_and_insertion():
    # Deletion: characters missing in hypothesis
    ref = "PLTGU JAWA SATU"
    hyp = "PLTGU JAWA"  # " SATU" missing (5 chars)
    res_del = calculate_cer_wer(ref, hyp)
    assert res_del["deletions"] == 5
    assert res_del["total_reference_chars"] == len(ref)

    # Insertion: extra noisy characters in hypothesis
    ref2 = "MESIN TURBIN"
    hyp2 = "MESIN TURBIN XYZ"  # " XYZ" inserted (4 chars)
    res_ins = calculate_cer_wer(ref2, hyp2)
    assert res_ins["insertions"] == 4


def test_cer_empty_and_whitespace_edge_cases():
    # Both empty
    assert calculate_cer_wer("", "")["cer"] == 0.0
    assert calculate_cer_wer("", "")["character_accuracy"] == 100.0

    # Reference empty, hypothesis non-empty
    res1 = calculate_cer_wer("", "teks tambahan")
    assert res1["cer"] == 100.0
    assert res1["character_accuracy"] == 0.0

    # Reference non-empty, hypothesis empty
    res2 = calculate_cer_wer("teks referensi", "")
    assert res2["cer"] == 100.0
    assert res2["character_accuracy"] == 0.0


def test_extract_pdf_text_from_file(tmp_path):
    # Create a temporary PDF with PyMuPDF
    pdf_path = str(tmp_path / "sample_test.pdf")
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 100), "Dokumen Uji Akurasi OCR Jawa Satu Power", fontsize=14)
    doc.save(pdf_path)
    doc.close()

    result = extract_pdf_text(pdf_path)
    assert result["success"] is True
    assert result["page_count"] == 1
    assert "Dokumen Uji Akurasi" in result["full_text"]
    assert len(result["pages"]) == 1
    assert result["pages"][0]["char_count"] > 0
    assert result["pages"][0]["word_count"] > 0


def test_inspect_text_and_calculate_accuracy_endpoints(client, app, test_user, tmp_path, monkeypatch):
    # 1. Login user
    client.post("/login", data={"username": "admin_test", "password": "password123"})

    # 2. Setup mock output directory with a sample PDF
    from models.model_provider import db_model
    monkeypatch.setattr(db_model, "output_dir", str(tmp_path))

    sample_pdf = str(tmp_path / "report_2026.pdf")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "Laporan Operasional Turbin PLTGU Jawa Satu", fontsize=12)
    doc.save(sample_pdf)
    doc.close()

    # 3. Test GET /documents/<filename>/inspect-text
    res_inspect = client.get("/documents/report_2026.pdf/inspect-text")
    assert res_inspect.status_code == 200
    data_inspect = res_inspect.get_json()
    assert data_inspect["success"] is True
    assert "Turbin PLTGU" in data_inspect["full_text"]
    assert data_inspect["page_count"] == 1

    # 4. Test POST /documents/calculate-accuracy
    res_calc = client.post("/documents/calculate-accuracy", json={
        "reference_text": "Laporan Operasional Turbin PLTGU Jawa Satu",
        "ocr_text": "Laporan 0perasional Turbin PLTGU Jawa Satu"
    })
    assert res_calc.status_code == 200
    data_calc = res_calc.get_json()
    assert data_calc["success"] is True
    assert "metrics" in data_calc
    assert data_calc["metrics"]["substitutions"] == 1
    assert data_calc["metrics"]["character_accuracy"] > 95.0
    assert "diff_tokens" in data_calc["metrics"]

