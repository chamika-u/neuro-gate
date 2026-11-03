from pathlib import Path

from diagram_export.cli import parser
from diagram_export.models import ExportConfig


def test_parser_defaults_are_validated(tmp_path: Path) -> None:
    args = parser().parse_args(["--docs-dir", str(tmp_path / "docs"), "--out-dir", str(tmp_path / "out")])
    config = ExportConfig(docs_dir=args.docs_dir, out_dir=args.out_dir, scale=args.scale,
                          check=args.check, json_output=args.json, timeout=args.timeout)
    assert config.scale == 2
