"""
tools/d5s/contracts/plan.py
Analiz → Execute arası köprü. Engine üretir, Executor uygular.
Kullanıcı onayı bu objeyi temel alır.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ActionType(str, Enum):
    MOVE            = "move"
    COPY            = "copy"
    DELETE          = "delete"
    RENAME          = "rename"
    CREATE_FOLDER   = "create_folder"
    COMPRESS        = "compress"
    NO_ACTION       = "no_action"    # bilgi amaçlı, işlem yok


class RiskLevel(str, Enum):
    LOW     = "low"      # tamamen geri alınabilir
    MEDIUM  = "medium"   # geri alınabilir ama dikkat
    HIGH    = "high"     # geri alınamaz veya yüksek etki


class S5Phase(str, Enum):
    SEIRI    = "seiri"      # Sort
    SEITON   = "seiton"     # Set in order
    SEISO    = "seiso"      # Shine
    SEIKETSU = "seiketsu"   # Standardize
    SHITSUKE = "shitsuke"   # Sustain


class PlanItem(BaseModel):
    """Tek bir önerilen aksiyon. Plan'ın atomik birimi."""
    id:             str  = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    phase:          S5Phase
    action:         ActionType
    source:         Path
    destination:    Optional[Path]   = None
    new_name:       Optional[str]    = None   # RENAME için
    reason:         str                        # kullanıcıya gösterilecek
    confidence:     float = Field(ge=0.0, le=1.0, default=1.0)
    risk:           RiskLevel = RiskLevel.LOW
    size_bytes:     int = 0
    reversible:     bool = True

    @property
    def is_destructive(self) -> bool:
        return self.action == ActionType.DELETE and not self.reversible


class Plan(BaseModel):
    """
    Tek bir analiz oturumunun tüm önerilerini içerir.
    Engine üretir → kullanıcıya sunulur → onaylananlar Executor'a geçer.
    Bu obje hiçbir şekilde dosya sistemine dokunmaz.
    """
    id:             str  = Field(default_factory=lambda: str(uuid.uuid4()))
    target_folder:  Path
    archive_root:   Path
    rule_version:   str  = "0.1.0"
    items:          list[PlanItem] = []
    generated_at:   datetime = Field(default_factory=datetime.now)

    def summary_by_phase(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.items:
            counts[item.phase.value] = counts.get(item.phase.value, 0) + 1
        return counts

    def summary_by_action(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.items:
            counts[item.action.value] = counts.get(item.action.value, 0) + 1
        return counts

    def filter_by_phase(self, phase: S5Phase) -> list[PlanItem]:
        return [i for i in self.items if i.phase == phase]

    def high_risk_items(self) -> list[PlanItem]:
        return [i for i in self.items if i.risk == RiskLevel.HIGH]

    @property
    def total_reclaimable_bytes(self) -> int:
        return sum(
            i.size_bytes for i in self.items
            if i.action in (ActionType.DELETE, ActionType.COMPRESS)
        )


class DryRunReport(BaseModel):
    """dry_run() çıktısı — hiçbir dosyaya dokunulmadığının kanıtı."""
    plan:           Plan
    simulated_ok:   bool
    warnings:       list[str] = []
    destination_conflicts: list[str] = []   # aynı hedefe giden iki dosya
