# MySQL ORM Migration Design

## Objective
Migrate the existing OCR application database from SQLite (using raw `sqlite3` queries) to MySQL using Flask-SQLAlchemy as the Object Relational Mapper (ORM). This will make the codebase more maintainable, secure against SQL injections, and database-agnostic for future scaling.

## Current State
- **Database Engine:** SQLite (`ocr_database.db`)
- **Interaction Method:** Raw SQL queries executed via `sqlite3` module.
- **Key Models:** `models/user_model.py` and `models/dashboard_model.py` hold large amounts of raw SQL queries.

## Architecture & Implementation Plan

### 1. Dependencies and Configuration
- **Libraries:** Install `Flask-SQLAlchemy` and `mysql-connector-python` (or `PyMySQL`).
- **Configuration:** Update `config/settings.py` or `app.py` to include `SQLALCHEMY_DATABASE_URI` pointing to the local Laragon MySQL server (`mysql+mysqlconnector://root:@localhost/ocr_database`).
- **Extensions Module:** Create `models/extensions.py` to initialize `db = SQLAlchemy()`. This avoids circular imports between the main app and models.
- **App Initialization:** Bind the `db` instance to the Flask app in `app.py` (`db.init_app(app)`).

### 2. Model Refactoring
- **Users Table (`models/user_model.py`):**
  - Convert to a SQLAlchemy model: `class User(db.Model)`.
  - Replace raw SQL queries for authentication and user retrieval with ORM queries (e.g., `User.query.filter_by(username=username).first()`).
- **Riwayat/Dashboard Table (`models/dashboard_model.py`):**
  - Convert to a SQLAlchemy model: `class Riwayat(db.Model)`.
  - Define columns matching the current SQLite schema (e.g., `id`, `document_key`, `folder_path`, `nama_file`, `status`, `waktu`, `keterangan`, `file_size`, `author`, `page_count`, `creation_date`, `ocr_confidence`).
  - Rewrite all raw SQL methods (insertions, updates, filtering, statistics) into their respective SQLAlchemy ORM equivalents.
- **Cleanup:** 
  - Remove `models/database.py` since custom connection management is no longer needed.

### 3. Database Initialization Strategy
- Implement `db.create_all()` within an application context in `app.py` (or an initialization script) to automatically generate the database schema in the Laragon MySQL server if it does not exist.

## Out of Scope
- Migrating existing data from the SQLite database to MySQL. The application will start with a fresh, empty MySQL database.
- Refactoring the frontend logic or API routes beyond adapting them to the new ORM-based models.

## Success Criteria
- The application connects successfully to a local MySQL server via Laragon.
- All CRUD operations (user login, registering documents, dashboard metrics) work seamlessly using Flask-SQLAlchemy.
- No raw `sqlite3` syntax or imports remain in the codebase.
