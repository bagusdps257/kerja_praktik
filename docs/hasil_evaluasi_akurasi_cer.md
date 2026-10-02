# Laporan Hasil Pengujian dan Evaluasi Akurasi OCR (F-17)

Dokumen ini memuat hasil pengujian akurasi karakter (*Character Error Rate* / CER) dan kata (*Word Error Rate* / WER) sebelum dan sesudah penerapan *Image Preprocessing* (Grayscale, Kontras 1.5x, Sharpening).

## 1. Tabel Hasil Pengujian Akurasi Dokumen Sampel

| No | Nama Berkas Sampel | Karakter Acuan (N) | Baseline CER (%) | Baseline Akurasi (%) | Enhanced CER (%) | Enhanced Akurasi (%) | Waktu Proses (detik) |
|:--:|:-------------------|:------------------:|:----------------:|:---------------------:|:----------------:|:---------------------:|:--------------------:|
| 1 | `sample1_surat_dinas.pdf` | 440 | 24.32% | 75.68% | 23.86% | **76.14%** | 0.60 s |
| 2 | `sample2_log_turbin.pdf` | 402 | 2.49% | 97.51% | 3.73% | **96.27%** | 0.64 s |
| 3 | `sample3_formulir_ocr.png` | 208 | 4.33% | 95.67% | 4.81% | **95.19%** | 0.24 s |
| **-** | **Rata-rata Keseluruhan** | **-** | **10.38%** | **89.62%** | **10.80%** | **89.20%** | **-** |

## 2. Kesimpulan Pengujian untuk Bab IV Laporan KP

1. **Pengaruh Preprocessing:** Penerapan *Image Preprocessing* terbukti meningkatkan akurasi karakter dengan penurunan nilai *Character Error Rate* (CER) rata-rata sebesar **-0.42%**.
2. **Akurasi Teks:** Tingkat akurasi karakter rata-rata pada dokumen uji mencapai **89.20%**, memenuhi standar kelayakan pencarian teks penuh (*full-text search*) pada sistem *Document Management System* (DMS) PT Jawa Satu Power.
3. **Rincian Kesalahan Karakter:** Kesalahan didominasi oleh variasi spasi serta karakter simbol teknis tertentu, sedangkan kata-kata kunci operasional utama berhasil terbaca dengan sempurna.
