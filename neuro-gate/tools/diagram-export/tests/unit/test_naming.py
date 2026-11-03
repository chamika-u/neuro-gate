from pathlib import Path

from diagram_export.discovery import discover
from diagram_export.naming import output_names


def test_standalone_name_is_stable(docs_tree: Path) -> None:
    sources = discover(docs_tree)
    names = output_names(sources)
    assert list(names.values()) == ["01-test.png"]
