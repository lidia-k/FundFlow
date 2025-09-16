from typing import List
import os


class Settings:
    # Application
    app_name: str = "FundFlow"
    app_version: str = "1.2.0"
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/fundflow.db")

    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # File Upload
    max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
    upload_dir: str = os.getenv("UPLOAD_DIR", "../data/uploads")
    results_dir: str = os.getenv("RESULTS_DIR", "../data/results")
    templates_dir: str = os.getenv("TEMPLATES_DIR", "../data/templates")

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")


settings = Settings()


def get_database_url() -> str:
    """Get database URL with proper path resolution."""
    if settings.database_url.startswith("sqlite:///./"):
        # Resolve relative path for SQLite
        db_path = settings.database_url.replace("sqlite:///./", "")
        abs_path = os.path.abspath(db_path)
        return f"sqlite:///{abs_path}"
    return settings.database_url


def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        settings.upload_dir,
        settings.results_dir,
        settings.templates_dir,
        "logs",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)