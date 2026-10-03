from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

from config.settings import SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, FLASK_DEBUG
from models.extensions import db
from models.user_model import UserModel
from routes.dashboard import dashboard_bp
from routes.ocr import ocr_bp
from routes.folder import folder_bp
from routes.export import export_bp
from routes.auth import auth_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['WTF_CSRF_TIME_LIMIT'] = None
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

db.init_app(app)

csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Silakan login terlebih dahulu untuk mengakses halaman ini."
login_manager.login_message_category = "warning"

user_model = UserModel()


@login_manager.user_loader
def load_user(user_id):
    try:
        return user_model.get_by_id(int(user_id))
    except (ValueError, TypeError):
        return None


# Register Blueprint
app.register_blueprint(dashboard_bp)
app.register_blueprint(ocr_bp)
app.register_blueprint(folder_bp)
app.register_blueprint(export_bp)
app.register_blueprint(auth_bp)

@app.template_filter('format_datetime')
def format_datetime_filter(value):
    if not value or value == '-':
        return '-'
    try:
        from datetime import datetime
        clean_ts = str(value).replace('T', ' ')
        if '.' in clean_ts:
            clean_ts = clean_ts.split('.')[0]
        dt = datetime.strptime(clean_ts, '%Y-%m-%d %H:%M:%S')
        bulan = [
            '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
            'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
        ]
        return f"{dt.day} {bulan[dt.month]} {dt.year}, {dt.strftime('%H:%M')} WIB"
    except Exception:
        return str(value).replace('T', ' ').split('.')[0]


if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print("\n" + "="*70)
            print("❌ GAGAL MENGHUBUNGI SERVER DATABASE (MySQL / MariaDB):")
            print(f"Detail error: {e}")
            print("\n💡 PANDUAN PENYELESAIAN:")
            print("1. Jika menggunakan Laragon:")
            print("   - Buka aplikasi Laragon, lalu klik tombol 'Start All' (pastikan MySQL menyala hijau).")
            print("2. Jika menggunakan XAMPP:")
            print("   - Buka XAMPP Control Panel, lalu klik tombol 'Start' pada modul MySQL.")
            print("3. Jika ingin menggunakan database lokal SQLite sebagai alternatif:")
            print("   - Ubah baris DATABASE_URL di file .env menjadi:")
            print("     DATABASE_URL=sqlite:///database/ocr_database.db")
            print("="*70 + "\n")
            raise SystemExit(1)

    app.run(debug=FLASK_DEBUG)