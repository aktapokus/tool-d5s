"""
tools/d5s/reporting/html_report.py
5S tarama sonucundan HTML rapor üretir.
Dış bağımlılık yok — sadece stdlib string formatting.
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path

from ..contracts.report import ScanReport
from ..contracts.plan import Plan, ActionType, S5Phase
from ..scanner.metadata import human_size


def _phase_bar(score: float) -> str:
    filled = int(score / 5)
    empty  = 20 - filled
    color  = "#057A55" if score >= 80 else "#B45309" if score >= 60 else "#C81E1E"
    return (
        f'<div class="bar-track">'
        f'<div class="bar-fill" style="width:{score}%;background:{color}"></div>'
        f'</div>'
    )


def _grade_color(grade: str) -> str:
    return {"A": "#057A55", "B": "#1A56DB", "C": "#B45309",
            "D": "#C81E1E", "F": "#9B1C1C"}.get(grade, "#6B7280")


def generate_html(
    report: ScanReport,
    plan: Plan,
    output_path: Path | None = None,
) -> str:
    """ScanReport + Plan'dan HTML string üretir, opsiyonel dosyaya yazar."""

    score     = report.score
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    duration  = f"{report.duration_ms / 1000:.1f}s"

    # Plan özeti
    action_counts: dict[str, int] = {}
    phase_counts:  dict[str, int] = {}
    for item in plan.items:
        action_counts[item.action.value] = action_counts.get(item.action.value, 0) + 1
        phase_counts[item.phase.value]   = phase_counts.get(item.phase.value, 0) + 1

    recommendations_rows = ""
    for item in plan.items[:50]:   # ilk 50 göster
        risk_color = {"low": "#057A55", "medium": "#B45309", "high": "#C81E1E"}.get(
            item.risk.value, "#6B7280"
        )
        if item.action == ActionType.MOVE and item.destination:
            islem_gosterim = f'move → <span class="mono">{item.destination}</span>'
        elif item.action == ActionType.RENAME and item.new_name:
            islem_gosterim = f'rename → <span class="mono">{item.new_name}</span>'
        else:
            islem_gosterim = item.action.value
        recommendations_rows += f"""
        <tr>
          <td><span class="tag tag-{item.phase.value}">{item.phase.value.upper()}</span></td>
          <td>{islem_gosterim}</td>
          <td class="mono">{item.source.name}</td>
          <td>{item.reason}</td>
          <td style="color:{risk_color};font-weight:500">{item.risk.value}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>D5S Raporu — {report.target_folder.name}</title>
<style>
  :root {{
    --blue: #1A56DB; --green: #057A55; --red: #C81E1E;
    --border: #E5E7EB; --surface: #F9FAFB; --text: #111928;
    --text-dim: #6B7280;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; font-size: 13px;
          color: var(--text); background: #fff; padding: 32px; }}
  h1 {{ font-size: 20px; font-weight: 600; margin-bottom: 4px; }}
  h2 {{ font-size: 13px; font-weight: 600; text-transform: uppercase;
        letter-spacing: .08em; color: var(--text-dim); margin: 24px 0 12px; }}
  .meta {{ color: var(--text-dim); font-size: 11px; margin-bottom: 24px; }}
  .mono {{ font-family: 'Consolas', monospace; font-size: 11px; }}
  /* KPI grid */
  .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }}
  .kpi {{ border: 1px solid var(--border); padding: 14px; background: var(--surface); }}
  .kpi-val {{ font-size: 24px; font-weight: 700; color: var(--blue); font-family: monospace; }}
  .kpi-label {{ font-size: 10px; text-transform: uppercase; letter-spacing: .08em;
                color: var(--text-dim); margin-top: 4px; }}
  /* Score */
  .score-box {{ border: 1px solid var(--border); padding: 20px; margin-bottom: 24px;
                display: flex; align-items: center; gap: 24px; background: var(--surface); }}
  .score-num {{ font-size: 48px; font-weight: 700; font-family: monospace; }}
  .score-grade {{ font-size: 32px; font-weight: 700; margin-left: 8px; }}
  .phase-list {{ flex: 1; }}
  .phase-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }}
  .phase-name {{ width: 80px; font-size: 11px; text-transform: uppercase;
                 letter-spacing: .06em; color: var(--text-dim); }}
  .phase-val {{ width: 36px; text-align: right; font-family: monospace; font-weight: 600; }}
  .bar-track {{ flex: 1; height: 6px; background: var(--border); }}
  .bar-fill  {{ height: 100%; transition: width .3s; }}
  /* Table */
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th {{ text-align: left; padding: 8px 10px; border-bottom: 2px solid var(--border);
        font-size: 10px; text-transform: uppercase; letter-spacing: .08em;
        color: var(--text-dim); }}
  td {{ padding: 7px 10px; border-bottom: 1px solid var(--border); vertical-align: top; }}
  tr:hover td {{ background: var(--surface); }}
  .tag {{ font-size: 9px; font-weight: 600; padding: 2px 6px; text-transform: uppercase; }}
  .tag-seiri    {{ background: #EBF2FF; color: #1A56DB; }}
  .tag-seiton   {{ background: #F0FDF4; color: #057A55; }}
  .tag-seiso    {{ background: #FEF9C3; color: #B45309; }}
  .tag-seiketsu {{ background: #FDF2F8; color: #9D174D; }}
  .tag-shitsuke {{ background: #F5F3FF; color: #5B21B6; }}
  footer {{ margin-top: 32px; color: var(--text-dim); font-size: 10px;
            text-align: center; border-top: 1px solid var(--border); padding-top: 12px; }}
</style>
</head>
<body>

<h1>// D5S Tarama Raporu</h1>
<div class="meta">
  Klasör: <span class="mono">{report.target_folder}</span>
  &nbsp;·&nbsp; Tarama: {report.started_at:%Y-%m-%d %H:%M}
  &nbsp;·&nbsp; Süre: {duration}
  &nbsp;·&nbsp; Rapor: {generated}
</div>

<h2>// Özet</h2>
<div class="kpi-grid">
  <div class="kpi">
    <div class="kpi-val">{report.total_files:,}</div>
    <div class="kpi-label">Toplam Dosya</div>
  </div>
  <div class="kpi">
    <div class="kpi-val">{report.total_folders:,}</div>
    <div class="kpi-label">Toplam Klasör</div>
  </div>
  <div class="kpi">
    <div class="kpi-val">{human_size(report.total_size_bytes)}</div>
    <div class="kpi-label">Toplam Boyut</div>
  </div>
  <div class="kpi">
    <div class="kpi-val">{human_size(report.reclaimable_bytes)}</div>
    <div class="kpi-label">Kazanılabilecek Alan</div>
  </div>
  <div class="kpi">
    <div class="kpi-val">{report.duplicate_count}</div>
    <div class="kpi-label">Duplicate Dosya</div>
  </div>
  <div class="kpi">
    <div class="kpi-val">{report.empty_folder_count}</div>
    <div class="kpi-label">Boş Klasör</div>
  </div>
  <div class="kpi">
    <div class="kpi-val">{report.old_file_count}</div>
    <div class="kpi-label">Eski Dosya</div>
  </div>
  <div class="kpi">
    <div class="kpi-val">{report.recommendations}</div>
    <div class="kpi-label">Öneri</div>
  </div>
</div>

<h2>// 5S Puanı</h2>
<div class="score-box">
  <div>
    <span class="score-num" style="color:{_grade_color(score.grade)}">{score.total}</span>
    <span class="score-grade" style="color:{_grade_color(score.grade)}">{score.grade}</span>
    <div style="font-size:11px;color:var(--text-dim);margin-top:4px">
      Risk: {score.risk_level.upper()}
      {'&nbsp;·&nbsp; Önceki: ' + str(report.previous_score) if report.previous_score else ''}
    </div>
  </div>
  <div class="phase-list">
    {''.join(f'''
    <div class="phase-row">
      <span class="phase-name">{ph}</span>
      <span class="phase-val">{getattr(score, ph).score:.0f}</span>
      {_phase_bar(getattr(score, ph).score)}
    </div>''' for ph in ['seiri','seiton','seiso','seiketsu','shitsuke'])}
  </div>
</div>

<h2>// Öneriler ({len(plan.items)} adet, ilk 50 gösteriliyor)</h2>
<table>
  <thead>
    <tr>
      <th>Faz</th><th>İşlem</th><th>Dosya</th><th>Gerekçe</th><th>Risk</th>
    </tr>
  </thead>
  <tbody>
    {recommendations_rows}
  </tbody>
</table>

<footer>
  Aktapokus D5S Engine v{plan.rule_version} &nbsp;·&nbsp; {generated}
</footer>
</body>
</html>"""

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

    return html
