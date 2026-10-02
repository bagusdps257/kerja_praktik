import io
import math
import os
import subprocess
import tempfile

from flask import Blueprint, render_template, jsonify, redirect, url_for, request, send_file, flash
from flask_login import login_required, current_user

import core_engine
from core_engine import ambil_progress_ocr


from models.model_provider import db_model

from services.storage_service import (
    hitung_total_ukuran_folder,
    cek_kapasitas_penyimpanan
)
from services.settings_service import load_settings, save_settings, get_tesseract_version, resolve_tesseract_cmd
from config.settings import DB_PATH, SQLALCHEMY_DATABASE_URI
import shutil


dashboard_bp = Blueprint("dashboard", __name__)

def ambil_data_dashboard():

    stats = db_model.ambil_statistik()
    logs = db_model.baca_log_terbaru()
    riwayat = db_model.ambil_riwayat_db()

    # Tambahan baru (50 files limit)
    recent_files = db_model.ambil_riwayat_db(batas=50, order_by_updated=True)

    total_ukuran = hitung_total_ukuran_folder(db_model.output_dir)
    info_penyimpanan = cek_kapasitas_penyimpanan(db_model.output_dir)

    return {
        "stats": stats,
        "logs": logs,
        "riwayat": riwayat,
        "recent_files": recent_files,
        "total_ukuran": total_ukuran,
        "penyimpanan": info_penyimpanan
    }

@dashboard_bp.route("/")
@login_required
def index():

    data = ambil_data_dashboard()

    return render_template("index.html", **data)

MONTH_NAMES = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
    7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
}

def get_period_label(period, month='', year=''):
    if period == 'today':
        return 'Today'
    elif period == '7d':
        return 'Last 7 Days'
    elif period == '30d':
        return 'Last 30 Days'
    elif period == 'month':
        from datetime import datetime
        m_int = int(month) if month and str(month).isdigit() else datetime.now().month
        y_str = str(year) if year else str(datetime.now().year)
        m_name = MONTH_NAMES.get(m_int, 'Current Month')
        return f"{m_name} {y_str}"
    elif period == 'year':
        from datetime import datetime
        y_str = str(year) if year else str(datetime.now().year)
        return f"Year {y_str}"
    elif month and year:
        m_int = int(month) if str(month).isdigit() else 1
        m_name = MONTH_NAMES.get(m_int, '')
        return f"{m_name} {year}"
    elif year:
        return f"Year {year}"
    return 'All Time'

@dashboard_bp.route('/documents')
@login_required
def documents():
    status = request.args.get('status', '')
    q = request.args.get('q', '')
    period = request.args.get('period', '') or request.args.get('range', '')
    month = request.args.get('month', '')
    year = request.args.get('year', '')
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = int(request.args.get('per_page', 50))
        if per_page not in (10, 25, 50, 100, 250):
            per_page = 50
    except (ValueError, TypeError):
        per_page = 50

    offset = (page - 1) * per_page

    stats = db_model.ambil_statistik()
    available_years = db_model.ambil_tahun_tersedia()

    riwayat, total_data = db_model.ambil_dokumen(
        limit=per_page,
        offset=offset,
        status=status if status else None,
        q=q if q else None,
        period=period if period else None,
        month=month if month else None,
        year=year if year else None
    )
    total_pages = math.ceil(total_data / per_page) if total_data > 0 else 1

    current_period_label = get_period_label(period, month, year)

    return render_template(
        'documents.html',
        stats=stats,
        riwayat=riwayat,
        current_status=status,
        current_q=q,
        current_period=period,
        current_month=month,
        current_year=year,
        current_period_label=current_period_label,
        available_years=available_years,
        page=page,
        total_pages=total_pages,
        total_data=total_data,
        per_page=per_page
    )

@dashboard_bp.route('/monitoring')
@login_required
def monitoring():
    data = db_model.ambil_data_monitoring()
    return render_template('monitoring.html', **data)

@dashboard_bp.route('/api/monitoring')
@login_required
def api_monitoring():
    data = db_model.ambil_data_monitoring()
    return jsonify(data)

