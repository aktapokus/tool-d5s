"""
tools/d5s/engine/scoring.py
5S puanlama algoritması.

Her faz için 0-100 puan hesaplar.
Girdi: ScanResult + PlanItem listesi
Çıktı: D5SScore
"""

from __future__ import annotations
import math
from ..contracts.file_record import ScanResult
from ..contracts.plan import PlanItem, S5Phase, ActionType
from ..contracts.report import D5SScore, PhaseScore


def _penalty(issue_count: int, total: int, max_penalty: float = 100.0) -> float:
    """
    Logaritmik ceza — az sorun büyük etki, çok sorun azalan etki.
    0 sorun → ceza yok. 10% sorun oranı → ~40 puan ceza.
    """
    if total == 0 or issue_count == 0:
        return 0.0
    ratio = issue_count / total
    penalty = max_penalty * (1 - math.exp(-5 * ratio))
    return min(penalty, max_penalty)


def score_seiri(
    scan: ScanResult,
    items: list[PlanItem],
) -> PhaseScore:
    """Seiri — gereksiz dosya oranına göre puan."""
    seiri_items = [i for i in items if i.phase == S5Phase.SEIRI]
    issue_count = len(seiri_items)
    total = scan.total_files + scan.total_folders or 1

    penalty = _penalty(issue_count, total)
    score = max(0.0, 100.0 - penalty)

    notes = []
    if issue_count == 0:
        notes.append("Mükemmel — gereksiz dosya tespit edilmedi.")
    elif issue_count < 10:
        notes.append(f"{issue_count} küçük sorun — kolayca temizlenebilir.")
    else:
        notes.append(f"{issue_count} sorun — düzenleme gerekli.")

    return PhaseScore(
        phase="seiri",
        score=round(score, 1),
        issues_found=issue_count,
        notes=notes,
    )


def score_seiton(
    scan: ScanResult,
    items: list[PlanItem],
) -> PhaseScore:
    """Seiton — yanlış yerleştirilmiş dosya oranı."""
    seiton_items = [
        i for i in items
        if i.phase == S5Phase.SEITON and i.action == ActionType.MOVE
    ]
    issue_count = len(seiton_items)
    total = scan.total_files or 1

    penalty = _penalty(issue_count, total, max_penalty=80.0)
    score = max(0.0, 100.0 - penalty)

    notes = []
    if issue_count == 0:
        notes.append("Dosyalar doğru konumda görünüyor.")
    else:
        notes.append(f"{issue_count} dosya daha uygun bir klasöre taşınabilir.")

    return PhaseScore(
        phase="seiton",
        score=round(score, 1),
        issues_found=issue_count,
        notes=notes,
    )


def score_seiso(
    scan: ScanResult,
    items: list[PlanItem],
) -> PhaseScore:
    """Seiso — temizlik sorunları."""
    seiso_items = [i for i in items if i.phase == S5Phase.SEISO]
    issue_count = len(seiso_items)

    if issue_count == 0:
        score = 100.0
        notes = ["Sistem temiz — artık dosya tespit edilmedi."]
    elif issue_count < 5:
        score = 85.0
        notes = [f"{issue_count} küçük temizlik öğesi bulundu."]
    elif issue_count < 20:
        score = 65.0
        notes = [f"{issue_count} artık dosya — temizlik önerilir."]
    else:
        score = 40.0
        notes = [f"{issue_count} artık dosya — acil temizlik gerekli."]

    return PhaseScore(
        phase="seiso",
        score=score,
        issues_found=issue_count,
        notes=notes,
    )


def score_seiketsu(
    scan: ScanResult,
    items: list[PlanItem],
) -> PhaseScore:
    """
    Seiketsu — standartlaşma.
    Şu an: isimlendirme sorunları + versiyon dosyaları oranı.
    İleride: naming convention compliance ile zenginleştirilecek.
    """
    naming_issues = [
        i for i in items
        if i.phase == S5Phase.SEIRI
        and "versiyon" in i.reason.lower()
    ]
    issue_count = len(naming_issues)
    total = scan.total_files or 1

    penalty = _penalty(issue_count, total, max_penalty=60.0)
    score = max(40.0, 100.0 - penalty)  # min 40 — ilk versiyonda veri yetersiz

    return PhaseScore(
        phase="seiketsu",
        score=round(score, 1),
        issues_found=issue_count,
        notes=["Naming convention analizi temel seviyede."],
    )


def score_shitsuke(
    previous_score: float | None,
    scan_count: int = 1,
) -> PhaseScore:
    """
    Shitsuke — sürdürülebilirlik.
    İlk taramada bilgi yok → 50 başlangıç puanı.
    Düzenli tarama yapıldıkça ve puan artışı gözlemlendikçe yükselir.
    """
    if scan_count <= 1 or previous_score is None:
        return PhaseScore(
            phase="shitsuke",
            score=50.0,
            notes=["İlk tarama — geçmiş veri yok. Düzenli tarama ile puan artacak."],
        )

    # Bir önceki taramaya göre trend
    if previous_score >= 80:
        score = 90.0
        notes = ["Düzenli bakım sürdürülüyor."]
    elif previous_score >= 60:
        score = 70.0
        notes = ["İyileşme eğilimi görülüyor."]
    else:
        score = 50.0
        notes = ["Henüz tutarlı bir bakım rutini oluşmadı."]

    return PhaseScore(
        phase="shitsuke",
        score=score,
        notes=notes,
    )


def calculate_score(
    scan: ScanResult,
    items: list[PlanItem],
    previous_score: float | None = None,
    scan_count: int = 1,
) -> D5SScore:
    """Ana giriş noktası — tüm fazları puanlar, D5SScore döner."""
    return D5SScore(
        seiri    = score_seiri(scan, items),
        seiton   = score_seiton(scan, items),
        seiso    = score_seiso(scan, items),
        seiketsu = score_seiketsu(scan, items),
        shitsuke = score_shitsuke(previous_score, scan_count),
    )
