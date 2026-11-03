"""Shared test configuration."""

import pytest


@pytest.fixture
def docs_tree(tmp_path):
    """Create a small documentation tree for discovery tests."""
    docs = tmp_path / "docs"
    (docs / "diagrams").mkdir(parents=True)
    (docs / "diagrams" / "01-test.mmd").write_text("flowchart LR\n A-->B\n", encoding="utf-8")
    (docs / "page.md").write_text(
        "# Heading\n\n```mermaid\nflowchart LR\n A-->B\n```\n",
        encoding="utf-8",
    )
    return docs
