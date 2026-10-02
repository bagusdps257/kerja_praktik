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
    assert (b"Status & Kontrol" in res_ok.data or b"Operasional" in res_ok.data)

    # 3. Logout
    res_logout = client.get("/logout", follow_redirects=True)
    assert (b"Portal Petugas" in res_logout.data or b"Masuk Sistem" in res_logout.data)

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
    assert (b"Otorisasi Petugas" in res_op.data or b"Otorisasi" in res_op.data)


def test_ui_role_visibility_and_user_crud_endpoints(client, app):
    with app.app_context():
        op = UserModel.create_user("operator_boss", "pass1234", role="operator")
        staff = UserModel.create_user("staff_member", "pass1234", role="user")
        staff_id = staff.id

    # 1. Staff view /documents: Hapus Riwayat and Otorisasi Petugas must NOT appear
    client.post("/login", data={"username": "staff_member", "password": "pass1234"})
    res_staff_doc = client.get("/documents")
    assert b"Hapus Riwayat" not in res_staff_doc.data
    assert b"Otorisasi Petugas" not in res_staff_doc.data
    client.get("/logout")

    # 2. Operator view /documents: Hapus Riwayat and Otorisasi Petugas MUST appear
    client.post("/login", data={"username": "operator_boss", "password": "pass1234"})
    res_op_doc = client.get("/documents")
    assert b"Hapus Riwayat" in res_op_doc.data
    assert b"Otorisasi Petugas" in res_op_doc.data

    # 3. Operator creates new user via HTTP POST
    res_create = client.post("/users/create", data={
        "username": "new_hire",
        "password": "hirepassword",
        "role": "user"
    }, follow_redirects=True)
    assert res_create.status_code == 200
    assert b"new_hire" in res_create.data

    # Check new hire in DB
    with app.app_context():
        new_hire = UserModel.get_by_username("new_hire")
        assert new_hire is not None
        assert new_hire.role == "user"
        new_hire_id = new_hire.id

    # 4. Operator changes role of new_hire to operator
    res_role = client.post(f"/users/change-role/{new_hire_id}", data={
        "new_role": "operator"
    }, follow_redirects=True)
    assert res_role.status_code == 200
    with app.app_context():
        assert UserModel.get_by_id(new_hire_id).role == "operator"

    # 5. Operator resets password of new_hire
    res_reset_pwd = client.post(f"/users/reset-password/{new_hire_id}", data={
        "new_password": "brandnewpassword123",
        "confirm_password": "brandnewpassword123"
    }, follow_redirects=True)
    assert res_reset_pwd.status_code == 200

    # 6. Operator deletes staff_member
    res_del = client.post(f"/users/delete/{staff_id}", follow_redirects=True)
    assert res_del.status_code == 200
    with app.app_context():
        assert UserModel.get_by_id(staff_id) is None



