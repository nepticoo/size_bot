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

    @property
    def resolved_database_url(self) -> str:
        # sqlite path in .env is written relative to the project root; resolve it
        # to an absolute path so it works no matter which directory a command runs from.
        prefix = "sqlite+aiosqlite:///./"
        if self.database_url.startswith(prefix):
            rel = self.database_url[len(prefix) :]
            abs_path = (PROJECT_ROOT / rel).resolve()
            return f"sqlite+aiosqlite:///{abs_path.as_posix()}"
        return self.database_url

    @property
    def resolved_uploads_dir(self) -> Path:
        if self.uploads_dir.startswith("./"):
            return (PROJECT_ROOT / self.uploads_dir[2:]).resolve()
        return Path(self.uploads_dir).resolve()


settings = Settings()
