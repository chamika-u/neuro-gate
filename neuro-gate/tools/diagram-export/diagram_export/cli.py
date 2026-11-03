"""Command-line orchestration for Mermaid export."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from . import __version__
from .discovery import discover
from .errors import ConfigurationError, RenderError, exit_code
from .manifest import is_current, load, write
from .models import ExportConfig, ExportReport, Manifest, ManifestEntry, RenderedDiagram
from .naming import output_names
from .render import render
from .report import format_human, format_json


def parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    root = Path(__file__).resolve().parents[3]
    result = argparse.ArgumentParser()
    result.add_argument("--docs-dir", type=Path, default=root / "docs")
    result.add_argument("--out-dir", type=Path, default=root / "diagrams")
    result.add_argument("--scale", type=int, default=2)
    result.add_argument("--check", action="store_true")
    result.add_argument("--json", action="store_true")
    result.add_argument("--timeout", type=int, default=30)
    return result


def run(args: argparse.Namespace) -> tuple[ExportReport, int]:
    """Execute discovery, rendering, publication, and reporting."""
    config = ExportConfig(
        docs_dir=args.docs_dir, out_dir=args.out_dir, scale=args.scale,
        check=args.check, json_output=args.json, timeout=args.timeout,
    )
    sources = discover(config.docs_dir)
    canonical = [source for source in sources if source.canonical]
    names = output_names(sources)
    now = datetime.now(UTC).isoformat()
    items: list[RenderedDiagram] = []
    temporary_root = Path(tempfile.mkdtemp(prefix="diagram-export-", dir=config.out_dir.parent))
    staged = temporary_root / "output"
    staged.mkdir()
    try:
        for source in canonical:
            destination = staged / names[source.source_id]
            try:
                width, height, size = render(source.content, destination, config.scale, config.timeout,
                                             Path(__file__).resolve().parents[1])
                items.append(RenderedDiagram(source_id=source.source_id,
                    output_name=destination.name, status="rendered", scale=config.scale,
                    width_px=width, height_px=height, size_bytes=size))
            except RenderError as exc:
                items.append(RenderedDiagram(source_id=source.source_id,
                    output_name=names[source.source_id], status="failed", scale=config.scale,
                    error=str(exc)))
        failed = sum(item.status == "failed" for item in items)
        report = ExportReport(tool_version=__version__, generated_at=now,
            docs_dir=config.docs_dir.as_posix(), out_dir=config.out_dir.as_posix(), scale=config.scale,
            check_only=config.check, total_discovered=len(sources), total_unique=len(canonical),
            exported=len(canonical) - failed, skipped=len(sources) - len(canonical), failed=failed,
            diagrams=items, success=failed == 0)
        if failed == 0 and config.check:
            current = load(config.out_dir / "manifest.json")
            expected = Manifest(tool_version=__version__, generated_at=current.generated_at if current else now,
                scale=config.scale, entries=[ManifestEntry(output_name=item.output_name,
                    source_path=next(s.path for s in canonical if names[s.source_id] == item.output_name),
                    origin=next(s.origin for s in canonical if names[s.source_id] == item.output_name),
                    content_hash=item.source_id, width_px=item.width_px or 1,
                    height_px=item.height_px or 1, size_bytes=item.size_bytes or 1)
                    for item in items])
            report.success = is_current(current, config.out_dir, expected)
            if not report.success:
                return report, 1
        if failed == 0 and not config.check:
            manifest = Manifest(tool_version=__version__, generated_at=now, scale=config.scale,
                entries=[ManifestEntry(output_name=item.output_name,
                    source_path=next(s.path for s in canonical if names[s.source_id] == item.output_name),
                    origin=next(s.origin for s in canonical if names[s.source_id] == item.output_name),
                    content_hash=item.source_id, width_px=item.width_px or 1,
                    height_px=item.height_px or 1, size_bytes=item.size_bytes or 1)
                    for item in items])
            staged_manifest = staged / "manifest.json"
            write(staged_manifest, manifest)
            backup = config.out_dir.with_name(config.out_dir.name + ".backup")
            if backup.exists():
                shutil.rmtree(backup)
            try:
                if config.out_dir.exists():
                    config.out_dir.replace(backup)
                staged.replace(config.out_dir)
            except OSError:
                if config.out_dir.exists():
                    shutil.rmtree(config.out_dir)
                if backup.exists():
                    backup.replace(config.out_dir)
                raise
            if backup.exists():
                shutil.rmtree(backup)
        return report, exit_code(None if report.success else RenderError("render failure"))
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and print its report."""
    args = parser().parse_args(argv)
    try:
        report, code = run(args)
        print(format_json(report) if args.json else format_human(report))
        return code
    except (ConfigurationError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}")
        return 2
