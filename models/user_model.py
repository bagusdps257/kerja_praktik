from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.String(50), nullable=False)
    last_login = db.Column(db.String(50))

    def check_password(self, password):
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def formatted_created_at(self):
        return self._format_timestamp(self.created_at)

    @property
    def formatted_last_login(self):
        return self._format_timestamp(self.last_login)

    def _format_timestamp(self, ts_str):
        if not ts_str or ts_str == '-':
            return '-'
        try:
            # Handle ISO string with or without microsecond / T
            clean_ts = str(ts_str).replace('T', ' ')
            if '.' in clean_ts:
                clean_ts = clean_ts.split('.')[0]
            dt = datetime.strptime(clean_ts, '%Y-%m-%d %H:%M:%S')
            
            bulan = [
                '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
            ]
            return f"{dt.day} {bulan[dt.month]} {dt.year}, {dt.strftime('%H:%M')} WIB"
        except Exception:
            return str(ts_str).replace('T', ' ').split('.')[0]

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"


class UserModel:
    def __init__(self):
        pass # init_db is handled globally by db.create_all()

    @classmethod
    def get_by_id(cls, user_id):
        if user_id is None:
            return None
        return db.session.get(User, int(user_id))

    @classmethod
    def get_by_username(cls, username):
        if not username or not isinstance(username, str):
            return None
        clean_username = username.strip().lower()
        if not clean_username:
            return None
        return User.query.filter_by(username=clean_username).first()

    @classmethod
    def create_user(cls, username, password):
        if not username or not password:
            raise ValueError("Username dan password harus diisi")
            
        clean_username = username.strip().lower()
        if cls.get_by_username(clean_username):
            raise ValueError("Username sudah terdaftar")
            
        password_hash = generate_password_hash(password)
        created_at = datetime.now().isoformat()
        
        new_user = User(
            username=clean_username,
            password_hash=password_hash,
            created_at=created_at
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            return new_user
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Gagal membuat user: {str(e)}")

    @classmethod
    def update_last_login(cls, user_id):
        user = cls.get_by_id(user_id)
        if user:
            user.last_login = datetime.now().isoformat()
            db.session.commit()
            return True
        return False
        
    @classmethod
    def update_password(cls, user_id, new_password):
        if user_id is None or not new_password:
            return False
        user = cls.get_by_id(user_id)
        if user:
            user.password_hash = generate_password_hash(new_password)
            try:
                db.session.commit()
                return True
            except Exception:
                db.session.rollback()
                return False
        return False
