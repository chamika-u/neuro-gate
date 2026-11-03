from diagram_export.discovery import discover, normalize


def test_normalize_and_deduplicate(docs_tree):
    assert normalize(" a  \r\n") == "a"
    sources = discover(docs_tree)
    assert len(sources) == 2
    assert sum(source.canonical for source in sources) == 1
    assert next(source for source in sources if source.canonical).origin == "standalone"
