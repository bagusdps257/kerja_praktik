# Fix OCR Fatal Error Saving Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Catch fatal OCR worker crashes and record them as failed in the database to prevent missing files and persistent queue statuses.

**Architecture:** Modify `jalankan_sistem_ocr` in `core_engine.py` to extract file metadata in the `except Exception` block of `future.result()` and call `simpan_riwayat` with status "GAGAL".

**Tech Stack:** Python, Flask-SQLAlchemy (via `models.extensions.db`)

## Global Constraints
- Do not affect normal non-crashing OCR operations.
- The exception handling block must safely read metadata without throwing an unhandled exception itself.

---
### Task 1: Add DB logging for Fatal Worker Exceptions

**Files:**
- Create: `scratch/test_fatal_error.py`
- Modify: `core_engine.py`

**Interfaces:**
- Consumes: `sedot_metadata`, `compute_file_hash`, `simpan_riwayat`
- Produces: Correct DB records on fatal crashes.

- [ ] **Step 1: Write the failing test**

```python
import os
import unittest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core_engine import jalankan_sistem_ocr
from app import create_app
from models.extensions import db
from models.dashboard_model import Riwayat

class TestFatalError(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        self.input_dir = "test_input_fatal"
        self.output_dir = "test_output_fatal"
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        with open(os.path.join(self.input_dir, "test.pdf"), "w") as f:
            f.write("dummy pdf")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.input_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('core_engine.concurrent.futures.ProcessPoolExecutor')
    def test_fatal_crash_logged(self, mock_executor_class):
        # Mock executor to raise an exception when accessing future.result()
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        mock_future = MagicMock()
        mock_future.result.side_effect = Exception("Simulated Broken Process")
        
        # When submit is called, it returns our mock future
        mock_executor.submit.return_value = mock_future
        
        # as_completed yields our mock future
        with patch('core_engine.concurrent.futures.as_completed', return_value=[mock_future]):
            jalankan_sistem_ocr(self.input_dir, self.output_dir, flask_app=self.app)
            
        # Check DB to see if the exception was recorded
        record = Riwayat.query.first()
        self.assertIsNotNone(record)
        self.assertEqual(record.status, "GAGAL")
        self.assertIn("Simulated Broken Process", record.keterangan)

if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3 scratch/test_fatal_error.py`
Expected: FAIL. `AssertionError: unexpectedly None` because no record is saved.

- [ ] **Step 3: Write minimal implementation**

In `core_engine.py`:
```python
                    except Exception as exc:
                        task_info = future_map[future]
                        catat_log(f"ERROR: {task_info[2]} - {exc}")
                        
                        try:
                            jalur_awal = task_info[0]
                            document_key = task_info[2]
                            folder_path = task_info[3]
                            nama_file_only = task_info[4]
                            
                            metadata = sedot_metadata(jalur_awal)
                            file_hash = compute_file_hash(jalur_awal)
                            
                            simpan_riwayat(
                                db,
                                document_key,
                                folder_path,
                                nama_file_only,
                                "GAGAL",
                                f"Fatal Error: {exc}",
                                metadata,
                                processing_time=0.0,
                                retry_count=0,
                                relative_path=document_key,
                                file_hash=file_hash
                            )
                        except Exception as inner_exc:
                            catat_log(f"Failed to log fatal error to DB: {inner_exc}")
                            
                        file_diproses += 1
                        update_progress(file_diproses)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3 scratch/test_fatal_error.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add core_engine.py scratch/test_fatal_error.py
git commit -m "fix(core): save fatal worker crashes to database"
```
