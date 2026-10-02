# Technical Design Specification: Authentic Industrial UI/UX Redesign (PT Jawa Satu Power)

## 1. Overview & Objectives
Desain antarmuka saat ini memiliki beberapa karakteristik visual yang sering diasosiasikan dengan "template AI modern" (misalnya: gradasi warna-warni pada tombol, efek melayang `translateY(-2px)` dengan drop-shadow tebal, animasi getar/glow, ikon *tech chip*, dan terminologi bergaya marketing bahasa Inggris/terjemahan kaku).

Tujuan perancangan ini adalah merekonstruksi UI/UX menjadi sistem internal korporat/industri yang **100% autentik, grounded, dan natural** untuk lingkungan **PT Jawa Satu Power (PLTGU Jawa-1)**:
1. **Gaya Visual Industri**: Menghilangkan seluruh gradasi warna-warni (`linear-gradient`), efek tombol melayang, dan animasi berlebihan. Mengadopsi palet warna korporat pembangkit listrik (*Deep Industrial Navy*, *Steel Slate*, *Forest Green*, dan *Crimson Brick*).
2. **Karakteristik Komponen**: Tombol dan kartu berorientasi solid, kokoh, dan presisi dengan aksen garis khas panel SCADA / sistem kearsipan enterprise.
3. **Simbol & Ikon**: Mengganti ikon generik (seperti `bi-cpu`, `bi-spellcheck`) dengan simbol operasional kearsipan riil (`bi-sliders2`, `bi-file-earmark-check`, `bi-journal-text`, `bi-person-badge`).
4. **Bahasa & Terminologi**: Redaksi bahasa Indonesia operasional murni yang lazim digunakan di instansi pembangkitan dan arsip teknis, bebas dari jargon marketing AI.

---

## 2. Palet Warna & Visual Identity (PT Jawa Satu Power)

| Peruntukan | Warna / Nilai | Karakteristik |
| :--- | :--- | :--- |
| **Brand Primary (Navy)** | `#0f3c68` (Hover: `#0a2947`, Focus ring: `#0f3c6833`) | Warna biru dongker korporat resmi untuk tombol utama, link aktif, dan header brand. |
| **Secondary (Steel Slate)** | `#334155` (Border: `#cbd5e1`, Background: `#f8fafc`) | Warna netral elemen pendukung, form border, dan tombol sekunder. |
| **Success / Export** | `#166534` (Hover: `#14532d`, Soft bg: `#f0fdf4`) | Warna solid tombol ekspor laporan dan badge sukses. |
| **Danger / Destructive** | `#991b1b` (Hover: `#7f1d1d`, Soft bg: `#fef2f2`) | Warna merah bata solid untuk tombol berhenti dan pembersihan database. |
| **Background Aplikasi** | `#f1f5f9` (Surface: `#ffffff`, Border: `#e2e8f0`) | Abu-abu lembut sejuk, tidak menyilaukan mata untuk durasi kerja panjang. |

---

## 3. Komponen yang Diredesain

### 3.1 Tombol (Buttons)
- **Hapus**: `.btn-gradient-*`, `transform: translateY(...)`, `box-shadow` tebal berwarna neon.
- **Terapkan**:
  - `.btn-primary`: Solid Navy `#0f3c68`, font weight 600, border radius 8px, transisi warna latar sederhana saat hover (tanpa loncat ke atas).
  - `.btn-danger` / `.btn-destructive`: Solid Dark Red `#991b1b`.
  - `.btn-success` / `.btn-export`: Solid Dark Green `#166534`.
  - `.btn-secondary` / `.btn-light`: Border tipis abu-abu baja `#cbd5e1` dengan background `#ffffff`.

### 3.2 Kartu Metrik & Panel (Cards)
- **Hapus**: Efek melayang `kpi-card:hover { transform: translateY(-3px); }`.
- **Terapkan**: Struktur kontainer kokoh dengan border `1px solid #e2e8f0`, border radius 10px, dan strip aksen border 3px di bagian atas kartu untuk memberikan identitas fungsional yang tegas (SCADA/Industrial Panel look).

### 3.3 Sidebar & Navigasi
- Logo sidebar: Menggunakan lencana resmi berlatar Navy `#0f3c68` dengan monogram/ikon berkas operasional.
- Menu aktif: Highlight solid Navy `#0f3c68` dengan teks putih bersih, bukan gradasi dengan bayangan biru terang.

### 3.4 Terminologi & Redaksi Teks
- Header: **"Sistem Digitalisasi Dokumen Operasional"** — *PT Jawa Satu Power (PLTGU Jawa-1)*.
- Folder: **"Direktori Berkas Masuk"** dan **"Direktori Arsip Searchable PDF"**.
- Tombol: **"Mulai Pemrosesan Berkas"** dan **"Hentikan Pemrosesan"**.
- Role: **"Operator Sistem"** (akses penuh & kelola akun) dan **"Staf Operasional"** (eksekusi konversi & penelusuran dokumen).
- Evaluasi: **"Evaluasi Akurasi Pembacaan Karakter (CER & WER)"**.
- Ekspor: **"Unduh Laporan Excel"** dan **"Unduh Cadangan SQL"**.
