# Excel Export Design Specification

## Goal
Upgrade the current plain CSV export feature to generate a rich Excel (`.xlsx`) report with styling, proper data types, and a summary sheet to make the exported data more meaningful and easier to analyze.

## Architecture & Dependencies
- **Library**: Use `openpyxl` to construct and style the Excel workbook in memory before sending it to the client via Flask's `send_file` or `Response`.
- **Dependency**: Add `openpyxl` to `requirements.txt`.
- **Route**: Change the route from `/export_csv` to `/export_excel` in `routes/export.py` (and update the blueprint/references accordingly).

## Workbook Structure

### Sheet 1: Summary ("Ringkasan")
This sheet provides a high-level overview of the exported data batch.
- **Filters Applied**: Show what filters were active when the report was generated (e.g., Period, Status, Search Query).
- **Global Metrics**:
  - Total Documents
  - Success Count
  - Failed Count
  - Skipped Count
  - Success Rate (%)
  - Average Processing Time (seconds)
- **Formatting**: Use bold labels, light background colors for the metric blocks, and ensure it looks like a clean dashboard summary.

### Sheet 2: Detailed Data ("Data Lengkap")
This sheet contains the row-by-row transaction data currently present in the CSV, but enhanced.
- **Columns**: Waktu, Nama File, Status, Processing Time, Retry Count, Keterangan, Ukuran, Halaman, Author, Tanggal, First Processed At, Last Processed At.
- **Styling**:
  - **Headers**: Bold text with a dark blue background and white font. Freeze the top row so scrolling is easier.
  - **Auto-Width**: Column widths will be adjusted based on the maximum length of the content in each column to prevent cut-off text.
  - **Conditional Formatting**:
    - Rows/cells with Status `SUKSES` -> Light green background.
    - Rows/cells with Status `GAGAL` -> Light red background.
    - Rows/cells with Status `SKIP` -> Light gray or orange background.
- **Data Types**:
  - Numerical columns (Processing Time, Size, Pages, Retry Count) must be stored as numbers, not strings.
  - Timestamps must be stored as Excel dates/times (if parsable) or formatted consistently.

## Frontend UI Changes
- **documents.html**: Update the export button label to "Export Excel" and the `href` to point to `/export_excel`. Update icon if necessary.
- **analytics.html**: Update the export button label to "Export Report" or "Export Excel" and ensure it points to the correct endpoint if it previously triggered a CSV download.

## Error Handling
- If no data matches the current filters, the Excel file should still be generated but the Summary sheet will reflect 0 totals and the Detailed Data sheet will just have headers.
- Graceful fallbacks for missing data points in the database.
