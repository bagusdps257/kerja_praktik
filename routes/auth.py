from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.user_model import UserModel

auth_bp = Blueprint("auth", __name__)
user_model = UserModel()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login.
    If user is already authenticated, redirect to dashboard.index.
    On POST: validate form parameters username & password, lookup user via user_model,
    verify password, log in user with remember=True, update last login timestamp,
    and redirect to 'next' URL parameter or dashboard.index.
    Flash alert messages on invalid credentials or empty fields.
    """
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username dan password wajib diisi.", "danger")
            return render_template("login.html")

        user = user_model.get_by_username(username)
        if user and user.check_password(password):
            login_user(user, remember=True)
            user_model.update_last_login(user.id)
            flash("Login berhasil!", "success")

            next_page = request.args.get("next")
            if not next_page or not next_page.startswith("/") or next_page.startswith("//"):
                next_page = url_for("dashboard.index")
            return redirect(next_page)
        else:
            flash("Username atau password salah.", "danger")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle user registration.
    If user is already authenticated, redirect to dashboard.index.
    On POST: validate username, password, and confirm_password form parameters.
    Check fields are non-empty, passwords match, and username is unique.
    Create user via user_model.create_user(), flash success message, and redirect to auth.login.
    Render register.html.
    """
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password or not confirm_password:
            flash("Semua bidang harus diisi.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Konfirmasi password tidak cocok.", "danger")
            return render_template("register.html")

        if user_model.get_by_username(username):
            flash("Username sudah digunakan.", "danger")
            return render_template("register.html")

        new_user = user_model.create_user(username, password)
        if new_user:
            flash("Registrasi berhasil! Silakan login.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Gagal mendaftarkan pengguna.", "danger")

    return render_template("register.html")


@auth_bp.route("/logout", methods=["GET"])
@login_required
def logout():
    """
    Handle user logout.
    Call logout_user(), flash info message, and redirect to auth.login.
    """
    logout_user()
    flash("Anda telah keluar.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    """
    Render user profile page.
    """
    return render_template("profile.html")


@auth_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    """
    Handle password change for current user.
    Accepts form parameters: old_password, new_password, confirm_password.
    Validations:
      1. current_user.check_password(old_password) -> Flash danger message if incorrect.
      2. len(new_password) >= 6 -> Flash danger message if too short.
      3. new_password == confirm_password -> Flash danger message if mismatch.
    If all validations pass:
      user_model.update_password(current_user.id, new_password)
      flashes success message and redirects to url_for('auth.profile').
    """
    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_user.check_password(old_password):
        flash("Password lama salah.", "danger")
        return redirect(url_for("auth.profile"))

    if len(new_password) < 6:
        flash("Password baru minimal 6 karakter.", "danger")
        return redirect(url_for("auth.profile"))

    if new_password != confirm_password:
        flash("Konfirmasi password baru tidak cocok.", "danger")
        return redirect(url_for("auth.profile"))

    user_model.update_password(current_user.id, new_password)
    flash("Password berhasil diubah.", "success")
    return redirect(url_for("auth.profile"))

