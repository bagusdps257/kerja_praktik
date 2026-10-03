---
title: "Proposal_KP_OCR_DMS_Revisi (1)"
date: "2026-08-17"
original_file: "Proposal_KP_OCR_DMS_Revisi (1).docx"
words: 3820
---

**PROPOSAL KERJA PRAKTIK**

**PENGEMBANGAN DOCUMENT MANAGEMENT SYSTEM BERBASIS OPTICAL CHARACTER RECOGNITION (OCR) UNTUK DIGITALISASI DAN PENCARIAN DOKUMEN DI PT JAWA SATU POWER**

*Diajukan Sebagai Salah Satu Syarat Melaksanakan Kerja Praktik*

\[ LOGO UNIVERSITAS JENDERAL ACHMAD YANI \]

Disusun Oleh:

**Bagus Dwi Putra Setiawan**

NIM: 3411221XXX

Kelas A

**PROGRAM STUDI INFORMATIKA**

**FAKULTAS SAINS DAN INFORMATIKA**

**UNIVERSITAS JENDERAL ACHMAD YANI**

**CIMAHI**

**2026**

**DAFTAR ISI**

1\. Judul Kerja Praktik 3

2\. Deskripsi Singkat Masalah/Kebutuhan 3

2.1 Latar Belakang Masalah 3

2.2 Rumusan Masalah 5

2.3 Batasan Masalah 5

2.4 Maksud dan Tujuan Kerja Praktik 7

2.5 Teori Pendukung 8

2.6 Sejarah Perusahaan 11

2.7 Gambaran Umum Sistem 12

2.8 Jadwal Kegiatan 16

3\. Daftar Literatur 17

*Catatan berkas: dokumen ini memuat bagian Materi Kerja Praktik (butir 9 pada Sistematika Proposal KP) yaitu Judul, Deskripsi Singkat Masalah/Kebutuhan, dan Daftar Literatur. Halaman administratif lain yang disyaratkan pada urutan dokumen proposal — Lampiran Form KP-F01, Halaman Penunjukan Dosen Reviewer, Berita Acara Review Proposal, Berita Acara Review Ulang, Pengajuan Dosen Pembimbing, dan Kesediaan Menjadi Dosen Pembimbing — disiapkan sebagai berkas administratif terpisah sesuai prosedur program studi dan akan disatukan pada bundel proposal final.*

**1\. JUDUL KERJA PRAKTIK**

Pengembangan Document Management System Berbasis Optical Character Recognition (OCR) untuk Digitalisasi dan Pencarian Dokumen di PT Jawa Satu Power.

**2\. DESKRIPSI SINGKAT MASALAH/KEBUTUHAN**

PT Jawa Satu Power, sebagai perusahaan yang mengoperasikan Pembangkit Listrik Tenaga Gas Uap (PLTGU) Jawa-1, mengelola berbagai dokumen operasional dalam jumlah yang cukup besar, seperti manual instruksi, laporan inspeksi, dan dokumen administratif lainnya. Berdasarkan pengamatan awal, sebagian dokumen tersebut—khususnya dokumen historis atau hasil pemindaian (scanning)—masih berbentuk gambar atau berkas PDF yang belum memiliki lapisan teks (non-searchable), sehingga isinya belum dapat ditelusuri secara otomatis melalui pencarian kata kunci.

Untuk merespons kebutuhan tersebut, kerja praktik ini difokuskan pada pengembangan Document Management System (DMS) berbasis web yang dilengkapi teknologi Optical Character Recognition (OCR) untuk mendigitalisasi dokumen, dengan tiga komponen pendukung utama: (1) image preprocessing untuk meningkatkan kualitas hasil OCR, (2) pemrosesan paralel (multiprocessing) untuk mempercepat konversi dokumen dalam jumlah besar, dan (3) dashboard monitoring agar administrator dapat memantau status proses OCR yang sedang berjalan.

*Catatan: kondisi pengelolaan dokumen di atas merupakan asumsi awal berdasarkan pengamatan sekilas dan literatur umum industri sejenis. Kondisi aktual di PT Jawa Satu Power—termasuk volume dokumen, format yang dominan, serta proses pencarian dokumen yang berjalan saat ini—akan divalidasi melalui observasi/survei lapangan pada minggu pertama pelaksanaan kerja praktik (Form KP-F01), dan uraian pada proposal ini akan disesuaikan bila diperlukan.*

**2.1 Latar Belakang Masalah**

