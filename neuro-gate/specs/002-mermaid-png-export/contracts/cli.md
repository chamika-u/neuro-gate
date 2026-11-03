# CLI Contract: `export_diagrams.py`

**Contract version**: 1.0.0 | **Feature**: `002-mermaid-png-export`

The export tool exposes one command. Everything it prints and every exit code it
returns is part of this contract and is covered by contract tests.

## Invocation

```text
python tools/diagram-export/export_diagrams.py [options]
```

Run from the repository root (`neuro-gate/`) or invoke the script by path; all
default paths are resolved relative to the script location, not the current
working directory.

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--docs-dir PATH` | path | `neuro-gate/docs` (resolved from the tool location) | Directory scanned for `.mmd` files and Markdown fenced blocks. |
| `--out-dir PATH` | path | `neuro-gate/diagrams` (resolved from the tool location) | Directory where PNGs and `manifest.json` are written. |
| `--scale N` | integer >= 2 | `2` | Render scale passed to the renderer. |
| `--check` | flag | off | Verify that the committed PNG set is current without writing anything. |
| `--json` | flag | off | Emit the machine-readable report from `report.schema.json` to stdout. |
| `--timeout SECONDS` | integer > 0 | `30` | Per-diagram render timeout. |

Unknown options are a usage error.

## Output

### Default (human) output

A single stable, line-oriented report on stdout:

```text
Mermaid Diagram Export
docs:    neuro-gate/docs
out:     neuro-gate/diagrams
scale:   2x
discovered: 12  unique: 11  exported: 11  skipped: 1  failed: 0

RENDERED  01-system-context.png        <- docs/diagrams/01-system-context.mmd
...
SKIPPED   06-sequence-happy-path.mmd   (duplicate of docs/diagrams/06-sequence-happy-path.mmd)
...
FAILED    05-failure-handling.png      <- docs/05-safety-and-ethics.md (2. Failure handling)
          reason: <actionable message>

Result: SUCCESS (11 exported, 1 skipped, 0 failed)
```

- The summary line always uses this label order: `discovered`, `unique`,
  `exported`, `skipped`, `failed`.
- Failures are always listed after rendered and skipped entries and include a
  reason.
- A successful run ends with `Result: SUCCESS (...)`; a failed run ends with
  `Result: FAILURE (...)`.

### `--json` output

A single JSON object matching [`report.schema.json`](./report.schema.json),
written to stdout with no other stdout content. Diagnostics still go to stderr.

### Errors (stderr)

- Usage errors print the usage synopsis and a specific message.
- Configuration errors (missing renderer, unreadable docs directory, invalid
  manifest) print `error: <actionable message>`.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success: every unique diagram rendered and published (`--check`: outputs current). |
| `1` | Render or validation failure: at least one diagram failed, or `--check` found stale/missing output. |
| `2` | Usage or configuration error: bad arguments, missing renderer/Chromium, unreadable docs directory, invalid existing manifest. |

## Side effects

- On success, writes `*.png` files and `manifest.json` under `--out-dir`, and
  removes generated PNGs listed in the previous manifest that are no longer
  expected.
- On failure, does not modify the existing output directory.
- Never modifies files under `--docs-dir`.
- `--check` never writes to disk.

## Guarantees

- **Idempotent**: rerunning with unchanged inputs yields the same set of PNGs and
  a manifest differing only in `generated_at`.
- **Deterministic naming**: given the same docs tree, output names are stable
  across runs and machines.
- **Atomic publish**: a failed render cannot leave a partially updated image set.
- **Committed output**: generated PNGs and `manifest.json` are intended to be
  committed to version control (FR-016).
