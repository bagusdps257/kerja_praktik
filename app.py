from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

from config.settings import SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)