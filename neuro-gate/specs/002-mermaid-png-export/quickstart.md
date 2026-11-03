# Quickstart & Validation Guide: Mermaid Diagram PNG Export

**Feature**: `002-mermaid-png-export` | **Date**: 2026-11-03

This guide proves the feature end to end. Paths are relative to the repository
root unless stated otherwise.

## Prerequisites

- Python 3.11 or newer.
- Node.js 22.13 or newer and npm.
- Network access only for the one-time `npm ci` install; rendering itself is
  offline.
- Optional: Sinhala/Tamil fonts (for example Noto Sans Sinhala and Noto Sans Tamil)
  if diagrams with those labels are added later.

## Setup

```bash
# From the repository root
cd neuro-gate/tools/diagram-export
npm ci
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -e ".[dev]"
```

`npm ci` installs the pinned `@mermaid-js/mermaid-cli` and Puppeteer/Chromium.
If Chromium cannot be downloaded, install Chrome separately and set
`PUPPETEER_EXECUTABLE_PATH` to its executable.

## Run the export

```bash
# From the repository root
python neuro-gate/tools/diagram-export/export_diagrams.py
```

Expected result:

- `neuro-gate/diagrams/` contains one PNG per unique normalized diagram. The
  discovered and unique counts are reported from the current docs tree; they are
  not assumed from a fixed inventory.
- `neuro-gate/diagrams/manifest.json` lists every published PNG with its source,
  content hash, dimensions, and size.
- stdout ends with a `Result: SUCCESS (...)` line and discovery-derived counts
  for `discovered`, `unique`, `exported`, `skipped`, and `failed`.
- Exit code is `0`.

Machine-readable variant:

```bash
python neuro-gate/tools/diagram-export/export_diagrams.py --json > report.json
```

The output validates against
[`contracts/report.schema.json`](./contracts/report.schema.json).

## Validation scenarios

Map each scenario to the specification's acceptance criteria.

| # | Scenario | Command | Expected outcome |
|---|----------|---------|------------------|
| V1 | Fresh export creates the directory and all images (US1) | Delete `neuro-gate/diagrams/`, then run the export | Directory is recreated; the number of valid PNGs equals `total_unique` in the report; exit `0`. |
| V2 | Standalone names are traceable (US1/FR-005) | Inspect `manifest.json` entries | Each `output_name` maps to a `source_path`; standalone names match the `.mmd` stems. |
| V3 | Inline-only diagram included (US2) | Inspect manifest origins and source paths | Every inline-only definition has one published PNG and a traceable source path. |
| V4 | Duplicate collapsed (US2/FR-004) | Count files and compare `skipped` | `skipped` equals duplicate definitions reported by discovery; identical content appears once. |
| V5 | Idempotent rerun (US3) | Run the export twice, compare manifests | Same PNG set; manifests differ only in `generated_at`. |
| V6 | Refresh after edit (US3/SC-004) | Change a word in one `.mmd`, rerun | Only that PNG changes; no orphaned files; exit `0`. |
| V7 | Failure leaves output intact (US3/FR-010) | Introduce invalid Mermaid syntax, rerun | Exit `1`; failing source named; existing PNGs unchanged. |
| V8 | Check mode never writes (FR-015) | Run with `--check` | No file timestamps change; exit `0` when current, `1` when stale. |
| V9 | 2x scale (FR-017/SC-008) | Run the scale comparison integration test | Scale-2 output is twice the scale-1 width and height within renderer rounding tolerance. |
| V10 | Non-ASCII labels (FR-011/SC-006) | Render a fixture with an em dash and a Sinhala/Tamil label | Characters are legible, not replacement glyphs. |
| V11 | Missing renderer is a config error (edge case) | Temporarily hide `node_modules`, run | Exit `2` with an actionable message; no partial PNGs. |

## Automated tests

```bash
cd neuro-gate/tools/diagram-export
pytest                     # fast suite: unit + contract, no browser
pytest --cov --cov-branch  # enforce coverage gates
pytest -m render           # opt-in real-render integration test
ruff check .               # lint
ruff format --check .      # formatting
mypy --strict .            # static types
```

Coverage gates: at least 90% line coverage overall and 100% branch coverage on the
discovery, naming, and manifest-validation modules.

## Performance check

The full export of the current discovery-derived diagram set must finish in under
two minutes (SC-003). Record the wall-clock time, diagram count, OS, Python/Node
versions, and renderer versions in the benchmark artifact. Treat a result above
two minutes or more than 20% slower than the approved baseline as a release
blocker.

## Troubleshooting

- **`mmdc` not found / renderer missing**: run `npm ci` in
  `tools/diagram-export`; the tool intentionally does not auto-install.
- **Chromium sandbox error in a container**: the committed
  `puppeteer-config.json` already passes `--no-sandbox`; ensure it is being used.
- **Missing glyphs for Sinhala/Tamil**: install the Noto fonts named in the
  renderer stylesheet.
- **Invalid existing `manifest.json`**: fix or delete it; the tool fails closed
  rather than silently discarding stale state.

## Related artifacts

- [Specification](./spec.md)
- [Implementation plan](./plan.md)
- [Data model](./data-model.md)
- [CLI contract](./contracts/cli.md)
- [Report schema](./contracts/report.schema.json)
- [Manifest schema](./contracts/manifest.schema.json)
- [Research decisions](./research.md)
