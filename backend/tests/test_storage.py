import tempfile
from pathlib import Path

from app.core.storage import LocalStorage


def test_save_open_delete_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        storage = LocalStorage(base_dir=Path(tmp))
        key = storage.save(b"hello world", ".jpg")
        assert key.endswith(".jpg")
        assert storage.open(key) == b"hello world"
        storage.delete(key)
        assert not (Path(tmp) / key).exists()
