"""
tools/d5s/scanner/walker.py
Dizin tarayıcı. Tek I/O noktası — sadece okur, hiçbir şey değiştirmez.

scan() → ScanResult üretir.
Engine ve Executor bu çıktıyı tüketir.
"""

from __future__ import annotations
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from ..contracts.file_record import (
    FileRecord, FolderRecord, ScanResult, FileCategory,
)


# ── Uzantı → Kategori haritası ───────────────────────────────────────────────
_EXT_CATEGORY: dict[str, FileCategory] = {
    # Doküman
    ".pdf": FileCategory.DOCUMENT, ".docx": FileCategory.DOCUMENT,
    ".doc": FileCategory.DOCUMENT, ".xlsx": FileCategory.DOCUMENT,
    ".xls": FileCategory.DOCUMENT, ".pptx": FileCategory.DOCUMENT,
    ".ppt": FileCategory.DOCUMENT, ".odt": FileCategory.DOCUMENT,
    ".txt": FileCategory.DOCUMENT, ".rtf": FileCategory.DOCUMENT,
    # Resim
    ".jpg": FileCategory.IMAGE, ".jpeg": FileCategory.IMAGE,
    ".png": FileCategory.IMAGE, ".gif": FileCategory.IMAGE,
    ".bmp": FileCategory.IMAGE, ".tif": FileCategory.IMAGE,
    ".tiff": FileCategory.IMAGE, ".webp": FileCategory.IMAGE,
    ".raw": FileCategory.IMAGE, ".cr2": FileCategory.IMAGE,
    # Video
    ".mp4": FileCategory.VIDEO, ".avi": FileCategory.VIDEO,
    ".mkv": FileCategory.VIDEO, ".mov": FileCategory.VIDEO,
    ".wmv": FileCategory.VIDEO, ".flv": FileCategory.VIDEO,
    ".m4v": FileCategory.VIDEO, ".webm": FileCategory.VIDEO,
    # Ses
    ".mp3": FileCategory.AUDIO, ".wav": FileCategory.AUDIO,
    ".flac": FileCategory.AUDIO, ".aac": FileCategory.AUDIO,
    ".ogg": FileCategory.AUDIO, ".m4a": FileCategory.AUDIO,
    # Arşiv
    ".zip": FileCategory.ARCHIVE, ".rar": FileCategory.ARCHIVE,
    ".7z": FileCategory.ARCHIVE, ".tar": FileCategory.ARCHIVE,
    ".gz": FileCategory.ARCHIVE, ".bz2": FileCategory.ARCHIVE,
    ".xz": FileCategory.ARCHIVE, ".iso": FileCategory.ISO_DOC,
    ".img": FileCategory.ISO_DOC,
    # Kurulum
    ".exe": FileCategory.INSTALLER, ".msi": FileCategory.INSTALLER,
    ".pkg": FileCategory.INSTALLER, ".dmg": FileCategory.INSTALLER,
    ".deb": FileCategory.INSTALLER, ".rpm": FileCategory.INSTALLER,
    # Kod
    ".py": FileCategory.CODE, ".js": FileCategory.CODE,
    ".ts": FileCategory.CODE, ".cs": FileCategory.CODE,
    ".cpp": FileCategory.CODE, ".c": FileCategory.CODE,
    ".h": FileCategory.CODE, ".java": FileCategory.CODE,
    ".go": FileCategory.CODE, ".rs": FileCategory.CODE,
    # PLC
    ".mcd": FileCategory.PLC, ".acd": FileCategory.PLC,
    ".zap15": FileCategory.PLC, ".xap": FileCategory.PLC,
    ".pro": FileCategory.PLC, ".st": FileCategory.PLC,
    # CAD
    ".dwg": FileCategory.CAD, ".dxf": FileCategory.CAD,
    ".stp": FileCategory.CAD, ".step": FileCategory.CAD,
    ".igs": FileCategory.CAD, ".iges": FileCategory.CAD,
    # Log
    ".log": FileCategory.LOG, ".out": FileCategory.LOG,
    ".err": FileCategory.LOG, ".trace": FileCategory.LOG,
    # Temp/Cache
    ".tmp": FileCategory.TEMP, ".temp": FileCategory.TEMP,
    ".bak": FileCategory.TEMP, ".old": FileCategory.TEMP,
    ".swp": FileCategory.TEMP, ".cache": FileCategory.CACHE,
}

