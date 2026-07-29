"""
tools/d5s/scanner/metadata.py
os.stat() çıktısını FileRecord alanlarına çeviren yardımcılar.
Walker bu modülü import eder.
"""

from __future__ import annotations
import os
import stat as stat_module
from datetime import datetime
from pathlib import Path


def stat_to_record(path: Path, st: os.stat_result) -> dict:
    """os.stat_result'ı FileRecord constructor kwargs'ına çevirir."""
    return {
        "size_bytes" : st.st_size,
        "mtime"      : datetime.fromtimestamp(st.st_mtime),
        "atime"      : datetime.fromtimestamp(st.st_atime),
        "ctime"      : datetime.fromtimestamp(st.st_ctime),
        "is_hidden"  : path.name.startswith(".") or path.name.startswith("~$"),
        "is_readonly": not bool(st.st_mode & stat_module.S_IWRITE),
    }


def human_size(size_bytes: int) -> str:
    """İnsan okunabilir boyut string'i."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes //= 1024
    return f"{size_bytes:.1f} PB"
