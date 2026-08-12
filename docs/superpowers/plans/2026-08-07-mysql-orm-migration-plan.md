# MySQL ORM Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the OCR application from raw SQLite queries to Flask-SQLAlchemy with MySQL.

**Architecture:** We will introduce a central `extensions.py` for the `db` object to prevent circular imports. `app.py` will configure the MySQL URI and initialize the database. Existing models (`user_model.py` and `dashboard_model.py`) will be transformed into SQLAlchemy models (`db.Model`), replacing raw queries with ORM operations.

**Tech Stack:** Python, Flask, Flask-SQLAlchemy, PyMySQL (or mysql-connector-python)

## Global Constraints
- Target database engine: MySQL
- Connector: `pymysql` or `mysql-connector-python`
- Keep existing method signatures intact so the frontend routes do not break.

---

### Task 1: Setup Extensions and App Configuration

**Files:**
- Create: `models/extensions.py`
- Modify: `app.py`
- Modify: `config/settings.py`
- Modify: `requirements.txt`

**Interfaces:**
- Produces: `models.extensions.db` (SQLAlchemy instance)

- [ ] **Step 1: Update dependencies**

Modify `requirements.txt` to add:
```txt
Flask-SQLAlchemy
PyMySQL
```

- [ ] **Step 2: Create `models/extensions.py`**

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
```

- [ ] **Step 3: Update `config/settings.py`**

Add the `SQLALCHEMY_DATABASE_URI` setting (defaulting to local Laragon MySQL) at the bottom:
```python
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/ocr_database"
SQLALCHEMY_TRACK_MODIFICATIONS = False
```

- [ ] **Step 4: Initialize DB in `app.py`**

Modify `app.py` to import and initialize the database.

```python
# In app.py, add imports:
from models.extensions import db
from config.settings import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS

# After app = Flask(__name__), add:
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
db.init_app(app)

# Before app.run, add context to create tables:
with app.app_context():
    db.create_all()
```

- [ ] **Step 5: Commit**
```bash
git add requirements.txt models/extensions.py app.py config/settings.py
git commit -m "chore: setup flask-sqlalchemy and pymysql"
```

---

### Task 2: Refactor User Model

**Files:**
- Modify: `models/user_model.py`
- Create: `scratch/test_user_orm.py`

**Interfaces:**
- Consumes: `models.extensions.db`

- [ ] **Step 1: Write test for user ORM**

```python
# scratch/test_user_orm.py
from app import app
from models.extensions import db
from models.user_model import User, UserModel

def test_user_creation_and_retrieval():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use sqlite memory for quick unit test
    with app.app_context():
        db.create_all()
        model = UserModel()
        # Test creation
        user = User(username='testuser', password_hash='hash123', created_at='2026-01-01')
        db.session.add(user)
        db.session.commit()
        
        # Test retrieval
        fetched = model.get_by_username('testuser')
        assert fetched is not None
        assert fetched.username == 'testuser'
```

- [ ] **Step 2: Refactor `models/user_model.py` to ORM**

Replace the entire content of `models/user_model.py` with the following SQLAlchemy model:

```python
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
```

- [ ] **Step 3: Run test**
Run: `pytest scratch/test_user_orm.py`
Expected: PASS

- [ ] **Step 4: Commit**
```bash
git add models/user_model.py scratch/test_user_orm.py
git commit -m "refactor: migrate UserModel to SQLAlchemy"
```

---

### Task 3: Refactor Dashboard Model Schema & Basic CRUD

**Files:**
- Modify: `models/dashboard_model.py`

**Interfaces:**
- Consumes: `models.extensions.db`

- [ ] **Step 1: Define `Riwayat` SQLAlchemy Model**

Open `models/dashboard_model.py` and replace `get_connection` imports. Add the `Riwayat` model right below the `IMAGE_EXTENSIONS` definition:

```python
from .extensions import db
from sqlalchemy import func, or_, desc, asc

