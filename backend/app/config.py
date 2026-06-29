# Application configuration loaded from environment variables.
# Keeps secrets and database URLs out of source code.

import os
from pathlib import Path

from dotenv import load_dotenv

# Load variables from backend/.env when running locally
load_dotenv()

# Base directory for the backend package (used for upload storage)
BASE_DIR = Path(__file__).resolve().parent.parent

# PostgreSQL connection string
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/study_companion",
)

# JWT settings for authentication
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
print(repr(GEMINI_API_KEY))
# Local folder where uploaded PDF files are stored
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Maximum upload size in bytes (10 MB)
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024

# Allowed MIME types for document upload in Phase 2 (PDF only)
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
