"""
tools/d5s/scanner/hasher.py
Dosya hash hesaplama — duplicate tespiti için.
Büyük dosyalarda chunk'lı okuma yapar, RAM'i patlatmaz.
"""

from __future__ import annotations
import hashlib
from pathlib import Path

CHUNK_SIZE = 65_536  # 64 KB


def hash_file(path: Path) -> str | None:
    """SHA-256 hash döner. Hata durumunda None."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def hash_partial(path: Path, bytes_to_read: int = 65_536) -> str | None:
    """
    Sadece ilk N byte'ı hash'ler — büyük dosyalarda hızlı ön-eleme için.
    Tam hash'ten önce kullanılır: partial hash farklıysa duplicate olamaz.
    """
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            h.update(f.read(bytes_to_read))
        return h.hexdigest()
    except OSError:
        return None
