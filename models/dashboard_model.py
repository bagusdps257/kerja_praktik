import os
import time
import re
import math
import shutil
from datetime import datetime

from .extensions import db
from sqlalchemy import func, or_, desc, asc

from config.settings import (
    INPUT_DEFAULT,
    OUTPUT_DEFAULT,
    LOG_PATH
)


from services.settings_service import load_settings

SUPPORTED_EXTENSIONS = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp')
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp')

def _safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


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
    processing_time = db.Column(db.Float, default=0.0)
    retry_count = db.Column(db.Integer, default=0)
    relative_path = db.Column(db.String(500))
    file_hash = db.Column(db.String(255))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class OCRDashboardModel:
    SUPPORTED_EXTENSIONS = SUPPORTED_EXTENSIONS
    IMAGE_EXTENSIONS = IMAGE_EXTENSIONS

    def __init__(self):
        settings = load_settings()
        self.input_dir = settings.get("input_dir", INPUT_DEFAULT)
        self.output_dir = settings.get("output_dir", OUTPUT_DEFAULT)
        self.log_path = LOG_PATH
        self.init_db()

    def init_db(self):
        pass # Schema is managed globally via db.create_all()

    def catat_ke_db(
        self,
        document_key,
        folder_path="",
        nama_file="",
        status="SUKSES",
        keterangan="",
        file_size="-",
        author="-",
        page_count="-",
        creation_date="-",
        processing_time=0.0,
        retry_count=0,
        relative_path="",
        file_hash=""
    ):
        import time
        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                doc_key_query = document_key if document_key else ""
                if not doc_key_query and nama_file:
                    doc_key_query = nama_file

                existing = None
                if doc_key_query:
                    # Primary: match by document_key (unique relative path)
                    existing = Riwayat.query.filter(
                        Riwayat.document_key == doc_key_query
                    ).first()
                    # Fallback: match by nama_file ONLY if doc_key has no path separator
                    # (i.e., it's just a filename, not a relative path)
                    if not existing and '/' not in doc_key_query and '\\' not in doc_key_query:
                        existing = Riwayat.query.filter(
                            Riwayat.nama_file == doc_key_query
                        ).first()

                if existing:
                    existing.status = status
                    if keterangan: existing.keterangan = keterangan
                    if file_size: existing.file_size = file_size
                    if author: existing.author = author
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
                        keterangan=keterangan or "",
                        file_size=file_size or "",
                        author=author or "",
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
                    print(f"Database error in catat_ke_db: {e}. Retrying in {sleep_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(sleep_time)
                else:
                    print(f"Fatal database error in catat_ke_db after {max_retries} attempts: {e}")
                    return False

    def tambah_riwayat(
        self,
        document_key,
        folder_path="",
        nama_file="",
        status="SUKSES",
        keterangan="",
        file_size="-",
        author="-",
        page_count="-",
        creation_date="-",
        processing_time=0.0,
        retry_count=0
    ):
        return self.catat_ke_db(
            document_key=document_key,
            folder_path=folder_path,
            nama_file=nama_file,
            status=status,
            keterangan=keterangan,
            file_size=file_size,
            author=author,
            page_count=page_count,
            creation_date=creation_date,
            processing_time=processing_time,
            retry_count=retry_count
        )

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
                    Riwayat.keterangan.ilike(search_term),
                    Riwayat.author.ilike(search_term)
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


    def ambil_riwayat_db(self, batas=50, status=None, q=None, period=None, month=None, year=None):
        try:
            query = self._build_orm_query(status, q, period, month, year)
            results = query.order_by(desc(Riwayat.waktu)).limit(batas).all()
            return [r.to_dict() for r in results]
        except Exception as e:
            print(f"Error ambil_riwayat_db: {e}")
            return []

    def ambil_dokumen(self, limit, offset, status=None, q=None, period=None, month=None, year=None):
        try:
            query = self._build_orm_query(status, q, period, month, year)
            total = query.count()
            
            results = query.order_by(desc(Riwayat.waktu)).limit(limit).offset(offset).all()
            documents = [r.to_dict() for r in results]
            
            return documents, total
        except Exception as e:
            print(f"Error ambil_dokumen: {e}")
            return [], 0

    def update_folder(self, input_baru, output_baru):

        self.input_dir = input_baru
        self.output_dir = output_baru

    def hitung_pdf(self, direktori):

        jumlah = 0

        if os.path.exists(direktori):

            for root, dirs, files in os.walk(direktori):

                for file in files:

                    if file.lower().endswith(SUPPORTED_EXTENSIONS):
                        jumlah += 1

        return jumlah

    def hitung_ukuran_folder(self, direktori):
        """Calculate total size of all files in a directory (bytes)."""
        total = 0
        if not direktori:
            return 0
        try:
            if os.path.exists(direktori):
                for root, _, files in os.walk(direktori):
                    for file in files:
                        path = os.path.join(root, file)
                        if os.path.isfile(path) and not os.path.islink(path):
                            try:
                                total += os.path.getsize(path)
                            except OSError:
                                pass
        except Exception:
            pass
        return total

    def format_size(self, byte):
        """Format bytes into human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if byte < 1024:
                return f'{byte:.2f} {unit}'
            byte /= 1024
        return f'{byte:.2f} PB'

    _stats_cache = None
    _stats_cache_time = 0
    _page_count_cache = {}

    def hitung_total_halaman_folder(self, direktori):
        """Count total PDF and image pages in a folder using PyMuPDF with mtime caching."""
        total_pages = 0
        if os.path.exists(direktori):
            try:
                import fitz
            except ImportError:
                fitz = None

            for root, _, files in os.walk(direktori):
                for file in files:
                    file_lower = file.lower()
                    if file_lower.endswith('.pdf') and fitz is not None:
                        path = os.path.join(root, file)
                        try:
                            mtime = os.path.getmtime(path)
                            cached = self._page_count_cache.get(path)
                            if cached and cached[0] == mtime:
                                total_pages += cached[1]
                            else:
                                doc = fitz.open(path)
                                pc = doc.page_count
                                doc.close()
                                self._page_count_cache[path] = (mtime, pc)
                                total_pages += pc
                        except Exception:
                            pass
                    elif file_lower.endswith(IMAGE_EXTENSIONS):
                        total_pages += 1
        return total_pages

    def invalidate_stats_cache(self):
        self._stats_cache = None
        self._stats_cache_time = 0

    def ambil_statistik(self, force_refresh=False):
        import time
        now = time.time()
        if not force_refresh and hasattr(self, '_stats_cache') and self._stats_cache and hasattr(self, '_stats_cache_time') and (now - self._stats_cache_time < 1.5):
            return self._stats_cache

        try:
            db_rows = db.session.query(
                Riwayat.document_key,
                Riwayat.nama_file,
                Riwayat.relative_path,
                Riwayat.status,
                Riwayat.page_count
            ).order_by(desc(Riwayat.waktu), desc(Riwayat.id)).all()
        except Exception:
            db_rows = []

        db_status_map = {}
        for doc_key, nama, rel_p, st, pc in db_rows:
            info = {
                'status': (st or '').upper(),
                'page_count': pc
            }
            # Index by all available identifiers for robust matching
            keys_to_add = set()
            if doc_key:
                keys_to_add.add(str(doc_key).replace('\\', '/').lower())
            if nama:
                if not doc_key or ('/' not in str(doc_key).replace('\\', '/')):
                    keys_to_add.add(str(nama).replace('\\', '/').lower())
            if rel_p:
                keys_to_add.add(str(rel_p).replace('\\', '/').lower())
            for key_norm in keys_to_add:
                if key_norm not in db_status_map:
                    db_status_map[key_norm] = info

        total_input = 0
        total_output = 0
        total_gagal = 0
        pending = 0
        total_halaman = 0
        active_output_size_bytes = 0
        active_output_pages = 0

        try:
            import fitz
        except ImportError:
            fitz = None

        import os
        import shutil

        output_dir_has_files = os.path.exists(self.output_dir) and (self.hitung_ukuran_folder(self.output_dir) > 0)

        if os.path.exists(self.input_dir):
            for root, _, files in os.walk(self.input_dir):
                folder_rel = os.path.relpath(root, self.input_dir)
                for file_name in files:
                    if file_name.lower().endswith(SUPPORTED_EXTENSIONS):
                        total_input += 1
                        jalur_awal = os.path.join(root, file_name)
                        rel_path = os.path.relpath(jalur_awal, self.input_dir).replace('\\', '/')

                        if file_name.lower().endswith(IMAGE_EXTENSIONS):
                            out_file_name = os.path.splitext(file_name)[0] + ".pdf"
                        else:
                            out_file_name = file_name

                        if folder_rel and folder_rel != ".":
                            target_output_file = os.path.join(self.output_dir, folder_rel, out_file_name)
                        else:
                            target_output_file = os.path.join(self.output_dir, out_file_name)

                        output_exists = os.path.isfile(target_output_file)

                        candidate_keys = [rel_path.lower()]
                        if not folder_rel or folder_rel == ".":
                            candidate_keys.append(file_name.lower())

                        if file_name.lower().endswith(IMAGE_EXTENSIONS):
                            rel_pdf = os.path.splitext(rel_path)[0] + ".pdf"
                            candidate_keys.append(rel_pdf.lower())
                            if not folder_rel or folder_rel == ".":
                                file_pdf = os.path.splitext(file_name)[0] + ".pdf"
                                candidate_keys.append(file_pdf.lower())

                        db_info = None
                        for ck in candidate_keys:
                            if ck in db_status_map:
                                db_info = db_status_map[ck]
                                break

                        db_status = db_info['status'] if db_info else ''
                        is_success = db_status in ('SUKSES', 'SUCCESS', 'SKIP')
                        is_failed = db_status in ('GAGAL', 'FAILED')

                        if output_exists or (is_success and output_dir_has_files):
                            total_output += 1
                            file_pages = 0
                            if db_info and db_info.get('page_count') is not None:
                                pc_str = str(db_info['page_count']).strip()
                                if pc_str not in ('-', '', 'None'):
                                    try:
                                        file_pages = int(pc_str)
                                    except (ValueError, TypeError):
                                        file_pages = 0

                            if file_pages <= 0:
                                if fitz is not None:
                                    path_to_check = None
                                    if output_exists and target_output_file.lower().endswith('.pdf'):
                                        path_to_check = target_output_file
                                    elif jalur_awal.lower().endswith('.pdf'):
                                        path_to_check = jalur_awal

                                    if path_to_check and os.path.exists(path_to_check):
                                        try:
                                            mtime = os.path.getmtime(path_to_check)
                                            cached = self._page_count_cache.get(path_to_check)
                                            if cached and cached[0] == mtime:
                                                file_pages = cached[1]
                                            else:
                                                doc = fitz.open(path_to_check)
                                                file_pages = doc.page_count
                                                doc.close()
                                                self._page_count_cache[path_to_check] = (mtime, file_pages)
                                        except Exception:
                                            file_pages = 0

                                if file_pages <= 0:
                                    file_pages = 1

                            total_halaman += file_pages

                            if output_exists:
                                active_output_size_bytes += os.path.getsize(target_output_file)
                                active_output_pages += file_pages
                            elif is_success and output_dir_has_files:
                                active_output_pages += file_pages

                        elif is_failed:
                            total_gagal += 1
                        else:
                            pending += 1

        # Reconcile: ensure filesystem counts match DB counts for consistency.
        try:
            db_total = db.session.query(Riwayat).count()
            db_sukses = db.session.query(Riwayat).filter(
                Riwayat.status.in_(['SUKSES', 'SUCCESS', 'SKIP'])
            ).count()
            db_gagal = db.session.query(Riwayat).filter(
                Riwayat.status.in_(['GAGAL', 'FAILED'])
            ).count()
        except Exception:
            db_total = 0
            db_sukses = 0
            db_gagal = 0

        # Check if OCR is currently running
        try:
            from services.progress_service import ambil_progress as _ambil_progress_sync
            _progress_state = _ambil_progress_sync()
            _ocr_running = _progress_state.get("status") == "RUNNING"
        except Exception:
            _ocr_running = False

        if _ocr_running:
            # When OCR is RUNNING, use ONLY DB-based counts.
            # DB records are created synchronously in main thread AFTER each file
            # is processed, in the same sequence as update_progress() calls.
            # This prevents stats cards from racing ahead of progress bar.
            total_output = db_sukses
            total_gagal = db_gagal
        else:
            # When IDLE/FINISHED, use the higher of filesystem vs DB counts
            # as safety net for any key matching misses
            if db_sukses > total_output:
                total_output = db_sukses
            if db_gagal > total_gagal:
                total_gagal = db_gagal

        # Recalculate pending to ensure counts add up
        pending = max(0, total_input - total_output - total_gagal)


        input_size_bytes = self.hitung_ukuran_folder(self.input_dir)

        try:
            disk = shutil.disk_usage(self.output_dir if os.path.exists(self.output_dir) else '.')
            free_bytes = disk.free
            used_percent = round((disk.used / disk.total) * 100, 1) if disk.total > 0 else 0
        except Exception:
            free_bytes = 0
            used_percent = 0

        total_input_pages = self.hitung_total_halaman_folder(self.input_dir)

        try:
            latest = Riwayat.query.order_by(desc(Riwayat.waktu)).first()
            last_activity = latest.waktu if latest else "Belum ada aktivitas"
        except Exception:
            last_activity = "-"

        result = {
            "total_input": total_input,
            "total_output": total_output,
            "pending": pending,
            "total_gagal": total_gagal,
            "total_halaman": total_halaman,
            "input_dir": self.input_dir,
            "output_dir": self.output_dir,
            "input_size": self.format_size(input_size_bytes),
            "input_size_bytes": input_size_bytes,
            "output_size": self.format_size(active_output_size_bytes),
            "output_size_bytes": active_output_size_bytes,
            "free_bytes": free_bytes,
            "free_space": self.format_size(free_bytes),
            "used_percent": used_percent,
            "total_input_pages": total_input_pages,
            "total_output_pages": active_output_pages,
            "total_dokumen": db_total,
            "berhasil": db_sukses,
            "gagal": db_gagal,
            "terakhir_aktif": last_activity
        }
        
        self._stats_cache = result
        self._stats_cache_time = now
        return result

    def baca_log_terbaru(self, batas=20):
        import os, re
        logs = []
        if self.log_path and os.path.exists(self.log_path):
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if any(x in line for x in ["Running on", "HTTP", "Press CTRL"]):
                        continue
                    clean_line = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
                    if clean_line:
                        logs.append(clean_line)
        logs = logs[-batas:]
        return logs

    def ambil_data_analitik(self, period=None, month=None, year=None):
        try:
            query = self._build_orm_query(status=None, q=None, period=period, month=month, year=year)
            results = query.all()
            
            total_files = len(results)
            success_files = sum(1 for r in results if r.status in ('SUKSES', 'SUCCESS', 'SKIP'))
            failed_files = sum(1 for r in results if r.status in ('GAGAL', 'FAILED'))
            skipped_files = sum(1 for r in results if r.status == 'SKIP')
            
            success_rate = round((success_files / total_files) * 100, 1) if total_files > 0 else 0.0
            
            processed_results = [r for r in results if r.status != 'SKIP']
            total_time = sum(_safe_float(getattr(r, 'processing_time', 0)) for r in processed_results)
            avg_processing_time = round(total_time / len(processed_results), 2) if len(processed_results) > 0 else 0.0
            
            daily_stats = {}
            user_stats = {}
            
            for r in results:
                date_str = r.waktu[:10] if r.waktu else ""
                if date_str:
                    if date_str not in daily_stats:
                        daily_stats[date_str] = {'success': 0, 'failed': 0, 'total': 0}
                    daily_stats[date_str]['total'] += 1
                    if r.status in ('SUKSES', 'SUCCESS', 'SKIP'):
                        daily_stats[date_str]['success'] += 1
                    elif r.status in ('GAGAL', 'FAILED'):
                        daily_stats[date_str]['failed'] += 1
                
                author = r.author or "Unknown"
                user_stats[author] = user_stats.get(author, 0) + 1
            
            sorted_dates = sorted(daily_stats.keys())
            daily_trend = [{'tanggal': d, 'success': daily_stats[d]['success'], 'failed': daily_stats[d]['failed']} for d in sorted_dates]
            daily_volume = [{'tanggal': d, 'jumlah': daily_stats[d]['total']} for d in sorted_dates]
            
            sorted_users = sorted([{'author': k, 'docs': v} for k, v in user_stats.items()], key=lambda x: x['docs'], reverse=True)[:5]
            
            import shutil
            import os
            
            try:
                disk_path = self.output_dir if (self.output_dir and os.path.exists(self.output_dir)) else '.'
                disk = shutil.disk_usage(disk_path)
                total_gb = round(disk.total / (1024**3), 1)
                used_gb = round(disk.used / (1024**3), 1)
                used_percent = round((disk.used / disk.total) * 100, 1) if disk.total > 0 else 0
                free_formatted = self.format_size(disk.free)
            except Exception:
                total_gb = 0
                used_gb = 0
                used_percent = 0
                free_formatted = "0 B"
                
            try:
                out_size = self.hitung_ukuran_folder(self.output_dir)
                out_formatted = self.format_size(out_size)
            except Exception:
                out_formatted = "0 B"
            
            try:
                log_dir = (os.path.dirname(self.log_path) or ".") if self.log_path else None
                log_size = self.hitung_ukuran_folder(log_dir)
                log_formatted = self.format_size(log_size)
            except Exception:
                log_formatted = "0 B"

            return {
                "total_files": total_files,
                "success_files": success_files,
                "failed_files": failed_files,
                "skipped_files": skipped_files,
                "success_rate": success_rate,
                "avg_processing_time": avg_processing_time,
                "daily_trend": daily_trend,
                "daily_volume": daily_volume,
                "most_active_users": sorted_users,
                "storage_used_percent": used_percent,
                "storage_total_gb": total_gb,
                "storage_used_gb": used_gb,
                "storage_free_formatted": free_formatted,
                "output_size_formatted": out_formatted,
                "log_size_formatted": log_formatted
            }
        except Exception as e:
            print(f"Error ambil_data_analitik: {e}")
            return {
                "total_files": 0, "success_files": 0, "failed_files": 0, "skipped_files": 0,
                "success_rate": 0, "avg_processing_time": 0,
                "daily_trend": [], "daily_volume": [], "most_active_users": [],
                "storage_used_percent": 0, "storage_total_gb": 0, "storage_used_gb": 0,
                "storage_free_formatted": "0 B", "output_size_formatted": "0 B", "log_size_formatted": "0 B"
            }

    def ambil_data_monitoring(self):
        from services.progress_service import ambil_progress, is_queue_paused
        import psutil
        from datetime import datetime, timedelta

        try:
            progress = ambil_progress()
            queue_paused = is_queue_paused()
            status_ocr = progress.get("status", "IDLE")

            if queue_paused:
                engine_status = "PAUSED"
                engine_health = "Paused"
            elif status_ocr == "RUNNING":
                engine_status = "ONLINE"
                engine_health = "Processing"
            else:
                engine_status = "IDLE"
                engine_health = "Optimal"

            try:
                # Add interval=0.1 to force an accurate reading window
                cpu_usage = int(psutil.cpu_percent(interval=0.1))
                memory_usage = int(psutil.virtual_memory().percent)
            except Exception:
                cpu_usage = 0
                memory_usage = 0

            # Processing Speed (docs/hr in last 1 hour)
            one_hour_ago = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            speed_count = Riwayat.query.filter(
                Riwayat.status == 'SUKSES',
                Riwayat.waktu >= one_hour_ago
            ).count()
            
            processing_speed = speed_count

            live_logs = self.baca_log_terbaru(30)

            queue_tasks = []
            stats = self.ambil_statistik()
            pending_count = stats.get("pending", 0)

            if status_ocr == "RUNNING":
                curr_file = progress.get("current_file", "-")
                selesai = progress.get("selesai", 0)
                total = progress.get("total", 0)
                persen = progress.get("persen", 0)

                queue_tasks.append({
                    'file_name': curr_file if curr_file != "-" else "Processing PDF Batch",
                    'worker': 'Worker Alpha',
                    'status': 'PROCESSING',
                    'current_page': selesai + 1 if (total > 0 and selesai < total) else max(1, selesai),
                    'total_pages': max(1, total),
                    'progress': persen
                })

                rem = max(0, total - selesai - 1)
                if rem > 0:
                    queue_tasks.append({
                        'file_name': f'Pending Batch ({rem} files)',
                        'worker': 'Pending Assignment',
                        'status': 'QUEUED',
                        'pending_files': rem
                    })
            else:
                if pending_count > 0:
                    queue_tasks.append({
                        'file_name': f'Pending Batch ({pending_count} files)',
                        'worker': 'Pending Assignment',
                        'status': 'QUEUED',
                        'pending_files': pending_count
                    })

            active_task_count = len(queue_tasks)

            return {
                'engine_status': engine_status,
                'engine_health': engine_health,
                'processing_speed': processing_speed,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'live_logs': live_logs,
                'queue_tasks': queue_tasks,
                'active_task_count': active_task_count,
                'queue_paused': queue_paused
            }
        except Exception as e:
            print(f"Error in ambil_data_monitoring: {e}")
            return {
                'engine_status': 'IDLE',
                'engine_health': 'Error',
                'processing_speed': 0,
                'cpu_usage': 0,
                'memory_usage': 0,
                'live_logs': [],
                'queue_tasks': [],
                'active_task_count': 0,
                'queue_paused': False
            }