# Implementation Plan: Mermaid Diagram PNG Export

**Branch**: `002-mermaid-png-export` | **Date**: 2026-11-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/neuro-gate/specs/002-mermaid-png-export/spec.md`

## Summary

Add a repeatable, offline documentation tool that discovers every Mermaid diagram in
`neuro-gate/docs/` (standalone `.mmd` sources and fenced `mermaid` blocks inside
Markdown), renders each unique normalized definition to a 2x-scale PNG, and writes
the committed image set plus a manifest to `neuro-gate/diagrams/`. Counts are
discovery-derived rather than hard-coded because the current repository contains
10 standalone files and 12 inline blocks whose normalized contents are distinct.

The tool is a small, strictly typed Python CLI (Python 3.11+, Pydantic v2 for the
outbound report and manifest) that drives the pinned `@mermaid-js/mermaid-cli`
renderer under Node.js. Rendering is staged in a temporary directory, validated,
and published through a directory swap only after every diagram succeeds, so a
broken diagram can never corrupt an already-valid image set. Identical normalized
diagram content is deduplicated by content hash, and standalone `.mmd` sources win
over inline copies only when their hashes match.

## Technical Context

**Language/Version**: Python 3.11+ (tool orchestration and tests); Node.js >= 22.13
(pinned renderer runtime only, not a product runtime dependency)

**Primary Dependencies**: Python standard library plus `pydantic` v2 (report and
manifest contracts); dev-only `pytest`, `pytest-cov`, `ruff`, `mypy`; build-time
`@mermaid-js/mermaid-cli@12.2.0` and `puppeteer@25.16.0` pinned in
`tools/diagram-export/package.json`

**Storage**: Files only. Output PNGs and `manifest.json` are written to
`neuro-gate/diagrams/`. No database and no business-data persistence; the export
tool is build-time documentation tooling, not the NeuroGate runtime.

**Testing**: `pytest` with unit tests for discovery, normalization, deduplication,
naming, manifest validation, and reporting; contract tests for the CLI JSON report
and exit codes; an opt-in integration test that renders a tiny diagram with the real
renderer. `pytest-cov` enforces >= 90% line coverage and 100% branch coverage on the
discovery/naming/manifest-validation modules. `ruff` and `mypy --strict` are the
quality gates.

**Target Platform**: Developer workstations and CI on Windows, Linux, or macOS
(x86-64 or ARM64) with Node.js >= 22.13 and a headless Chromium supplied by
Puppeteer.

**Project Type**: Developer/documentation CLI tooling (single subproject), kept
isolated from the runtime service planned in `001-neuro-gate-assistive-middleware`.

**Performance Goals**: Full export of the discovery-derived current set completes
in under 2 minutes (SC-003); each diagram render has a 30 s timeout and a clear
failure report. A CI benchmark records the diagram count, environment, and elapsed
time and fails on budget breach or a regression beyond 20%.

**Constraints**: Offline (no hosted rendering service); deterministic and idempotent
output; no partial/corrupt PNGs on failure; non-ASCII labels preserved; 2x render
scale; PNG only; generated PNGs are committed.

**Scale/Scope**: The current repository has 10 standalone `.mmd` files and 12
inline Mermaid blocks; the exporter derives the unique count from normalized
content and is designed to scale to tens of diagrams without configuration changes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status | Evidence / notes |
|-----------|-------------|--------|------------------|
| I. Stateless by Design (NON-NEGOTIABLE) | No external DB or durable business-data store; request-scoped processing | **PASS (scoped)** | This is a build-time documentation tool, not the NeuroGate runtime. It writes only the static PNG/manifest artifacts the feature explicitly requires. No business data, sessions, or runtime state. |
| II. Pydantic-Validated Data Contracts | Boundary payloads validated with Pydantic v2 with explicit schemas | **PASS** | CLI `--json` report and `manifest.json` are outbound payloads modeled as Pydantic v2 models; manifest is validated on read. JSON Schemas are published under `contracts/`. |
| III. Code Quality & Maintainability | Typed public API, `ruff`/format clean, `mypy` clean, docstrings, no dead code, pinned dependencies | **PASS** | `ruff format` + `ruff check` + `mypy --strict` on `tools/diagram-export`; exact npm versions and a committed lockfile; all public functions documented. |
| IV. Test-First with Mandatory Edge-Case Coverage (NON-NEGOTIABLE) | Tests precede implementation; >= 90% line coverage; 100% branch on validation/boundary modules | **PASS** | Red-first tasks per behavior; discovery/naming/manifest modules enumerated as boundary surfaces with 100% branch coverage. |
| V. UX Consistency & Performance | Stable output/error schema, actionable errors, performance budget and benchmark evidence | **PASS** | One stable human report and one `--json` report schema; exit codes are documented; CI records the full-export benchmark and enforces the 2-minute budget plus the constitution's 20% regression rule. |
| Additional constraints | Python 3.11+, Pydantic v2 only, no external DB, secrets from env, no secret logging, portability | **PASS (justified deviation)** | Python 3.11+ and Pydantic v2 are used. Node.js is a build-time-only dependency of the renderer, not of the product runtime; exact versions and the lockfile make it reproducible. No secrets are required. |

**Gate result**: PASS. The only deviation is the build-time Node.js dependency,
which is justified below and does not affect the product runtime.

## Project Structure

### Documentation (this feature)

```text
neuro-gate/specs/002-mermaid-png-export/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── cli.md
│   ├── report.schema.json
│   └── manifest.schema.json
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created here)
```

### Source Code (repository root)

```text
neuro-gate/
├── diagrams/                        # NEW: committed rendered output
│   ├── 01-system-context.png
│   ├── ...
│   └── manifest.json                # generated mapping + content hashes
├── docs/                            # existing inputs (unchanged)
│   ├── *.md                         # inline fenced mermaid blocks
│   └── diagrams/*.mmd               # standalone sources
└── tools/
    └── diagram-export/              # NEW: isolated documentation tooling
        ├── pyproject.toml           # ruff / mypy / pytest / coverage config
        ├── package.json             # pinned mermaid-cli + puppeteer
        ├── package-lock.json        # reproducible npm install
        ├── puppeteer-config.json    # headless Chromium, no-sandbox for CI
        ├── export_diagrams.py       # thin CLI entry point
        ├── diagram_export/
        │   ├── __init__.py
        │   ├── models.py            # Pydantic v2: DiagramSource, RenderedDiagram, ExportReport, Manifest
        │   ├── discovery.py         # scan .mmd files + inline fenced blocks
        │   ├── naming.py            # deterministic slugs and collision resolution
        │   ├── render.py            # mmdc subprocess wrapper + staging
        │   ├── manifest.py          # manifest read/write + reconciliation
        │   └── cli.py               # argparse, orchestration, exit codes
        └── tests/
            ├── fixtures/
            ├── unit/
            ├── contract/
            └── integration/
```

**Structure Decision**: Single isolated tooling subproject under
`neuro-gate/tools/diagram-export/`, with output at `neuro-gate/diagrams/`. The
runtime service planned in feature `001` will own `src/neurogate/` and the root
`pyproject.toml`; this tool keeps its own `pyproject.toml` so documentation tooling
neither depends on nor blocks the runtime service. Diagram sources in
`neuro-gate/docs/` are read-only inputs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Build-time Node.js dependency (`@mermaid-js/mermaid-cli` + Puppeteer/Chromium) in a Python-first repository | Mermaid rendering requires a real browser layout engine; the maintained official renderer is Node-based and can run fully offline once installed. | A pure-Python renderer is immature and the common Python wrapper (`mermaid-py`) calls the hosted `mermaid.ink` service, which the spec forbids (offline, no hosted service). Re-implementing Mermaid layout is out of scope. |
| Pydantic v2 dependency for a documentation tool | Constitution II requires boundary payloads to be Pydantic-validated; the CLI `--json` report and committed `manifest.json` are outbound payloads. | Emitting unvalidated dictionaries would violate Constitution II and make the manifest schema unverifiable. |

## Post-Design Constitution Re-check

*Re-evaluated after Phase 1 design artifacts were produced.*

| Principle | Status | Post-design evidence |
|-----------|--------|----------------------|
| I. Stateless by Design | PASS (scoped) | The design writes only the requested static PNG/manifest artifacts; no database, sessions, or runtime state. Documented in [data-model.md](./data-model.md) and [research.md](./research.md). |
| II. Pydantic-Validated Data Contracts | PASS | `ExportReport` and `Manifest` are Pydantic v2 models with published JSON Schemas in [contracts/](./contracts/); the manifest is validated on read. |
| III. Code Quality & Maintainability | PASS | Module boundaries (`discovery`, `naming`, `render`, `manifest`, `cli`) are single-purpose with typed, documented interfaces; exact npm versions and lockfile are required. |
| IV. Test-First with Mandatory Edge-Case Coverage | PASS | The design requires red-first tests for every behavior, including publication rollback and check mode; boundary modules are fully enumerable. |
| V. UX Consistency & Performance | PASS | [contracts/cli.md](./contracts/cli.md) fixes report format, `--json` schema, and exit codes; CI measures the SC-003 budget and enforces the 20% regression rule. |
| Additional constraints | PASS (justified deviation) | Python 3.11+ / Pydantic v2 / no DB / no secrets. The Node.js renderer remains build-time only, exact-pinned, and lockfile-backed. |

**Gate result after design**: PASS. No unresolved violations.
