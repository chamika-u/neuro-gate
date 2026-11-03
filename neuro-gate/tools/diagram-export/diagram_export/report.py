"""Human-readable and JSON report formatting."""

import json

from .models import ExportReport


def format_human(report: ExportReport) -> str:
    """Format the stable line-oriented report."""
    lines = [
        "Mermaid Diagram Export",
        f"docs:    {report.docs_dir}",
        f"out:     {report.out_dir}",
        f"scale:   {report.scale}x",
        (f"discovered: {report.total_discovered}  unique: {report.total_unique}  "
         f"exported: {report.exported}  skipped: {report.skipped}  failed: {report.failed}"),
    ]
    for item in report.diagrams:
        lines.append(f"{item.status.upper():<9} {item.output_name}")
        if item.error:
            lines.append(f"          reason: {item.error}")
    result = "SUCCESS" if report.success else "FAILURE"
    lines.append(f"Result: {result} ({report.exported} exported, {report.skipped} skipped, {report.failed} failed)")
    return "\n".join(lines)


def format_json(report: ExportReport) -> str:
    """Format the validated report as JSON."""
    return json.dumps(report.model_dump(), indent=2)