Transformasi digital menuntut setiap organisasi, termasuk perusahaan pembangkit listrik, untuk mengelola informasi secara lebih efisien. Di lingkungan industri energi, kecepatan menemukan dokumen teknis—seperti manual operasi atau laporan inspeksi—berkaitan erat dengan kecepatan pengambilan keputusan dan efisiensi operasional. PT Jawa Satu Power, sebagaimana perusahaan pembangkit skala besar pada umumnya, berpotensi menghadapi tantangan serupa: sebagian dokumen yang dikelola berupa hasil pemindaian yang belum dapat ditelusuri isinya secara otomatis.

Ketika dokumen hanya dapat ditelusuri berdasarkan nama berkas atau metadata yang dimasukkan secara manual, proses pencarian menjadi rentan terhadap kesalahan manusia dan ketidakkonsistenan penamaan. Teknologi Optical Character Recognition (OCR) menawarkan solusi dengan mengonversi teks pada gambar menjadi teks yang dapat dibaca dan dicari oleh mesin. Akan tetapi, akurasi OCR sangat dipengaruhi oleh kualitas citra input; dokumen hasil pemindaian sering kali memiliki noise, kontras rendah, atau resolusi yang tidak merata. El Harraj dan Raissouni (2015) melaporkan bahwa penerapan tahapan image preprocessing berupa penyesuaian kontras, konversi grayscale, dan penajaman (sharpening) sebelum OCR dapat meningkatkan akurasi karakter secara terukur pada dokumen uji mereka, sehingga tahapan serupa diadopsi sebagai bagian dari pipeline pemrosesan pada sistem yang akan dibangun.

Selain isu akurasi, volume dokumen yang besar menuntut efisiensi waktu pemrosesan. Pemrosesan dokumen secara berurutan (sequential) menjadi kurang efisien ketika jumlah dokumen mencapai ratusan atau ribuan berkas. Oleh karena itu, kerja praktik ini juga menerapkan pemrosesan paralel berbasis multiprocessing pada satu mesin server—bukan pemrosesan terdistribusi lintas beberapa server—untuk memanfaatkan beberapa inti CPU secara bersamaan guna meningkatkan throughput konversi dokumen.

Dari sisi penyimpanan, sistem menggunakan basis data relasional MySQL untuk menyimpan data pengguna, metadata dokumen, riwayat pemrosesan, serta indeks teks hasil OCR yang mendukung pencarian teks penuh (full-text search). Pemilihan MySQL didasarkan pada kebutuhan relasi antar-entitas (pengguna, dokumen, riwayat pemrosesan) dan konsistensi transaksi, dan bukan semata-mata karena volume data yang besar—mengingat beban komputasi terberat pada sistem ini sesungguhnya terletak pada tahap rendering PDF, image preprocessing, dan OCR, bukan pada operasi basis data.

Berdasarkan uraian tersebut, kerja praktik ini difokuskan untuk mengembangkan Document Management System berbasis Optical Character Recognition untuk digitalisasi dan pencarian dokumen di PT Jawa Satu Power, dengan harapan dapat membantu perusahaan memiliki repositori dokumen digital yang lebih mudah ditelusuri isinya.

**2.2 Rumusan Masalah**

Berdasarkan uraian pada latar belakang, rumusan masalah dalam kerja praktik ini adalah:

1\. Bagaimana membangun aplikasi Document Management System berbasis web yang terintegrasi dengan teknologi OCR untuk mendigitalisasi dokumen hasil pemindaian menjadi dokumen yang dapat dicari (searchable) di PT Jawa Satu Power?

2\. Bagaimana menerapkan teknik image preprocessing dan pemrosesan paralel (multiprocessing) untuk meningkatkan akurasi dan efisiensi waktu proses OCR pada dokumen dalam jumlah besar?

3\. Bagaimana merancang dashboard monitoring yang dapat menampilkan status, progres, dan log proses OCR secara real-time bagi administrator?

**2.3 Batasan Masalah**

Agar kerja praktik ini lebih terarah, ditetapkan batasan masalah sebagai berikut.

**Cakupan Inti (Fokus Utama)**

1\. Sistem memproses input berupa berkas PDF dan gambar (PNG, JPG, JPEG, TIFF, BMP, WEBP).

2\. Proses OCR dikonfigurasi untuk mengenali bahasa Indonesia dan bahasa Inggris (ind+eng) menggunakan Tesseract OCR versi 5 melalui pustaka pytesseract.

3\. Aplikasi web dibangun menggunakan Python 3.8+ dengan framework Flask beserta arsitektur Blueprint.

