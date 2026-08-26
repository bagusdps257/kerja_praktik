# 🚀 Panduan Deployment Server Ubuntu (Production Setup)
**Sistem:** Intelligent OCR & Document Management System (DMS)  
**Target:** Ubuntu Server 22.04 / 24.04 LTS

---

## 1. Prasyarat Sistem di Server Ubuntu

Pastikan dependensi sistem operasi terpasang:

```bash
sudo apt update && sudo apt install -y \
    python3-pip \
    python3-venv \
    tesseract-ocr \
    tesseract-ocr-ind \
    tesseract-ocr-eng \
    mysql-server \
    libmupdf-dev \
    git
```

---

## 2. Setup Virtual Environment & Dependensi

1. Masuk ke direktori proyek:
   ```bash
   cd /var/www/ocr-dms   # Atau direktori proyek Anda di Ubuntu
   ```

2. Buat virtual environment Python dan aktifkan:
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```

3. Install library dependensi Python:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install gunicorn
   ```

---

## 3. Konfigurasi File Lingkungan (`.env`)

Salin file template konfigurasi:
```bash
cp .env.example .env
nano .env
```

Sesuaikan isi `.env`:
```ini
SECRET_KEY=ganti_dengan_token_acak_yang_panjang_dan_aman
FLASK_DEBUG=false
ALLOW_REGISTRATION=false
DATABASE_URL=mysql+pymysql://ocr_user:PasswordKuat123!@localhost/ocr_database
TESSERACT_CMD=/usr/bin/tesseract
```

---

## 4. Setup Service Otomatis (Systemd Service)

Agar aplikasi otomatis berjalan di background dan otomatis hidup kembali saat server restart/reboot:

1. Buat file service systemd:
   ```bash
   sudo nano /etc/systemd/system/ocr-dms.service
   ```

2. Isi dengan konfigurasi berikut:
   ```ini
   [Unit]
   Description=OCR Document Management System Gunicorn Service
   After=network.target mysql.service

   [Service]
   User=ubuntu
   Group=ubuntu
   WorkingDirectory=/var/www/ocr-dms
   Environment="PATH=/var/www/ocr-dms/env/bin"
   ExecStart=/var/www/ocr-dms/env/bin/gunicorn --workers 2 --bind 0.0.0.0:5000 --timeout 300 app:app
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

3. Aktifkan dan jalankan service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable ocr-dms
   sudo systemctl start ocr-dms
   ```

4. Cek status service:
   ```bash
   sudo systemctl status ocr-dms
   ```

---

## 5. Menjalankan Pengujian Otomatis (*Test Suite*)

Untuk memastikan seluruh fungsi keamanan, autentikasi, dan database bekerja 100% sempurna di Ubuntu:

```bash
source env/bin/activate
pytest tests/ -v
```

---

## 6. Perintah Pemeliharaan Rutin

* **Melihat Log Aplikasi Real-time:**
  ```bash
  tail -f logs/sistem_ocr.log
  ```
* **Melihat Log Systemd Gunicorn:**
  ```bash
  sudo journalctl -u ocr-dms -f
  ```
* **Restart Aplikasi setelah Update Kode:**
  ```bash
  sudo systemctl restart ocr-dms
  ```
