# User Profile & Password Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement dedicated user profile page (`/profile`), password change functionality (`/profile/change-password`), and navbar link integration.

**Architecture:** 
1. `models/user_model.py`: Add `update_password` method to hash new password and update database record.
2. `routes/auth.py`: Add `GET /profile` and `POST /profile/change-password` endpoints protected with `@login_required`.
3. `templates/profile.html`: Build modern dark-themed user account summary card and password change form with CSRF protection.
4. Navigation: Add user profile page link to navbar/topbar user badge.

**Tech Stack:** Python 3, Flask, Flask-Login, Flask-WTF, werkzeug.security, HTML/CSS

## Global Constraints

- Protect all profile endpoints with `@login_required`.
- Validate old password correctness and new password matching + minimum length (>= 6).
- Include CSRF token in password update form.

---

### Task 1: Extend User Model (`models/user_model.py`)

**Files:**
- Modify: [`models/user_model.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/models/user_model.py)

**Interfaces:**
- Consumes: `werkzeug.security.generate_password_hash`, `models.database.get_connection`
- Produces: `UserModel.update_password(user_id, new_password)`

- [ ] **Step 1: Add `update_password` method to `UserModel`**

In `models/user_model.py`:
```python
    def update_password(self, user_id, new_password):
        conn = get_connection()
        cursor = conn.cursor()
        pwd_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, user_id))
        conn.commit()
        conn.close()
        return True
```

---

### Task 2: Profile & Password Change Routes (`routes/auth.py`)

**Files:**
- Modify: [`routes/auth.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/routes/auth.py)

**Interfaces:**
- Consumes: `flask_login.login_required`, `current_user`, `UserModel.update_password`
- Produces: `/profile` and `/profile/change-password` routes.

- [ ] **Step 1: Add `/profile` and `/profile/change-password` to `routes/auth.py`**

In `routes/auth.py`:
```python
@auth_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    return render_template("profile.html")

@auth_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_user.check_password(old_password):
        flash("Password lama yang Anda masukkan salah.", "danger")
    elif len(new_password) < 6:
        flash("Password baru minimal harus 6 karakter.", "danger")
    elif new_password != confirm_password:
        flash("Konfirmasi password baru tidak cocok.", "danger")
    else:
        user_model.update_password(current_user.id, new_password)
        flash("Password Anda berhasil diperbarui! Silakan gunakan password baru pada login berikutnya.", "success")

    return redirect(url_for("auth.profile"))
```

---

### Task 3: Profile UI Template & Navigation Integration

**Files:**
- Create: `templates/profile.html`
- Modify: [`templates/partials/topbar.html`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/templates/partials/topbar.html)
- Modify: [`templates/partials/navbar.html`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/templates/partials/navbar.html)

- [ ] **Step 1: Create `templates/profile.html`**

Dark-themed layout with:
- Flash messages block.
- Account Summary Card (Username, Account Created Date, Last Login Timestamp).
- Password Change Form with `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>`, fields for `old_password`, `new_password`, `confirm_password`, and Submit button.

- [ ] **Step 2: Update Navbar / Topbar links**

Link user profile badge to `url_for('auth.profile')`.

---

### Task 4: End-to-End Verification

**Files:** All modified files

- [ ] **Step 1: Run end-to-end verification script testing password change flow**

Verify profile page rendering, password validation, successful password change, login with new password, and rejection of old password.
