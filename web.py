"""
tools/d5s/web.py
core/api.py'nin çağırdığı TEK yüzey — AGENTS.md Madde 2 sözleşmesi.
Plan, PlanItem, ScanResult gibi iç nesneler bu modülün dışına sızmaz;
core sadece JSON-serileştirilebilir dict görür.
"""
from __future__ import annotations
import json
import uuid
from pathlib import Path

from fastapi import HTTPException

from . import (
    scan as _scan,
    analyze as _analyze,
    execute as _execute,
    get_score as _get_score,
    generate_report as _generate_report,
    rollback_session as _rollback_session,
    list_sessions as _list_sessions,
)
from ._shared_intent import parse_istek, ozet_llm

ETIKETLER = {
    "seiri":    "Seiri (Ayıklama)",
    "seiton":   "Seiton (Düzenleme)",
    "seiso":    "Seiso (Temizlik)",
    "seiketsu": "Seiketsu (Standart)",
}

_plan_store: dict[str, tuple] = {}   # plan_id -> (plan, scan_result)


def _faz_skoru(ps):
    return {"skor": ps.score, "sorun": ps.issues_found, "notlar": ps.notes}


def web_analyze(istek: str, klasor: str, llm_complete) -> dict:
    klasor_p = Path(klasor)
    if not klasor_p.exists():
        if klasor.startswith(("C:\\", "C:/")):
            raise ValueError(
                "Docker içinde Windows path görünmüyor. "
                "/data altındaki bir klasör seçin."
            )
        raise ValueError(f"Klasör bulunamadı: {klasor}")

    try:
        params = parse_istek(istek, llm_complete)
    except RuntimeError as e:
        # llm.py'den gelen kullanıcı-dostu bağlantı/zaman aşımı mesajı —
        # burada yakalanmazsa Starlette'e sızıp JSON olmayan düz bir
        # "Internal Server Error" sayfası döner (frontend'de "Unexpected
        # token" hatası olarak görünür).
        raise HTTPException(503, str(e))
    except json.JSONDecodeError:
        raise HTTPException(502, "LLM geçerli JSON döndürmedi. Modeli veya isteği değiştirip tekrar deneyin.")
    aciklama  = params.get("aciklama", "")
    config    = params.get("kurallar", {})
    topic_map = params.get("topic_map")

    scan_result = _scan(klasor_p)
    plan        = _analyze(scan_result, config=config,
                           topic_map=topic_map if config.get("topic") else None)

    if not plan.items:
        return {"bos": True, "mesaj": "Önerilen aksiyon yok — klasör zaten düzenli."}

    score        = _get_score(scan_result, plan)
    ozet         = plan.summary_by_phase()
    aciklama_llm = ozet_llm(ozet, llm_complete) if ozet else aciklama

    plan_id = str(uuid.uuid4())
    _plan_store[plan_id] = (plan, scan_result)

    return {
        "bos":      False,
        "plan_id":  plan_id,
        "aciklama": aciklama_llm,
        "score": {
            "total": score.total, "grade": score.grade, "risk": score.risk_level,
            "fazlar": {
                "seiri":    _faz_skoru(score.seiri),
                "seiton":   _faz_skoru(score.seiton),
                "seiso":    _faz_skoru(score.seiso),
                "seiketsu": _faz_skoru(score.seiketsu),
                "shitsuke": _faz_skoru(score.shitsuke),
            },
        },
        "ozet": [
            {"kural": k, "etiket": ETIKETLER.get(k, k.upper()), "sayi": v}
            for k, v in ozet.items()
        ],
        "toplam": sum(ozet.values()),
        "items": [
            {
                "id":          i.id,
                "phase":       i.phase.value,
                "faz_etiket":  ETIKETLER.get(i.phase.value, i.phase.value),
                "action":      i.action.value,
                "source":      str(i.source),
                "destination": str(i.destination) if i.destination else None,
                "reason":      i.reason,
                "risk":        i.risk.value,
                "confidence":  i.confidence,
                "size_bytes":  i.size_bytes,
            }
            for i in plan.items
        ],
    }


def web_execute(plan_id: str, approved_ids: list[str] | None) -> dict:
    entry = _plan_store.get(plan_id)
    if not entry:
        raise KeyError(f"Plan bulunamadı veya süresi doldu: {plan_id}")
    plan, scan_result = entry

    entries, errors = _execute(plan, approved_ids=approved_ids)
    del _plan_store[plan_id]

    return {
        "uygulanan":  len([e for e in entries if e.status.value == "success"]),
        "basarisiz":  errors,
        "uyarilar":   [],
        "session_id": entries[0].session_id if entries else None,
    }


def web_rollback(klasor: str, session_id: str | None) -> dict:
    """
    SQLite audit log'undan geri alır. Process/Docker restart'ından,
    tarayıcı sekmesi kapanmasından bağımsız çalışır — kayıt kalıcıdır.
    session_id verilmezse, klasörün en son D5S oturumu otomatik bulunur.
    """
    if not session_id and klasor:
        sessions = _list_sessions(target_folder=klasor, limit=1)
        if sessions:
            session_id = sessions[0]["id"]

    if not session_id:
        return {
            "hatalar":   ["Bu klasör için geri alınacak D5S işlemi bulunamadı."],
            "basarili":  False,
            "session_id": None,
        }

    rb_entries, errors = _rollback_session(session_id)
    return {
        "hatalar":     errors,
        "basarili":    len(errors) == 0,
        "geri_alinan": len(rb_entries),
        "session_id":  session_id,
    }


def web_report(plan_id: str, format: str = "html") -> str:
    entry = _plan_store.get(plan_id)
    if not entry:
        raise KeyError(f"Plan bulunamadı: {plan_id}")
    plan, scan_result = entry
    score = _get_score(scan_result, plan)
    return _generate_report(scan_result, plan, score, format=format)


def web_history(klasor: str, limit: int = 5) -> dict:
    sessions = _list_sessions(target_folder=klasor, limit=limit)
    return {
        "oturumlar": [
            {
                "session_id": s["id"],
                "baslangic":  s["started_at"].isoformat() if s["started_at"] else None,
                "basarili":   s["successful"],
                "basarisiz":  s["failed"],
            }
            for s in sessions
        ]
    }
