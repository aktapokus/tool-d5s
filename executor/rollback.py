"""
tools/d5s/executor/rollback.py

Geri alma mekanizması.
AuditEntry listesini okur, MOVE işlemlerini tersine çevirir.
DELETE geri alınamaz — bu kontratta açıkça belirtilir.
"""

from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path

from ..contracts.audit import AuditEntry, AuditStatus


def rollback(
    entries: list[AuditEntry],
    since: datetime | None = None,
) -> tuple[list[AuditEntry], list[str]]:
    """
    Verilen AuditEntry listesini tersten uygular.
    since: sadece bu tarihten sonraki işlemleri geri al.
    Döner: (rollback AuditEntry listesi, hata mesajları)
    """
    rollback_entries: list[AuditEntry] = []
    errors: list[str] = []

    # En yeniden en eskiye doğru işle
    candidates = [
        e for e in reversed(entries)
        if e.status == AuditStatus.SUCCESS
        and not e.rolled_back
        and (since is None or e.ts >= since)
    ]

    for entry in candidates:
        if entry.action == "move":
            try:
                src = entry.dst   # taşınan yer (geri dönecek yer)
                dst = entry.src   # orijinal yer
                if src and src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                    entry.rolled_back    = True
                    entry.rolled_back_at = datetime.now()
                    rollback_entries.append(AuditEntry(
                        session_id   = entry.session_id,
                        plan_item_id = entry.plan_item_id,
                        action       = "rollback_move",
                        src          = src,
                        dst          = dst,
                        status       = AuditStatus.SUCCESS,
                        rule_version = entry.rule_version,
                        llm_suggested = False,
                        user_approved = True,
                    ))
                else:
                    errors.append(f"Geri alınamadı — dosya bulunamadı: {src}")
            except Exception as exc:
                errors.append(f"Geri alma hatası: {exc}")

        elif entry.action == "delete":
            errors.append(
                f"DELETE geri alınamaz: {entry.src} "
                f"(silinme zamanı: {entry.ts:%Y-%m-%d %H:%M})"
            )

        elif entry.action == "rename":
            try:
                if entry.new_name and entry.src.exists() is False:
                    # rename sonrası dosya new_name ile src.parent'ta
                    current = entry.src.parent / entry.new_name
                    if current.exists():
                        current.rename(entry.src)
                        entry.rolled_back = True
                        rollback_entries.append(AuditEntry(
                            session_id   = entry.session_id,
                            plan_item_id = entry.plan_item_id,
                            action       = "rollback_rename",
                            src          = current,
                            dst          = entry.src,
                            status       = AuditStatus.SUCCESS,
                            rule_version = entry.rule_version,
                            llm_suggested = False,
                            user_approved = True,
                        ))
            except Exception as exc:
                errors.append(f"Rename geri alma hatası: {exc}")

    return rollback_entries, errors
