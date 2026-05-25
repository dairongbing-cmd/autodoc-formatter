from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "temp"
UPLOAD_DIR = TEMP_DIR / "uploads"
OUTPUT_DIR = TEMP_DIR / "outputs"
PRESETS_DIR = BASE_DIR / "presets"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".docx", ".txt", ".md", ".markdown"}
STALE_CLEANUP_MINUTES = 30
CLEANUP_INTERVAL_SECONDS = 300  # 5 minutes
