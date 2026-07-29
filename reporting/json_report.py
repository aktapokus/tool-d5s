"""
tools/d5s/reporting/json_report.py
JSON ve CSV rapor üreticileri.
"""

from __future__ import annotations
import csv
import json
from pathlib import Path

from ..contracts.report import ScanReport
from ..contracts.plan import Plan


def generate_json(
    report: ScanReport,
    plan: Plan,
    output_path: Path | None = None,
    indent: int = 2,
) -> str:
    """ScanReport + Plan → JSON string."""
    data = {
        "scan_id":       report.scan_id,
        "target_folder": str(report.target_folder),
        "started_at":    report.started_at.isoformat(),
        "completed_at":  report.completed_at.isoformat(),
        "duration_ms":   report.duration_ms,
        "summary": {
            "total_files":         report.total_files,
            "total_folders":       report.total_folders,
            "total_size_bytes":    report.total_size_bytes,
            "duplicate_count":     report.duplicate_count,
            "empty_folder_count":  report.empty_folder_count,
            "old_file_count":      report.old_file_count,
            "temp_file_count":     report.temp_file_count,
            "large_file_count":    report.large_file_count,
            "reclaimable_bytes":   report.reclaimable_bytes,
            "recommendations":     report.recommendations,
        },
        "score": {
            "total":     report.score.total,
            "grade":     report.score.grade,
            "risk":      report.score.risk_level,
            "previous":  report.previous_score,
            "phases": {
                phase: {
                    "score":        getattr(report.score, phase).score,
                    "issues_found": getattr(report.score, phase).issues_found,
                    "notes":        getattr(report.score, phase).notes,
                }
                for phase in ["seiri", "seiton", "seiso", "seiketsu", "shitsuke"]
            },
        },
        "recommendations": [
            {
                "id":          item.id,
                "phase":       item.phase.value,
                "action":      item.action.value,
                "source":      str(item.source),
                "destination": str(item.destination) if item.destination else None,
                "reason":      item.reason,
                "risk":        item.risk.value,
                "confidence":  item.confidence,
                "size_bytes":  item.size_bytes,
                "reversible":  item.reversible,
            }
            for item in plan.items
        ],
    }

    output = json.dumps(data, ensure_ascii=False, indent=indent)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")

    return output


def generate_csv(
    plan: Plan,
    output_path: Path | None = None,
) -> str:
    """Plan önerilerini CSV formatında döner."""
    import io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=[
        "faz", "islem", "kaynak", "hedef",
        "gerekce", "risk", "guven", "boyut_bytes", "geri_alinabilir",
    ])
    writer.writeheader()

    for item in plan.items:
        writer.writerow({
            "faz":           item.phase.value,
            "islem":         item.action.value,
            "kaynak":        str(item.source),
            "hedef":         str(item.destination) if item.destination else "",
            "gerekce":       item.reason,
            "risk":          item.risk.value,
            "guven":         f"{item.confidence:.2f}",
            "boyut_bytes":   item.size_bytes,
            "geri_alinabilir": "evet" if item.reversible else "hayir",
        })

    output = buf.getvalue()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8-sig")  # Excel BOM

    return output
