"""
tools/d5s/__init__.py
D5S public API.
"""

from __future__ import annotations
import uuid
from datetime import datetime
from pathlib import Path

from .contracts import (
    Plan, PlanItem, ScanResult, ScanReport,
    D5SScore, AuditEntry, AuditStatus, ScanSession,
)
from .scanner   import scan as _scan
from .engine    import run_seiri, run_seiton, run_seiso, calculate_score
from .executor  import dry_run as _dry_run, execute as _execute
from .executor  import rollback as _rollback
from .audit     import AuditRepository
from .audit.database import get_engine as _get_engine
from .reporting import generate_html, generate_json, generate_csv


def _deduplicate(items: list[PlanItem]) -> list[PlanItem]:
    seen: dict[str, PlanItem] = {}
    for item in items:
        key = str(item.source)
        if key not in seen or item.confidence > seen[key].confidence:
            seen[key] = item
    return list(seen.values())


def _make_repo(db_path=None):
    engine = _get_engine(Path(db_path)) if db_path else _get_engine()
    return AuditRepository(engine)


def scan(target_folder, compute_hash=False, progress_cb=None):
    return _scan(Path(target_folder), compute_hash=compute_hash, progress_cb=progress_cb)


def analyze(scan_result, archive_root=None, topic_map=None, config=None):
    archive = Path(archive_root) if archive_root else scan_result.root / "_arsiv"
    cfg     = config or {}
    items   = []
    items  += run_seiri(scan_result.files, scan_result.folders, archive, cfg)
    items  += run_seiton(scan_result.files, scan_result.root, archive, topic_map, cfg)
    items  += run_seiso(scan_result.files, scan_result.folders, cfg)
    items   = _deduplicate(items)
    return Plan(target_folder=scan_result.root, archive_root=archive, items=items)


def dry_run(plan):
    return _dry_run(plan)


def execute(plan, approved_ids=None, db_path=None):
    session_id = str(uuid.uuid4())
    repo       = _make_repo(db_path)
    session    = ScanSession(id=session_id, target_folder=plan.target_folder, started_at=datetime.now())
    repo.create_session(session)
    entries, errors = _execute(plan, session_id=session_id, approved_ids=approved_ids)
    repo.save_entries(entries)
    repo.complete_session(
        session_id=session_id,
        successful=sum(1 for e in entries if e.status.value == "success"),
        failed=len(errors),
    )
    return entries, errors


def rollback(entries, db_path=None):
    rb_entries, errors = _rollback(entries)
    if rb_entries:
        repo = _make_repo(db_path)
        repo.mark_rolled_back([e.plan_item_id for e in rb_entries])
        repo.save_entries(rb_entries)
    return rb_entries, errors


def _row_to_entry(row: dict) -> AuditEntry:
    """SQLite'tan okunan audit satırını AuditEntry nesnesine çevirir."""
    return AuditEntry(
        id             = row["id"],
        session_id     = row["session_id"],
        plan_item_id   = row["plan_item_id"],
        ts             = row["ts"],
        action         = row["action"],
        src            = Path(row["src"]),
        dst            = Path(row["dst"]) if row["dst"] else None,
        new_name       = row["new_name"],
        status         = AuditStatus(row["status"]),
        error_message  = row["error_message"],
        rule_version   = row["rule_version"],
        llm_suggested  = row["llm_suggested"],
        user_approved  = row["user_approved"],
        rolled_back    = row["rolled_back"],
        rolled_back_at = row["rolled_back_at"],
    )


def rollback_session(session_id: str, db_path=None):
    """
    Bir oturumu SQLite audit log'undan okuyup geri alır.
    Bellekte (process içi) hiçbir şeye ihtiyaç duymaz — Docker restart'tan,
    tarayıcı sekmesi kapanmasından sonra bile çalışır. Kayıt kalıcıdır.
    """
    repo = _make_repo(db_path)
    rows = repo.get_session_entries(session_id)
    if not rows:
        return [], [f"Oturum bulunamadı: {session_id}"]
    entries = [_row_to_entry(r) for r in rows]
    rb_entries, errors = _rollback(entries)
    if rb_entries:
        repo.mark_rolled_back([e.plan_item_id for e in rb_entries])
        repo.save_entries(rb_entries)
    return rb_entries, errors


def list_sessions(target_folder=None, limit=20, db_path=None):
    """Bir klasörün (veya tümünün) geçmiş D5S oturumlarını döner — en yeni önce."""
    repo = _make_repo(db_path)
    tf = str(Path(target_folder)) if target_folder else None
    return repo.get_recent_sessions(target_folder=tf, limit=limit)


def get_score(scan_result, plan, db_path=None):
    repo     = _make_repo(db_path)
    previous = repo.get_last_score(str(scan_result.root))
    return calculate_score(scan_result, plan.items, previous_score=previous)


def generate_report(scan_result, plan, score, format="html", output_path=None):
    report = ScanReport(
        scan_id            = str(uuid.uuid4()),
        target_folder      = scan_result.root,
        started_at         = scan_result.scanned_at,
        completed_at       = datetime.now(),
        duration_ms        = scan_result.scan_duration_ms,
        total_files        = scan_result.total_files,
        total_folders      = scan_result.total_folders,
        total_size_bytes   = scan_result.total_size_bytes,
        duplicate_count    = sum(1 for i in plan.items if "sha-256" in i.reason.lower()),
        empty_folder_count = sum(1 for i in plan.items if "boş" in i.reason.lower()),
        old_file_count     = sum(1 for i in plan.items if "gündür değiştirilmedi" in i.reason),
        temp_file_count    = sum(1 for i in plan.items if "geçici" in i.reason.lower()),
        large_file_count   = sum(1 for i in plan.items if "büyük" in i.reason.lower()),
        reclaimable_bytes  = plan.total_reclaimable_bytes,
        recommendations    = len(plan.items),
        score              = score,
    )
    out = Path(output_path) if output_path else None
    if format == "json":
        return generate_json(report, plan, out)
    elif format == "csv":
        return generate_csv(plan, out)
    return generate_html(report, plan, out)


# web.py bu modüldeki scan/analyze/execute/get_score/rollback_session/
# list_sessions/generate_report'a bağımlı — bu yüzden import en sonda
# olmak zorunda (circular import önlemi).
from .web import web_analyze, web_execute, web_rollback, web_report, web_history  # noqa: E402
