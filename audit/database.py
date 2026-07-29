"""
tools/d5s/audit/database.py
SQLite şeması ve bağlantı yönetimi.
SQLAlchemy Core kullanır (ORM değil — hafif, bağımlılık az).
"""

from __future__ import annotations
import os
from pathlib import Path
from datetime import datetime

from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    String, Integer, Float, Boolean, DateTime, Text,
    event,
)
from sqlalchemy.engine import Engine

# DB dosyası: tools/d5s/audit/ içinde veya env variable ile override
_DEFAULT_DB = Path(__file__).parent / "d5s_audit.sqlite"
_DB_PATH    = Path(os.getenv("D5S_DB_PATH", str(_DEFAULT_DB)))

metadata = MetaData()

# ── Tablolar ─────────────────────────────────────────────────────────────────

scan_sessions = Table(
    "scan_sessions", metadata,
    Column("id",             String(36),  primary_key=True),
    Column("target_folder",  Text,        nullable=False),
    Column("started_at",     DateTime,    nullable=False),
    Column("completed_at",   DateTime,    nullable=True),
    Column("total_files",    Integer,     default=0),
    Column("total_folders",  Integer,     default=0),
    Column("total_actions",  Integer,     default=0),
    Column("successful",     Integer,     default=0),
    Column("failed",         Integer,     default=0),
    Column("score_before",   Float,       nullable=True),
    Column("score_after",    Float,       nullable=True),
)

audit_entries = Table(
    "audit_entries", metadata,
    Column("id",             String(36),  primary_key=True),
    Column("session_id",     String(36),  nullable=False, index=True),
    Column("plan_item_id",   String(36),  nullable=False),
    Column("ts",             DateTime,    nullable=False),
    Column("action",         String(32),  nullable=False),
    Column("src",            Text,        nullable=False),
    Column("dst",            Text,        nullable=True),
    Column("new_name",       String(255), nullable=True),
    Column("status",         String(16),  nullable=False),
    Column("error_message",  Text,        nullable=True),
    Column("rule_version",   String(32),  nullable=False),
    Column("llm_suggested",  Boolean,     default=True),
    Column("user_approved",  Boolean,     default=True),
    Column("rolled_back",    Boolean,     default=False),
    Column("rolled_back_at", DateTime,    nullable=True),
)

scan_reports = Table(
    "scan_reports", metadata,
    Column("scan_id",            String(36),  primary_key=True),
    Column("target_folder",      Text,        nullable=False),
    Column("started_at",         DateTime,    nullable=False),
    Column("completed_at",       DateTime,    nullable=False),
    Column("duration_ms",        Integer,     nullable=False),
    Column("total_files",        Integer,     default=0),
    Column("total_folders",      Integer,     default=0),
    Column("total_size_bytes",   Integer,     default=0),
    Column("duplicate_count",    Integer,     default=0),
    Column("empty_folder_count", Integer,     default=0),
    Column("old_file_count",     Integer,     default=0),
    Column("temp_file_count",    Integer,     default=0),
    Column("large_file_count",   Integer,     default=0),
    Column("reclaimable_bytes",  Integer,     default=0),
    Column("recommendations",    Integer,     default=0),
    # 5S puanları
    Column("score_total",        Float,       nullable=True),
    Column("score_seiri",        Float,       nullable=True),
    Column("score_seiton",       Float,       nullable=True),
    Column("score_seiso",        Float,       nullable=True),
    Column("score_seiketsu",     Float,       nullable=True),
    Column("score_shitsuke",     Float,       nullable=True),
    Column("score_grade",        String(2),   nullable=True),
    Column("previous_score",     Float,       nullable=True),
)


def _enable_wal(dbapi_conn, connection_record):
    """WAL modu — eş zamanlı okuma/yazma için."""
    dbapi_conn.execute("PRAGMA journal_mode=WAL")
    dbapi_conn.execute("PRAGMA foreign_keys=ON")


def get_engine(db_path: Path | None = None) -> Engine:
    """Engine singleton — uygulama boyunca tek instance."""
    path = db_path or _DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}", echo=False)
    event.listen(engine, "connect", _enable_wal)
    return engine


def init_db(engine: Engine | None = None) -> Engine:
    """Tabloları oluşturur (varsa dokunmaz)."""
    eng = engine or get_engine()
    metadata.create_all(eng)
    return eng
