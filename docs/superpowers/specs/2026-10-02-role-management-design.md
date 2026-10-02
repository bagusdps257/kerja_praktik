# Spesifikasi Desain: Manajemen Peran & Hak Akses Pengguna (Operator vs User)

## 1. Ringkasan Eksekutif
Fitur ini mengimplementasikan sistem *Role-Based Access Control* (RBAC) pada aplikasi **OCR & DMS** untuk memenuhi kebutuhan bimbingan akademik (Kebutuhan Fungsional F-12, F-13, F-14). Sistem membedakan dua tingkatan peran (*role*):
1. **Operator (Admin)**: Memegang kontrol penuh atas sistem, termasuk manajemen akun pengguna (tambah, hapus, reset password, ubah peran) dan tindakan destruktif penghapusan/reset riwayat database.
2. **User Biasa**: Memiliki keleluasaan operasional (menjalankan/menghentikan OCR, mengganti path direktori input/output, menyesuaikan parameter pengaturan Tesseract, mencari dokumen, dan mengekspor laporan), namun **tidak memiliki izin untuk menghapus** (dilarang mereset riwayat database dan dilarang mengelola/menghapus akun pengguna).

Pendaftaran akun publik (*public registration*) dinonaktifkan secara default agar pembuatan akun dikelola secara terpusat oleh Operator.

---

## 2. Perubahan Skema Database

### Tabel `users`
Tabel `users` ditambahkan satu kolom baru:
* **`role`**: `VARCHAR(20) NOT NULL DEFAULT 'user'`
  * Nilai valid: `'operator'` atau `'user'`.
  * Akun lama yang sudah ada di database (`bagus`, `bagusdps`) otomatis dimigrasikan dengan peran `'operator'`.

### Mekanisme Auto-Migration
Pada [models/user_model.py](file:///d:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/models/user_model.py), fungsi inisialisasi model memeriksa keberadaan kolom `role` melalui SQLAlchemy `inspect`. Jika kolom belum ada:
```sql
ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user';
UPDATE users SET role = 'operator' WHERE username IN ('bagus', 'bagusdps');
```

---

## 3. Komponen Backend

### A. Model Pengguna ([models/user_model.py](file:///d:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/models/user_model.py))
1. **Class `User`**:
   * Menambahkan atribut `role = db.Column(db.String(20), default='user')`.
   * Menambahkan properti helper:
     ```python
     @property
     def is_operator(self):
         return self.role == 'operator'
     ```
   * Menambahkan properti badge warna peran untuk UI (`role_badge_class`).
2. **Class `UserModel`**:
   * `get_all_users()`: Mengambil list seluruh entitas user terurut dari yang terbaru.
   * `create_user(username, password, role='user')`: Membuat user baru dengan penetapan peran spesifik.
   * `delete_user(user_id, current_user_id)`: Menghapus user dengan validasi agar operator tidak dapat menghapus akunnya sendiri.
   * `reset_user_password(user_id, new_password)`: Mengatur ulang kata sandi pengguna oleh operator.
   * `update_user_role(user_id, new_role)`: Mengubah peran pengguna antara `'user'` dan `'operator'`.

### B. Dekorator Otorisasi ([routes/auth.py](file:///d:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/routes/auth.py))
Membuat decorator `@operator_required`:
```python
def operator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_operator:
            flash("Akses ditolak: Tindakan ini memerlukan hak akses Operator.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated_function
```

### C. Rute Baru Manajemen Pengguna ([routes/auth.py](file:///d:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/routes/auth.py))
* `GET /users`: Halaman antarmuka manajemen pengguna (dilindungi `@operator_required`).
* `POST /users/create`: Menambahkan akun baru (username, password, role).
* `POST /users/delete/<int:user_id>`: Menghapus pengguna yang dipilih.
* `POST /users/reset-password/<int:user_id>`: Reset kata sandi pengguna oleh operator.
* `POST /users/change-role/<int:user_id>`: Mengubah status peran pengguna.

### D. Proteksi Rute Eksisting
* `POST /reset_db` pada [routes/dashboard.py](file:///d:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/routes/dashboard.py): Ditambahkan dekorator `@operator_required` agar user biasa tidak bisa memicu penghapusan database meskipun mengetahui URL endpoint.
* `GET /register`: Menolak registrasi mandiri dan mengarahkan ke halaman login dengan notifikasi bahwa akun harus dibuatkan oleh operator.

---

## 4. Perancangan Antarmuka Pengguna (UI/UX)

### A. Komponen Sidebar ([templates/partials/sidebar.html](file:///d:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/templates/partials/sidebar.html))
* Menambahkan item menu baru:
  ```html
  {% if current_user.is_operator %}
  <li>
      <a href="{{ url_for('auth.users_list') }}" class="{% if request.endpoint == 'auth.users_list' %}active{% endif %}">
          <i class="bi bi-people"></i>
          <span>Kelola Pengguna</span>
      </a>
  </li>
  {% endif %}
  ```

### B. Komponen Navigasi Atas ([templates/partials/navbar.html](file:///d:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/templates/partials/navbar.html))
* Di samping nama user pada tombol dropdown profil, ditambahkan pill badge:
  * Jika Operator: Badge hijau toska `[Operator]` (`badge-soft-success`).
  * Jika User Biasa: Badge abu-abu netral `[User]` (`badge-soft-secondary`).

### C. Proteksi Tampilan Reset Database ([templates/documents.html](file:///d:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/templates/documents.html))
* Tombol **"Reset Database"** / **"Hapus Riwayat"** dibungkus dengan kondisi:
  ```html
  {% if current_user.is_operator %}
  <button data-bs-target="#resetDbModal" ...>Hapus Riwayat</button>
  {% endif %}
  ```
* User biasa tidak melihat tombol atau modal penghapusan riwayat dokumen.

### D. Halaman Baru: Kelola Pengguna ([templates/users.html](file:///d:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/templates/users.html))
* **Header**: Judul "Manajemen Pengguna", deskripsi peran, dan tombol "+ Tambah Pengguna Baru".
* **Tabel Pengguna**:
  * Kolom: No, Username, Peran (Badge), Tanggal Dibuat, Login Terakhir, dan Kolom Aksi.
  * Aksi:
    * Tombol *Reset Password* (membuka modal input password baru).
    * Tombol *Ubah Peran* (toggle antara Operator dan User).
    * Tombol *Hapus* (modal konfirmasi; dinonaktifkan jika target adalah akun yang sedang login).
* **Modal Tambah Pengguna**: Form validasi username minimal 3 karakter, password minimal 6 karakter, dan dropdown pilihan peran.

---

## 5. Rencana Pengujian (Test Suite)

Pengujian otomatis ditambahkan pada [tests/test_auth.py](file:///d:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/tests/test_auth.py):
1. `test_user_role_assignment`: Memastikan user baru memiliki peran default `'user'` dan operator `'operator'`.
2. `test_operator_access_to_users_page`: Memastikan akun operator dapat membuka `/users` (status 200).
3. `test_standard_user_blocked_from_users_page`: Memastikan user biasa dialihkan (302) dengan flash error ketika mencoba mengakses `/users`.
4. `test_standard_user_blocked_from_reset_db`: Memastikan user biasa tidak dapat mengeksekusi `POST /reset_db`.
5. `test_operator_cannot_delete_self`: Memastikan sistem menolak percobaan operator menghapus akunnya sendiri.
6. `test_user_can_edit_settings_and_folder`: Memastikan user biasa tetap diizinkan mengakses `/settings` dan `/update_folder`.
