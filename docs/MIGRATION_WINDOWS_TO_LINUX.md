# Catatan Migrasi Project OCR (Windows ke Linux Server)

Dokumen ini mencatat perbedaan konfigurasi, kode, dan cara menjalankan aplikasi antara lingkungan *development* di Windows (Laptop) dan lingkungan *production* di Linux (Server/VPS).

## 1. Lokasi Aplikasi Tesseract OCR
Karena ini adalah aplikasi OCR, letak mesin utama (Tesseract) sangat bergantung pada sistem operasi.

*   **Di Windows (Laptop):**
    ```python
    # config/settings.py
    TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    ```
*   **Di Linux (Server):**
    Di Linux, tidak ada konsep *Local Disk C*. Instalasi dilakukan lewat terminal (`sudo apt install tesseract-ocr`), sehingga lokasinya selalu ada di sistem utama:
    ```python
    # config/settings.py
    TESSERACT_CMD = "/usr/bin/tesseract"
    ```

## 2. Koneksi Database MySQL
Di lingkungan Windows, biasanya pengembang menggunakan user `root` tanpa password menggunakan aplikasi seperti XAMPP atau Laragon. Namun, di server, keamanan harus ditingkatkan.

*   **Di Windows (Laptop):**
    ```python
    # config/settings.py
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/ocr_database"
    ```
    *(Username: root, Password: kosong)*

*   **Di Linux (Server):**
    Kita membuat *user* MySQL khusus agar lebih aman.
    ```python
    # config/settings.py
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://ocr_user:rahasia123@localhost/ocr_database"
    ```
    *(Username: ocr_user, Password: rahasia123)*

## 3. Package Tambahan yang Terlupakan
Saat memindahkan project dari laptop, beberapa *library* kadang luput dari file `requirements.txt`.
Saat *deploy* di Linux server tadi, kita harus menambahkan secara manual:
*   `Flask-WTF` (Untuk proteksi Form dari serangan CSRF)
*   `Flask-Login` (Untuk sistem login dan *session*)
*   `PyMuPDF` (Untuk membaca dan mengolah file PDF, di-import sebagai `fitz`)
*   `pytesseract` (Jembatan antara Python dan mesin Tesseract)
*   `Pillow` (Untuk memanipulasi gambar)
*   `psutil` (Untuk membaca statistik RAM & CPU di halaman Dashboard Monitoring)

## 4. Cara Menyalakan Server (Web Server)
Di Windows, menyalakan web untuk sekadar tes sangatlah sederhana, namun tidak cocok untuk publik.

*   **Di Windows (Laptop / Development):**
    ```bash
    python app.py
    ```
    *(Hanya bisa diakses di laptop itu sendiri, dan akan mati jika CMD/Terminal ditutup).*

*   **Di Linux (Server / Production):**
    Kita menggunakan *WSGI Server* tingkat lanjut yaitu **Gunicorn** agar lebih stabil menahan puluhan *request* OCR sekaligus, serta menggunakan perintah `nohup` agar aplikasi terus hidup di *background* meskipun layar PuTTY ditutup.
    ```bash
    nohup gunicorn --workers 3 --bind 0.0.0.0:5000 app:app > server.log 2>&1 &
    ```
    *(IP `0.0.0.0` mengizinkan aplikasi diakses dari luar (publik) menggunakan IP Server).*

---
**Rekomendasi dari Asisten AI (Antigravity):**
Jika ke depannya Anda akan terus memperbarui kode (*update*) di laptop Windows lalu memindahkannya lagi ke Server Linux, pastikan untuk **tidak menimpa (*overwrite*)** file `config/settings.py` yang ada di server. Biarkan file pengaturan di server tetap menggunakan versi Linux-nya. 
