"""
tools/d5s/contracts/audit.py
ISO9001 mantığında audit log modelleri.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class AuditStatus(str, Enum):
    SUCCESS  = "success"
    FAILED   = "failed"
    SKIPPED  = "skipped"
    ROLLEDBACK = "rolledback"


class AuditEntry(BaseModel):
    """
    Tek bir dosya işleminin tam kaydı.
    SQLite'a yazılır, asla silinemez (soft-delete yok).
    """
    id:             str  = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id:     str                          # hangi scan oturumu
    plan_item_id:   str                          # hangi PlanItem
    ts:             datetime = Field(default_factory=datetime.now)

    action:         str                          # ActionType.value
    src:            Path
    dst:            Optional[Path]  = None
    new_name:       Optional[str]   = None

    status:         AuditStatus     = AuditStatus.SUCCESS
    error_message:  Optional[str]   = None

    # ISO9001 alanları
    rule_version:   str
    llm_suggested:  bool = True                  # LLM mi önerdi?
    user_approved:  bool = True                  # kullanıcı onayladı mı?
    rolled_back:    bool = False
    rolled_back_at: Optional[datetime] = None


class ScanSession(BaseModel):
    """Tek bir tarama oturumu kaydı."""
    id:             str  = Field(default_factory=lambda: str(uuid.uuid4()))
    target_folder:  Path
    started_at:     datetime = Field(default_factory=datetime.now)
    completed_at:   Optional[datetime] = None
    total_files:    int  = 0
    total_actions:  int  = 0
    successful:     int  = 0
    failed:         int  = 0
    score_before:   Optional[float] = None
    score_after:    Optional[float] = None
