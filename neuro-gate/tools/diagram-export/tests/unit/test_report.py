from diagram_export.models import ExportReport
from diagram_export.report import format_human, format_json


def test_report_formats() -> None:
    report = ExportReport(
        tool_version="1", generated_at="2026-01-01T00:00:00Z",
        docs_dir="docs", out_dir="diagrams", scale=2, check_only=False,
        total_discovered=0, total_unique=0, exported=0, skipped=0, failed=0,
        diagrams=[], success=True,
    )
    assert "Result: SUCCESS" in format_human(report)
    assert '"success": true' in format_json(report)
