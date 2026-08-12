# User Profile & Password Management Design Spec

## Overview
Implement dedicated `/profile` user account management page and `/profile/change-password` endpoint in `routes/auth.py`, extending `models/user_model.py` with secure password update capability and rendering a modern dark-themed profile template.

## User Model Extension (`models/user_model.py`)
Add method to `UserModel`:
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

## Route Endpoints (`routes/auth.py`)

### 1. `GET /profile`
- Protected with `@login_required`.
- Renders `profile.html` passing `current_user` object.

### 2. `POST /profile/change-password`
- Protected with `@login_required`.
- Validates:
  - `old_password` matches `current_user.check_password(old_password)`.
  - `new_password` has minimum length of 6 characters.
  - `new_password == confirm_password`.
- Calls `user_model.update_password(current_user.id, new_password)`.
- Flashes success/danger alert messages and redirects to `url_for('auth.profile')`.

## UI Template & Navigation (`templates/profile.html`)
- Extends dashboard base theme.
- **Account Summary Card**: Username, Registration Date, Last Login Timestamp.
- **Change Password Card**: Form with CSRF token `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>`, inputs for `old_password`, `new_password`, `confirm_password`, and Submit button.
- **Navigation Integration**: Update header badge in `navbar.html` / `topbar.html` to include clickable Profile link to `url_for('auth.profile')`.
