"""
tools/d5s/contracts/report.py
5S puanlama ve raporlama modelleri.
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import ClassVar
from pydantic import BaseModel, Field


class PhaseScore(BaseModel):
    """Tek bir 5S fazının puanı."""
    phase:          str
    score:          float = Field(ge=0.0, le=100.0)
    max_score:      float = 100.0
    issues_found:   int   = 0
    issues_fixed:   int   = 0
    notes:          list[str] = []


class D5SScore(BaseModel):
    """
    Tek tarama sonucundaki 5S puanı.
    Her faz 0-100 arası puan alır, ağırlıklı ortalama toplam puanı verir.
    """
    seiri:          PhaseScore
    seiton:         PhaseScore
    seiso:          PhaseScore
    seiketsu:       PhaseScore
    shitsuke:       PhaseScore
    scored_at:      datetime = Field(default_factory=datetime.now)

    # Ağırlıklar: Seiri en kritik, Shitsuke en az (ilk taramada veri yok)
    WEIGHTS: ClassVar[dict[str, float]] = {
        "seiri":    0.30,
        "seiton":   0.25,
        "seiso":    0.20,
        "seiketsu": 0.15,
        "shitsuke": 0.10,
    }

    @property
    def total(self) -> float:
        return round(
            self.seiri.score    * self.WEIGHTS["seiri"]    +
            self.seiton.score   * self.WEIGHTS["seiton"]   +
            self.seiso.score    * self.WEIGHTS["seiso"]    +
            self.seiketsu.score * self.WEIGHTS["seiketsu"] +
            self.shitsuke.score * self.WEIGHTS["shitsuke"],
            1
        )

    @property
    def grade(self) -> str:
        t = self.total
        if t >= 90: return "A"
        if t >= 80: return "B"
        if t >= 70: return "C"
        if t >= 60: return "D"
        return "F"

    @property
    def risk_level(self) -> str:
        t = self.total
        if t >= 80: return "low"
        if t >= 60: return "medium"
        return "high"


class ScanReport(BaseModel):
    """
    Tek bir tarama oturumunun tam raporu.
    Dashboard ve raporlama katmanı bu modeli kullanır.
    """
    scan_id:            str
    target_folder:      Path
    started_at:         datetime
    completed_at:       datetime
    duration_ms:        int

    # Sayılar
    total_files:        int
    total_folders:      int
    total_size_bytes:   int
    duplicate_count:    int   = 0
    empty_folder_count: int   = 0
    old_file_count:     int   = 0     # 180+ gün
    temp_file_count:    int   = 0
    large_file_count:   int   = 0     # 500MB+
    naming_issue_count: int   = 0

    # Kazanç
    reclaimable_bytes:  int   = 0
    recommendations:    int   = 0

    # Puan
    score:              D5SScore
    previous_score:     float | None = None   # trend için

    @property
    def total_size_gb(self) -> float:
        return round(self.total_size_bytes / 1_073_741_824, 3)

    @property
    def reclaimable_mb(self) -> float:
        return round(self.reclaimable_bytes / 1_048_576, 1)

    @property
    def score_delta(self) -> float | None:
        if self.previous_score is None:
            return None
        return round(self.score.total - self.previous_score, 1)
