# Role Management & User Access Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Role-Based Access Control (RBAC) distinguishing `operator` and `user`, provide a complete user management UI, protect destructive endpoints (database reset & user deletion), while allowing standard users to run OCR, update folders, and adjust OCR settings.

**Architecture:** Extend `User` model with a `role` column, add an auto-migration check on application initialization, create an `@operator_required` authorization decorator in Flask, introduce `/users/*` management endpoints, and adapt Jinja2 views (sidebar, topbar, documents reset modal, and a new `users.html` template).

**Tech Stack:** Python 3.12+, Flask 3.0+, Flask-SQLAlchemy, Flask-Login, PyMySQL / SQLite, Jinja2, Bootstrap 5.3, pytest.

---

## Global Constraints

- Role values must strictly be `'operator'` or `'user'`.
- Default role for new users is `'user'`.
- Existing default administrators (`bagus`, `bagusdps`) must have `'operator'` role.
- Operator cannot delete their own account (`current_user.id != target_user_id`).
- Standard users must retain access to run OCR (`/jalankan`, `/stop`), change folders (`/update_folder`), and modify OCR parameters (`/settings`).
- Standard users must be blocked from `/users/*` and `/reset_db`.
- Public registration (`/register`) must be closed so accounts are created exclusively by the Operator.
- All 11 existing unit tests must continue to pass, plus new tests for all role rules.

---

### Task 1: Database Schema & User Model RBAC Support

**Files:**
- Modify: `models/user_model.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- `User.role`: String column (`'operator'` or `'user'`).
- `User.is_operator`: Property returning `bool` (`self.role == 'operator'`).
- `UserModel.init_db()`: Checks and adds `role` column to `users` table via SQLAlchemy `inspect`.
- `UserModel.get_all_users()`: Returns `list[User]` ordered by `User.id.desc()`.
- `UserModel.create_user(username, password, role='user')`: Accepts role parameter and creates user.
- `UserModel.delete_user(user_id, current_user_id)`: Deletes user if `user_id != current_user_id`.
- `UserModel.reset_user_password(user_id, new_password)`: Resets target user's password hash.
- `UserModel.update_user_role(user_id, new_role)`: Updates target user's role.

- [ ] **Step 1: Write failing tests for User model RBAC extensions**

In `tests/test_auth.py`, add:
```python
def test_user_role_assignment_and_operator_property(app):
    with app.app_context():
        u_default = UserModel.create_user("operator_tester", "pass123", role="operator")
        u_standard = UserModel.create_user("standard_tester", "pass123", role="user")

        assert u_default.role == "operator"
        assert u_default.is_operator is True

        assert u_standard.role == "user"
        assert u_standard.is_operator is False

def test_user_management_methods(app):
    with app.app_context():
        op = UserModel.create_user("main_op", "pass123", role="operator")
        staff = UserModel.create_user("staff_member", "pass123", role="user")

        # Operator cannot delete self
        assert UserModel.delete_user(op.id, op.id) is False

        # Operator can reset staff password
        assert UserModel.reset_user_password(staff.id, "new_secure_pass") is True
        refreshed_staff = UserModel.get_by_id(staff.id)
        assert refreshed_staff.check_password("new_secure_pass") is True

        # Operator can update role
        assert UserModel.update_user_role(staff.id, "operator") is True
        assert UserModel.get_by_id(staff.id).is_operator is True

        # Operator can delete staff
        assert UserModel.delete_user(staff.id, op.id) is True
        assert UserModel.get_by_id(staff.id) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\env\Scripts\python.exe -m pytest tests/test_auth.py::test_user_role_assignment_and_operator_property -v`  
Expected: FAIL (argument or attribute error for `role`).

- [ ] **Step 3: Implement RBAC methods and schema in `models/user_model.py`**

Update `User` class to include `role` column, `is_operator` property, and update `UserModel` with `init_db()`, `get_all_users()`, `delete_user()`, `reset_user_password()`, and `update_user_role()`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.\env\Scripts\python.exe -m pytest tests/test_auth.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit changes**

```bash
git add models/user_model.py tests/test_auth.py
git commit -m "feat(auth): add role column, is_operator property, and user management methods"
```

---

### Task 2: Backend Authorization Decorator & Management Endpoints

**Files:**
- Modify: `routes/auth.py`
- Modify: `routes/dashboard.py:425-459`
- Modify: `config/settings.py` and `.env`
- Test: `tests/test_auth.py`

**Interfaces:**
- `@operator_required`: Decorator protecting route access.
- `GET /users`: Renders user management template.
- `POST /users/create`: Endpoint to add new user.
- `POST /users/delete/<int:user_id>`: Endpoint to delete user.
- `POST /users/reset-password/<int:user_id>`: Endpoint to reset password.
- `POST /users/change-role/<int:user_id>`: Endpoint to switch role.
- `POST /reset_db`: Decorated with `@operator_required`.

- [ ] **Step 1: Write failing tests for route authorization**

In `tests/test_auth.py`, add:
```python
def test_operator_routes_authorization(client, app):
    with app.app_context():
        op = UserModel.create_user("super_op", "pass123", role="operator")
        reg = UserModel.create_user("regular_joe", "pass123", role="user")

    # 1. Anonymous redirected to login
    res = client.get("/users")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]

    # 2. Regular user blocked from /users
    client.post("/login", data={"username": "regular_joe", "password": "pass123"})
    res_reg = client.get("/users", follow_redirects=True)
    assert b"Akses ditolak" in res_reg.data

    # 3. Regular user blocked from /reset_db
    res_reset = client.post("/reset_db", data={"password": "pass123"}, follow_redirects=True)
    assert b"Akses ditolak" in res_reset.data
    client.get("/logout")

    # 4. Operator allowed to view /users
    client.post("/login", data={"username": "super_op", "password": "pass123"})
    res_op = client.get("/users")
    assert res_op.status_code == 200
    assert b"Manajemen Pengguna" in res_op.data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\env\Scripts\python.exe -m pytest tests/test_auth.py::test_operator_routes_authorization -v`  
Expected: FAIL (route `/users` 404 not found).

- [ ] **Step 3: Implement `@operator_required` and user management routes**

1. In `routes/auth.py`:
   - Implement `operator_required(f)` decorator.
   - Enforce closed registration in `is_registration_allowed()`.
   - Add routes: `/users`, `/users/create`, `/users/delete/<int:user_id>`, `/users/reset-password/<int:user_id>`, `/users/change-role/<int:user_id>`.
2. In `routes/dashboard.py`:
   - Add `@operator_required` decorator to `reset_db()` route.
3. In `.env`:
   - Set `ALLOW_REGISTRATION=false`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.\env\Scripts\python.exe -m pytest tests/test_auth.py -v`  
