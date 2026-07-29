"""
tools/d5s/engine/seiton.py
5S — Seiton (Set in Order) fazı.

Dosyaları doğru yere yerleştirme önerileri.
- Konu bazlı sınıflandırma (anahtar kelime eşleşmesi)
- Yıl bazlı arşivleme önerisi
- Standart klasör yapısına yönlendirme

Pure functions. LLM bu fazda devreye girer ama
bu modül deterministik öneri üretir — LLM bunu zenginleştirir.
"""

from __future__ import annotations
from pathlib import Path

from ..contracts.file_record import FileRecord, FileCategory
from ..contracts.plan import PlanItem, ActionType, RiskLevel, S5Phase


# Standart klasör yapısı ve anahtar kelimeler
TOPIC_MAP: dict[str, list[str]] = {
    "faturalar":      ["fatura", "invoice", "bill", "odeme", "payment"],
    "sozlesmeler":    ["sozlesme", "contract", "agreement", "anlasma", "protokol"],
    "raporlar":       ["rapor", "report", "analiz", "analysis", "ozet", "summary"],
    "sunumlar":       ["sunum", "presentation", "pptx", "slide"],
    "toplanti":       ["toplanti", "meeting", "gundem", "agenda", "tutanak"],
    "plc":            ["plc", "ladder", "function_block", "grafcet", "scl", "st",
                       "twincat", "schneider", "rockwell", "siemens", "codesys"],
    "cad":            ["dwg", "dxf", "stp", "step", "igs", "iges", "cad", "teknik_resim"],
    "python":         ["python", ".py", "script", "notebook", "jupyter"],
    "musteri":        ["musteri", "customer", "client", "muster"],
    "tedarikci":      ["tedarikci", "supplier", "vendor", "satinalma"],
    "fotograflar":    ["foto", "photo", "resim", "img", "image", "picture"],
    "videolar":       ["video", "film", "kayit", "recording"],
    "iso_belgeler":   ["iso", "kalite", "quality", "prosedur", "procedure",
                       "talimat", "instruction", "form"],
    "yedekler":       ["backup", "yedek", "kopyala", "archive"],
    "muhasebe":       ["muhasebe", "accounting", "gelir", "gider", "vergi", "tax"],
}

# Dosya kategorisi → hedef klasör
CATEGORY_FOLDER: dict[FileCategory, str] = {
    FileCategory.IMAGE:    "fotograflar",
    FileCategory.VIDEO:    "videolar",
    FileCategory.PLC:      "plc",
    FileCategory.CAD:      "cad",
    FileCategory.CODE:     "python",
    FileCategory.ISO_DOC:  "iso_belgeler",
}


def rule_topic_based(
    files: list[FileRecord],
    target_root: Path,
    topic_map: dict[str, list[str]] | None = None,
) -> list[PlanItem]:
    """Dosya adındaki anahtar kelimeye göre konu klasörüne öner."""
    tm = topic_map or TOPIC_MAP
    items: list[PlanItem] = []
    for f in files:
        name_lower = f.path.stem.lower()
        for topic, keywords in tm.items():
            if any(kw.lower() in name_lower for kw in keywords):
                dest = target_root / topic / f.path.name
                if dest.parent == f.path.parent:
                    break  # zaten doğru klasörde
                items.append(PlanItem(
                    phase=S5Phase.SEITON,
                    action=ActionType.MOVE,
                    source=f.path,
                    destination=dest,
                    reason=f"Dosya adı '{topic}' kategorisiyle eşleşti.",
                    risk=RiskLevel.LOW,
                    size_bytes=f.size_bytes,
                    confidence=0.65,
                ))
                break
    return items


def rule_category_based(
    files: list[FileRecord],
    target_root: Path,
) -> list[PlanItem]:
    """Dosya kategorisine göre standart klasöre öner."""
    items: list[PlanItem] = []
    for f in files:
        folder_name = CATEGORY_FOLDER.get(f.category)
        if not folder_name:
            continue
        dest = target_root / folder_name / f.path.name
        if dest.parent == f.path.parent:
            continue
        items.append(PlanItem(
            phase=S5Phase.SEITON,
            action=ActionType.MOVE,
            source=f.path,
            destination=dest,
            reason=f"'{f.category.value}' kategorisi için standart klasör: '{folder_name}'.",
            risk=RiskLevel.LOW,
            size_bytes=f.size_bytes,
            confidence=0.8,
        ))
    return items


def rule_year_based(
    files: list[FileRecord],
    archive_root: Path,
    older_than_years: int = 3,
) -> list[PlanItem]:
    """3+ yıllık dosyaları yıl bazlı arşive öner."""
    from datetime import datetime
    threshold_year = datetime.now().year - older_than_years
    items: list[PlanItem] = []
    for f in files:
        if f.mtime.year <= threshold_year:
            dest = archive_root / str(f.mtime.year) / f.path.name
            if dest.parent == f.path.parent:
                continue
            items.append(PlanItem(
                phase=S5Phase.SEITON,
                action=ActionType.MOVE,
                source=f.path,
                destination=dest,
                reason=f"{f.mtime.year} yılına ait — yıl bazlı arşiv klasörüne taşınabilir.",
                risk=RiskLevel.LOW,
                size_bytes=f.size_bytes,
            ))
    return items


def run_seiton(
    files: list[FileRecord],
    target_root: Path,
    archive_root: Path,
    topic_map: dict[str, list[str]] | None = None,
    config: dict | None = None,
) -> list[PlanItem]:
    cfg = config or {}
    items: list[PlanItem] = []
    if cfg.get("topic", True):
        items += rule_topic_based(files, target_root, topic_map)
    if cfg.get("category", True):
        items += rule_category_based(files, target_root)
    if cfg.get("year", False):   # default off — agresif
        items += rule_year_based(files, archive_root)
    return items