4\. Basis data menggunakan MySQL yang diakses melalui ORM Flask-SQLAlchemy dan PyMySQL. Mekanisme fallback ke SQLite untuk lingkungan pengembangan akan dipertimbangkan sebagai penyempurnaan konfigurasi pada tahap implementasi apabila diperlukan; pada purwarupa saat ini konfigurasi basis data masih mengarah langsung ke MySQL tanpa fallback.

5\. Output sistem mencakup dua hal yang secara konsep berbeda: (a) Searchable PDF, yaitu berkas PDF dengan lapisan teks hasil OCR yang dapat dicari menggunakan Ctrl+F pada berkas tersebut; dan (b) indeks teks pada basis data yang mendukung pencarian teks penuh (full-text search) lintas dokumen di dalam aplikasi.

6\. Sistem dikembangkan untuk lingkungan multi-user dengan peran Admin dan User; kolom peran (role) pada model pengguna serta pembatasan akses admin/user akan diimplementasikan pada tahap awal kerja praktik. Akun pengguna direncanakan dibuat oleh Administrator, bukan melalui pendaftaran mandiri (self-register), mengikuti pola umum sistem internal perusahaan. Pada purwarupa yang ada saat ini, halaman pendaftaran (register) masih dapat diakses secara publik tanpa pembatasan peran; hal ini akan disesuaikan pada tahap implementasi awal kerja praktik agar konsisten dengan desain akses berbasis peran di atas, dan ketentuan akhir akan dikonfirmasi kembali bersama pembimbing lapangan pada tahap observasi.

7\. Keamanan tingkat dasar diterapkan berupa proteksi CSRF dan hashing kata sandi menggunakan Werkzeug Security.

8\. Peningkatan kinerja dicapai melalui pemrosesan paralel multi-core pada satu server menggunakan modul Python ProcessPoolExecutor, bukan pemrosesan terdistribusi lintas mesin.

**Fitur Pendukung (Menyesuaikan Ketersediaan Waktu)**

9\. Dashboard ringkasan (KPI card), log proses real-time (bukan terminal interaktif), dan indikator antrean dokumen (worker queue).

10\. Fitur Smart Skip untuk melewati dokumen yang telah memiliki lapisan teks native agar tidak diproses ulang oleh OCR.

11\. Ekspor log dan metadata ke format Excel.

12\. Penanganan kesalahan dasar: dokumen yang gagal diproses dicatat statusnya sebagai failed dan proses dilanjutkan ke dokumen berikutnya.

Di luar cakupan kerja praktik ini adalah keamanan tingkat produksi (production-grade security), skema fault tolerance kompleks (retry berlapis dengan exponential backoff), fitur pencadangan basis data otomatis sebagai fitur inti, author leaderboard, serta kontrol pause/resume granular per halaman dokumen. Butir-butir tersebut berpotensi menjadi arah pengembangan lanjutan di luar kerja praktik ini.

**2.4 Maksud dan Tujuan Kerja Praktik**

**Maksud**

Maksud dari pelaksanaan kerja praktik ini adalah untuk menerapkan dan mengintegrasikan ilmu pengetahuan dalam bidang rekayasa perangkat lunak, pemrosesan citra digital, dan pemrosesan paralel yang telah dipelajari di bangku perkuliahan ke dalam studi kasus nyata di lingkungan industri pembangkit listrik.

**Tujuan**

1\. Membangun aplikasi DMS berbasis web yang mengonversi dokumen hasil pemindaian menjadi dokumen yang dapat dicari (Searchable PDF) serta terindeks untuk pencarian teks penuh (full-text search).

2\. Menerapkan pipeline image preprocessing (grayscale, contrast enhancement, sharpening) menggunakan pustaka Pillow, serta mengukur pengaruhnya terhadap akurasi OCR menggunakan metrik Character Error Rate (CER) pada berkas uji, sebelum dan sesudah preprocessing.

3\. Mengimplementasikan pemrosesan paralel multi-core menggunakan ProcessPoolExecutor, serta membandingkan waktu pemrosesan antara skema sequential dan paralel (misalnya 2, 4, dan 8 worker) pada jumlah dokumen uji tertentu untuk mengevaluasi peningkatan throughput.

4\. Merancang dashboard monitoring yang menyajikan progress bar, log status proses secara real-time, dan indikator antrean dokumen, tanpa menyediakan akses shell/terminal ke server.

