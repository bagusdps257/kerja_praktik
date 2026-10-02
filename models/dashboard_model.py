import os
import time
from datetime import datetime
from sqlalchemy import desc, func, or_

from config.settings import LOG_PATH, INPUT_DEFAULT, OUTPUT_DEFAULT
from models.extensions import db
from services.settings_service import load_settings
from services.system_service import (
    format_size,
    hitung_ukuran_folder,
    hitung_total_halaman_folder,
    baca_log_terbaru,
    SUPPORTED_EXTENSIONS,
    IMAGE_EXTENSIONS
)
from services.analytics_service import (
    hitung_statistik_dashboard,
    ambil_data_analitik as service_ambil_data_analitik,
    ambil_data_monitoring as service_ambil_data_monitoring
)


class Riwayat(db.Model):
    """
    Model representasi entitas data riwayat pemrosesan dokumen OCR di MySQL.
    """
    __tablename__ = 'riwayat'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_key = db.Column(db.String(255), index=True)
    folder_path = db.Column(db.String(500))
    nama_file = db.Column(db.String(255), index=True)
    status = db.Column(db.String(50), index=True)
    waktu = db.Column(db.String(50), index=True)
    updated_waktu = db.Column(db.String(50))
    keterangan = db.Column(db.Text)
    file_size = db.Column(db.String(50))
    author = db.Column(db.String(100), index=True)
    subject = db.Column(db.String(255))
    keywords = db.Column(db.String(500))
    page_count = db.Column(db.String(50))
    creation_date = db.Column(db.String(50))
    processing_time = db.Column(db.Float, default=0.0)
    retry_count = db.Column(db.Integer, default=0)
    relative_path = db.Column(db.String(500))
    file_hash = db.Column(db.String(255))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class OCRDashboardModel:
    """
    Data Access Layer (Repository Pattern) untuk entitas Riwayat dokumen OCR.
    Menyediakan query ORM, filter, paging, dan delegasi ke Service Layer.
    """
    SUPPORTED_EXTENSIONS = SUPPORTED_EXTENSIONS
    IMAGE_EXTENSIONS = IMAGE_EXTENSIONS

    def __init__(self):
        settings = load_settings()
        self.input_dir = settings.get("input_dir", INPUT_DEFAULT)
        self.output_dir = settings.get("output_dir", OUTPUT_DEFAULT)
        self.log_path = LOG_PATH
        self._stats_cache = None
        self._stats_cache_time = 0
        self._page_count_cache = {}
        self.init_db()

    def init_db(self):
        """Auto-migration fallback: memastikan kolom dan tabel siap di database aktif."""
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            if 'riwayat' in inspector.get_table_names():
                existing_cols = {col['name'] for col in inspector.get_columns('riwayat')}
                cols_to_add = [
                    ("subject", "VARCHAR(255)"),
                    ("keywords", "VARCHAR(500)"),
                    ("updated_waktu", "VARCHAR(50)")
                ]
                with db.engine.connect() as conn:
                    for col_name, col_type in cols_to_add:
                        if col_name not in existing_cols:
                            try:
                                conn.execute(text(f"ALTER TABLE riwayat ADD COLUMN {col_name} {col_type}"))
                                conn.commit()
                            except Exception:
                                pass
        except Exception:
            pass

    def catat_ke_db(
        self,
        document_key,
        folder_path="",
        nama_file="",
        status="SUKSES",
        keterangan="",
        file_size="-",
        author="-",
        subject="-",
        keywords="-",
        page_count="-",
        creation_date="-",
        processing_time=0.0,
        retry_count=0,
        relative_path="",
        file_hash=""
    ):
        """
        Menyimpan atau memperbarui data riwayat pengerjaan dokumen ke database MySQL.
        Dilengkapi mekanisme retry eksponensial untuk keamanan konkurensi multiprocessing.
        """
        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        max_retries = 5

        for attempt in range(max_retries):
            try:
                doc_key_query = document_key if document_key else ""
                if not doc_key_query and nama_file:
                    doc_key_query = nama_file

                existing = None
                if doc_key_query:
                    existing = Riwayat.query.filter(
                        Riwayat.document_key == doc_key_query
                    ).first()
                    if not existing and '/' not in doc_key_query and '\\' not in doc_key_query:
                        existing = Riwayat.query.filter(
                            Riwayat.nama_file == doc_key_query
                        ).first()

                if existing:
                    existing.status = status
                    existing.updated_waktu = waktu
                    if keterangan: existing.keterangan = keterangan
                    if file_size: existing.file_size = file_size
                    if author: existing.author = author
                    if subject: existing.subject = subject
                    if keywords: existing.keywords = keywords
                    if page_count: existing.page_count = page_count
                    if creation_date: existing.creation_date = creation_date
                    if processing_time: existing.processing_time = processing_time
                    if relative_path: existing.relative_path = relative_path
                    if file_hash: existing.file_hash = file_hash
                    existing.retry_count = (existing.retry_count or 0) + retry_count
                    if folder_path: existing.folder_path = folder_path
                else:
                    new_record = Riwayat(
                        document_key=doc_key_query,
                        folder_path=folder_path or "",
                        nama_file=nama_file or "",
                        status=status,
                        waktu=waktu,
                        updated_waktu=waktu,
                        keterangan=keterangan or "",
                        file_size=file_size or "",
                        author=author or "",
                        subject=subject or "",
                        keywords=keywords or "",
                        page_count=page_count or "",
                        creation_date=creation_date or "",
                        processing_time=processing_time or 0.0,
                        retry_count=retry_count or 0,
                        relative_path=relative_path or doc_key_query,
                        file_hash=file_hash or ""
                    )
                    db.session.add(new_record)

                db.session.commit()
                self.invalidate_stats_cache()
                return True
            except Exception as e:
                db.session.rollback()
                if attempt < max_retries - 1:
                    sleep_time = 0.5 * (2 ** attempt)
                    time.sleep(sleep_time)
                else:
                    print(f"Database error in catat_ke_db after {max_retries} attempts: {e}")
                    return False

    def tambah_riwayat(self, **kwargs):
        return self.catat_ke_db(**kwargs)

    def ambil_tahun_tersedia(self):
        """Mengambil daftar tahun unik dari kolom waktu untuk dropdown filter."""
        try:
            results = db.session.query(func.substr(Riwayat.waktu, 1, 4)).distinct().all()
            years = [r[0] for r in results if r[0]]
            current_year = str(datetime.now().year)
            if current_year not in years:
                years.append(current_year)
            return sorted(years, reverse=True)
        except Exception:
            return [str(datetime.now().year)]

    def _build_orm_query(self, status=None, q=None, period=None, month=None, year=None):
        """Query builder fleksibel untuk filtering status, pencarian q, dan rentang tanggal."""
        query = Riwayat.query

        if status and status != 'all':
            query = query.filter(Riwayat.status == status)

        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    Riwayat.nama_file.ilike(search_term),
                    Riwayat.folder_path.ilike(search_term),
                    Riwayat.keterangan.ilike(search_term),
                    Riwayat.author.ilike(search_term),
                    Riwayat.subject.ilike(search_term),
                    Riwayat.keywords.ilike(search_term)
                )
            )

        if period and period != 'all':
            now = datetime.now()
            if period == 'today':
                date_prefix = now.strftime('%Y-%m-%d')
                query = query.filter(Riwayat.waktu.like(f"{date_prefix}%"))
            elif period in ('week', '7d'):
                from datetime import timedelta
                week_ago = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
                query = query.filter(Riwayat.waktu >= week_ago)
            elif period in ('month_specific', 'month') and month and year:
                date_prefix = f"{year}-{month.zfill(2)}"
                query = query.filter(Riwayat.waktu.like(f"{date_prefix}%"))
            elif period == '30d':
                from datetime import timedelta
                month_ago = (now - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
                query = query.filter(Riwayat.waktu >= month_ago)
            elif period in ('year_specific', 'year') and year:
                date_prefix = f"{year}-"
                query = query.filter(Riwayat.waktu.like(f"{date_prefix}%"))

        return query

    def ambil_riwayat_db(self, batas=50, status=None, q=None, period=None, month=None, year=None, order_by_updated=False):
        """Mengambil data riwayat dokumen dalam bentuk list of dictionary."""
        try:
            query = self._build_orm_query(status, q, period, month, year)
            if order_by_updated:
                results = query.order_by(desc(func.coalesce(Riwayat.updated_waktu, Riwayat.waktu))).limit(batas).all()
            else:
                results = query.order_by(desc(Riwayat.waktu)).limit(batas).all()
            return [r.to_dict() for r in results]
        except Exception as e:
            print(f"Error ambil_riwayat_db: {e}")
            return []

    def ambil_dokumen(self, limit, offset, status=None, q=None, period=None, month=None, year=None):
        """Mengambil data riwayat dengan pagination (limit & offset)."""
        try:
            query = self._build_orm_query(status, q, period, month, year)
            total = query.count()
            results = query.order_by(desc(Riwayat.waktu)).limit(limit).offset(offset).all()
            return [r.to_dict() for r in results], total
        except Exception as e:
            print(f"Error ambil_dokumen: {e}")
            return [], 0

    def update_folder(self, input_baru, output_baru):
        """Memperbarui path folder input dan output pada runtime instance."""
        self.input_dir = input_baru
        self.output_dir = output_baru
        self.invalidate_stats_cache()

    def invalidate_stats_cache(self):
        """Mereset cache statistik agar kalkulasi berikutnya membaca data terbaru."""
        self._stats_cache = None
        self._stats_cache_time = 0

    # --------------------------------------------------------------------------
    # DELEGASI KE SERVICE LAYER (SYSTEM_SERVICE & ANALYTICS_SERVICE)
    # --------------------------------------------------------------------------
    def ambil_statistik(self, force_refresh=False):
        return hitung_statistik_dashboard(self, db, Riwayat, force_refresh)

    def ambil_data_analitik(self, period=None, month=None, year=None):
        return service_ambil_data_analitik(self, period, month, year)

    def ambil_data_monitoring(self):
        return service_ambil_data_monitoring(self, Riwayat)

    def format_size(self, byte):
        return format_size(byte)

    def hitung_ukuran_folder(self, direktori):
        return hitung_ukuran_folder(direktori)

    def hitung_total_halaman_folder(self, direktori):
        return hitung_total_halaman_folder(direktori, self._page_count_cache)

    def baca_log_terbaru(self, batas=20):
        return baca_log_terbaru(self.log_path, batas)