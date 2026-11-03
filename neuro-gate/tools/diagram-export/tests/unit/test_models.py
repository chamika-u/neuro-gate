import pytest
from pydantic import ValidationError

from diagram_export.models import Manifest, ManifestEntry, RenderedDiagram


def test_rendered_diagram_requires_scale_and_error_for_failure() -> None:
    with pytest.raises(ValidationError):
        RenderedDiagram(source_id="a" * 64, output_name="a.png", status="failed", scale=2)


def test_manifest_rejects_duplicate_names() -> None:
    entry = ManifestEntry(output_name="a.png", source_path="docs/a.mmd", origin="standalone",
                          content_hash="a" * 64, width_px=1, height_px=1, size_bytes=1)
    with pytest.raises(ValidationError):
        Manifest(tool_version="1", generated_at="now", scale=2, entries=[entry, entry])
