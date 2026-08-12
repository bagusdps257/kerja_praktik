import io
from datetime import datetime
from flask import Blueprint, send_file, request
from flask_login import login_required
from models import OCRDashboardModel
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

export_bp = Blueprint("export", __name__)
db_model = OCRDashboardModel()

@export_bp.route("/export_excel")
@login_required
def export_excel():
    status = request.args.get('status', '')
    q = request.args.get('q', '')
    period = request.args.get('period', '') or request.args.get('range', '')
    month = request.args.get('month', '')
    year = request.args.get('year', '')

    riwayat = db_model.ambil_riwayat_db(
        batas=10000,
        status=status if status else None,
        q=q if q else None,
        period=period if period else None,
        month=month if month else None,
        year=year if year else None
    )

    wb = openpyxl.Workbook()
    
    # Sheet 1: Summary
    ws_summary = wb.active
    ws_summary.title = "Ringkasan"
    ws_summary.sheet_view.showGridLines = False
    
    # Define styles
    title_font = Font(name="Segoe UI", size=20, bold=True, color="1F4E78")
    subtitle_font = Font(name="Segoe UI", size=12, bold=True, color="333333")
    normal_font = Font(name="Segoe UI", size=11, color="555555")
    value_font = Font(name="Segoe UI", size=11, bold=True, color="000000")
    
    header_fill = PatternFill("solid", fgColor="E9ECEF")
    metric_fill = PatternFill("solid", fgColor="F8F9FA")
    
    thin_border = Border(
        left=Side(style='thin', color='DDDDDD'),
        right=Side(style='thin', color='DDDDDD'),
        top=Side(style='thin', color='DDDDDD'),
        bottom=Side(style='thin', color='DDDDDD')
    )
    
    # Title
    ws_summary.merge_cells("B2:D2")
    ws_summary["B2"] = "Laporan Eksekusi OCR"
    ws_summary["B2"].font = title_font
    
    ws_summary.merge_cells("B3:D3")
    ws_summary["B3"] = f"Dibuat pada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws_summary["B3"].font = normal_font

    total_docs = len(riwayat)
    success = sum(1 for r in riwayat if r['status'] in ('SUKSES', 'SUCCESS', 'SKIP'))
    failed = sum(1 for r in riwayat if r['status'] in ('GAGAL', 'FAILED'))
    skipped = sum(1 for r in riwayat if r['status'] == 'SKIP')
    
    processed_riwayat = [r for r in riwayat if r['status'] != 'SKIP']
    total_time = sum(float(r.get('processing_time', 0) or 0) for r in processed_riwayat)
    avg_time = round(total_time / len(processed_riwayat), 2) if processed_riwayat else 0.0
    success_rate = round((success / total_docs) * 100, 1) if total_docs > 0 else 0.0

    # Filters Section
    ws_summary["B5"] = "🔍 FILTER AKTIF"
    ws_summary["B5"].font = subtitle_font
    ws_summary["B5"].fill = header_fill
    ws_summary["B5"].border = thin_border
    ws_summary["C5"] = ""
    ws_summary["C5"].fill = header_fill
    ws_summary["C5"].border = thin_border
    ws_summary.merge_cells("B5:C5")

    filters = [
        ("Status", status if status else "Semua"),
        ("Pencarian", q if q else "Tidak ada"),
        ("Periode", period if period else "Semua Waktu")
    ]

    row_idx = 6
    for label, val in filters:
        ws_summary[f"B{row_idx}"] = label
        ws_summary[f"B{row_idx}"].font = normal_font
        ws_summary[f"B{row_idx}"].border = thin_border
        ws_summary[f"C{row_idx}"] = val
        ws_summary[f"C{row_idx}"].font = value_font
        ws_summary[f"C{row_idx}"].border = thin_border
        row_idx += 1

    # Metrics Section
    row_idx += 1
    ws_summary[f"B{row_idx}"] = "📊 METRIK KINERJA"
    ws_summary[f"B{row_idx}"].font = subtitle_font
    ws_summary[f"B{row_idx}"].fill = header_fill
    ws_summary[f"B{row_idx}"].border = thin_border
    ws_summary[f"C{row_idx}"] = ""
    ws_summary[f"C{row_idx}"].fill = header_fill
    ws_summary[f"C{row_idx}"].border = thin_border
    ws_summary.merge_cells(f"B{row_idx}:C{row_idx}")

    row_idx += 1
    metrics = [
        ("Total Dokumen", total_docs),
        ("Berhasil (Termasuk Skip)", success),
        ("Gagal", failed),
        ("Di-skip", skipped),
        ("Success Rate (%)", f"{success_rate}%"),
        ("Rata-rata Waktu Proses", f"{avg_time} detik")
    ]

    for label, val in metrics:
        ws_summary[f"B{row_idx}"] = label
        ws_summary[f"B{row_idx}"].font = normal_font
        ws_summary[f"B{row_idx}"].border = thin_border
        ws_summary[f"B{row_idx}"].fill = metric_fill

        ws_summary[f"C{row_idx}"] = val
        ws_summary[f"C{row_idx}"].font = value_font
        ws_summary[f"C{row_idx}"].border = thin_border
        ws_summary[f"C{row_idx}"].fill = metric_fill
        
        if "Success Rate" in label:
            if success_rate >= 90:
                ws_summary[f"C{row_idx}"].font = Font(name="Segoe UI", size=11, bold=True, color="28A745")
            elif success_rate < 50:
                ws_summary[f"C{row_idx}"].font = Font(name="Segoe UI", size=11, bold=True, color="DC3545")

        row_idx += 1

    ws_summary.column_dimensions['A'].width = 4
    ws_summary.column_dimensions['B'].width = 35
    ws_summary.column_dimensions['C'].width = 30
    
    # Sheet 2: Detailed Data
    ws_data = wb.create_sheet(title="Data Lengkap")
    headers = [
        "Waktu Proses Terakhir", "Nama File", "Status", "Processing Time (s)", 
        "Retry Count", "Keterangan", "Ukuran", "Halaman", 
        "Author", "Tanggal Dibuat"
    ]
    
    data_header_font = Font(name="Segoe UI", bold=True, color="FFFFFF")
    data_header_fill = PatternFill("solid", fgColor="1F4E78")
    
    ws_data.append(headers)
    for cell in ws_data[1]:
        cell.font = data_header_font
        cell.fill = data_header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
        
    ws_data.row_dimensions[1].height = 25
    ws_data.freeze_panes = "A2"
    
    success_fill = PatternFill("solid", fgColor="D4EDDA")
    failed_fill = PatternFill("solid", fgColor="F8D7DA")
    skip_fill = PatternFill("solid", fgColor="E2E3E5")
    
    data_font = Font(name="Segoe UI", size=10)

    for row_idx, r in enumerate(riwayat, start=2):
        row_data = [
            r.get("waktu", ""),
            r.get("nama_file", ""),
            r.get("status", ""),
            float(r.get("processing_time", 0) or 0),
            int(r.get("retry_count", 0) or 0),
            r.get("keterangan", ""),
            r.get("file_size", ""),
            r.get("page_count", ""),
            r.get("author", ""),
            r.get("creation_date", "")
        ]
        ws_data.append(row_data)
        
        for col_idx in range(1, len(row_data) + 1):
            cell = ws_data.cell(row=row_idx, column=col_idx)
            cell.font = data_font
            cell.border = thin_border
            if col_idx in (4, 5, 7, 8):
                cell.alignment = Alignment(horizontal="right")
        
        status_cell = ws_data.cell(row=row_idx, column=3)
        if status_cell.value in ("SUKSES", "SUCCESS"):
            status_cell.fill = success_fill
        elif status_cell.value in ("GAGAL", "FAILED"):
            status_cell.fill = failed_fill
        elif status_cell.value == "SKIP":
            status_cell.fill = skip_fill

    for col in ws_data.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws_data.column_dimensions[column].width = min(adjusted_width, 50)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"Laporan_OCR_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(output, download_name=filename, as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
