from typing import List
import os


class Settings:
    # Application
    app_name: str = "FundFlow"
    app_version: str = "1.2.0"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./data/fundflow.db"

    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # File Upload
    max_upload_size: int = 10485760  # 10MB
    upload_dir: str = "../data/uploads"
    results_dir: str = "../data/results"
    templates_dir: str = "../data/templates"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"


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