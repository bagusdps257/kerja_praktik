# Multi-User Authentication & CSRF Protection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement multi-user authentication (Login, Register, Logout) using `Flask-Login` & `werkzeug.security` and project-wide CSRF protection using `Flask-WTF` in the OCR Project.

**Architecture:** 
1. Database: Add `users` table to SQLite (`database/ocr_database.db`).
2. Data Model: Create `models/user_model.py` implementing `Flask-Login` `UserMixin` with secure password hashing.
3. Routes: Create `routes/auth.py` for `/login`, `/register`, `/logout`.
4. Security: Initialize `LoginManager` and `CSRFProtect` in `app.py` and protect all dashboard endpoints with `@login_required`.
5. UI: Build `login.html` and `register.html` templates matching existing dark dashboard aesthetics, and embed `csrf_token` into all HTML forms.

**Tech Stack:** Python 3, Flask, Flask-Login, Flask-WTF, werkzeug.security, SQLite3, HTML/CSS

## Global Constraints

- Retain existing dashboard routes and functionality.
- Ensure all user passwords are properly hashed with `generate_password_hash`.
- Protect all form submissions against CSRF attacks.

---

### Task 1: Environment Dependencies & Config Setup

**Files:**
- Modify: [`config/settings.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/config/settings.py)

**Interfaces:**
- Consumes: System Python environment (`env/Scripts/python.exe`)
- Produces: Installed `Flask-Login` and `Flask-WTF` packages, `SECRET_KEY` constant in `settings.py`.

- [ ] **Step 1: Install `Flask-Login` and `Flask-WTF` in virtual environment**

Run: `.\env\Scripts\python.exe -m pip install Flask-Login Flask-WTF`

- [ ] **Step 2: Add `SECRET_KEY` in `config/settings.py`**

In `config/settings.py`:
```python
SECRET_KEY = os.environ.get("SECRET_KEY", "ocr_project_secret_key_2026_super_secure")
```

---

### Task 2: User Model & Database Table (`models/user_model.py`)

**Files:**
- Create: `models/user_model.py`
- Test: Virtual environment python command checking user CRUD operations.

**Interfaces:**
- Consumes: `models.database.get_connection`, `werkzeug.security`
- Produces: `UserModel` class and `User` class for `Flask-Login`.

- [ ] **Step 1: Create `models/user_model.py`**

```python
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import get_connection

class User(UserMixin):
    def __init__(self, id, username, password_hash, created_at, last_login=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.created_at = created_at
        self.last_login = last_login

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserModel:
    def __init__(self):
        self.init_db()

    def init_db(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT
            )
        """)
        conn.commit()
        conn.close()

    def get_by_id(self, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, created_at, last_login FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(row[0], row[1], row[2], row[3], row[4])
        return None

    def get_by_username(self, username):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, created_at, last_login FROM users WHERE username = ?", (username.strip().lower(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(row[0], row[1], row[2], row[3], row[4])
        return None

    def create_user(self, username, password):
        conn = get_connection()
        cursor = conn.cursor()
        pwd_hash = generate_password_hash(password)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username.strip().lower(), pwd_hash, now)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return self.get_by_id(user_id)
        except Exception:
            conn.close()
            return None

    def update_last_login(self, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, user_id))
        conn.commit()
        conn.close()
```

- [ ] **Step 2: Verify user model CRUD via CLI**

Run: `.\env\Scripts\python.exe -c "from models.user_model import UserModel; um = UserModel(); u = um.create_user('testadmin', 'admin123'); print('User created:', u.username if u else 'exists')" `

---

### Task 3: Authentication Routes Blueprint (`routes/auth.py`)

**Files:**
- Create: `routes/auth.py`

**Interfaces:**
- Consumes: `Flask-Login` (`login_user`, `logout_user`, `login_required`, `current_user`), `models.user_model.UserModel`
- Produces: `auth_bp` Blueprint with `/login`, `/register`, `/logout` routes.

- [ ] **Step 1: Create `routes/auth.py`**

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.user_model import UserModel

auth_bp = Blueprint("auth", __name__)
user_model = UserModel()

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = user_model.get_by_username(username)
        if user and user.check_password(password):
            login_user(user, remember=True)
            user_model.update_last_login(user.id)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))

        flash("Username atau password salah.", "danger")

    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password:
            flash("Username dan password tidak boleh kosong.", "danger")
        elif password != confirm_password:
            flash("Konfirmasi password tidak cocok.", "danger")
        elif user_model.get_by_username(username):
            flash("Username sudah digunakan.", "danger")
        else:
            new_user = user_model.create_user(username, password)
            if new_user:
                flash("Pendaftaran berhasil! Silakan login.", "success")
                return redirect(url_for("auth.login"))
            flash("Gagal mendaftarkan akun.", "danger")

    return render_template("register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Anda telah keluar dari akun.", "info")
    return redirect(url_for("auth.login"))
```

---

### Task 4: Application Integration in `app.py` & Route Protection

**Files:**
- Modify: [`app.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/app.py)
- Modify: [`routes/dashboard.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/routes/dashboard.py)
- Modify: [`routes/ocr.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/routes/ocr.py)
- Modify: [`routes/folder.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/routes/folder.py)
- Modify: [`routes/export.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/routes/export.py)

- [ ] **Step 1: Configure `LoginManager` & `CSRFProtect` in `app.py`**

In `app.py`:
```python
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config.settings import SECRET_KEY
from models.user_model import UserModel
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.ocr import ocr_bp
from routes.folder import folder_bp
from routes.export import export_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY

# CSRF Protection
csrf = CSRFProtect(app)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Silakan login terlebih dahulu untuk mengakses halaman ini."
login_manager.login_message_category = "warning"

user_model = UserModel()

@login_manager.user_loader
def load_user(user_id):
    return user_model.get_by_id(int(user_id))

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(ocr_bp)
app.register_blueprint(folder_bp)
app.register_blueprint(export_bp)

if __name__ == "__main__":
    app.run(debug=True)
```

- [ ] **Step 2: Add `@login_required` to all protected routes in blueprints**

Add `@login_required` from `flask_login` to:
- `routes/dashboard.py`: `index`, `documents`, `monitoring`, `api_monitoring`, `pause_queue`, `resume_queue`, `analytics`, `settings`, `save_settings_route`, `backup_db`, `api_status`, `progress`, `reset_db`.
- `routes/ocr.py`: `jalankan`, `stop_ocr`.
- `routes/folder.py`: `update_folder`, `pilih_folder`, `lihat_pdf`.
- `routes/export.py`: `export_csv`.

---

### Task 5: UI Templates (`login.html`, `register.html`) & CSRF Token Injection

**Files:**
- Create: `templates/login.html`
- Create: `templates/register.html`
- Modify: Existing HTML templates in `templates/` to include `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>` in all `<form>` elements.

- [ ] **Step 1: Create `templates/login.html`**

Sleek, dark-themed login interface matching dashboard styling.

- [ ] **Step 2: Create `templates/register.html`**

Matching registration interface.

- [ ] **Step 3: Add CSRF token fields to all HTML forms in `templates/`**

Add `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>` inside all `<form>` tags.

- [ ] **Step 4: Add User badge & Logout link in Navigation Header**

Include current user display name and Logout link when `current_user.is_authenticated`.

---

### Task 6: End-to-End Verification

**Files:** All modified files

- [ ] **Step 1: Test Flask app initialization**
Run: `.\env\Scripts\python.exe -c "from app import app; print('App initialized cleanly!')"`

- [ ] **Step 2: Test User Registration & Login flow with Flask test client**
Run test script verifying `/register`, `/login`, and protected route redirects.
