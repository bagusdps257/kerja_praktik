# Database Retry Mechanism Design Spec

## 1. Overview
During bulk OCR processing, concurrent updates to the MySQL database (Laragon) occasionally cause transient errors (e.g., Deadlocks or Connection Lock Wait Timeouts). Currently, the `catat_ke_db` function silently catches these exceptions, rolls back the session, and returns `False` without attempting to save again. Meanwhile, the core engine process increments the progress counter as if the file was processed successfully. This results in missing records in the database (e.g., 412 out of 415 files).

This design introduces an exponential backoff retry mechanism inside the database logging function to ensure all records are safely committed despite temporary database contention.

## 2. Architecture & Approach
The chosen approach focuses on the database layer (`models/dashboard_model.py`) to provide a resilient saving mechanism without requiring changes to the core engine's asynchronous workflow.

- **Target Component:** `DashboardModel.catat_ke_db`
- **Mechanism:** A synchronous retry loop wrapping the database query, update/insert, and commit operations.
- **Backoff Strategy:** If a commit fails, the system rolls back, sleeps for a short duration (increasing exponentially), and tries again.

## 3. Data Flow
1. `core_engine.py` calls `simpan_riwayat()`, which in turn calls `db.catat_ke_db(...)`.
2. Inside `catat_ke_db`:
   - A `for` loop executes up to `MAX_RETRIES` (e.g., 5).
   - Within the loop, a `try` block attempts to query the database, construct the record (`Riwayat`), and `commit()`.
   - If successful, it breaks the loop and returns `True`.
   - If an exception occurs, the `except` block catches it:
     - Calls `db.session.rollback()`.
     - Checks if the current attempt is the last one.
     - If not the last attempt, it pauses execution (`time.sleep()`) for a duration that increases per attempt (e.g., `0.5 * (2 ** attempt)`).
3. If all attempts fail, the function logs a fatal database error and returns `False`.

## 4. Error Handling
- **Database Rollback:** Mandatory upon any exception to clear the failed transaction state before retrying.
- **Ultimate Failure:** If all retries are exhausted, the application falls back to the existing behavior (returning `False`), but logs the failure heavily to indicate that manual intervention or a broader system check is necessary.

## 5. Scope
- This change is strictly scoped to the `catat_ke_db` method.
- It does not refactor the queuing architecture, preventing broad architectural regressions.
