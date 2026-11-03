# Phase 1 Data Model: Mermaid Diagram PNG Export

**Feature**: `002-mermaid-png-export` | **Date**: 2026-11-03

All structured payloads are Pydantic v2 models (Constitution II). The JSON Schemas
published under `contracts/` are the external, reviewable form of these models.

## Entities

### 1. `DiagramSource`

Represents one discovered Mermaid definition before rendering.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | `str` | yes | Stable identity derived from the normalized content hash (equal to `content_hash`). |
| `origin` | `Literal["standalone", "inline"]` | yes | Whether it came from a `.mmd` file or a fenced Markdown block. |
| `path` | `str` | yes | Repository-relative path of the defining file. |
| `document_heading` | `str \| None` | no | Nearest preceding heading; required for `inline` sources, `None` for standalone. |
| `block_index` | `int \| None` | no | Zero-based index of the fenced block within the document; required for `inline`, `None` for standalone. |
| `content` | `str` | yes | Normalized Mermaid definition. |
| `content_hash` | `str` | yes | SHA-256 hex digest (64 lowercase hex characters) of `content`. |
| `canonical` | `bool` | yes | `True` for the single source chosen to represent a content hash. |
| `discovery_order` | `int` | yes | Deterministic order: standalone sources first (sorted by path), then inline blocks (sorted by document path, then block index). |

**Validation rules**

- `content_hash` MUST match `^[0-9a-f]{64}$`.
- `origin == "inline"` MUST have both `document_heading` and `block_index`;
  `origin == "standalone"` MUST have neither.
- `path` MUST resolve inside the configured docs directory (no traversal).
- `content` MUST be non-empty after normalization.

**Identity and uniqueness**

- The unit of uniqueness is `content_hash`. Exactly one source per hash has
  `canonical = True`.
- Canonical precedence: `standalone` beats `inline`; otherwise the lowest
  `discovery_order` wins.

### 2. `RenderedDiagram`

Represents the outcome of rendering one canonical diagram.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | `str` | yes | References `DiagramSource.source_id`. |
| `output_name` | `str` | yes | File name only, e.g. `01-system-context.png`. |
| `status` | `Literal["rendered", "skipped_duplicate", "failed"]` | yes | Per-diagram result. |
| `scale` | `int` | yes | Render scale; MUST be >= 2. |
| `width_px` | `int \| None` | no | Rendered width when known. |
| `height_px` | `int \| None` | no | Rendered height when known. |
| `size_bytes` | `int \| None` | no | Rendered file size when known. |
| `error` | `str \| None` | no | Human-readable failure reason; required when `status == "failed"`. |

**Validation rules**

- `output_name` MUST match `^[a-z0-9][a-z0-9-]*\.png$` and contain no path
  separators.
- `status == "failed"` requires a non-empty `error`; other statuses MUST have
  `error is None` and non-null dimensions when published.
- `scale >= 2` (FR-017).

**State transitions**

```text
discovered -> canonical | skipped_duplicate
canonical  -> staged   -> published
canonical  -> staged   -> failed
```

A failed render aborts publication: `staged` files are discarded and the previously
published set is unchanged.

### 3. `ExportReport`

The CLI result, emitted as text by default and as JSON with `--json`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | `str` | yes | Contract version, e.g. `"1.0.0"`. |
| `tool_version` | `str` | yes | Version of the export tool. |
| `generated_at` | `str` | yes | ISO 8601 UTC timestamp. |
| `docs_dir` | `str` | yes | Repository-relative docs directory. |
| `out_dir` | `str` | yes | Repository-relative output directory. |
| `scale` | `int` | yes | Render scale (>= 2). |
| `check_only` | `bool` | yes | Whether the run was a no-write `--check`. |
| `total_discovered` | `int` | yes | All definitions found, including duplicates. |
| `total_unique` | `int` | yes | Distinct content hashes. |
| `exported` | `int` | yes | PNGs successfully rendered/published. |
| `skipped` | `int` | yes | Duplicate definitions skipped. |
| `failed` | `int` | yes | Diagrams that failed to render. |
| `diagrams` | `list[RenderedDiagram]` | yes | One entry per unique diagram. |
| `success` | `bool` | yes | `True` only when `failed == 0` (and, in check mode, outputs are current). |

**Validation rules**

- `exported + failed == total_unique`.
- `skipped == total_discovered - total_unique`.
- `success == (failed == 0 and freshness_ok)`.
- Counts are non-negative.

### 4. `Manifest`

Committed at `neuro-gate/diagrams/manifest.json`; enables orphan cleanup and
reviewer traceability.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | `str` | yes | Contract version, e.g. `"1.0.0"`. |
| `tool_version` | `str` | yes | Version of the export tool. |
| `generated_at` | `str` | yes | ISO 8601 UTC timestamp of the successful publish. |
| `scale` | `int` | yes | Render scale used for every entry (>= 2). |
| `entries` | `list[ManifestEntry]` | yes | One entry per published PNG, sorted by `output_name`. |

#### `ManifestEntry`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `output_name` | `str` | yes | Published PNG file name. |
| `source_path` | `str` | yes | Repository-relative path of the canonical source. |
| `origin` | `Literal["standalone", "inline"]` | yes | Canonical source kind. |
| `content_hash` | `str` | yes | SHA-256 of the normalized source. |
| `width_px` | `int` | yes | Published image width. |
| `height_px` | `int` | yes | Published image height. |
| `size_bytes` | `int` | yes | Published file size. |

**Validation rules**

- Every `content_hash` is unique within a manifest.
- Every `output_name` is unique within a manifest.
- On read, a malformed or schema-invalid manifest fails the run with an actionable
  error rather than silently ignoring stale state.

## Relationships

```text
DiagramSource (many) ──content_hash──> DiagramSource (one canonical)
RenderedDiagram (one) ──source_id────> DiagramSource
ExportReport (one) ────diagrams─────> RenderedDiagram (many)
Manifest (one) ────────entries──────> ManifestEntry (many)
```

## Boundary and error rules

- Exit codes: `0` success; `1` one or more render/validation failures; `2` usage or
  configuration error (bad arguments, missing renderer, unreadable docs directory).
- Errors are actionable, name the offending source, and never include secrets.
- No network access is required at render time; a missing renderer or Chromium is a
  configuration error (`2`), not a render failure (`1`).
- Idempotence: re-running with unchanged sources produces byte-comparable PNGs and a
  manifest whose only volatile field is `generated_at`.
