# Technical Design Specification: OCR Accuracy and Quality Evaluation (F-17 / Tahap 8)

## 1. Overview
Berdasarkan arahan Dosen Bimbingan KP (*Panduan Bimbingan Kerja Praktik - Kelompok Said & Bagus*, Kebutuhan Fungsional F-17 & Tahap 8 Alur Kerja), sistem tidak boleh berhenti pada "file PDF berhasil dibuat", melainkan harus menyediakan mekanisme untuk memeriksa kualitas dan mengukur akurasi teks hasil OCR.

Fitur ini menyediakan:
1. **Interactive Web UI**: Modal inspeksi teks hasil OCR per dokumen dan kalkulator komparasi teks acuan (*Ground Truth*) yang menghitung metrik *Character Error Rate* (CER) dan *Word Error Rate* (WER) secara seketika dengan visual diff highlight.
2. **Service Layer**: Algoritma perhitungan Levenshtein edit-distance untuk karakter dan kata serta ekstraktor teks dari Searchable PDF.
3. **Batch Accuracy Evaluator CLI (`tools/eval_accuracy.py`)**: Skrip pengujian otomatis untuk memproses sekumpulan sampel dokumen uji, membandingkan performa OCR **Tanpa Preprocessing** vs **Dengan Preprocessing**, serta mencetak tabel metrik CER (%) dan throughput waktu (detik) untuk Bab 4 Laporan KP.
4. **Data Uji Sampel (`data_uji/`)**: Sampel dokumen uji dengan variasi kualitas dan teks referensi ground truth.

---

## 2. Metrik Akademik & Algoritma

### 2.1 Character Error Rate (CER)
CER mengukur persentase kesalahan karakter antara teks referensi ($T_{ref}$) dan teks hasil OCR ($T_{hyp}$):
$$\text{CER} = \frac{S + D + I}{N} \times 100\%$$
- $S$ (*Substitutions*): Jumlah karakter yang salah dikenali (misal `'O'` dibaca `'0'`).
- $D$ (*Deletions*): Jumlah karakter yang hilang/terlewat.
- $I$ (*Insertions*): Jumlah karakter noise tambahan yang tidak ada di teks asli.
- $N$: Jumlah total karakter pada teks referensi ($|T_{ref}|$).
- **Akurasi Karakter**: $\max(0.0\%, 100\% - \text{CER})$.

### 2.2 Word Error Rate (WER)
WER mengukur kesalahan pada level kata (token terpisah spasi):
$$\text{WER} = \frac{S_w + D_w + I_w}{N_w} \times 100\%$$
- **Akurasi Kata**: $\max(0.0\%, 100\% - \text{WER})$.

### 2.3 Visual Diff Highlight
Tokenisasi teks komparasi menghasilkan token berlabel status:
- `equal`: Karakter/kata identik (ditampilkan teks normal/hijau).
- `replace`: Karakter/kata substitusi/salah (ditampilkan teks kuning).
- `delete`: Karakter/kata yang hilang di OCR (ditampilkan teks merah tercoret).
- `insert`: Karakter/kata noise yang muncul di OCR (ditampilkan teks biru).

---

## 3. Komponen & Arsitektur

### 3.1 Service Layer (`services/accuracy_service.py`)
- `calculate_cer_wer(reference_text: str, hypothesis_text: str) -> dict`:
  Menghitung $S, D, I, N$, nilai CER, WER, akurasi, dan diff tokens.
- `extract_pdf_text(filepath: str) -> dict`:
  Membaca berkas PDF keluaran menggunakan `fitz` (PyMuPDF), mengekstrak teks per halaman, total karakter, total kata, dan metadata.

### 3.2 Endpoints (`routes/dashboard.py`)
- `GET /documents/<path:filename>/inspect-text`
  - Parameter: `filename` (document key relatif dalam output folder).
  - Mengembalikan JSON: `{ status: "success", nama_file, page_count, full_text, pages: [...] }`.
  - Proteksi: `@login_required`.
- `POST /documents/calculate-accuracy`
  - Body JSON: `{ reference_text: "...", ocr_text: "..." }`.
  - Mengembalikan JSON: `{ status: "success", metrics: { cer, character_accuracy, wer, word_accuracy, ... }, diff: [...] }`.
  - Proteksi: `@login_required`.

### 3.3 Antarmuka Web (`templates/documents.html`)
- Tombol aksi `bi bi-spellcheck` ("Periksa Teks & Akurasi") pada setiap baris riwayat tabel dokumen berstatus `SUKSES` / `SKIP`.
- Modal interaktif `#accuracyModal`:
  - **Tab 1: Ekstraksi Teks Lengkap**: Menampilkan teks yang diekstrak per halaman dengan tombol salin cepat (*copy to clipboard*).
  - **Tab 2: Uji Akurasi (Ground Truth)**:
    - Textarea teks OCR (terisi otomatis).
    - Textarea teks acuan (*Ground Truth*) yang dapat diisi pengguna.
    - Tombol "Hitung Akurasi (CER & WER)".
    - KPI Cards: Nilai CER (%), Akurasi Karakter (%), WER (%), Akurasi Kata (%).
    - Rincian: Jumlah Karakter, Substitusi, Deletion, Insertion.
    - Diff viewer interaktif.

### 3.4 CLI Evaluator (`tools/eval_accuracy.py`) & Sampel Data
- Script mandiri yang dapat dipanggil:
  `python tools/eval_accuracy.py --sample-dir data_uji/samples --ground-truth-dir data_uji/ground_truth`
- Menjalankan 2 mode OCR:
  1. *Raw OCR* (tanpa preprocessing).
  2. *Enhanced OCR* (Grayscale + Contrast + Sharpening).
- Mencetak tabel komparasi CER dan waktu proses dalam format Markdown tabel.

---

## 4. Rencana Pengujian
1. Unit test untuk algoritma CER & WER di `tests/test_accuracy.py`:
   - Teks identik -> CER = 0%, Akurasi = 100%.
   - Substitusi, deletion, insertion -> Perhitungan metrik akurat.
   - String kosong / edge case handling.
2. Endpoint integration test:
   - `GET /documents/<filename>/inspect-text` -> status 200, mengembalikan teks valid.
   - `POST /documents/calculate-accuracy` -> status 200, mengembalikan metrik yang benar.
3. Batch CLI test:
   - Menjalankan evaluasi pada sampel dokumen uji dan memverifikasi keluaran tabel.
