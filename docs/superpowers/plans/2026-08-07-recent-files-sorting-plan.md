# Recent Files Sorting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change the sorting of the OCR documents list and Recent Processed Files list to be chronological based on the last time the file was processed or updated (`waktu` column).

**Architecture:** We will modify the SQLAlchemy ORM `order_by` clauses in `models/dashboard_model.py` so that documents with a recent `waktu` string appear at the top.

**Tech Stack:** Python, Flask, Flask-SQLAlchemy

## Global Constraints

- Target database engine: MySQL (via SQLAlchemy ORM)
- Keep existing method signatures intact.

---

### Task 1: Update Sorting Logic in OCRDashboardModel

**Files:**
- Modify: `models/dashboard_model.py:220-243`
- Test: `scratch/test_sorting.py` (Create new scratch file for verification)

**Interfaces:**
- Consumes: `Riwayat` ORM Model
- Produces: `ambil_riwayat_db` and `ambil_dokumen` returning dict lists sorted by `waktu` descending, then `id` descending.

- [ ] **Step 1: Write the failing test**

```python
# scratch/test_sorting.py
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from models.extensions import db
from models.dashboard_model import Riwayat, OCRDashboardModel

class TestSorting(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.model = OCRDashboardModel()
        
        # Insert dummy data out of order
        db.session.query(Riwayat).filter(Riwayat.document_key.like("test_sort_%")).delete()
        db.session.commit()
        
        r1 = Riwayat(document_key="test_sort_1", waktu="2026-08-01 10:00:00")
        r2 = Riwayat(document_key="test_sort_2", waktu="2026-08-03 10:00:00")
        r3 = Riwayat(document_key="test_sort_3", waktu="2026-08-02 10:00:00")
        db.session.add_all([r1, r2, r3])
        db.session.commit()

    def tearDown(self):
        db.session.query(Riwayat).filter(Riwayat.document_key.like("test_sort_%")).delete()
        db.session.commit()
        self.app_context.pop()

    def test_ambil_riwayat_db_sorting(self):
        results = self.model.ambil_riwayat_db(batas=5, q="test_sort_")
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["document_key"], "test_sort_2")
        self.assertEqual(results[1]["document_key"], "test_sort_3")
        self.assertEqual(results[2]["document_key"], "test_sort_1")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\env\Scripts\python.exe -m unittest scratch/test_sorting.py -v`
Expected: FAIL because the current implementation sorts by `id` descending, which will return `test_sort_3` (last inserted) first, not `test_sort_2`.

- [ ] **Step 3: Write minimal implementation**

Modify `models/dashboard_model.py` by replacing `desc(Riwayat.id)` with `desc(Riwayat.waktu), desc(Riwayat.id)` in two places:

```python
    def ambil_riwayat_db(self, batas=50, status=None, q=None, period=None, month=None, year=None):
        try:
            query = self._build_orm_query(status, q, period, month, year)
            results = query.order_by(desc(Riwayat.waktu), desc(Riwayat.id)).limit(batas).all()
            return [r.to_dict() for r in results]
        except Exception as e:
            print(f"Error ambil_riwayat_db: {e}")
            return []

    def ambil_dokumen(self, limit, offset, status=None, q=None, period=None, month=None, year=None):
        try:
            query = self._build_orm_query(status, q, period, month, year)
            total = query.count()
            
            results = query.order_by(desc(Riwayat.waktu), desc(Riwayat.id)).limit(limit).offset(offset).all()
            documents = [r.to_dict() for r in results]
            
            return documents, total
        except Exception as e:
            print(f"Error ambil_dokumen: {e}")
            return [], 0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\env\Scripts\python.exe -m unittest scratch/test_sorting.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add models/dashboard_model.py scratch/test_sorting.py
git commit -m "fix: sort recent files and documents by last processed time"
```
