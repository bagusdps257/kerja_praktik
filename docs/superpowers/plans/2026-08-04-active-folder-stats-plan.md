# Active Folder Statistics Synchronization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `ambil_statistik` in `models/dashboard_model.py` to calculate dashboard metrics dynamically based on physical files in `input_dir` and output files in `output_dir`.

**Architecture:** 
1. `models/dashboard_model.py`: Update `ambil_statistik` to scan physical files in `self.input_dir`.
2. Cross-reference each physical file against `self.output_dir` target path and DB `riwayat` latest status.
3. Calculate exact `total_input`, `total_output`, `total_gagal`, `pending`, and `total_halaman` satisfying `total_input == total_output + total_gagal + pending`.
4. Testing: Verify metric values when output folder is empty vs populated.

**Tech Stack:** Python 3, SQLite3, PyMuPDF (fitz), OS File System

## Global Constraints

- Retain return dictionary key structure for `ambil_statistik()`.
- Ensure invariant `total_input == total_output + total_gagal + pending`.

---

### Task 1: Refactor `ambil_statistik` in `models/dashboard_model.py`

**Files:**
- Modify: [`models/dashboard_model.py`](file:///D:/SEMESTER%207/KERJAPRAKTIK/OCR_Project/models/dashboard_model.py:532-630)

**Interfaces:**
- Consumes: `self.input_dir`, `self.output_dir`, `database.get_connection`
- Produces: Synchronized statistics dict for active folders.

- [ ] **Step 1: Refactor `ambil_statistik` logic**

In `models/dashboard_model.py`:
```python
    def ambil_statistik(self):
        conn = get_connection()
        cursor = conn.cursor()

        # Query latest status per document_key / file_id
        cursor.execute("""
            WITH latest_riwayat AS (
                SELECT 
                    COALESCE(NULLIF(document_key, ''), nama_file) AS file_id,
                    status,
                    page_count,
                    ROW_NUMBER() OVER (
                        PARTITION BY COALESCE(NULLIF(document_key, ''), nama_file)
                        ORDER BY datetime(COALESCE(last_processed_at, waktu)) DESC, id DESC
                    ) AS rn
                FROM riwayat
            )
            SELECT file_id, UPPER(status), page_count
            FROM latest_riwayat
            WHERE rn = 1
        """)
        db_status_map = {}
        for r in cursor.fetchall():
            if r[0]:
                db_status_map[r[0]] = (r[1], r[2])
        conn.close()

        total_output = 0
        total_gagal = 0
        pending = 0
        total_halaman = 0
        physical_input_files = []

        if os.path.exists(self.input_dir):
            for root, _, files in os.walk(self.input_dir):
                for file_name in files:
                    if file_name.lower().endswith(SUPPORTED_EXTENSIONS):
                        jalur_awal = os.path.join(root, file_name)
                        rel_path = os.path.relpath(jalur_awal, self.input_dir).replace('\\', '/')

                        if file_name.lower().endswith(IMAGE_EXTENSIONS):
                            target_rel = os.path.splitext(rel_path)[0] + ".pdf"
                        else:
                            target_rel = rel_path

                        target_output_file = os.path.join(self.output_dir, target_rel)
                        output_exists = os.path.exists(target_output_file)

                        # Lookup DB status
                        db_info = db_status_map.get(rel_path) or db_status_map.get(file_name)
                        db_status = db_info[0] if db_info else None
                        db_pages = db_info[1] if db_info else None

                        if output_exists or db_status in ('SUKSES', 'SUCCESS', 'SKIP'):
                            total_output += 1
                            if db_pages and db_pages != '-' and str(db_pages).isdigit():
                                total_halaman += int(db_pages)
                            else:
                                total_halaman += 1
                        elif db_status in ('GAGAL', 'FAILED'):
                            total_gagal += 1
                        else:
                            pending += 1

                        physical_input_files.append(rel_path)

        total_input = len(physical_input_files)

        # Storage info
        input_size_bytes = self.hitung_ukuran_folder(self.input_dir)
        output_size_bytes = self.hitung_ukuran_folder(self.output_dir)

        try:
            disk = shutil.disk_usage(self.output_dir if os.path.exists(self.output_dir) else '.')
            free_bytes = disk.free
            used_percent = round((disk.used / disk.total) * 100, 1) if disk.total > 0 else 0
        except Exception:
            free_bytes = 0
            used_percent = 0

        total_input_pages = self.hitung_total_halaman_folder(self.input_dir)
        total_output_pages = self.hitung_total_halaman_folder(self.output_dir)

        return {
            "total_input": total_input,
            "total_output": total_output,
            "pending": pending,
            "total_gagal": total_gagal,
            "total_halaman": total_halaman,
            "input_dir": self.input_dir,
            "output_dir": self.output_dir,
            "input_size": self.format_size(input_size_bytes),
            "input_size_bytes": input_size_bytes,
            "output_size": self.format_size(output_size_bytes),
            "output_size_bytes": output_size_bytes,
            "free_bytes": free_bytes,
            "free_space": self.format_size(free_bytes),
            "used_percent": used_percent,
            "total_input_pages": total_input_pages,
            "total_output_pages": total_output_pages
        }
```

---

### Task 2: Verification & Test

**Files:** All modified files

- [ ] **Step 1: Run unit test script testing active folder stats**

Verify that changing `output_dir` to an empty folder resets `total_output` to 0 and `pending` to `total_input`.
