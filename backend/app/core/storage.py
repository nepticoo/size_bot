import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from app.config import settings


class Storage(Protocol):
    def save(self, data: bytes, suffix: str) -> str: ...  # returns an opaque key

    def open(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...


class LocalStorage:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or settings.resolved_uploads_dir

    def save(self, data: bytes, suffix: str) -> str:
        today = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        shard = self.base_dir / today
        shard.mkdir(parents=True, exist_ok=True)
        name = f"{secrets.token_urlsafe(16)}{suffix}"
        path = shard / name
        path.write_bytes(data)
        return f"{today}/{name}"

    def open(self, key: str) -> bytes:
        return (self.base_dir / key).read_bytes()

    def delete(self, key: str) -> None:
        path = self.base_dir / key
        if path.exists():
            path.unlink()
