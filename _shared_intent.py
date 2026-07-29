"""
tools/d5s/_shared_intent.py
Kullanıcının serbest metin isteğini LLM ile yapılandırılmış JSON'a çevirir.

Bu, D5S'in KENDİ kopyasıdır — folder_5s'in de aynı isimde ayrı bir kopyası
var. Repo'lar tamamen bağımsız olduğu için (AGENTS.md Madde 1) çapraz-repo
bir "shared" pakete bağımlı olunmaz; kod tekrarı, repo bağımsızlığının
kabul edilebilir maliyetidir. İçerik değişirse iki kopya birbirinden
bağımsız evrilebilir — bu bilinçli bir tercih, senkronize tutulması
gereken bir borç değil.
"""
from __future__ import annotations
import json

SYSTEM_PROMPT = """
Sen bir dosya organizasyon asistanısın. Kullanıcının isteğini analiz edip SADECE JSON döndür.
Başka hiçbir şey yazma.

Format:
{
  "kurallar": {
    "stale": true/false,
    "unused": true/false,
    "temp": true/false,
    "empty_folders": true/false,
    "installer": true/false,
    "archive": true/false,
    "iso": true/false,
    "log": true/false,
    "cache": true/false,
    "large": true/false,
    "version": true/false,
    "duplicate": false,
    "topic": true/false,
    "category": true/false
  },
  "topic_map": {"konu": ["kelime1", "kelime2"]} veya null,
  "aciklama": "1-2 cümle Türkçe özet"
}
"""


def parse_istek(istek: str, llm_complete) -> dict:
    """İsteği LLM ile parse eder. llm_complete: core'un llm.complete fonksiyonu."""
    raw = llm_complete(istek, system=SYSTEM_PROMPT, json_mode=True)
    return json.loads(raw)


def ozet_llm(ozet: dict, llm_complete) -> str:
    """Faz/kural sayımlarını 2 cümlelik sade Türkçe özete çevirir."""
    try:
        return llm_complete(
            f"Dosya analizi: {json.dumps(ozet, ensure_ascii=False)}. "
            "2 cümle, sade Türkçe, teknik detay yok."
        ).strip()
    except Exception:
        return " | ".join(f"{k}: {v} öğe" for k, v in ozet.items())