5\. Membangun modul analitik dasar berbasis Chart.js sebagai fitur pendukung untuk memvisualisasikan tren pemrosesan dokumen.

6\. Mengimplementasikan sistem autentikasi multi-user berbasis Flask-Login dengan peran Admin/User dan proteksi CSRF, dengan akun yang disediakan oleh Administrator.

**2.5 Teori Pendukung**

**a. Optical Character Recognition (OCR)**

OCR adalah teknologi yang secara otomatis mendeteksi dan mengekstraksi teks dari gambar digital atau dokumen pindaian, lalu mengubahnya menjadi karakter yang dikodekan mesin sehingga dapat dicari, disalin, atau diedit. OCR berperan penting dalam digitalisasi dokumen arsip cetak menjadi basis data yang terstruktur.

**b. Metrik Evaluasi OCR: Character Error Rate (CER) dan Word Error Rate (WER)**

CER dan WER adalah metrik umum untuk mengevaluasi kinerja OCR dengan membandingkan teks hasil ekstraksi terhadap teks acuan (ground truth), dihitung dari jumlah penyisipan, penghapusan, dan substitusi karakter atau kata yang diperlukan agar kedua teks sama. Darpito, Firdausy, dan Fadlil (2025) membandingkan Tesseract dan EasyOCR pada dokumen digital berbahasa Indonesia menggunakan WER dan CER, dan menemukan bahwa Tesseract secara konsisten lebih cepat memproses dokumen dibandingkan EasyOCR, meskipun EasyOCR menghasilkan WER yang lebih rendah pada dokumen formulir yang diuji. Rahmdani (2025) mengevaluasi kinerja Tesseract pada teks tulisan tangan berbahasa Indonesia dan melaporkan CER rata-rata di atas 30% untuk kasus tersebut, yang menunjukkan bahwa akurasi Tesseract sangat bergantung pada jenis dan kualitas dokumen yang diproses. Kedua penelitian ini menjadi acuan bagi rencana pengujian akurasi pada kerja praktik ini.

**c. Image Preprocessing untuk OCR**

Sebelum OCR dijalankan, citra dokumen umumnya melalui tahap prapemrosesan untuk meningkatkan peluang keberhasilan pengenalan karakter. Konversi ke grayscale menyederhanakan citra dengan membuang informasi warna yang tidak diperlukan; contrast enhancement memperjelas perbedaan antara latar belakang dan teks; sedangkan sharpening (unsharp masking) mempertegas tepi (edge) huruf. El Harraj dan Raissouni (2015) mengusulkan pipeline serupa (penyesuaian kontras, konversi grayscale, unsharp masking, dan binarisasi) dan melaporkan peningkatan akurasi karakter antara sekitar 2% hingga 6,8% pada dataset uji mereka dibandingkan tanpa preprocessing. Angka tersebut bersifat indikatif dari studi lain dan akan diverifikasi ulang pada dataset dokumen milik PT Jawa Satu Power, bukan dijadikan target yang dijanjikan di awal.

**d. Tesseract OCR Engine**

Tesseract adalah perangkat lunak OCR open-source yang pada versi 5 mengandalkan arsitektur berbasis neural network (LSTM). Konfigurasi kunci meliputi Page Segmentation Mode (PSM) untuk menentukan layout halaman dan OCR Engine Mode (OEM) untuk memilih algoritma intinya. Perbandingan oleh Darpito dkk. (2025) menunjukkan Tesseract lebih unggul dari sisi kecepatan pemrosesan dibandingkan EasyOCR, sehingga lebih sesuai untuk kebutuhan pemrosesan dokumen dalam jumlah besar seperti pada kerja praktik ini, dengan konsekuensi akurasi yang perlu dikompensasi melalui tahap image preprocessing.

**e. Python Flask Framework dan Arsitektur Blueprint**

Flask adalah microframework web Python. Blueprint pada Flask digunakan untuk membuat komponen aplikasi yang modular, sehingga kode dapat dibagi ke dalam direktori berdasarkan fungsionalitasnya (seperti auth, dashboard, ocr, api) dan memudahkan pemeliharaan kode sumber pada proyek berskala menengah.

**f. Flask-SQLAlchemy ORM**

Flask-SQLAlchemy adalah ekstensi yang mengintegrasikan SQLAlchemy ke aplikasi Flask. Object-Relational Mapping (ORM) ini memungkinkan interaksi dengan basis data melalui objek Python alih-alih menulis query SQL mentah, sehingga membantu mencegah SQL injection dan memudahkan transisi antarsistem basis data.

