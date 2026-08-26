import os

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    dotenv_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
except ImportError:
    pass

# Security & App Config
SECRET_KEY = os.environ.get("SECRET_KEY", "ocr_project_secret_key_2026_super_secure")
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
ALLOW_REGISTRATION = os.environ.get("ALLOW_REGISTRATION", "false").lower() in ("true", "1", "yes")

# Database Configuration
SQLALCHEMY_DATABASE_URI = (
    os.environ.get("DATABASE_URL") 
    or os.environ.get("SQLALCHEMY_DATABASE_URI") 
    or "mysql+pymysql://root:@localhost/ocr_database"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Database file fallback (if sqlite ever referenced)
DB_PATH = os.path.join(BASE_DIR, "database", "ocr_database.db")

# Log Path
LOG_PATH = os.path.join(BASE_DIR, "logs", "sistem_ocr.log")

# Folder Default
INPUT_DEFAULT = os.path.join(BASE_DIR, "input_pdf")
OUTPUT_DEFAULT = os.path.join(BASE_DIR, "output_pdf")

# Tesseract Executable (Linux Ubuntu default / override via env or settings)
TESSERACT_CMD = os.environ.get("TESSERACT_CMD", "/usr/bin/tesseract")