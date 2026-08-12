# Analytics Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `ambil_data_analitik` to provide comprehensive KPIs, daily trends, active users, and storage metrics to resolve the `UndefinedError` in the analytics template.

**Architecture:** We will modify `models/dashboard_model.py`. The SQL queries will fetch records, which we will aggregate in Python to compute the necessary metrics. Storage metrics will reuse existing folder size calculation helpers.

**Tech Stack:** Python, Flask, SQLAlchemy, built-in shutil/os

## Global Constraints

- Do not alter `analytics.html` or `routes/dashboard.py`.
- Handle potential zero divisions gracefully (e.g., when calculating success rate).
- Do not use advanced SQL grouping (e.g., `DATE()`) via SQLAlchemy that might break SQLite; do aggregations in Python memory.

---

### Task 1: Basic KPIs, Daily Charts, and User Metrics

**Files:**
- Modify: `models/dashboard_model.py`
- Create/Modify: `scratch/test_analytics_task1.py`

**Interfaces:**
- Consumes: The existing ORM query built by `self._build_orm_query`
- Produces: Updates `ambil_data_analitik` to return a dictionary including keys: `total_files`, `success_files`, `failed_files`, `skipped_files`, `success_rate`, `avg_processing_time`, `daily_trend`, `daily_volume`, and `most_active_users`.

- [ ] **Step 1: Write the failing test**

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.dashboard_model import OCRDashboardModel
from models.extensions import db
from app import create_app