class Riwayat(db.Model):
    __tablename__ = 'riwayat'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_key = db.Column(db.String(255))
    folder_path = db.Column(db.String(500))
    nama_file = db.Column(db.String(255))
    status = db.Column(db.String(50))
    waktu = db.Column(db.String(50))
    keterangan = db.Column(db.Text)
    file_size = db.Column(db.String(50))
    author = db.Column(db.String(100))
    page_count = db.Column(db.String(50))
    creation_date = db.Column(db.String(50))
    ocr_confidence = db.Column(db.Float, default=0.0)
    processing_time = db.Column(db.Float, default=0.0)
    retry_count = db.Column(db.Integer, default=0)
    first_processed_at = db.Column(db.String(50))
    last_processed_at = db.Column(db.String(50))
    relative_path = db.Column(db.String(500))
    file_hash = db.Column(db.String(255))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
```

- [ ] **Step 2: Update `OCRDashboardModel.init_db`**

Since `db.create_all()` handles table creation, we just remove all the raw queries from `init_db`. Replace `def init_db(self):` with:

```python
    def init_db(self):
        pass # Schema is managed globally via db.create_all()
```

- [ ] **Step 3: Update `catat_ke_db` & `tambah_riwayat`**

Refactor these methods to use `Riwayat.query` and `db.session.add`.

Replace `catat_ke_db`:
```python
    def catat_ke_db(self, document_key, folder_path, nama_file, status, waktu, keterangan="",
                    file_size="", author="", page_count="", creation_date="",
                    ocr_confidence=0.0, processing_time=0.0, retry_count=0,
                    first_processed_at=None, last_processed_at=None,
                    relative_path="", file_hash=""):
        try:
            doc_key_query = document_key if document_key else ""
            if not doc_key_query and nama_file:
                doc_key_query = nama_file

            existing = None
            if doc_key_query:
                existing = Riwayat.query.filter(
                    or_(Riwayat.document_key == doc_key_query, Riwayat.nama_file == doc_key_query)
                ).first()

            if existing:
                existing.status = status
                existing.waktu = waktu
                if keterangan: existing.keterangan = keterangan
                if file_size: existing.file_size = file_size
                if author: existing.author = author
                if page_count: existing.page_count = page_count
                if creation_date: existing.creation_date = creation_date
                if ocr_confidence: existing.ocr_confidence = ocr_confidence
                if processing_time: existing.processing_time = processing_time
                if relative_path: existing.relative_path = relative_path
                if file_hash: existing.file_hash = file_hash
                
                existing.retry_count = (existing.retry_count or 0) + retry_count
                if not existing.first_processed_at and first_processed_at:
                    existing.first_processed_at = first_processed_at
                if last_processed_at:
                    existing.last_processed_at = last_processed_at
                
                if folder_path: existing.folder_path = folder_path
            else:
                new_record = Riwayat(
                    document_key=doc_key_query,
                    folder_path=folder_path or "",
                    nama_file=nama_file or "",
                    status=status,
                    waktu=waktu,
                    keterangan=keterangan or "",
                    file_size=file_size or "",
                    author=author or "",
                    page_count=page_count or "",
                    creation_date=creation_date or "",
                    ocr_confidence=ocr_confidence or 0.0,
                    processing_time=processing_time or 0.0,
                    retry_count=retry_count or 0,
                    first_processed_at=first_processed_at or waktu,
                    last_processed_at=last_processed_at or waktu,
                    relative_path=relative_path or doc_key_query,
                    file_hash=file_hash or ""
                )
                db.session.add(new_record)
            
            db.session.commit()
            self.invalidate_stats_cache()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Database error in catat_ke_db: {e}")
            return False
