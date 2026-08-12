# Excel Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the CSV export feature to generate a fully styled Excel (`.xlsx`) workbook with a Summary sheet and a Detailed Data sheet.

**Architecture:** Use `openpyxl` in `routes/export.py` to construct the Excel file in memory, replacing the standard `csv` library.

**Tech Stack:** Python, Flask, openpyxl, HTML.

## Global Constraints

- Must use `openpyxl` for Excel generation.
- Must preserve all existing filtering logic in the export route.

---

### Task 1: Add Dependency

**Files:**
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: Existing dependencies.
- Produces: Updated dependencies containing `openpyxl`.

- [ ] **Step 1: Add openpyxl to requirements**

Add `openpyxl` to the end of the file.

```txt
Flask-SQLAlchemy
PyMySQL
openpyxl
```

- [ ] **Step 2: Install openpyxl locally**

Run: `pip install openpyxl`
Expected: Successfully installs openpyxl.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add openpyxl for Excel export"
```

### Task 2: Implement Excel Export Route

**Files:**
- Modify: `routes/export.py:16-100`

**Interfaces:**
- Consumes: The `db_model.ambil_riwayat_db()` output and request args.
- Produces: An Excel file stream via `send_file`.

- [ ] **Step 1: Write the Excel generation logic**

Replace the `export_csv` function with `export_excel` using `openpyxl`.

```python
import io
from datetime import datetime
from flask import Blueprint, send_file, request
from flask_login import login_required
from models import OCRDashboardModel
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

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
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E78")
    
    ws_summary["A1"] = "Export Report Summary"
    ws_summary["A1"].font = Font(bold=True, size=14)
    
    ws_summary["A3"] = "Filter Status"
    ws_summary["B3"] = status if status else "Semua"
    ws_summary["A4"] = "Filter Pencarian"
    ws_summary["B4"] = q if q else "Tidak ada"
    ws_summary["A5"] = "Filter Periode"
    ws_summary["B5"] = period if period else "Semua Waktu"
    
    total_docs = len(riwayat)
    success = sum(1 for r in riwayat if r['status'] in ('SUKSES', 'SUCCESS', 'SKIP'))
    failed = sum(1 for r in riwayat if r['status'] in ('GAGAL', 'FAILED'))
    skipped = sum(1 for r in riwayat if r['status'] == 'SKIP')
    
    processed_riwayat = [r for r in riwayat if r['status'] != 'SKIP']
    total_time = sum(float(r.get('processing_time', 0) or 0) for r in processed_riwayat)
    avg_time = round(total_time / len(processed_riwayat), 2) if processed_riwayat else 0.0
    success_rate = round((success / total_docs) * 100, 1) if total_docs > 0 else 0.0
    
    ws_summary["A7"] = "Metrics"
    ws_summary["A7"].font = Font(bold=True)
    ws_summary["A8"] = "Total Documents"
    ws_summary["B8"] = total_docs
    ws_summary["A9"] = "Success Count (inc. Skip)"
    ws_summary["B9"] = success
    ws_summary["A10"] = "Failed Count"
    ws_summary["B10"] = failed
    ws_summary["A11"] = "Skipped Count"
    ws_summary["B11"] = skipped
    ws_summary["A12"] = "Success Rate (%)"
    ws_summary["B12"] = success_rate
    ws_summary["A13"] = "Avg Processing Time (s)"
    ws_summary["B13"] = avg_time

    ws_summary.column_dimensions['A'].width = 25
    ws_summary.column_dimensions['B'].width = 20
    
    # Sheet 2: Detailed Data
    ws_data = wb.create_sheet(title="Data Lengkap")
    headers = [
        "Waktu", "Nama File", "Status", "Processing Time (s)", 
        "Retry Count", "Keterangan", "Ukuran", "Halaman", 
        "Author", "Tanggal", "First Processed At", "Last Processed At"
    ]
    
    ws_data.append(headers)
    for cell in ws_data[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        
    ws_data.freeze_panes = "A2"
    
    success_fill = PatternFill("solid", fgColor="C6EFCE")
    failed_fill = PatternFill("solid", fgColor="FFC7CE")
    skip_fill = PatternFill("solid", fgColor="F2F2F2")

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
            r.get("creation_date", ""),
            r.get("first_processed_at", ""),
            r.get("last_processed_at", "")
        ]
        ws_data.append(row_data)
        
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
```

- [ ] **Step 2: Commit**

```bash
git add routes/export.py
git commit -m "feat: implement Excel export with openpyxl"
```

### Task 3: Update Frontend Buttons

**Files:**
- Modify: `templates/documents.html`
- Modify: `templates/analytics.html`

**Interfaces:**
- Consumes: The newly created `/export_excel` route.
- Produces: Updated UI buttons for the user to download the file.

- [ ] **Step 1: Modify documents.html**

Find the CSV export button (around line 117) and replace `/export_csv` with `/export_excel` and `Export CSV` with `Export Excel`.

```html
        <a href="/export_excel?q={{ current_q }}&status={{ current_status }}&period={{ current_period }}&month={{ current_month }}&year={{ current_year }}"
           class="btn btn-primary">
            <i class="bi bi-file-earmark-excel me-1"></i>Export Excel
        </a>
```

- [ ] **Step 2: Modify analytics.html**

Find the Export Report button (around line 78). Replace the `onclick="window.print()"` with a link to `/export_excel` so it downloads the global Excel report instead of printing to PDF.

```html
            <a href="/export_excel" class="btn btn-primary btn-sm analytics-export-btn">
                <i class="bi bi-file-earmark-excel me-1"></i>
                Export Excel
            </a>
```

- [ ] **Step 3: Commit**

```bash
git add templates/documents.html templates/analytics.html
git commit -m "feat: update UI to reflect Excel export"
```