**g. MySQL Database dan Pengindeksan Teks Penuh**

MySQL adalah sistem manajemen basis data relasional (RDBMS) sumber terbuka yang umum digunakan karena keandalan dan dukungan relasinya. Pada sistem ini, MySQL menyimpan data pengguna, metadata dokumen, dan riwayat pemrosesan, serta menyimpan teks hasil ekstraksi OCR pada kolom yang dapat diberi indeks FULLTEXT untuk mendukung pencarian teks penuh (full-text search) lintas dokumen. Kapabilitas ini berbeda dari Searchable PDF, yang hanya menyediakan pencarian teks di dalam satu berkas menggunakan pembaca PDF.

**h. Document Management System (DMS)**

DMS adalah sistem perangkat lunak yang digunakan untuk menerima, melacak, mengelola, dan menyimpan dokumen guna mengurangi ketergantungan pada berkas fisik (paperless). DMS yang matang umumnya dilengkapi kapabilitas indexing dan pencarian (searchability) terhadap konten dokumen, bukan hanya terhadap metadata atau nama berkas.

**i. PyMuPDF (fitz)**

PyMuPDF, sering direferensikan sebagai fitz, adalah modul untuk pemrosesan berkas PDF di Python. Library ini mampu merender halaman PDF menjadi gambar, mengekstraksi teks native (bila tersedia), serta menyusun kembali halaman menjadi berkas Searchable PDF setelah teks hasil OCR disisipkan.

**j. Multiprocessing dan ProcessPoolExecutor**

Keterbatasan Global Interpreter Lock (GIL) pada Python mengharuskan penggunaan modul multiprocessing agar tugas CPU-bound seperti OCR dapat dieksekusi secara paralel pada beberapa inti CPU. ProcessPoolExecutor mengelola kumpulan proses pekerja (worker) dan mengalokasikan pekerjaan secara otomatis. Perlu ditegaskan bahwa pendekatan ini merupakan pemrosesan paralel pada satu mesin (single-machine parallel processing), bukan sistem terdistribusi (distributed system) yang melibatkan banyak server.

**k. Bootstrap 5 dan Chart.js**

Bootstrap 5 menyediakan kerangka kerja antarmuka pengguna yang responsif dan mobile-first, sementara Chart.js memungkinkan perenderan grafik interaktif berbasis canvas HTML5. Kombinasi keduanya mendukung pengembangan dashboard yang fungsional tanpa memerlukan banyak kode front-end kustom.

**l. Metode Waterfall (RPL)**

Waterfall adalah metodologi rekayasa perangkat lunak sekuensial yang meliputi fase analisis kebutuhan, perancangan sistem, implementasi, pengujian, hingga pemeliharaan. Metode ini cocok digunakan apabila kebutuhan utama sudah dapat didefinisikan secara memadai sebelum masuk ke tahap perancangan. Pada kerja praktik ini, requirement awal yang tercantum pada proposal akan divalidasi dan difinalisasi sebagai baseline pada minggu pertama melalui observasi lapangan, sehingga perubahan kebutuhan pada tahap-tahap berikutnya dapat diminimalkan.

**m. Unified Modeling Language (UML)**

UML merupakan standar visualisasi arsitektur sistem. Use Case Diagram menjelaskan interaksi pengguna dengan sistem, Activity Diagram menjelaskan alur proses bisnis, Sequence Diagram menggambarkan pertukaran pesan antar-komponen, dan Class Diagram memetakan struktur objek beserta relasinya di dalam sistem.

**2.6 Sejarah Perusahaan**

PT Jawa Satu Power (JSP) merupakan perusahaan patungan (joint venture) antara PT Pertamina Power Indonesia (Pertamina NRE), Marubeni Corporation, dan Sojitz Corporation, yang didirikan pada 5 Desember 2016 sebagai perusahaan bertujuan khusus (Special Purpose Company) untuk menjalankan, mengendalikan, dan mengelola aset kegiatan usaha pembangkit listrik Jawa-1.

Pembangkit yang dikelola JSP menggunakan teknologi Combined Cycle Gas Turbine (CCGT/PLTGU) berkapasitas 1.760 MW yang berlokasi di Subang, Jawa Barat, dan disebut sebagai pembangkit berbahan bakar gas dengan teknologi CCGT terbesar di Asia Tenggara. Pasokan gas alam cair (LNG) untuk pembangkit ini didukung oleh unit Floating Storage Regasification Unit (FSRU) yang dikelola oleh entitas terkait, PT Jawa Satu Regas, yang didirikan pada Juni 2018. Listrik yang dihasilkan disalurkan ke sistem interkoneksi Jawa-Bali melalui jaringan PT PLN (Persero).