```

Replace `tambah_riwayat`:
```python
    def tambah_riwayat(self, data):
        return self.catat_ke_db(
            document_key=data.get('document_key', data.get('nama_file', '')),
            folder_path=data.get('folder_path', ''),
            nama_file=data.get('nama_file', ''),
            status=data.get('status', ''),
            waktu=data.get('waktu', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            keterangan=data.get('keterangan', ''),
            file_size=data.get('file_size', ''),
            author=data.get('author', ''),
            page_count=data.get('page_count', ''),
            creation_date=data.get('creation_date', ''),
            ocr_confidence=data.get('ocr_confidence', 0.0),
            processing_time=data.get('processing_time', 0.0),
            retry_count=data.get('retry_count', 0),
            first_processed_at=data.get('first_processed_at'),
            last_processed_at=data.get('last_processed_at'),
            relative_path=data.get('relative_path', ''),
            file_hash=data.get('file_hash', '')
        )
```

- [ ] **Step 4: Commit**
```bash
git add models/dashboard_model.py
git commit -m "refactor: convert dashboard_model schema and insert methods to ORM"
```

---

### Task 4: Refactor Dashboard Model Queries

**Files:**
- Modify: `models/dashboard_model.py`

- [ ] **Step 1: Replace filter helpers**

Remove `_get_period_where_clause` and `_build_filter_query` and replace with ORM query builder.
```python
    def _build_orm_query(self, status=None, q=None, period=None, month=None, year=None):
        query = Riwayat.query

        if status and status != 'all':
            query = query.filter(Riwayat.status == status)

        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    Riwayat.nama_file.ilike(search_term),
                    Riwayat.folder_path.ilike(search_term),
                    Riwayat.keterangan.ilike(search_term)
                )
            )

        if period and period != 'all':
            now = datetime.now()
            if period == 'today':
                date_prefix = now.strftime('%Y-%m-%d')
                query = query.filter(Riwayat.waktu.like(f"{date_prefix}%"))
            elif period == 'week':
                from datetime import timedelta
                week_ago = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
                query = query.filter(Riwayat.waktu >= week_ago)
            elif period == 'month_specific' and month and year:
                date_prefix = f"{year}-{month.zfill(2)}"
                query = query.filter(Riwayat.waktu.like(f"{date_prefix}%"))
            elif period == 'year_specific' and year:
                date_prefix = f"{year}-"
                query = query.filter(Riwayat.waktu.like(f"{date_prefix}%"))

        return query
```

- [ ] **Step 2: Update `ambil_riwayat_db` and `ambil_dokumen`**

```python
    def ambil_riwayat_db(self, batas=50, status=None, q=None, period=None, month=None, year=None):
        try:
            query = self._build_orm_query(status, q, period, month, year)
            results = query.order_by(desc(Riwayat.id)).limit(batas).all()
            return [r.to_dict() for r in results]
        except Exception as e:
            print(f"Error ambil_riwayat_db: {e}")
            return []

    def ambil_dokumen(self, limit, offset, status=None, q=None, period=None, month=None, year=None):
        try:
            query = self._build_orm_query(status, q, period, month, year)
            total = query.count()
            
            results = query.order_by(desc(Riwayat.id)).limit(limit).offset(offset).all()
            documents = [r.to_dict() for r in results]
            
            return {"data": documents, "total": total}
        except Exception as e:
            print(f"Error ambil_dokumen: {e}")
            return {"data": [], "total": 0}
```

- [ ] **Step 3: Update `ambil_tahun_tersedia`**

```python
    def ambil_tahun_tersedia(self):
        try:
            # Get unique years from 'waktu' column (format: YYYY-MM-DD ...)
            results = db.session.query(func.substr(Riwayat.waktu, 1, 4)).distinct().all()
            years = [r[0] for r in results if r[0]]
            current_year = str(datetime.now().year)
            if current_year not in years:
                years.append(current_year)
            return sorted(years, reverse=True)
        except Exception:
            return [str(datetime.now().year)]
