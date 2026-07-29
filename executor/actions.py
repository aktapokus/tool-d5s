"""
tools/d5s/executor/actions.py

Dosya sistemi üzerinde işlem yapan TEK bileşen.
Manifesto Madde 6: LLM buraya hiçbir şekilde erişemez.
Manifesto Madde 4: Her işlem önce dry_run, sonra kullanıcı onayı, sonra execute.

Her aksiyon:
1. İşlemi yapar
2. AuditEntry üretir
3. Hata durumunda exception fırlatır (rollback için)
"""

from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path

from ..contracts.plan import Plan, PlanItem, ActionType
from ..contracts.audit import AuditEntry, AuditStatus


# ── Dry Run ──────────────────────────────────────────────────────────────────

def dry_run(plan: Plan) -> list[str]:
    """
    Plan'ı simüle eder. Dosya sistemine dokunmaz.
    Olası sorunları (çakışma, eksik source) önceden tespit eder.
    Döner: uyarı listesi (boş = sorun yok)
    """
    warnings: list[str] = []
    seen_destinations: dict[Path, Path] = {}

    for item in plan.items:
        if item.action == ActionType.NO_ACTION:
            continue

        # Source var mı?
        if not item.source.exists():
            warnings.append(f"Kaynak bulunamadı: {item.source}")
            continue

        # Destination çakışması
        if item.action == ActionType.MOVE and item.destination:
            if item.destination in seen_destinations:
                warnings.append(
                    f"Hedef çakışması: '{item.source.name}' ve "
                    f"'{seen_destinations[item.destination].name}' "
                    f"→ {item.destination}"
                )
            seen_destinations[item.destination] = item.source

            # Hedef zaten var mı?
            if item.destination.exists():
                warnings.append(
                    f"Hedef zaten mevcut: {item.destination}"
                )

        # Readonly klasör silme
        if item.action == ActionType.DELETE and item.source.is_dir():
            if any(item.source.iterdir()):
                warnings.append(
                    f"Boş olmayan klasör silinmeye çalışılıyor: {item.source}"
                )

    return warnings


# ── Tek Aksiyon Uygulayıcılar ────────────────────────────────────────────────

def _do_move(item: PlanItem) -> None:
    if not item.destination:
        raise ValueError(f"MOVE aksiyonu için destination zorunlu: {item.source}")
    item.destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(item.source), str(item.destination))


def _do_copy(item: PlanItem) -> None:
    if not item.destination:
        raise ValueError(f"COPY aksiyonu için destination zorunlu: {item.source}")
    item.destination.parent.mkdir(parents=True, exist_ok=True)
    if item.source.is_dir():
        shutil.copytree(str(item.source), str(item.destination))
    else:
        shutil.copy2(str(item.source), str(item.destination))


def _do_delete(item: PlanItem) -> None:
    if item.source.is_dir():
        if any(item.source.iterdir()):
            raise ValueError(f"Boş olmayan klasör silinemez: {item.source}")
        item.source.rmdir()
    else:
        item.source.unlink()


def _do_rename(item: PlanItem) -> None:
    if not item.new_name:
        raise ValueError(f"RENAME aksiyonu için new_name zorunlu: {item.source}")
    dest = item.source.parent / item.new_name
    item.source.rename(dest)


def _do_create_folder(item: PlanItem) -> None:
    item.source.mkdir(parents=True, exist_ok=True)


# ── Execute ───────────────────────────────────────────────────────────────────

def execute(
    plan: Plan,
    session_id: str,
    approved_ids: list[str] | None = None,
) -> tuple[list[AuditEntry], list[str]]:
    """
    Onaylanmış plan öğelerini uygular.
    approved_ids: sadece bu id'leri uygula (None = hepsini uygula)
    Döner: (başarılı AuditEntry listesi, hata mesajları)
    """
    items_to_run = [
        i for i in plan.items
        if (approved_ids is None or i.id in approved_ids)
        and i.action != ActionType.NO_ACTION
    ]

    entries: list[AuditEntry] = []
    errors:  list[str]        = []

    ACTION_MAP = {
        ActionType.MOVE:          _do_move,
        ActionType.COPY:          _do_copy,
        ActionType.DELETE:        _do_delete,
        ActionType.RENAME:        _do_rename,
        ActionType.CREATE_FOLDER: _do_create_folder,
    }

    for item in items_to_run:
        handler = ACTION_MAP.get(item.action)
        if not handler:
            continue

        try:
            handler(item)
            entries.append(AuditEntry(
                session_id    = session_id,
                plan_item_id  = item.id,
                action        = item.action.value,
                src           = item.source,
                dst           = item.destination,
                new_name      = item.new_name,
                status        = AuditStatus.SUCCESS,
                rule_version  = plan.rule_version,
                llm_suggested = True,
                user_approved = True,
            ))

        except Exception as exc:
            errors.append(f"{item.source.name}: {exc}")
            entries.append(AuditEntry(
                session_id    = session_id,
                plan_item_id  = item.id,
                action        = item.action.value,
                src           = item.source,
                dst           = item.destination,
                status        = AuditStatus.FAILED,
                error_message = str(exc),
                rule_version  = plan.rule_version,
                llm_suggested = True,
                user_approved = True,
            ))

    return entries, errors
