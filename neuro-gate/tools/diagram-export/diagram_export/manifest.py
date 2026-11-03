"""Manifest persistence and freshness checks."""

import json
from pathlib import Path

from .errors import ConfigurationError
from .models import Manifest


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
