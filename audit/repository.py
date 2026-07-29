"""
tools/d5s/audit/repository.py
Audit CRUD — tüm veritabanı yazma/okuma işlemleri burada.
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, desc
from sqlalchemy.engine import Engine

from ..contracts.audit import AuditEntry, ScanSession, AuditStatus
from ..contracts.report import ScanReport
from .database import audit_entries, scan_sessions, scan_reports, init_db


class AuditRepository:
    """
    Audit log'u için tek erişim noktası.
    Engine dışarıdan inject edilir — test edilebilirlik için.
    """

    def __init__(self, engine: Engine | None = None):
        from .database import get_engine
        self._engine = engine or get_engine()
        init_db(self._engine)

    # ── Session ──────────────────────────────────────────────────────────────

    def create_session(self, session: ScanSession) -> None:
        with self._engine.begin() as conn:
            conn.execute(scan_sessions.insert().values(
                id            = session.id,
                target_folder = str(session.target_folder),
                started_at    = session.started_at,
                completed_at  = session.completed_at,
                total_files   = session.total_files,
                total_folders = 0,
                total_actions = session.total_actions,
                successful    = session.successful,
                failed        = session.failed,
                score_before  = session.score_before,
                score_after   = session.score_after,
            ))

    def complete_session(
        self,
        session_id: str,
        successful: int,
        failed: int,
        score_after: float | None = None,
    ) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                scan_sessions.update()
                .where(scan_sessions.c.id == session_id)
                .values(
                    completed_at = datetime.now(),
                    successful   = successful,
                    failed       = failed,
                    score_after  = score_after,
                )
            )

    # ── Audit Entries ─────────────────────────────────────────────────────────

    def save_entries(self, entries: list[AuditEntry]) -> None:
        if not entries:
            return
        with self._engine.begin() as conn:
            conn.execute(audit_entries.insert(), [
                dict(
                    id             = e.id,
                    session_id     = e.session_id,
                    plan_item_id   = e.plan_item_id,
                    ts             = e.ts,
                    action         = e.action,
                    src            = str(e.src),
                    dst            = str(e.dst) if e.dst else None,
                    new_name       = e.new_name,
                    status         = e.status.value,
                    error_message  = e.error_message,
                    rule_version   = e.rule_version,
                    llm_suggested  = e.llm_suggested,
                    user_approved  = e.user_approved,
                    rolled_back    = e.rolled_back,
                    rolled_back_at = e.rolled_back_at,
                )
                for e in entries
            ])

    def mark_rolled_back(self, entry_ids: list[str]) -> None:
        if not entry_ids:
            return
        with self._engine.begin() as conn:
            conn.execute(
                audit_entries.update()
                .where(audit_entries.c.id.in_(entry_ids))
                .values(rolled_back=True, rolled_back_at=datetime.now())
            )

    def get_session_entries(self, session_id: str) -> list[dict]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(audit_entries)
                .where(audit_entries.c.session_id == session_id)
                .order_by(audit_entries.c.ts)
            ).fetchall()
            return [dict(r._mapping) for r in rows]

    def get_recent_entries(self, limit: int = 50) -> list[dict]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(audit_entries)
                .order_by(desc(audit_entries.c.ts))
                .limit(limit)
            ).fetchall()
            return [dict(r._mapping) for r in rows]

    def get_recent_sessions(self, target_folder: str | None = None, limit: int = 20) -> list[dict]:
        """Geçmiş oturumları döner — GERİ AL için hangi işlemin geri alınacağını bulmakta kullanılır."""
        with self._engine.connect() as conn:
            q = select(scan_sessions)
            if target_folder:
                q = q.where(scan_sessions.c.target_folder == target_folder)
            q = q.order_by(desc(scan_sessions.c.started_at)).limit(limit)
            rows = conn.execute(q).fetchall()
            return [dict(r._mapping) for r in rows]

    # ── Scan Reports ──────────────────────────────────────────────────────────

    def save_report(self, report: ScanReport) -> None:
        with self._engine.begin() as conn:
            conn.execute(scan_reports.insert().values(
                scan_id            = report.scan_id,
                target_folder      = str(report.target_folder),
                started_at         = report.started_at,
                completed_at       = report.completed_at,
                duration_ms        = report.duration_ms,
                total_files        = report.total_files,
                total_folders      = report.total_folders,
                total_size_bytes   = report.total_size_bytes,
                duplicate_count    = report.duplicate_count,
                empty_folder_count = report.empty_folder_count,
                old_file_count     = report.old_file_count,
                temp_file_count    = report.temp_file_count,
                large_file_count   = report.large_file_count,
                reclaimable_bytes  = report.reclaimable_bytes,
                recommendations    = report.recommendations,
                score_total        = report.score.total,
                score_seiri        = report.score.seiri.score,
                score_seiton       = report.score.seiton.score,
                score_seiso        = report.score.seiso.score,
                score_seiketsu     = report.score.seiketsu.score,
                score_shitsuke     = report.score.shitsuke.score,
                score_grade        = report.score.grade,
                previous_score     = report.previous_score,
            ))

    def get_last_score(self, target_folder: str) -> float | None:
        """Bir klasörün son tarama puanını döner — Shitsuke trendi için."""
        with self._engine.connect() as conn:
            row = conn.execute(
                select(scan_reports.c.score_total)
                .where(scan_reports.c.target_folder == target_folder)
                .order_by(desc(scan_reports.c.started_at))
                .limit(1)
            ).fetchone()
            return float(row[0]) if row else None

    def get_scan_history(self, target_folder: str, limit: int = 10) -> list[dict]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(scan_reports)
                .where(scan_reports.c.target_folder == target_folder)
                .order_by(desc(scan_reports.c.started_at))
                .limit(limit)
            ).fetchall()
            return [dict(r._mapping) for r in rows]
