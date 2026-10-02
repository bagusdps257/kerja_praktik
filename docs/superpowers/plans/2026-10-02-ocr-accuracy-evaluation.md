# Implementation Plan: OCR Accuracy and Quality Evaluation (F-17 / Tahap 8)

## Overview
Implementasi mekanisme evaluasi kualitas dan akurasi OCR mencakup algoritma Character Error Rate (CER) & Word Error Rate (WER), service layer, endpoint backend untuk inspeksi teks, modal web UI interaktif di halaman dokumen, skrip batch pengujian evaluasi perbandingan sebelum vs sesudah preprocessing untuk Laporan KP Bab 4, serta dataset sampel uji.

---

## Tasks

- [ ] Task 1: Accuracy Algorithm & Service Layer (`services/accuracy_service.py`)
  - [ ] Step 1: Tulis unit test di `tests/test_accuracy.py` untuk `calculate_cer_wer` dan ekstraksi teks PDF
  - [ ] Step 2: Jalankan pytest untuk memverifikasi test gagal (RED)
  - [ ] Step 3: Implementasikan algoritma Levenshtein distance, CER, WER, dan ekstraksi teks PyMuPDF di `services/accuracy_service.py`
  - [ ] Step 4: Jalankan pytest untuk memverifikasi test lolos (GREEN)
  - [ ] Step 5: Commit perubahan

- [ ] Task 2: Backend API Endpoints untuk Text Inspection & Accuracy
  - [ ] Step 1: Tambahkan test di `tests/test_accuracy.py` untuk endpoint `GET /documents/<filename>/inspect-text` dan `POST /documents/calculate-accuracy`
  - [ ] Step 2: Jalankan test untuk memverifikasi kegagalan
  - [ ] Step 3: Implementasikan endpoint di `routes/dashboard.py`
  - [ ] Step 4: Jalankan pytest untuk memverifikasi test lolos
  - [ ] Step 5: Commit perubahan

- [ ] Task 3: Interactive Web UI di `templates/documents.html`
  - [ ] Step 1: Tambahkan tombol aksi "Periksa Teks & Akurasi" di tabel dokumen
  - [ ] Step 2: Tambahkan modal `#accuracyModal` dengan tab ekstraksi teks & tab komparasi ground truth
  - [ ] Step 3: Tambahkan logika JavaScript untuk fetching teks, kalkulasi CER ke backend, dan render diff highlight
  - [ ] Step 4: Verifikasi kompilasi template Jinja & render test
  - [ ] Step 5: Commit perubahan

- [ ] Task 4: CLI Batch Evaluator (`tools/eval_accuracy.py`) & Sampel Data Uji
  - [ ] Step 1: Buat folder `data_uji/` berisi sampel dokumen uji dan teks ground truth acuan
  - [ ] Step 2: Buat skrip `tools/eval_accuracy.py` yang membandingkan baseline OCR vs enhanced OCR dan mencetak tabel Markdown
  - [ ] Step 3: Uji eksekusi skrip CLI dan verifikasi tabel output
  - [ ] Step 4: Commit perubahan

- [ ] Task 5: End-to-End Verification & Merge
  - [ ] Step 1: Jalankan seluruh test suite (`pytest -v`)
  - [ ] Step 2: Review dan finalisasi
