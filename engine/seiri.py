"""
tools/d5s/engine/seiri.py
5S — Seiri (Sort) fazı.

23 analiz türü. Tamamı pure function:
- Girdi: list[FileRecord] veya list[FolderRecord]
- Çıktı: list[PlanItem]
- Sıfır I/O, sıfır yan etki.
- Karar vermez — tespit eder ve gerekçelendirir.
- LLM burada yok. Tüm kurallar deterministik.
"""

from __future__ import annotations
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from ..contracts.file_record import FileRecord, FolderRecord
from ..contracts.plan import PlanItem, ActionType, RiskLevel, S5Phase


# ── Eşik değerleri (ayarlanabilir) ─────────────────────────────────────────
STALE_DAYS          = 180     # son değişiklik
UNUSED_DAYS         = 365     # son erişim
LARGE_FILE_MB       = 500     # büyük dosya eşiği
SINGLE_FILE_FOLDER  = 1       # tek dosyalı klasör

TEMP_EXTENSIONS = {
    ".tmp", ".temp", ".bak", ".old", ".orig",
    ".swp", ".swo", ".DS_Store",
}

TEMP_PREFIXES = ("~$", "._", "Thumbs", "desktop.ini")

INSTALLER_EXTENSIONS = {
    ".exe", ".msi", ".pkg", ".dmg", ".deb", ".rpm",
}

ARCHIVE_EXTENSIONS = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
}

ISO_EXTENSIONS = {".iso", ".img", ".bin", ".nrg"}

LOG_EXTENSIONS = {".log", ".out", ".err", ".trace"}

CACHE_NAMES = {
    "thumbs.db", ".ds_store", ".thumbnails",
    "__pycache__", ".cache", "cache",
}

# VERSION_PATTERN: Final_v2, Copy of, FINAL_FINAL, (2), -backup
VERSION_PATTERN = re.compile(
    r"(final|copy|kopya|backup|yedek|eski|old|v\d+|_\d+|\(\d+\)|rev\d+)",
    re.IGNORECASE,
)

