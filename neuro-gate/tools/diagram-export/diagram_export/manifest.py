"""Manifest persistence and freshness checks."""

import json
from pathlib import Path

from .errors import ConfigurationError, RenderError
from .models import Manifest
from .render import png_dimensions


def load(path: Path) -> Manifest | None:
    """Load and validate a manifest, or return None when absent."""
    if not path.exists():
        return None
    try:
        return Manifest.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigurationError(f"invalid manifest {path}: {exc}") from exc


def write(path: Path, manifest: Manifest) -> None:
    """Write a validated manifest atomically."""
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(manifest.model_dump(), indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def is_current(manifest: Manifest | None, out_dir: Path, expected: Manifest) -> bool:
    """Return whether the published manifest and all owned PNGs match expected."""
    if manifest is None or manifest.scale != expected.scale:
        return False
    if manifest.entries != expected.entries:
        return False
    for entry in manifest.entries:
        image = out_dir / entry.output_name
        if not image.is_file() or image.stat().st_size != entry.size_bytes:
            return False
        if image.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            return False
        try:
            width, height = png_dimensions(image)
        except (OSError, RenderError):
            return False
        if width != entry.width_px or height != entry.height_px:
            return False
    return True
