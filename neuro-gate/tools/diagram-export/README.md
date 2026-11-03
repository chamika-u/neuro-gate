# Mermaid diagram export

From the repository root, install the pinned renderer and Python tooling:

```powershell
cd neuro-gate/tools/diagram-export
npm ci
py -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Run `python neuro-gate/tools/diagram-export/export_diagrams.py`. Use `--json` for
machine-readable output and `--check` to verify the committed output without writes.
The tool discovers standalone `.mmd` files and fenced Mermaid blocks under
`neuro-gate/docs/`, deduplicates normalized content, and publishes PNGs atomically.
