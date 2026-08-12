# Database Retry Mechanism Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure database updates during OCR processing survive transient connection errors or deadlocks by adding an exponential backoff retry mechanism.

**Architecture:** A synchronous `for` loop with exponential backoff (`time.sleep`) wrapping the `catat_ke_db` logic in `models/dashboard_model.py`.

**Tech Stack:** Python, SQLAlchemy

## Global Constraints

- No structural changes to the overall queue system; changes are strictly isolated to the database logging layer.
- `catat_ke_db` must return `True` on success and `False` on absolute failure (after all retries).

---

### Task 1: Add Retry Loop to `catat_ke_db`

**Files:**
- Modify: `models/dashboard_model.py:86-155`

**Interfaces:**
- Consumes: Existing `catat_ke_db` method arguments.
- Produces: Resilient database insertion/updates for the `Riwayat` table, returning `True` or `False`.

- [ ] **Step 1: Implement the retry mechanism inside `catat_ke_db`**

```python
    def catat_ke_db(
        self,
        document_key,
        folder_path="",
        nama_file="",
        status="SUKSES",
        keterangan="",
        file_size="-",
        author="-",
        page_count="-",
        creation_date="-",
        processing_time=0.0,
        retry_count=0,
        relative_path="",
        file_hash=""
    ):
        import time
        waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        first_processed_at = None
        last_processed_at = None
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                doc_key_query = document_key if document_key else ""
                if not doc_key_query and nama_file:
                    doc_key_query = nama_file

                existing = None
                if doc_key_query:
                    # Primary: match by document_key (unique relative path)
                    existing = Riwayat.query.filter(
                        Riwayat.document_key == doc_key_query
                    ).first()
                    # Fallback: match by nama_file ONLY if doc_key has no path separator
                    # (i.e., it's just a filename, not a relative path)
                    if not existing and '/' not in doc_key_query and '\\' not in doc_key_query:
                        existing = Riwayat.query.filter(
                            Riwayat.nama_file == doc_key_query
                        ).first()

                if existing:
                    existing.status = status
                    existing.waktu = waktu
                    if keterangan: existing.keterangan = keterangan
                    if file_size: existing.file_size = file_size
                    if author: existing.author = author
                    if page_count: existing.page_count = page_count
                    if creation_date: existing.creation_date = creation_date
                    if processing_time: existing.processing_time = processing_time
                    if relative_path: existing.relative_path = relative_path
                    if file_hash: existing.file_hash = file_hash
                    
                    existing.retry_count = (existing.retry_count or 0) + retry_count
                    if not existing.first_processed_at and first_processed_at:
                        existing.first_processed_at = first_processed_at
                    if last_processed_at:
                        existing.last_processed_at = last_processed_at
                    
                    if folder_path: existing.folder_path = folder_path
                else:
                    new_record = Riwayat(
                        document_key=doc_key_query,
                        folder_path=folder_path or "",
                        nama_file=nama_file or "",
                        status=status,
                        waktu=waktu,
                        keterangan=keterangan or "",
                        file_size=file_size or "",
                        author=author or "",
                        page_count=page_count or "",
                        creation_date=creation_date or "",
                        processing_time=processing_time or 0.0,
                        retry_count=retry_count or 0,
                        first_processed_at=first_processed_at or waktu,
                        last_processed_at=last_processed_at or waktu,
                        relative_path=relative_path or doc_key_query,
                        file_hash=file_hash or ""
                    )
                    db.session.add(new_record)
                
                db.session.commit()
                self.invalidate_stats_cache()
                return True
            except Exception as e:
                db.session.rollback()
                if attempt < max_retries - 1:
                    sleep_time = 0.5 * (2 ** attempt)
                    print(f"Database error in catat_ke_db: {e}. Retrying in {sleep_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(sleep_time)
                else:
                    print(f"Fatal database error in catat_ke_db after {max_retries} attempts: {e}")
                    return False
```

- [ ] **Step 2: Start the application locally (or let it restart via auto-reload) and test via OCR run**

Run the OCR application, ensuring no crash occurs. We won't test explicitly since it's hard to simulate a race condition via a simple command line trigger, but verify syntax correctness via app reload.
Expected: The Flask dev server (`app.py`) should reload successfully without syntax errors.

- [ ] **Step 3: Commit**

```bash
git add models/dashboard_model.py
git commit -m "fix(db): add exponential backoff retry to catat_ke_db"
```
