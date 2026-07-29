"""
tools/d5s/engine/seiso.py
5S — Seiso (Shine) fazı.

Sistem çöplerini tespit eder:
- Recycle Bin / Trash
- OS temp klasörleri
- Browser cache
- Thumbnail cache
- İstenmeyen system dosyaları

Pure functions, sıfır I/O.
"""

from __future__ import annotations
from pathlib import Path

from ..contracts.file_record import FileRecord, FolderRecord
from ..contracts.plan import PlanItem, ActionType, RiskLevel, S5Phase


SYSTEM_JUNK_NAMES = {
    "thumbs.db", "desktop.ini", ".ds_store",
    ".localized", ".spotlight-v100", ".fseventsd",
    ".trashes", ".volumeicon.icns",
}

SYSTEM_JUNK_EXTENSIONS = {
    ".lnk",   # Windows shortcut
    ".url",   # Web shortcut (geçici)
}

OS_TEMP_MARKERS = {
    "windows\\temp", "appdata\\local\\temp",
    "tmp", "temp", "$recycle.bin",
    ".trash", ".trashes",
}

BROWSER_CACHE_MARKERS = {
    "cache", "cache2", "code cache",
    "gpucache", "shadercache", "jscache",
    "service worker", "cookies", "web data",
}


def _path_contains(path: Path, markers: set[str]) -> bool:
    path_lower = str(path).lower().replace("\\", "/")
    return any(m in path_lower for m in markers)


def rule_system_junk(files: list[FileRecord]) -> list[PlanItem]:
    items: list[PlanItem] = []
    for f in files:
        if (
            f.name.lower() in SYSTEM_JUNK_NAMES
            or f.extension.lower() in SYSTEM_JUNK_EXTENSIONS
        ):
            items.append(PlanItem(
                phase=S5Phase.SEISO,
                action=ActionType.DELETE,
                source=f.path,
                reason=f"OS sistem dosyası/kısayolu — gerekli değil.",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
            ))
    return items


def rule_os_temp(
    files: list[FileRecord],
    folders: list[FolderRecord],
) -> list[PlanItem]:
    items: list[PlanItem] = []
    for f in files:
        if _path_contains(f.path, OS_TEMP_MARKERS):
            items.append(PlanItem(
                phase=S5Phase.SEISO,
                action=ActionType.DELETE,
                source=f.path,
                reason="OS geçici dizininde — güvenle silinebilir.",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
            ))
    for folder in folders:
        if _path_contains(folder.path, OS_TEMP_MARKERS) and folder.is_empty:
            items.append(PlanItem(
                phase=S5Phase.SEISO,
                action=ActionType.DELETE,
                source=folder.path,
                reason="Boş OS geçici klasörü.",
                risk=RiskLevel.LOW,
            ))
    return items


def rule_browser_cache(files: list[FileRecord]) -> list[PlanItem]:
    items: list[PlanItem] = []
    for f in files:
        if _path_contains(f.path, BROWSER_CACHE_MARKERS):
            items.append(PlanItem(
                phase=S5Phase.SEISO,
                action=ActionType.DELETE,
                source=f.path,
                reason="Browser cache dosyası — yeniden oluşturulabilir.",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
            ))
    return items


def run_seiso(
    files: list[FileRecord],
    folders: list[FolderRecord],
    config: dict | None = None,
) -> list[PlanItem]:
    cfg = config or {}
    items: list[PlanItem] = []
    if cfg.get("system_junk", True):
        items += rule_system_junk(files)
    if cfg.get("os_temp", True):
        items += rule_os_temp(files, folders)
    if cfg.get("browser_cache", False):  # default off — path tespiti zor
        items += rule_browser_cache(files)
    return items
