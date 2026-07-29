# Digital 5S (D5S)

Lean manufacturing'in 5S metodolojisini (Seiri/Seiton/Seiso/Seiketsu/
Shitsuke) dosya sistemine uygulayan Aktapokus Tool'u. `core.*`
namespace, Faz 1 (reversible/IT-domain).

## Ne yapar

Bir klasörü tarar, LLM'in yorumladığı serbest-metin isteğe göre
öneri planı çıkarır (sil/taşı/yeniden adlandır), kullanıcı onayı
sonrası uygular. Her işlem SQLite audit log'una yazılır — kalıcı,
Docker restart'tan bağımsız geri alma (`rollback`) buradan gelir.
5S skoru (her faz için 0-100) ve HTML/JSON/CSV rapor üretir.

## Kurulum

1. Bu repo'yu klonlayın.
2. Dosyaları çalışan bir Aktapokus core kurulumunun `tools/d5s/`
   klasörüne kopyalayın (veya `setup.bat` varsa onu çalıştırın).
3. `docker compose restart app`

## Bağımlılıklar

- `pydantic>=2.0`
- `sqlalchemy>=2.0` (audit log için)

Bu ikisi core'un `requirements.txt`'ine dahil edilmelidir (bkz.
AGENTS.md Madde 1.1 — tool paket sözleşmesi, requirements otomasyonu).

## Mimari

`web.py`, core'un çağırdığı tek yüzey — `web_analyze`/`web_execute`/
`web_rollback`/`web_report`/`web_history`. Bkz. ana core repo'sundaki
`AGENTS.md` Madde 3 (backend sözleşmesi). Bu tool, yeni tool'lar için
**mimari referans örnektir** — `folder_5s` (legacy) değil.

```
tools/d5s/
  contracts/   ← Plan, PlanItem, D5SScore, AuditEntry (pydantic modelleri)
  scanner.py   ← dosya sistemi tarama
  engine/      ← Seiri/Seiton/Seiso kuralları, skor hesaplama
  executor/    ← plan uygulama + rollback
  audit/       ← SQLite audit log (SQLAlchemy)
  reporting/   ← HTML/JSON/CSV rapor üretimi
  ui/panel.js  ← core'a mount edilen UI yüzeyi (AGENTS.md Madde 4)
  _shared_intent.py ← LLM prompt/parse — bu tool'un KENDİ kopyası,
                       folder_5s'inkiyle senkron tutulması zorunlu değil
  web.py       ← core'a sunulan tek yüzey
```

## Katkı

MANIFESTO.md ve AGENTS.md'yi (ana core repo) okuyun. Değişiklik
önerirken: engine mantığı (`contracts/`, `engine/`, `executor/`,
`audit/`) bu repo'da kalır; core'a hiçbir tool-özel kod eklenmez
(AGENTS.md Madde 2). PR açmadan önce ilgili testleri
(`tools/d5s/web.py` fonksiyonlarını FastAPI `TestClient` ile izole
test etmek) çalıştırın.