class TestAnalyticsTask1(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.model = OCRDashboardModel()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_ambil_data_analitik_kpis(self):
        self.model.catat_ke_db("doc1", status="SUKSES", author="User A", processing_time=2.0)
        self.model.catat_ke_db("doc2", status="GAGAL", author="User B", processing_time=3.0)
        self.model.catat_ke_db("doc3", status="SKIP", author="User A", processing_time=1.0)
        
        data = self.model.ambil_data_analitik()
        
        self.assertEqual(data["total_files"], 3)
        self.assertEqual(data["success_files"], 1)
        self.assertEqual(data["failed_files"], 1)
        self.assertEqual(data["skipped_files"], 1)
        self.assertAlmostEqual(data["success_rate"], 33.3, places=1)
        self.assertAlmostEqual(data["avg_processing_time"], 2.0, places=1)
        self.assertEqual(len(data["most_active_users"]), 2)
        self.assertEqual(data["most_active_users"][0]["author"], "User A")
        self.assertEqual(data["most_active_users"][0]["docs"], 2)

if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3 scratch/test_analytics_task1.py`
Expected: FAIL (KeyError: 'total_files')

- [ ] **Step 3: Write minimal implementation**

Modify `ambil_data_analitik` in `models/dashboard_model.py`:

```python
    def ambil_data_analitik(self, period=None, month=None, year=None):
        try:
            query = self._build_orm_query(status=None, q=None, period=period, month=month, year=year)
            results = query.all()
            
            total_files = len(results)
            success_files = sum(1 for r in results if r.status in ('SUKSES', 'SUCCESS'))
            failed_files = sum(1 for r in results if r.status in ('GAGAL', 'FAILED'))
            skipped_files = sum(1 for r in results if r.status == 'SKIP')
            
            success_rate = round((success_files / total_files) * 100, 1) if total_files > 0 else 0.0
            
            total_time = sum(float(r.processing_time or 0) for r in results)
            avg_processing_time = round(total_time / total_files, 2) if total_files > 0 else 0.0
            
            daily_stats = {}
            user_stats = {}
            
            for r in results:
                date_str = r.waktu[:10] if r.waktu else ""
                if date_str:
                    if date_str not in daily_stats:
                        daily_stats[date_str] = {'success': 0, 'failed': 0, 'total': 0}
                    daily_stats[date_str]['total'] += 1
                    if r.status in ('SUKSES', 'SUCCESS'):
                        daily_stats[date_str]['success'] += 1
                    elif r.status in ('GAGAL', 'FAILED'):
                        daily_stats[date_str]['failed'] += 1
                
                author = r.author or "Unknown"
                user_stats[author] = user_stats.get(author, 0) + 1
            
            sorted_dates = sorted(daily_stats.keys())
            daily_trend = [{'tanggal': d, 'success': daily_stats[d]['success'], 'failed': daily_stats[d]['failed']} for d in sorted_dates]
            daily_volume = [{'tanggal': d, 'jumlah': daily_stats[d]['total']} for d in sorted_dates]
            
            sorted_users = sorted([{'author': k, 'docs': v} for k, v in user_stats.items()], key=lambda x: x['docs'], reverse=True)[:5]
            
            # Temporary storage placeholders to avoid undefined error in HTML
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
                "storage_used_percent": 0,
                "storage_total_gb": 0,
                "storage_used_gb": 0,
                "storage_free_formatted": "0 B",
                "output_size_formatted": "0 B",
                "log_size_formatted": "0 B"
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3 scratch/test_analytics_task1.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scratch/test_analytics_task1.py models/dashboard_model.py
git commit -m "feat: add KPI and user metrics to analytics data"
```

---

### Task 2: Storage Metrics

**Files:**
- Modify: `models/dashboard_model.py`
- Create/Modify: `scratch/test_analytics_task2.py`

**Interfaces:**
- Consumes: Existing functions `self.hitung_ukuran_folder`, `self.format_size`, `shutil.disk_usage`.
- Produces: Finalizes `ambil_data_analitik` to return real storage data instead of placeholders.

- [ ] **Step 1: Write the failing test**

```python
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.dashboard_model import OCRDashboardModel
from models.extensions import db
from app import create_app

class TestAnalyticsTask2(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.model = OCRDashboardModel()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('models.dashboard_model.OCRDashboardModel.hitung_ukuran_folder')
    @patch('shutil.disk_usage')
    def test_storage_metrics(self, mock_disk, mock_folder_size):
        class MockDiskUsage:
            total = 100 * 1024**3
            used = 50 * 1024**3
            free = 50 * 1024**3
        
        mock_disk.return_value = MockDiskUsage()
        mock_folder_size.side_effect = [1024**2, 5 * 1024**2] # 1MB log, 5MB output
        
        data = self.model.ambil_data_analitik()
        
        self.assertEqual(data["storage_total_gb"], 100.0)
        self.assertEqual(data["storage_used_gb"], 50.0)
        self.assertEqual(data["storage_used_percent"], 50.0)
        
        # Format returns string like '50.00 GB' or '1.00 MB'
        self.assertIn("MB", data["output_size_formatted"])
        self.assertIn("MB", data["log_size_formatted"])

if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3 scratch/test_analytics_task2.py`
Expected: FAIL (because storage values are hardcoded to 0)

- [ ] **Step 3: Write minimal implementation**

Modify `ambil_data_analitik` in `models/dashboard_model.py` to replace the placeholder block with real data:

```python
            import shutil
            import os
            
            try:
                disk = shutil.disk_usage(self.output_dir if os.path.exists(self.output_dir) else '.')
                total_gb = round(disk.total / (1024**3), 1)
                used_gb = round(disk.used / (1024**3), 1)
                used_percent = round((disk.used / disk.total) * 100, 1) if disk.total > 0 else 0
                free_formatted = self.format_size(disk.free)
            except Exception:
                total_gb = 0
                used_gb = 0
                used_percent = 0
                free_formatted = "0 B"
                
            out_size = self.hitung_ukuran_folder(self.output_dir)
            out_formatted = self.format_size(out_size)
            
            log_dir = os.path.dirname(self.log_path) if self.log_path else "."
            log_size = self.hitung_ukuran_folder(log_dir)
            log_formatted = self.format_size(log_size)

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3 scratch/test_analytics_task2.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scratch/test_analytics_task2.py models/dashboard_model.py
git commit -m "feat: add real storage metrics to analytics data"
```
