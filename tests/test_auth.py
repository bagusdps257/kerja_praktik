import pytest
from models.user_model import UserModel, User
from models.extensions import db

def test_user_password_hashing(app):
    with app.app_context():
        user = UserModel.create_user("jawa_user", "SecurePass123!")
        assert user.id is not None
        assert user.username == "jawa_user"
        assert user.password_hash != "SecurePass123!"
        assert user.check_password("SecurePass123!") is True
        assert user.check_password("WrongPassword") is False

def test_duplicate_username_rejected(app):
    with app.app_context():
        UserModel.create_user("unique_admin", "pass123")
        with pytest.raises(ValueError, match="Username sudah terdaftar"):
            UserModel.create_user("unique_admin", "anotherpass")

def test_login_and_logout_flow(client, app, test_user):
    # 1. Failed login with wrong password
    res_fail = client.post("/login", data={
        "username": "admin_test",
        "password": "wrongpassword"
    }, follow_redirects=True)
    assert b"Username atau password salah" in res_fail.data

    # 2. Successful login with correct password
    res_ok = client.post("/login", data={
        "username": "admin_test",
        "password": "password123"
    }, follow_redirects=True)
    assert res_ok.status_code == 200
    assert b"Dashboard OCR" in res_ok.data

    # 3. Logout
    res_logout = client.get("/logout", follow_redirects=True)
    assert b"Masuk ke System" in res_logout.data

def test_registration_lockdown_when_user_exists(client, app, test_user):
    # When a user exists and ALLOW_REGISTRATION is False, /register should redirect to login
    res = client.get("/register", follow_redirects=True)
    assert b"Pendaftaran akun baru ditutup oleh administrator" in res.data
