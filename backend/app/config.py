from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    app_port: int = 8000
    app_url: str = "http://localhost:8000"
    secret_key: str
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    uploads_dir: str = "./uploads"
    admin_user: str = "admin"
    admin_password: str = ""


settings = Settings()