_HIDDEN_PREFIXES = (".", "~$", "._")

# Taranmayacak sistem klasörleri
_SKIP_DIRS = {
    "$recycle.bin", "system volume information",
    ".git", ".svn", "__pycache__", "node_modules",
    "windows", "program files", "program files (x86)",
}


def _classify(extension: str) -> FileCategory:
    return _EXT_CATEGORY.get(extension.lower(), FileCategory.UNKNOWN)


def _is_hidden(name: str) -> bool:
    return any(name.startswith(p) for p in _HIDDEN_PREFIXES)


def _should_skip(folder_name: str) -> bool:
    return folder_name.lower() in _SKIP_DIRS


def scan(
    root: Path,
    compute_hash: bool = False,
    max_depth: int = 20,
    progress_cb: Callable[[str], None] | None = None,
    skip_hidden: bool = False,
) -> ScanResult:
    """
    Dizini tarar. Alt dizinler dahil.
    - compute_hash=True: SHA-256 hesaplar (yavaş, duplicate tespiti için)
    - progress_cb: her klasörde çağrılan callback (UI live update için)
    - skip_hidden: gizli dosya/klasörleri atlar
    """
    from .hasher import hash_file
    from .metadata import stat_to_record

    t_start = time.time()
    files: list[FileRecord] = []
    folders: list[FolderRecord] = []
    total_size = 0

    def _walk(current: Path, depth: int) -> None:
        nonlocal total_size
        if depth > max_depth:
            return

        try:
            entries = list(os.scandir(current))
        except PermissionError:
            return

        if progress_cb:
            progress_cb(str(current))

        dir_file_count = 0
        dir_folder_count = 0
        dir_size = 0

        for entry in entries:
            if skip_hidden and _is_hidden(entry.name):
                continue

            try:
                if entry.is_dir(follow_symlinks=False):
                    if _should_skip(entry.name):
                        continue
                    dir_folder_count += 1
                    _walk(Path(entry.path), depth + 1)

                elif entry.is_file(follow_symlinks=False):
                    stat = entry.stat()
                    ext  = Path(entry.name).suffix

                    content_hash = None
                    if compute_hash:
                        content_hash = hash_file(Path(entry.path))

                    rec = FileRecord(
                        path          = Path(entry.path),
                        name          = entry.name,
                        extension     = ext,
                        size_bytes    = stat.st_size,
                        mtime         = datetime.fromtimestamp(stat.st_mtime),
                        atime         = datetime.fromtimestamp(stat.st_atime),
                        ctime         = datetime.fromtimestamp(stat.st_ctime),
                        category      = _classify(ext),
                        content_hash  = content_hash,
                        is_hidden     = _is_hidden(entry.name),
                        is_readonly   = not os.access(entry.path, os.W_OK),
                        depth         = depth,
                    )
                    files.append(rec)
                    dir_file_count += 1
                    dir_size       += stat.st_size
                    total_size     += stat.st_size

            except (OSError, PermissionError):
                continue

        # Klasör kaydı
        folders.append(FolderRecord(
            path          = current,
            name          = current.name,
            file_count    = dir_file_count,
            folder_count  = dir_folder_count,
            total_size_bytes = dir_size,
            depth         = depth,
            is_empty      = (dir_file_count == 0 and dir_folder_count == 0),
        ))

    _walk(root, 0)

    duration_ms = int((time.time() - t_start) * 1000)

    return ScanResult(
        root            = root,
        files           = files,
        folders         = folders,
        total_files     = len(files),
        total_folders   = len(folders),
        total_size_bytes = total_size,
        scan_duration_ms = duration_ms,
    )