Sejalan dengan operasionalnya, PT Jawa Satu Power turut mendorong pemanfaatan teknologi digital untuk mendukung tata kelola perusahaan, termasuk dalam pengelolaan dokumen teknis dan administratif sehari-hari, yang menjadi konteks dari kerja praktik ini.

*Catatan: informasi profil perusahaan di atas dirangkum dari situs resmi PT Jawa Satu Power dan sumber publik lain per Agustus 2026. Detail operasional yang lebih spesifik—seperti struktur organisasi dan unit kerja tempat kerja praktik akan dilaksanakan—akan dikonfirmasi kembali bersama pembimbing lapangan pada awal pelaksanaan kerja praktik.*

**2.7 Gambaran Umum Sistem**

Sistem yang akan dikembangkan menggunakan arsitektur Modular Monolith dengan pola MVC, dengan pembagian tanggung jawab antar-modul sebagai berikut.

**Aktor dan Use Case Utama (Ringkasan)**

Sebagai gambaran awal interaksi pengguna dengan sistem, berikut aktor dan use case utama yang akan dirinci lebih lanjut ke dalam diagram Use Case pada tahap System Design (Minggu 3–4):

• Admin & User — Login ke aplikasi; Memilih/mengunggah folder dokumen untuk diproses; Menjalankan proses OCR (Start / Pause / Resume / Cancel-Stop); Memantau progres dan log proses secara real-time; Mencari dan melihat dokumen melalui viewer PDF; Mengekspor log dan metadata ke Excel.

• Admin (khusus) — Mengelola akun pengguna; Mengatur konfigurasi engine OCR dan jumlah worker; Meninjau log kegagalan pemrosesan.

Web Browser (Antarmuka Pengguna)

↳ Flask Web App (Arsitektur Blueprint)

↳ Modul Autentikasi (Auth)

↳ Modul DMS & OCR

↳ OCR Job Manager

↳ ProcessPoolExecutor → Worker 1..N → Tesseract OCR Engine

↳ Modul Dashboard & Analytics

↳ Penyimpanan: File System (dokumen) dan MySQL (metadata, riwayat proses, indeks teks)

Status proses OCR disampaikan dari proses-proses worker kembali ke aplikasi Flask melalui antrean IPC (Inter-Process Communication) agar siklus HTTP tidak terblokir (non-blocking) selama pemrosesan berlangsung.

**2.7.1 Alur Pemrosesan OCR (Core Pipeline)**

Alur utama pemrosesan satu dokumen dirancang sebagai berikut:

Dokumen Masuk → Validasi Format → Deteksi PDF/Image → Smart Skip?

Rendering ke Gambar (PyMuPDF) → Grayscale → Contrast Enhancement → Sharpening

OCR (Tesseract) → Susun Searchable PDF → Simpan Teks + Metadata (MySQL) → Update Status

Dokumen yang dilewati oleh Smart Skip (karena sudah memiliki lapisan teks native) langsung menuju tahap penyimpanan metadata tanpa melalui preprocessing dan OCR ulang, sehingga menghemat waktu pemrosesan.

**2.7.2 Modul/Antarmuka Aplikasi**

**1\. Dashboard**

Pusat kontrol utama yang menampilkan ringkasan KPI, file browser untuk memilih folder target, kontrol eksekusi (Start, Cancel/Stop), serta tabel aktivitas terbaru yang diperbarui secara berkala.

**2\. Documents Management**

Repositori tempat pengguna mencari, memfilter (berdasarkan waktu atau status), dan melihat dokumen melalui viewer PDF bawaan. Modul ini juga menyediakan opsi ekspor log dan metadata ke format Excel.

**3\. OCR Monitoring**

Layar yang menyajikan log proses real-time mengenai progres OCR yang sedang berlangsung, disertai indikator antrean dokumen (worker queue) dan telemetri dasar (penggunaan CPU/RAM). Tampilan ini bersifat log status proses, bukan terminal interaktif yang memberi akses eksekusi perintah ke server, untuk menghindari risiko keamanan yang tidak perlu.

**4\. Analytics (Pendukung)**

Halaman analitik berbasis Chart.js yang menampilkan tren pemrosesan harian dan grafik volume dokumen sukses/gagal, sebagai fitur pendukung di luar fokus utama kerja praktik.

