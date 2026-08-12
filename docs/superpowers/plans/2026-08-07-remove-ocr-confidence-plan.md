# Remove `ocr_confidence` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Safely remove the unused `ocr_confidence` attribute from the database model and the OCR processing engine to reduce overhead.

**Architecture:** Remove the field from the SQLAlchemy `Riwayat` model and database operations in `dashboard_model.py`. Remove confidence extraction, calculation, and reporting from `core_engine.py` (specifically `ekstrak_teks_dan_pdf`, `ekstrak_teks_dari_gambar`, `_ocr_worker_task`, and `simpan_riwayat`).

**Tech Stack:** Python, SQLAlchemy, PyTesseract

## Global Constraints

- Do not alter any other metadata attributes (e.g., `creation_date`, `page_count`).
- Maintain the SQLite database stability. If dropping the column isn't directly supported by SQLite, the worker should use SQLite's table recreation method or SQLAlchemy's migration if applicable, or simply leave the column in DB but remove all code references to it. For this plan, we focus on removing it from the ORM and code first.

---

### Task 1: Remove `ocr_confidence` from ORM and Database Layer

**Files:**
- Modify: `models/dashboard_model.py`

**Interfaces:**
- Consumes: Existing SQLite database schema.
- Produces: Updated `Riwayat` ORM model, updated `catat_ke_db` and `tambah_riwayat` methods without `ocr_confidence`.

- [ ] **Step 1: Remove `ocr_confidence` column from `Riwayat` model**

In `models/dashboard_model.py`, remove:
```python
    ocr_confidence = db.Column(db.Float, default=0.0)
```

- [ ] **Step 2: Remove `ocr_confidence` from `catat_ke_db` arguments and logic**

In `models/dashboard_model.py`, within `catat_ke_db`:
- Remove `ocr_confidence=0.0,` from the method signature.
- Remove `if ocr_confidence: existing.ocr_confidence = ocr_confidence`.
- Remove `ocr_confidence=ocr_confidence or 0.0,` from the `new_record = Riwayat(...)` instantiation.

- [ ] **Step 3: Remove `ocr_confidence` from `tambah_riwayat`**

In `models/dashboard_model.py`, within `tambah_riwayat`:
- Remove `ocr_confidence=0.0,` from the signature.
- Remove `ocr_confidence=ocr_confidence,` from the `self.catat_ke_db(...)` call.

- [ ] **Step 4: Commit changes to `dashboard_model.py`**

```bash
git add models/dashboard_model.py
git commit -m "refactor: remove ocr_confidence from database model"
```

---

### Task 2: Remove `ocr_confidence` from Core Engine Extraction Logic

**Files:**
- Modify: `core_engine.py`

**Interfaces:**
- Consumes: Nothing.
- Produces: Updated extraction functions returning only `pdf_baru`.

- [ ] **Step 1: Simplify `ekstrak_teks_dan_pdf`**

In `core_engine.py`:
- Remove `confidences = []` initialization.
- Remove the block that calculates confidence:
  ```python
              # Calculate average confidence from valid values in data.get('conf', [])
              for c in data.get('conf', []):
                  try:
                      val = float(c)
                      if val >= 0:
                          confidences.append(val)
                  except (ValueError, TypeError):
                      pass
  ```
- Remove `avg_conf = sum(confidences) / len(confidences) if confidences else 95.0`.
- Change `return pdf_baru, avg_conf` to `return pdf_baru`.

- [ ] **Step 2: Simplify `ekstrak_teks_dari_gambar`**

In `core_engine.py`:
- Remove the confidence calculation loop:
  ```python
          # Calculate average confidence
          confidences = []
          for c in data.get('conf', []):
              try:
                  val = float(c)
                  if val >= 0:
                      confidences.append(val)
              except (ValueError, TypeError):
                  pass
  ```
- Remove `avg_conf = sum(confidences) / len(confidences) if confidences else 95.0`.
- Change `return pdf_baru, avg_conf` to `return pdf_baru`.

- [ ] **Step 3: Update `ekstrak_dokumen` caller in `_ocr_worker_task`**

In `core_engine.py`, inside `_ocr_worker_task`:
- Change `pdf_baru, confidence = ekstrak_dokumen(...)` to `pdf_baru = ekstrak_dokumen(...)`.
- Remove `"ocr_confidence": round(confidence, 1),` from the success return dictionary.
- Remove `"ocr_confidence": 0.0,` from the failure return dictionary.

- [ ] **Step 4: Commit changes for extraction logic**

```bash
git add core_engine.py
git commit -m "refactor: remove ocr_confidence calculation from core engine"
```

---

### Task 3: Remove `ocr_confidence` from Reporting Logic

**Files:**
- Modify: `core_engine.py`

**Interfaces:**
- Consumes: Dictionary returned by `_ocr_worker_task`.
- Produces: Final clean call to `simpan_riwayat`.

- [ ] **Step 1: Update `simpan_riwayat` signature**

In `core_engine.py`:
- Remove `ocr_confidence=0.0,` from `def simpan_riwayat(...)` signature.
- Remove `ocr_confidence=ocr_confidence,` from the `db.catat_ke_db(...)` call inside `simpan_riwayat`.

- [ ] **Step 2: Remove `ocr_confidence` argument in worker result handling**

In `core_engine.py`, inside `jalankan_sistem_ocr`, under `try: res = future.result()`:
- Remove `ocr_confidence=res["ocr_confidence"],` from the `simpan_riwayat(...)` call.

- [ ] **Step 3: Commit changes for reporting logic**

```bash
git add core_engine.py
git commit -m "refactor: remove ocr_confidence from simpan_riwayat tracking"
```
