import os
import time
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from services.system_service import (
    format_size,
    hitung_ukuran_folder,
    get_hardware_metrics,
    baca_log_terbaru,
    SUPPORTED_EXTENSIONS,
    IMAGE_EXTENSIONS
)
from services.progress_service import ambil_progress, is_queue_paused


def _safe_float(val):
    try:
        return float(val or 0)
    except (ValueError, TypeError):
        return 0.0


def hitung_statistik_dashboard(db_model, db, Riwayat, force_refresh=False):
    """
    Computes real-time dashboard stats: total input, total output, pending, failed,
    page counts, sizes, disk free space, and last processed activity.
    Uses caching (1.5s TTL) to prevent UI flickering during rapid polling.
    """
    from services.settings_service import load_settings

    # Refresh dynamic settings paths
    settings = load_settings()
    db_model.input_dir = settings.get("input_dir", db_model.input_dir)
    db_model.output_dir = settings.get("output_dir", db_model.output_dir)

    now = time.time()
    if (
        not force_refresh
        and hasattr(db_model, '_stats_cache')
        and db_model._stats_cache
        and hasattr(db_model, '_stats_cache_time')
        and (now - db_model._stats_cache_time < 1.5)
    ):
        return db_model._stats_cache

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
        info = {'status': (st or '').upper(), 'page_count': pc}
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
    total_halaman = 0
    active_output_size_bytes = 0
    active_output_pages = 0
    input_size_bytes = 0
    total_input_pages = 0

    try:
        import fitz
    except ImportError:
        fitz = None

    if os.path.exists(db_model.input_dir):
        for root, _, files in os.walk(db_model.input_dir):
            folder_rel = os.path.relpath(root, db_model.input_dir)
            for file_name in files:
                _fp = os.path.join(root, file_name)
                try:
                    if os.path.isfile(_fp) and not os.path.islink(_fp):
                        input_size_bytes += os.path.getsize(_fp)
                except OSError:
                    pass

                if file_name.lower().endswith(SUPPORTED_EXTENSIONS):
                    total_input += 1
                    jalur_awal = os.path.join(root, file_name)
                    rel_path = os.path.relpath(jalur_awal, db_model.input_dir).replace('\\', '/')

                    if file_name.lower().endswith(IMAGE_EXTENSIONS):
                        out_file_name = os.path.splitext(file_name)[0] + ".pdf"
                    else:
                        out_file_name = file_name

                    if folder_rel and folder_rel != ".":
                        target_output_file = os.path.join(db_model.output_dir, folder_rel, out_file_name)
                    else:
                        target_output_file = os.path.join(db_model.output_dir, out_file_name)

                    output_exists = os.path.isfile(target_output_file)
                    if output_exists:
                        try:
                            if os.path.getmtime(jalur_awal) > os.path.getmtime(target_output_file):
                                output_exists = False
                        except OSError:
                            pass

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
                    is_failed = db_status in ('GAGAL', 'FAILED')

                    if file_name.lower().endswith(IMAGE_EXTENSIONS):
                        total_input_pages += 1
                    elif file_name.lower().endswith('.pdf'):
                        _ipc = 0
                        if db_info and db_info.get('page_count') is not None:
                            _ipc_str = str(db_info['page_count']).strip()
                            if _ipc_str not in ('-', '', 'None'):
                                try:
                                    _ipc = int(_ipc_str)
                                except (ValueError, TypeError):
                                    _ipc = 0

                        if _ipc <= 0 and fitz is not None:
                            try:
                                mtime = os.path.getmtime(jalur_awal)
                                cached = db_model._page_count_cache.get(jalur_awal)
                                if cached and cached[0] == mtime:
                                    _ipc = cached[1]
                                else:
                                    doc = fitz.open(jalur_awal)
                                    _ipc = doc.page_count
                                    doc.close()
                                    db_model._page_count_cache[jalur_awal] = (mtime, _ipc)
                            except Exception:
                                _ipc = 1
                        elif _ipc <= 0:
                            _ipc = 1

                        total_input_pages += max(1, _ipc)

                    if output_exists:
                        total_output += 1
                        file_pages = 0
                        if db_info and db_info.get('page_count') is not None:
                            pc_str = str(db_info['page_count']).strip()
                            if pc_str not in ('-', '', 'None'):
                                try:
                                    file_pages = int(pc_str)
                                except (ValueError, TypeError):
                                    file_pages = 0

                        if file_pages <= 0 and fitz is not None and target_output_file.lower().endswith('.pdf'):
                            try:
                                mtime = os.path.getmtime(target_output_file)
                                cached = db_model._page_count_cache.get(target_output_file)
                                if cached and cached[0] == mtime:
                                    file_pages = cached[1]
                                else:
                                    doc = fitz.open(target_output_file)
                                    file_pages = doc.page_count
                                    doc.close()
                                    db_model._page_count_cache[target_output_file] = (mtime, file_pages)
                            except Exception:
                                file_pages = 1

                        if file_pages <= 0:
                            file_pages = 1

                        total_halaman += file_pages
                        active_output_size_bytes += os.path.getsize(target_output_file)
                        active_output_pages += file_pages
                    elif is_failed:
                        total_gagal += 1

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

    pending = max(0, total_input - total_output - total_gagal)

    hw = get_hardware_metrics(db_model.output_dir)

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
        "input_dir": db_model.input_dir,
        "output_dir": db_model.output_dir,
        "input_size": format_size(input_size_bytes),
        "input_size_bytes": input_size_bytes,
        "output_size": format_size(active_output_size_bytes),
        "output_size_bytes": active_output_size_bytes,
        "free_bytes": hw["disk_free_bytes"],
        "free_space": hw["disk_free_formatted"],
        "used_percent": hw["disk_used_percent"],
        "total_input_pages": total_input_pages,
        "total_output_pages": active_output_pages,
        "total_dokumen": db_total,
        "berhasil": db_sukses,
        "gagal": db_gagal,
        "terakhir_aktif": last_activity
    }

    db_model._stats_cache = result
    db_model._stats_cache_time = now
    return result