**5\. System Settings**

Modul konfigurasi engine OCR (bahasa, batas DPI, jumlah core multiprocessing) serta pengaturan dasar sistem. Utilitas pencadangan basis data dapat disediakan sebagai fungsi bantu, namun bukan merupakan fitur inti yang menjadi fokus evaluasi kerja praktik.

**2.7.3 Kontrol Eksekusi Proses**

Kontrol dasar berupa Start, Cancel/Stop, serta Pause/Resume pada tingkat batch (menghentikan dan melanjutkan antrean worker, bukan pada posisi halaman tertentu di dalam satu dokumen) telah tersedia pada purwarupa (prototype) awal aplikasi dan akan disempurnakan serta diuji lebih lanjut selama pelaksanaan kerja praktik. Adapun kontrol Pause/Resume granular yang menyimpan posisi pemrosesan tepat pada halaman tertentu di dalam satu dokumen memerlukan penanganan status worker yang sedang aktif, sinkronisasi antar-proses, dan pencegahan pemrosesan ganda yang lebih kompleks; butir ini diposisikan sebagai pengembangan lanjutan (stretch goal) di luar cakupan utama kerja praktik. Sebagai pelengkap, mekanisme resume sederhana juga tersedia secara alami melalui fitur Smart Skip: apabila proses dihentikan dan dijalankan kembali, dokumen yang telah berstatus selesai di basis data akan otomatis dilewati.

**2.7.4 Penanganan Kesalahan Proses OCR**

Sistem menerapkan penanganan kesalahan pada tingkat dasar, bukan skema fault tolerance tingkat produksi:

a. berkas yang rusak atau tidak dapat dibuka dicatat dengan status failed beserta pesan error;

b. kegagalan pada satu tahap pemrosesan halaman dapat dicoba ulang satu kali (retry sederhana); apabila tetap gagal, status dokumen ditandai failed;

c. kegagalan tak terduga pada satu worker tidak menghentikan seluruh antrean; proses dilanjutkan ke dokumen berikutnya, dan kegagalan tersebut tercatat pada log untuk ditinjau administrator.

**2.7.5 Evaluasi dan Metrik Keberhasilan**

Untuk memastikan klaim peningkatan akurasi dan kecepatan dapat dipertanggungjawabkan, keberhasilan sistem akan diukur menggunakan metrik berikut, bukan berdasarkan target angka yang ditetapkan di muka:

| 
**Aspek**

 | 

**Metrik**

 | 

**Cara Pengujian**

 |
| --- | --- | --- |
| 

Akurasi OCR

 | 

Character Error Rate (CER)

 | 

Membandingkan teks hasil OCR dengan ground truth pada sampel dokumen uji, sebelum dan sesudah preprocessing.

 |
| 

Kecepatan / Throughput

 | 

Dokumen per menit, waktu rata-rata per halaman

 | 

Mengukur waktu pemrosesan pada skema sequential dibandingkan paralel (misalnya 2, 4, 8 worker) pada jumlah dokumen uji yang sama.

 |
| 

Fungsionalitas

 | 

Checklist Black Box Testing

 | 

Pengujian terhadap tiap use case: login, unggah/pilih folder, monitoring, pencarian dokumen, ekspor.

 |
| 

Reliabilitas dasar

 | 

Rasio dokumen berstatus success vs failed

 | 

Menjalankan proses terhadap kumpulan dokumen uji yang sengaja menyertakan beberapa berkas rusak/corrupt.

 |

*Catatan: angka peningkatan akurasi maupun throughput tidak dijanjikan di awal proposal ini; keduanya akan diukur dan dilaporkan berdasarkan hasil pengujian aktual pada tahap Testing.*

**2.8 Jadwal Kegiatan**

Metodologi pengembangan perangkat lunak yang digunakan pada kerja praktik ini adalah model Waterfall, dengan tahapan requirements analysis, system design, implementation, testing, serta deployment & maintenance. Mengingat requirement rinci baru akan digali melalui observasi lapangan pada minggu-minggu awal, requirement utama yang telah teridentifikasi pada proposal ini digunakan sebagai baseline awal. Hasil observasi pada Minggu 1–2 digunakan untuk memvalidasi dan memfinalisasi baseline tersebut sebelum masuk ke tahap perancangan, sehingga perubahan requirement pada tahap-tahap berikutnya dapat diminimalkan, sejalan dengan prinsip dasar Waterfall.