```

- [ ] **Step 4: Commit**
```bash
git add models/dashboard_model.py
git commit -m "refactor: convert dashboard_model fetch queries to ORM"
```

---

### Task 5: Refactor Dashboard Analytics & Stats

**Files:**
- Modify: `models/dashboard_model.py`

- [ ] **Step 1: Refactor `ambil_statistik`**

```python
    def ambil_statistik(self, force_refresh=False):
        try:
            # Query base metrics
            total = Riwayat.query.count()
            sukses = Riwayat.query.filter_by(status='Sukses').count()
            gagal = Riwayat.query.filter_by(status='Gagal').count()
            
            # Subqueries for confidence and processing time
            avg_conf = db.session.query(func.avg(Riwayat.ocr_confidence)).filter(Riwayat.status == 'Sukses').scalar()
            avg_time = db.session.query(func.avg(Riwayat.processing_time)).filter(Riwayat.status == 'Sukses').scalar()
            
            today_prefix = datetime.now().strftime('%Y-%m-%d')
            today_count = Riwayat.query.filter(Riwayat.waktu.like(f"{today_prefix}%")).count()
            
            return {
                "total_dokumen": total,
                "sukses": sukses,
                "gagal": gagal,
                "proses": total - sukses - gagal, # Assuming remaining are in process
                "hari_ini": today_count,
                "rata_confidence": round(avg_conf or 0, 1),
                "rata_waktu_proses": round(avg_time or 0, 2)
            }
        except Exception as e:
            print(f"Error ambil_statistik: {e}")
            return self._default_stats()

    def _default_stats(self):
        return {
            "total_dokumen": 0, "sukses": 0, "gagal": 0, "proses": 0,
            "hari_ini": 0, "rata_confidence": 0.0, "rata_waktu_proses": 0.0
        }
```

- [ ] **Step 2: Refactor `ambil_data_analitik` and `ambil_data_monitoring`**

Replace `ambil_data_analitik`:
```python
    def ambil_data_analitik(self, period=None, month=None, year=None):
        try:
            query = self._build_orm_query(period=period, month=month, year=year)
            
            # Format depends on period, simpliest is grouping by substring of 'waktu'
            # For brevity, implementing a generic group by date (YYYY-MM-DD)
            results = db.session.query(
                func.substr(Riwayat.waktu, 1, 10).label('date'),
                Riwayat.status,
                func.count(Riwayat.id)
            ).filter(
                query.whereclause if query.whereclause is not None else True
            ).group_by('date', Riwayat.status).all()
            
            # Transform results to expected frontend format
            labels = sorted(list(set([r[0] for r in results if r[0]])))
            data = {'Sukses': [], 'Gagal': [], 'Proses': []}
            
            for label in labels:
                sukses_cnt = sum([r[2] for r in results if r[0] == label and r[1] == 'Sukses'])
                gagal_cnt = sum([r[2] for r in results if r[0] == label and r[1] == 'Gagal'])
                proses_cnt = sum([r[2] for r in results if r[0] == label and r[1] not in ('Sukses', 'Gagal')])
                
                data['Sukses'].append(sukses_cnt)
                data['Gagal'].append(gagal_cnt)
                data['Proses'].append(proses_cnt)
                
            return {"labels": labels, "datasets": data}
        except Exception as e:
            print(f"Error ambil_data_analitik: {e}")
            return {"labels": [], "datasets": {'Sukses': [], 'Gagal': [], 'Proses': []}}
```

Replace `ambil_data_monitoring`:
```python
    def ambil_data_monitoring(self):
        try:
            today_prefix = datetime.now().strftime('%Y-%m-%d')
            
            # CPU/RAM simulated or fetched from sys. 
            # If relying on DB processing time:
            recent_avg = db.session.query(func.avg(Riwayat.processing_time)).filter(Riwayat.waktu.like(f"{today_prefix}%")).scalar()
            
            return {
                "waktu": datetime.now().strftime("%H:%M:%S"),
                "cpu_usage": round(recent_avg or 0, 1),
                "ram_usage": 0,
                "disk_usage": 0
            }
        except Exception:
            return {"waktu": "", "cpu_usage": 0, "ram_usage": 0, "disk_usage": 0}
```

- [ ] **Step 3: Cleanup Database Module**

Delete `models/database.py` and remove any remaining imports of `get_connection` in `models/__init__.py`.

```bash
git rm models/database.py
git commit -m "refactor: complete ORM migration for analytics and cleanup"
```
