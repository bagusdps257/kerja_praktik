import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Security
SECRET_KEY = os.environ.get("SECRET_KEY", "ocr_project_secret_key_2026_super_secure")

# Database
DB_PATH = os.path.join(BASE_DIR, "database", "ocr_database.db")

# Log
LOG_PATH = os.path.join(BASE_DIR, "logs", "sistem_ocr.log")

# Folder default
INPUT_DEFAULT = os.path.join(BASE_DIR, "input_pdf")
OUTPUT_DEFAULT = os.path.join(BASE_DIR, "output_pdf")

# Tesseract
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost/ocr_database"
SQLALCHEMY_TRACK_MODIFICATIONS = False