Rencana waktu pelaksanaan kerja praktik selama 12 minggu adalah sebagai berikut.

| 
**Minggu**

 | 

**Fase (Waterfall)**

 | 

**Kegiatan**

 |
| --- | --- | --- |
| 

1–2

 | 

Requirements Analysis

 | 

Observasi lapangan (Form KP-F01), identifikasi jenis dan estimasi volume dokumen, studi kelayakan Tesseract dan PyMuPDF, finalisasi baseline requirement.

 |
| 

3–4

 | 

System Design

 | 

Perancangan ERD dan skema basis data (users, documents, processing\_log), diagram UML (use case, activity, sequence, class), arsitektur Blueprint Flask, wireframe antarmuka Bootstrap 5.

 |
| 

5–6

 | 

Implementation Fase I

 | 

Kerangka aplikasi Flask, integrasi ORM Flask-SQLAlchemy, modul autentikasi (Flask-Login, akun disediakan oleh Admin), halaman frontend dasar.

 |
| 

7–8

 | 

Implementation Fase II

 | 

Core engine OCR, pipeline image preprocessing dengan Pillow, penerapan ProcessPoolExecutor, fitur Smart Skip.

 |
| 

9

 | 

Implementation Fase III

 | 

Modul monitoring real-time (log proses, telemetri dasar), penyusunan indeks full-text search, visualisasi analitik dasar (Chart.js), ekspor Excel.

 |
| 

10–11

 | 

Testing

 | 

Black Box Testing fungsionalitas, pengujian akurasi OCR (CER sebelum/sesudah preprocessing), pengujian throughput sequential vs paralel, pengujian penanganan kesalahan dasar.

 |
| 

12

 | 

Deployment & Dokumentasi

 | 

Penyusunan laporan akhir kerja praktik, manual book aplikasi, serta deployment ke server intranet perusahaan.

 |

**3\. DAFTAR LITERATUR**

**Jurnal dan Prosiding Ilmiah**

1\. Smith, R. (2007). An Overview of the Tesseract OCR Engine. Ninth International Conference on Document Analysis and Recognition (ICDAR), 629–633.

2\. El Harraj, A., & Raissouni, N. (2015). OCR Accuracy Improvement on Document Images through a Novel Pre-Processing Approach. Signal & Image Processing: An International Journal (SIPIJ), 6(4), 1–17. https://doi.org/10.5121/sipij.2015.6401

3\. Darpito, M. N., Firdausy, K., & Fadlil, A. (2025). Perbandingan Unjuk Kerja Library Optical Character Recognition (OCR) dalam Pengenalan Teks pada Dokumen Digital. Jurnal Informatika Polinema, 11(3), 273–282. https://doi.org/10.33795/jip.v11i3.7025

4\. Rahmdani, O. (2025). Evaluasi Kinerja Tesseract-OCR dalam Pengenalan Teks Tulisan Tangan Menggunakan Dataset Kustom. Jurnal Informatika dan Teknik Elektro Terapan, 13(3). https://doi.org/10.23960/jitet.v13i3.7162

**Buku**

5\. Grinberg, M. (2018). Flask Web Development: Developing Web Applications with Python (2nd ed.). O'Reilly Media.

6\. Gorelick, M., & Ozsvald, I. (2020). High Performance Python: Practical Performant Programming for Humans (2nd ed.). O'Reilly Media.

7\. Pressman, R. S., & Maxim, B. R. (2014). Software Engineering: A Practitioner's Approach (8th ed.). McGraw-Hill Education.

8\. Summerfield, M. (2010). Programming in Python 3: A Complete Introduction to the Python Language (2nd ed.). Addison-Wesley Professional.

**Dokumentasi Resmi/Teknis**

9\. Artifex Software. (2023). PyMuPDF Documentation. Diakses dari https://pymupdf.readthedocs.io/

10\. Tesseract OCR. (2023). Tesseract Documentation. GitHub Repository. Diakses dari https://github.com/tesseract-ocr/tesseract

11\. Pallets Projects. (2023). Flask-SQLAlchemy Documentation. Diakses dari https://flask-sqlalchemy.palletsprojects.com/

12\. Clark, A. (2015). Pillow (PIL Fork) Documentation. Read the Docs.

13\. Bootstrap Core Team. (2023). Bootstrap 5 Documentation. Diakses dari https://getbootstrap.com/docs/5.3/

14\. Chart.js Contributors. (2023). Chart.js Documentation. Diakses dari https://www.chartjs.org/docs/latest/