def ambil_data_analitik(db_model, period=None, month=None, year=None):
    """
    Computes data for the Analytics Page (Trends, Success Rates, User Volumes, Storage).
    """
    try:
        query = db_model._build_orm_query(status=None, q=None, period=period, month=month, year=year)
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

        hw = get_hardware_metrics(db_model.output_dir)

        out_size = hitung_ukuran_folder(db_model.output_dir)
        out_formatted = format_size(out_size)

        log_dir = (os.path.dirname(db_model.log_path) or ".") if db_model.log_path else None
        log_size = hitung_ukuran_folder(log_dir)
        log_formatted = format_size(log_size)

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
            "storage_used_percent": hw["disk_used_percent"],
            "storage_total_gb": hw["disk_total_gb"],
            "storage_used_gb": hw["disk_used_gb"],
            "storage_free_formatted": hw["disk_free_formatted"],
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


def ambil_data_monitoring(db_model, Riwayat):
    """
    Computes data for the Real-time Monitoring Page (Hardware usage, queue tasks, live logs).
    """
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

        hw = get_hardware_metrics(db_model.output_dir)

        # Processing Speed in docs/hr in the last 1 hour
        one_hour_ago = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        speed_count = Riwayat.query.filter(
            Riwayat.status == 'SUKSES',
            func.coalesce(Riwayat.updated_waktu, Riwayat.waktu) >= one_hour_ago
        ).count()

        live_logs = baca_log_terbaru(db_model.log_path, 30)

        queue_tasks = []
        stats = db_model.ambil_statistik()
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

        return {
            'engine_status': engine_status,
            'engine_health': engine_health,
            'processing_speed': speed_count,
            'cpu_usage': hw["cpu_usage"],
            'memory_usage': hw["memory_usage"],
            'live_logs': live_logs,
            'queue_tasks': queue_tasks,
            'active_task_count': len(queue_tasks),
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
