"""
tools/d5s/contracts/file_record.py
Dosya sistemi scan çıktısı. Sıfır logic — sadece veri şekli.
I/O yapan hiçbir şey import edilmez.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class FileCategory(str, Enum):
    """Seiri analizi için dosya kategorisi."""
    DOCUMENT    = "document"       # pdf, docx, xlsx, pptx
    IMAGE       = "image"          # jpg, png, raw, tif
    VIDEO       = "video"          # mp4, avi, mkv
    AUDIO       = "audio"          # mp3, wav, flac
    ARCHIVE     = "archive"        # zip, rar, 7z, tar
    INSTALLER   = "installer"      # exe, msi, pkg, dmg
    CODE        = "code"           # py, cs, js, c, cpp
    PLC         = "plc"            # mcd, acd, zap15, xap
    CAD         = "cad"            # dwg, dxf, stp, igs
    ISO_DOC     = "iso_doc"        # ISO belgesi
    LOG         = "log"            # log, txt log
    TEMP        = "temp"           # tmp, bak, ~$
    CACHE       = "cache"          # thumbs.db, .ds_store
    UNKNOWN     = "unknown"


class FileRecord(BaseModel):
    """
    Taranan tek bir dosyanın ham verisi.
    Scanner katmanı üretir. Kullanıcıya asla direkt gösterilmez.
    Engine bu veriyi okur, değiştirmez.
    """
    path:           Path
    name:           str
    extension:      str
    size_bytes:     int
    mtime:          datetime           # son değişiklik
    atime:          datetime           # son erişim
    ctime:          datetime           # oluşturma (Windows) / meta değişiklik (Unix)
    category:       FileCategory = FileCategory.UNKNOWN
    content_hash:   Optional[str] = None    # SHA-256, duplicate tespiti için
    is_hidden:      bool = False
    is_readonly:    bool = False
    depth:          int  = 0               # root'tan itibaren klasör derinliği

    @property
    def size_mb(self) -> float:
        return round(self.size_bytes / 1_048_576, 2)

    @property
    def age_days(self) -> int:
        return (datetime.now() - self.mtime).days


class FolderRecord(BaseModel):
    """Taranan tek bir klasörün özeti."""
    path:           Path
    name:           str
    file_count:     int  = 0
    folder_count:   int  = 0
    total_size_bytes: int = 0
    depth:          int  = 0
    is_empty:       bool = False

    @property
    def total_size_mb(self) -> float:
        return round(self.total_size_bytes / 1_048_576, 2)


class ScanResult(BaseModel):
    """Scanner katmanının tam çıktısı."""
    root:           Path
    files:          list[FileRecord]
    folders:        list[FolderRecord]
    total_files:    int
    total_folders:  int
    total_size_bytes: int
    scan_duration_ms: int
    scanned_at:     datetime = Field(default_factory=datetime.now)

    @property
    def total_size_gb(self) -> float:
        return round(self.total_size_bytes / 1_073_741_824, 3)