@dashboard_bp.route('/api/queue/pause', methods=['POST'])
@login_required
def pause_queue():
    from services.progress_service import set_queue_paused
    set_queue_paused(True)
    return jsonify({'success': True, 'queue_paused': True})

@dashboard_bp.route('/api/queue/resume', methods=['POST'])
@login_required
def resume_queue():
    from services.progress_service import set_queue_paused
    set_queue_paused(False)
    return jsonify({'success': True, 'queue_paused': False})

@dashboard_bp.route("/analytics")
@login_required
def analytics():
    period = request.args.get('period', '') or request.args.get('range', '')
    month = request.args.get('month', '')
    year = request.args.get('year', '')

    analytics_data = db_model.ambil_data_analitik(
        period=period if period else None,
        month=month if month else None,
        year=year if year else None
    )
    available_years = db_model.ambil_tahun_tersedia()
    current_period_label = get_period_label(period, month, year)

    return render_template(
        "analytics.html",
        analytics=analytics_data,
        current_period=period,
        current_month=month,
        current_year=year,
        current_period_label=current_period_label,
        available_years=available_years
    )

@dashboard_bp.route('/settings')
@login_required
def settings():
    stats = db_model.ambil_statistik()
    user_settings = load_settings()
    tesseract_ver = get_tesseract_version(user_settings.get('tesseract_path', 'tesseract'))
    available_years = db_model.ambil_tahun_tersedia()

    return render_template(
        'settings.html',
        stats=stats,
        settings=user_settings,
        tesseract_version=tesseract_ver,
        available_years=available_years
    )

@dashboard_bp.route('/settings/save', methods=['POST'])
@login_required
def save_settings_route():
    try:
        def parse_int_safe(val, default):
            try:
                return int(val)
            except (ValueError, TypeError):
                return default

        new_data = {
            'tesseract_path': request.form.get('tesseract_path', '').strip(),
            'ocr_language': request.form.get('ocr_language', 'ind+eng').strip(),
            'dpi_render': parse_int_safe(request.form.get('dpi_render'), 200),
            'max_retry': parse_int_safe(request.form.get('max_retry'), 5),
            'generate_searchable_pdf': True,
            'input_dir': request.form.get('input_dir', '').strip(),
            'output_dir': request.form.get('output_dir', '').strip(),
            'storage_warning': parse_int_safe(request.form.get('storage_warning'), 85),
            'auto_cleanup': 'auto_cleanup' in request.form,
            'refresh_interval': parse_int_safe(request.form.get('refresh_interval'), 1),
            'enable_auto_refresh': 'enable_auto_refresh' in request.form,
            'remember_scroll': 'remember_scroll' in request.form,
            'pause_refresh': 'pause_refresh' in request.form,
            'notify_success': 'notify_success' in request.form,
            'notify_failed': 'notify_failed' in request.form,
            'sound_notify': 'sound_notify' in request.form
        }

        saved_data = save_settings(new_data)
        
        # Sync runtime variables
        if saved_data.get('input_dir') and saved_data.get('output_dir'):
            db_model.update_folder(saved_data['input_dir'], saved_data['output_dir'])

        if saved_data.get('tesseract_path'):
            import pytesseract
            resolved_tess = resolve_tesseract_cmd(saved_data['tesseract_path'])
            pytesseract.pytesseract.tesseract_cmd = resolved_tess

        core_engine.catat_log("✅ Settings berhasil diperbarui.")
    except Exception as e:
        core_engine.catat_log(f"❌ Gagal menyimpan settings: {str(e)}")

    return redirect(url_for('dashboard.settings'))

