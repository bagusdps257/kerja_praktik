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