Expected: PASS.

- [ ] **Step 5: Commit changes**

```bash
git add routes/auth.py routes/dashboard.py .env tests/test_auth.py
git commit -m "feat(auth): implement operator_required decorator and user management routes"
```

---

### Task 3: UI Templates Integration (Users View, Navigation, and Role Badges)

**Files:**
- Create: `templates/users.html`
- Modify: `templates/partials/sidebar.html`
- Modify: `templates/partials/navbar.html`
- Modify: `templates/documents.html:36-45`

**Interfaces:**
- `templates/users.html`: Extends `base.html`, displays user table, modal for creating user, modal for resetting password, modal for deleting user.
- `sidebar.html`: Displays "Kelola Pengguna" link if `current_user.is_operator`.
- `navbar.html`: Displays `Operator` or `User` badge alongside user's username.
- `documents.html`: Wraps `#resetDbModal` trigger button inside `{% if current_user.is_operator %}`.

- [ ] **Step 1: Create `templates/users.html`**

Create the template with:
- Page title & subtitle.
- "+ Tambah Pengguna Baru" button opening `#createUserModal`.
- User list table: No, Username, Role (Badge), Dibuat Pada, Login Terakhir, Aksi.
- Modals for Add User, Reset Password, and Delete Confirmation.
- CSRF token in all forms.

- [ ] **Step 2: Update `templates/partials/sidebar.html`**

Add navigation item for `Kelola Pengguna` protected by `{% if current_user.is_operator %}`.

- [ ] **Step 3: Update `templates/partials/navbar.html`**

Add dynamic role badge next to username:
```html
<span class="badge {% if current_user.is_operator %}bg-success-subtle text-success border border-success-subtle{% else %}bg-secondary-subtle text-secondary border border-secondary-subtle{% endif %} rounded-pill px-2 py-0.5 small">
    {{ 'Operator' if current_user.is_operator else 'User' }}
</span>
```

- [ ] **Step 4: Update `templates/documents.html`**

Wrap "Hapus Riwayat" button in `{% if current_user.is_operator %}`.

- [ ] **Step 5: Verify template syntax & rendering**

Run:
```powershell
.\env\Scripts\python.exe -c "from app import app; [app.jinja_env.get_template(t) for t in ['users.html', 'partials/sidebar.html', 'partials/navbar.html', 'documents.html']]; print('Templates compiled cleanly!')"
```

- [ ] **Step 6: Commit changes**

```bash
git add templates/users.html templates/partials/sidebar.html templates/partials/navbar.html templates/documents.html
git commit -m "feat(ui): add user management page, role badges, and access-restricted UI elements"
```

---

### Task 4: End-to-End System Verification & Migration Check

**Files:**
- Test: All unit test suites (`tests/test_*.py`)
- Runtime check: MySQL connection & database column update verification

- [ ] **Step 1: Run complete test suite**

Run: `.\env\Scripts\python.exe -m pytest -v`  
Expected: All tests pass.

- [ ] **Step 2: Verify live database migration on Laragon MySQL**

Run a script that initializes `app.app_context()` and calls `UserModel.init_db()` against MySQL:
```powershell
.\env\Scripts\python.exe -c "from app import app; from models.user_model import UserModel, User;
with app.app_context():
    UserModel.init_db()
    for u in User.query.all():
        print(f'User: {u.username}, Role: {u.role}, IsOperator: {u.is_operator}')
"
```
Verify that existing users (`bagus`, `bagusdps`) have role `'operator'`.

- [ ] **Step 3: Commit and finalize**

```bash
git add .
git commit -m "chore(release): complete role management and access control implementation"
```
