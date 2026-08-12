# Multi-User Authentication & CSRF Protection Design Spec

## Overview
Add multi-user account authentication (Login, Register, Logout) using `Flask-Login` and `werkzeug.security`, and project-wide CSRF protection using `Flask-WTF` (`CSRFProtect`).

## Architecture & Data Model

### 1. Database Schema (`users` table in `database/ocr_database.db`)
```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_login TEXT
);
```

### 2. User Model & Authentication (`models/user_model.py`)
- Define `User` class implementing `Flask-Login`'s `UserMixin`.
- Implement methods:
  - `get_by_id(user_id)`
  - `get_by_username(username)`
  - `create_user(username, password)`
  - `check_password(password)`
  - `update_last_login()`

### 3. Routes & Endpoints (`routes/auth.py`)
- `GET /login`, `POST /login`: Render login page, validate credentials, log user in via `login_user()`.
- `GET /register`, `POST /register`: Render registration page, create new user account, redirect to login.
- `GET /logout`: Log out current user via `logout_user()`, redirect to login page.

### 4. CSRF Protection
- Initialize `CSRFProtect(app)` in `app.py`.
- Set `SECRET_KEY` in `config/settings.py` / `app.config['SECRET_KEY']`.
- Embed `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>` in all POST forms across templates.

### 5. UI Templates
- `templates/login.html`: Modern, responsive dark-themed login interface matching dashboard aesthetics.
- `templates/register.html`: Registration form interface matching dashboard aesthetics.
- Add user identity and Logout button to navbar in existing layout/templates.

---

## Security Requirements
- Passwords must be hashed using `werkzeug.security.generate_password_hash` with standard PBKDF2/scrypt algorithm.
- All non-auth routes MUST require authentication (`@login_required`).
- Unauthorized requests redirect to `/login`.
- CSRF validation enforced on all `POST` requests.