@dashboard_bp.route('/backup_db')
@login_required
def backup_db():
    from datetime import datetime
    backup_name = f"ocr_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    # 1. Coba menggunakan mysqldump jika tersedia di sistem
    try:
        import re as _re
        _match = _re.match(r'mysql\+pymysql://([^:]+):([^@]*)@([^/]+)/(.+)', SQLALCHEMY_DATABASE_URI)
        if _match:
            _db_user = _match.group(1)
            _db_pass = _match.group(2)
            _db_host = _match.group(3)
            _db_name = _match.group(4)
        else:
            _db_user, _db_pass, _db_host, _db_name = "root", "", "localhost", "ocr_database"

        # Deteksi lokasi mysqldump (PATH sistem atau path umum XAMPP/Laragon/MySQL)
        mysqldump_bin = shutil.which("mysqldump")
        if not mysqldump_bin and os.name == 'nt':
            for candidate in [
                r"C:\xampp\mysql\bin\mysqldump.exe",
                r"C:\laragon\bin\mysql\mysql-8.0.30-winx64\bin\mysqldump.exe",
                r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
                r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqldump.exe"
            ]:
                if os.path.exists(candidate):
                    mysqldump_bin = candidate
                    break

        if mysqldump_bin:
            cmd = [mysqldump_bin, "-u", _db_user, "-h", _db_host]
            if _db_pass:
                cmd.append(f"-p{_db_pass}")
            cmd.append(_db_name)

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            if result.stdout:
                core_engine.catat_log("✅ Backup database berhasil via mysqldump.")
                return send_file(io.BytesIO(result.stdout), as_attachment=True, download_name=backup_name, mimetype='application/sql')
    except Exception as mysqldump_err:
        core_engine.catat_log(f"⚠️ mysqldump tidak tersedia/gagal: {mysqldump_err}. Menggunakan fallback Python SQL exporter.")

    # 2. Fallback Portable: Ekspor seluruh tabel ke format SQL standar via SQLAlchemy
    try:
        from models.extensions import db
        from models.dashboard_model import Riwayat
        from models.user_model import User

        sql_lines = [
            "-- ========================================================",
            f"-- OCR Project Database Backup (.SQL Dump)",
            f"-- Generated on : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "-- ========================================================\n",
            "SET FOREIGN_KEY_CHECKS=0;\n"
        ]

        # Backup Tabel `users`
        sql_lines.append("DROP TABLE IF EXISTS `users`;")
        sql_lines.append("""CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` varchar(50) NOT NULL,
  `last_login` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n""")

        users = db.session.query(User).all()
        if users:
            sql_lines.append("INSERT INTO `users` (`id`, `username`, `password_hash`, `created_at`, `last_login`) VALUES")
            u_rows = []
            for u in users:
                u_name = str(u.username or '').replace("'", "''")
                p_hash = str(u.password_hash or '').replace("'", "''")
                c_at = str(u.created_at or '').replace("'", "''")
                if u.last_login:
                    cleaned_ll = str(u.last_login).replace("'", "''")
                    l_log = f"'{cleaned_ll}'"
                else:
                    l_log = "NULL"
                u_rows.append(f"({u.id}, '{u_name}', '{p_hash}', '{c_at}', {l_log})")
            sql_lines.append(",\n".join(u_rows) + ";\n")

        # Backup Tabel `riwayat`
        sql_lines.append("DROP TABLE IF EXISTS `riwayat`;")
        sql_lines.append("""CREATE TABLE `riwayat` (
  `id` int NOT NULL AUTO_INCREMENT,
  `document_key` varchar(255) DEFAULT NULL,
  `folder_path` varchar(500) DEFAULT NULL,
  `nama_file` varchar(255) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `waktu` varchar(50) DEFAULT NULL,
  `updated_waktu` varchar(50) DEFAULT NULL,
  `keterangan` text,
  `file_size` varchar(50) DEFAULT NULL,
  `author` varchar(100) DEFAULT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `keywords` varchar(500) DEFAULT NULL,
  `page_count` varchar(50) DEFAULT NULL,
  `creation_date` varchar(50) DEFAULT NULL,
  `processing_time` float DEFAULT '0',
  `retry_count` int DEFAULT '0',
  `relative_path` varchar(500) DEFAULT NULL,
  `file_hash` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n""")

        riwayats = db.session.query(Riwayat).all()
        if riwayats:
            sql_lines.append("INSERT INTO `riwayat` (`id`, `document_key`, `folder_path`, `nama_file`, `status`, `waktu`, `updated_waktu`, `keterangan`, `file_size`, `author`, `subject`, `keywords`, `page_count`, `creation_date`, `processing_time`, `retry_count`, `relative_path`, `file_hash`) VALUES")
            r_rows = []
            for r in riwayats:
                def q_val(val):
                    if val is None:
                        return "NULL"
                    s = str(val).replace("\\", "\\\\").replace("'", "''")
                    return f"'{s}'"

                p_time = float(r.processing_time or 0.0)
                r_cnt = int(r.retry_count or 0)
                r_rows.append(f"({r.id}, {q_val(r.document_key)}, {q_val(r.folder_path)}, {q_val(r.nama_file)}, {q_val(r.status)}, {q_val(r.waktu)}, {q_val(r.updated_waktu)}, {q_val(r.keterangan)}, {q_val(r.file_size)}, {q_val(r.author)}, {q_val(r.subject)}, {q_val(r.keywords)}, {q_val(r.page_count)}, {q_val(r.creation_date)}, {p_time}, {r_cnt}, {q_val(r.relative_path)}, {q_val(r.file_hash)})")
            sql_lines.append(",\n".join(r_rows) + ";\n")

        sql_lines.append("SET FOREIGN_KEY_CHECKS=1;\n")
        sql_bytes = "\n".join(sql_lines).encode("utf-8")

        core_engine.catat_log("✅ Backup database berhasil via SQLAlchemy exporter.")
        return send_file(io.BytesIO(sql_bytes), as_attachment=True, download_name=backup_name, mimetype='application/sql')

    except Exception as e:
        core_engine.catat_log(f"❌ Backup gagal total: {str(e)}")
        flash(f"Gagal melakukan backup database: {str(e)}", "danger")
        return redirect(request.referrer or url_for("dashboard.documents"))