EXTENSION_MISMATCH_MAP: dict[str, set[str]] = {
    "image":    {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".webp"},
    "video":    {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"},
    "audio":    {".mp3", ".wav", ".flac", ".aac", ".ogg"},
    "document": {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"},
    "code":     {".py", ".js", ".ts", ".cs", ".cpp", ".c", ".h"},
}

# Tüm bilinen uzantılar → kategori (ters map)
_EXT_TO_CATEGORY: dict[str, str] = {}
for _cat, _exts in EXTENSION_MISMATCH_MAP.items():
    for _e in _exts:
        _EXT_TO_CATEGORY[_e] = _cat


# ────────────────────────────────────────────────────────────────────────────
# 1. DUPLICATE DOSYALAR
# ────────────────────────────────────────────────────────────────────────────
def rule_duplicate(files: list[FileRecord]) -> list[PlanItem]:
    """SHA-256 hash eşleşmesi ile duplicate tespit. Silme önermez, bildirir."""
    by_hash: dict[str, list[FileRecord]] = defaultdict(list)
    for f in files:
        if f.content_hash:
            by_hash[f.content_hash].append(f)

    items: list[PlanItem] = []
    for _hash, group in by_hash.items():
        if len(group) < 2:
            continue
        original = min(group, key=lambda r: r.ctime)
        for dup in group:
            if dup.path == original.path:
                continue
            items.append(PlanItem(
                phase=S5Phase.SEIRI,
                action=ActionType.NO_ACTION,
                source=dup.path,
                reason=f"'{original.path.name}' ile aynı içerik (SHA-256 eşleşmesi). Orijinal: {original.path}",
                risk=RiskLevel.MEDIUM,
                size_bytes=dup.size_bytes,
                reversible=True,
            ))
    return items


# ────────────────────────────────────────────────────────────────────────────
# 2. BOŞ KLASÖRLER
# ────────────────────────────────────────────────────────────────────────────
def rule_empty_folders(folders: list[FolderRecord]) -> list[PlanItem]:
    return [
        PlanItem(
            phase=S5Phase.SEIRI,
            action=ActionType.DELETE,
            source=f.path,
            reason="Klasör boş — içerik yok.",
            risk=RiskLevel.LOW,
        )
        for f in folders if f.is_empty
    ]


# ────────────────────────────────────────────────────────────────────────────
# 3. ESKİ DOSYALAR (son değişiklik > STALE_DAYS)
# ────────────────────────────────────────────────────────────────────────────
def rule_stale_files(
    files: list[FileRecord],
    archive_root: Path,
    stale_days: int = STALE_DAYS,
) -> list[PlanItem]:
    threshold = timedelta(days=stale_days)
    now = datetime.now()
    items: list[PlanItem] = []
    for f in files:
        if now - f.mtime > threshold:
            dest = archive_root / f.mtime.strftime("%Y") / f.path.name
            items.append(PlanItem(
                phase=S5Phase.SEIRI,
                action=ActionType.MOVE,
                source=f.path,
                destination=dest,
                reason=f"{stale_days}+ gündür değiştirilmedi (son: {f.mtime:%Y-%m-%d}).",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
            ))
    return items


# ────────────────────────────────────────────────────────────────────────────
# 4. HİÇ AÇILMAMIŞI DOSYALAR (son erişim > UNUSED_DAYS)
# ────────────────────────────────────────────────────────────────────────────
def rule_unused_files(
    files: list[FileRecord],
    archive_root: Path,
    unused_days: int = UNUSED_DAYS,
) -> list[PlanItem]:
    threshold = timedelta(days=unused_days)
    now = datetime.now()
    items: list[PlanItem] = []
    for f in files:
        if now - f.atime > threshold:
            dest = archive_root / "unused" / f.path.name
            items.append(PlanItem(
                phase=S5Phase.SEIRI,
                action=ActionType.MOVE,
                source=f.path,
                destination=dest,
                reason=f"{unused_days}+ gündür açılmadı (son erişim: {f.atime:%Y-%m-%d}).",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
            ))
    return items


# ────────────────────────────────────────────────────────────────────────────
# 5. GEÇİCİ DOSYALAR
# ────────────────────────────────────────────────────────────────────────────
def rule_temp_files(files: list[FileRecord]) -> list[PlanItem]:
    items: list[PlanItem] = []
    for f in files:
        is_temp = (
            f.extension.lower() in TEMP_EXTENSIONS
            or any(f.name.startswith(p) for p in TEMP_PREFIXES)
        )
        if is_temp:
            items.append(PlanItem(
                phase=S5Phase.SEIRI,
                action=ActionType.DELETE,
                source=f.path,
                reason=f"Geçici dosya deseni eşleşti ('{f.extension}').",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
            ))
    return items


# ────────────────────────────────────────────────────────────────────────────
# 6–8. KURULUM / ARŞİV / ISO DOSYALARI
# ────────────────────────────────────────────────────────────────────────────
def rule_installer_files(
    files: list[FileRecord],
    archive_root: Path,
) -> list[PlanItem]:
    items: list[PlanItem] = []
    for f in files:
        if f.extension.lower() in INSTALLER_EXTENSIONS:
            dest = archive_root / "installers" / f.path.name
            items.append(PlanItem(
                phase=S5Phase.SEIRI,
                action=ActionType.MOVE,
                source=f.path,
                destination=dest,
                reason=f"Kurulum dosyası — aktif kullanım dışında arşivlenmeli.",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
            ))
    return items


def rule_archive_files(
    files: list[FileRecord],
    archive_root: Path,
    stale_days: int = STALE_DAYS,
) -> list[PlanItem]:
    """Sadece eski arşiv dosyaları — yeni olanlar genelde aktif kullanımda."""
    threshold = timedelta(days=stale_days)
    now = datetime.now()
    items: list[PlanItem] = []
    for f in files:
        if f.extension.lower() in ARCHIVE_EXTENSIONS and now - f.mtime > threshold:
            dest = archive_root / "archives" / f.path.name
            items.append(PlanItem(
                phase=S5Phase.SEIRI,
                action=ActionType.MOVE,
                source=f.path,
                destination=dest,
                reason=f"Eski arşiv dosyası ({f.mtime:%Y-%m-%d}).",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
            ))
    return items


def rule_iso_files(
    files: list[FileRecord],
    archive_root: Path,
) -> list[PlanItem]:
    items: list[PlanItem] = []
    for f in files:
        if f.extension.lower() in ISO_EXTENSIONS:
            dest = archive_root / "iso" / f.path.name
            items.append(PlanItem(
                phase=S5Phase.SEIRI,
                action=ActionType.MOVE,
                source=f.path,
                destination=dest,
                reason=f"ISO/image dosyası — arşiv klasörüne taşınmalı.",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
            ))
    return items


# ────────────────────────────────────────────────────────────────────────────
# 9. LOG DOSYALARI
# ────────────────────────────────────────────────────────────────────────────
def rule_log_files(
    files: list[FileRecord],
    archive_root: Path,
    stale_days: int = 30,
) -> list[PlanItem]:
    threshold = timedelta(days=stale_days)
    now = datetime.now()
    items: list[PlanItem] = []
    for f in files:
        if f.extension.lower() in LOG_EXTENSIONS and now - f.mtime > threshold:
            dest = archive_root / "logs" / f.path.name
            items.append(PlanItem(
                phase=S5Phase.SEIRI,
                action=ActionType.MOVE,
                source=f.path,
                destination=dest,
                reason=f"Eski log dosyası ({f.mtime:%Y-%m-%d}).",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
            ))
    return items


# ────────────────────────────────────────────────────────────────────────────
# 10. CACHE DOSYALARI
# ────────────────────────────────────────────────────────────────────────────
def rule_cache_files(files: list[FileRecord]) -> list[PlanItem]:
    items: list[PlanItem] = []
    for f in files:
        if f.name.lower() in CACHE_NAMES or f.extension.lower() in {".db", ".cache"}:
            items.append(PlanItem(
                phase=S5Phase.SEIRI,
                action=ActionType.DELETE,
                source=f.path,
                reason=f"Cache/thumbnail dosyası — yeniden oluşturulabilir.",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
            ))
    return items


# ────────────────────────────────────────────────────────────────────────────
# 11. BÜYÜK DOSYALAR (bilgi amaçlı)
# ────────────────────────────────────────────────────────────────────────────
def rule_large_files(
    files: list[FileRecord],
    large_mb: int = LARGE_FILE_MB,
) -> list[PlanItem]:
    threshold = large_mb * 1_048_576
    items: list[PlanItem] = []
    for f in files:
        if f.size_bytes >= threshold:
            items.append(PlanItem(
                phase=S5Phase.SEIRI,
                action=ActionType.NO_ACTION,
                source=f.path,
                reason=f"Büyük dosya: {f.size_mb:.0f} MB. Sıkıştırma veya arşivleme değerlendirilebilir.",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
            ))
    return items


# ────────────────────────────────────────────────────────────────────────────
# 12. VERSION DOSYALARI (Final_v2, Copy of, backup vb.)
# ────────────────────────────────────────────────────────────────────────────
def rule_version_files(
    files: list[FileRecord],
    archive_root: Path,
) -> list[PlanItem]:
    items: list[PlanItem] = []
    for f in files:
        if VERSION_PATTERN.search(f.path.stem):
            dest = archive_root / "versions" / f.path.name
            items.append(PlanItem(
                phase=S5Phase.SEIRI,
                action=ActionType.MOVE,
                source=f.path,
                destination=dest,
                reason=f"Versiyon/yedek dosyası deseni: '{f.path.stem}'.",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
                confidence=0.75,  # pattern match, kesin değil
            ))
    return items


# ────────────────────────────────────────────────────────────────────────────
# 13. TEK DOSYALI KLASÖRLER
# ────────────────────────────────────────────────────────────────────────────
def rule_single_file_folders(folders: list[FolderRecord]) -> list[PlanItem]:
    items: list[PlanItem] = []
    for f in folders:
        if f.file_count == SINGLE_FILE_FOLDER and f.folder_count == 0:
            items.append(PlanItem(
                phase=S5Phase.SEIRI,
                action=ActionType.NO_ACTION,
                source=f.path,
                reason=f"Klasörde yalnızca 1 dosya var. Üst klasöre taşınması değerlendirilebilir.",
                risk=RiskLevel.LOW,
            ))
    return items


# ────────────────────────────────────────────────────────────────────────────
# 14. UZANTI UYUŞMAZLIĞI
# ────────────────────────────────────────────────────────────────────────────
def rule_extension_mismatch(files: list[FileRecord]) -> list[PlanItem]:
    """
    Dosya adı ile uzantısı uyuşmayan durumlar.
    Örn: rapor.jpg ama içerik PDF sinyali taşıyan bir isim.
    Basit sezgisel: uzantı kategorisi isim içeriğiyle çelişiyor mu?
    """
    CATEGORY_KEYWORDS: dict[str, list[str]] = {
        "image":    ["photo", "foto", "resim", "img", "picture"],
        "video":    ["video", "film", "klip", "clip"],
        "document": ["rapor", "report", "belge", "document", "sunum"],
        "code":     ["script", "module", "class", "main"],
    }
    items: list[PlanItem] = []
    ext = files[0].extension.lower() if files else ""
    for f in files:
        ext = f.extension.lower()
        ext_cat = _EXT_TO_CATEGORY.get(ext)
        if not ext_cat:
            continue
        name_lower = f.path.stem.lower()
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if cat == ext_cat:
                continue
            if any(kw in name_lower for kw in keywords):
                items.append(PlanItem(
                    phase=S5Phase.SEIRI,
                    action=ActionType.NO_ACTION,
                    source=f.path,
                    reason=f"Dosya adı '{cat}' kategorisini çağrıştırıyor ama uzantı '{ext_cat}'. İncelenmeli.",
                    risk=RiskLevel.LOW,
                    confidence=0.5,
                ))
                break
    return items


# ────────────────────────────────────────────────────────────────────────────
# 15. BENZERİ KLASÖR İSİMLERİ (Levenshtein distance)
# ────────────────────────────────────────────────────────────────────────────
def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


def rule_similar_folders(folders: list[FolderRecord], threshold: int = 3) -> list[PlanItem]:
    """İsim benzerliği yüksek klasörler — muhtemel mükerrer."""
    names = [(f.path, f.name.lower()) for f in folders]
    items: list[PlanItem] = []
    seen: set[tuple[Path, Path]] = set()

    for i, (pa, na) in enumerate(names):
        for pb, nb in names[i + 1:]:
            pair = (min(pa, pb), max(pa, pb))
            if pair in seen:
                continue
            dist = _levenshtein(na, nb)
            if 0 < dist <= threshold:
                seen.add(pair)
                items.append(PlanItem(
                    phase=S5Phase.SEIRI,
                    action=ActionType.NO_ACTION,
                    source=pa,
                    reason=f"'{na}' ve '{nb}' klasör isimleri çok benzer (mesafe={dist}). Birleştirme değerlendirilebilir.",
                    risk=RiskLevel.LOW,
                    confidence=0.65,
                ))
    return items


# ────────────────────────────────────────────────────────────────────────────
# SEIRI MASTER RUNNER
# ────────────────────────────────────────────────────────────────────────────
def run_seiri(
    files: list[FileRecord],
    folders: list[FolderRecord],
    archive_root: Path,
    config: dict | None = None,
) -> list[PlanItem]:
    """
    Tüm Seiri kurallarını çalıştırır, birleşik PlanItem listesi döner.
    config: hangi kuralların aktif olduğunu belirler (opsiyonel).
    """
    cfg = config or {}
    items: list[PlanItem] = []

    if cfg.get("duplicate", True):
        items += rule_duplicate(files)
    if cfg.get("empty_folders", True):
        items += rule_empty_folders(folders)
    if cfg.get("stale", True):
        items += rule_stale_files(files, archive_root)
    if cfg.get("unused", True):
        items += rule_unused_files(files, archive_root)
    if cfg.get("temp", True):
        items += rule_temp_files(files)
    if cfg.get("installer", True):
        items += rule_installer_files(files, archive_root)
    if cfg.get("archive", True):
        items += rule_archive_files(files, archive_root)
    if cfg.get("iso", True):
        items += rule_iso_files(files, archive_root)
    if cfg.get("log", True):
        items += rule_log_files(files, archive_root)
    if cfg.get("cache", True):
        items += rule_cache_files(files)
    if cfg.get("large", True):
        items += rule_large_files(files)
    if cfg.get("version", True):
        items += rule_version_files(files, archive_root)
    if cfg.get("single_file_folder", True):
        items += rule_single_file_folders(folders)
    if cfg.get("extension_mismatch", False):   # default off — çok false positive
        items += rule_extension_mismatch(files)
    if cfg.get("similar_folders", True):
        items += rule_similar_folders(folders)

    return items