@dashboard_bp.route("/api/status")
@login_required
def api_status():
    """Return JSON status containing statistics, recent logs, recent files, total storage, and notification preferences."""
    stats = db_model.ambil_statistik()
    logs = db_model.baca_log_terbaru()
    recent_files = db_model.ambil_riwayat_db(20)
    total_ukuran = hitung_total_ukuran_folder(db_model.output_dir)
    user_settings = load_settings()

    return jsonify({
        "stats": stats,
        "logs": logs,
        "recent_files": recent_files,
        "total_ukuran": total_ukuran,
        "notification_prefs": {
            "notify_success": user_settings.get("notify_success", True),
            "notify_failed": user_settings.get("notify_failed", True),
            "sound_notify": user_settings.get("sound_notify", False)
        }
    })

@dashboard_bp.route("/progress")
@login_required
def progress():

    return jsonify(ambil_progress_ocr())

from routes.auth import operator_required

@dashboard_bp.route("/reset_db", methods=["POST"])
@operator_required
def reset_db():
    password = request.form.get("password", "").strip()
    if not password or not current_user.check_password(password):
        flash("Password salah. Tindakan hapus riwayat dibatalkan demi keamanan.", "danger")
        return redirect(request.referrer or url_for("dashboard.documents"))

    try:
        from models.dashboard_model import Riwayat
        from models.extensions import db
        from datetime import datetime
        import json

        # Buat snapshot cadangan otomatis sebelum penghapusan dilakukan
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "auto_backups")
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = os.path.join(backup_dir, f"snapshot_before_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        riwayats = db.session.query(Riwayat).all()
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in riwayats], f, indent=2, ensure_ascii=False)

        deleted_count = db.session.query(Riwayat).delete()
        db.session.commit()
        db_model.invalidate_stats_cache()
        
        core_engine.catat_log(f"✅ Riwayat database berhasil dibersihkan ({deleted_count} data dihapus). Snapshot: {os.path.basename(backup_file)}")
        flash(f"Riwayat berhasil dibersihkan ({deleted_count} data). Cadangan otomatis tersimpan.", "success")
    except Exception as e:
        db.session.rollback()
        core_engine.catat_log(f"❌ Gagal reset database: {str(e)}")
        flash(f"Gagal mereset database: {str(e)}", "danger")

    return redirect(request.referrer or url_for("dashboard.documents"))