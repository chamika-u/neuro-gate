# Phase 0 Research: Mermaid Diagram PNG Export

**Feature**: `002-mermaid-png-export` | **Date**: 2026-11-03

All unknowns from the Technical Context are resolved below. Each decision records
the choice, the rationale, and the alternatives considered.

## 1. Renderer selection

- **Decision**: Use the official `@mermaid-js/mermaid-cli` (`mmdc`) at a pinned
  version, `12.2.0`, driven headlessly by Puppeteer `25.16.0`.
- **Rationale**: It is the maintained reference renderer, supports every diagram
  type used by the docs (flowchart, sequence, state, class), renders offline once
  installed, supports PNG output with a scale flag, and is Node.js-only as a
  build-time dependency. Node.js `22.20.0` is present locally and satisfies the
  package's `engines: node >=22.13.0` requirement.
- **Alternatives considered**:
  - Hosted `mermaid.ink` (used by `mermaid-py`): rejected because the feature must
    work offline and the spec forbids a hosted rendering service.
  - Kroki server: rejected because it requires running and maintaining a separate
    service.
  - Pure-Python/JS hand-rolled layout: rejected as out of scope and error-prone.
  - Browser screenshot automation without `mmdc`: rejected because `mmdc` already
    encapsulates Mermaid initialization, theming, and PNG encoding.

## 2. Node toolchain pinning and installation

- **Decision**: Add `tools/diagram-export/package.json` with exact versions
  `@mermaid-js/mermaid-cli@12.2.0` and `puppeteer@25.16.0`, commit
  `package-lock.json`, and install
  with `npm ci`. Invoke the local binary only (`npx --no-install mmdc` or the local
  `src/cli.js`) so the pinned version is always used.
- **Rationale**: The constitution requires pinned, justified dependencies.
  `npm ci` guarantees reproducible installs, and refusing to auto-install prevents
  silently rendering with a different version.
- **Alternatives considered**: Global `npx -y @mermaid-js/mermaid-cli` (unpinned,
  network-dependent); a system-installed `mmdc` (not reproducible).

## 3. Diagram discovery

- **Decision**: Scan `neuro-gate/docs/` recursively for two source kinds:
  1. standalone `*.mmd` files, and
  2. fenced code blocks in `*.md` files whose info string is `mermaid`
     (case-insensitive, optional whitespace).
  Normalize each definition (unify line endings, strip trailing whitespace, trim
  leading/trailing blank lines) before hashing. The current repository contains 10
  standalone files and 12 inline blocks; the exporter must report the measured
  discovered and unique counts rather than assuming that inline copies are
  duplicates.
- **Rationale**: The docs store each diagram twice (inline plus an optional
  standalone `.mmd`), and one diagram exists inline only. Scanning both kinds is
  required by FR-002 and US2.
- **Alternatives considered**: Only `.mmd` files (misses the inline-only diagram);
  only Markdown (loses the canonical standalone files and their stable names).

## 4. Deduplication and source precedence

- **Decision**: Compute a SHA-256 hash of normalized content. Collapse identical
  diagrams to one render. When a standalone `.mmd` and an inline block are
  identical, the standalone source is canonical: it provides the output name and
  the inline copy is recorded as skipped.
- **Rationale**: Satisfies FR-004 and SC-007, avoids duplicate images, and keeps
  stable, meaningful file names. Canonical precedence is deterministic and matches
  the   docs index, which treats `.mmd` as the standalone source of truth. Current
  repository inspection shows the 10 standalone files and 12 inline blocks have
  distinct normalized hashes, so the current output count must be discovered at
  runtime rather than hard-coded as 11.
- **Alternatives considered**: First-seen wins (order-dependent and surprising);
  render everything and deduplicate files afterward (wasteful and ambiguous naming).

## 5. Deterministic output naming

- **Decision**:
  - Standalone source: use its file stem, e.g. `01-system-context.mmd` →
    `01-system-context.png`.
  - Inline-only source: `<document-prefix>-<heading-slug>.png`, where the document
    prefix is the leading number of the Markdown file name and the slug comes from
    the nearest preceding heading (numbered prefixes removed). Example: the failure
    handling flowchart under heading `## 2. Failure handling` in `05-...md` →
    `05-failure-handling.png`.
  - On collision, append `-2`, `-3`, ... in deterministic source order.
- **Rationale**: Meets FR-005 and US2 scenario 3: every PNG is traceable to its
  source, and names are stable across runs.
- **Alternatives considered**: Hash-based names (traceable but unreadable); random
  or timestamped names (non-deterministic, breaks idempotence).

## 6. Atomic, idempotent publishing and orphan cleanup

- **Decision**: Render every diagram into a temporary staging directory first and
  validate PNG signatures, non-zero sizes, dimensions, and the staged manifest.
  Rename the existing managed output directory to a backup, rename staging into
  place, and remove the backup only after the replacement succeeds. If any render
  fails, roll back and leave the existing output directory untouched. Orphan
  cleanup is limited to files owned by the previous valid manifest.
- **Rationale**: Satisfies FR-007, FR-008, FR-009, FR-010 and the refresh/failure
  edge cases. Staging guarantees that a broken diagram cannot corrupt or partially
  overwrite a valid image set.
- **Alternatives considered**: In-place rendering (risks corrupt output on failure);
  delete-then-render (loses the last good set on failure).

## 7. Non-ASCII label rendering

- **Decision**: Pass a small CSS file to `mmdc` (`--cssFile`) that extends the
  text font stack with `"Noto Sans Sinhala"`, `"Noto Sans Tamil"`, and generic
  fallbacks. Document that those fonts must be installed on the machine (or the CI
  image) for full glyph coverage. Current diagrams are English with non-ASCII
  punctuation, which the default bundled fonts already handle.
- **Rationale**: Meets FR-011 and SC-006 while staying offline. `mmdc` supports
  injected CSS, so no renderer fork is needed.
- **Alternatives considered**: Bundling full font binaries in the repo (large);
  ignoring non-ASCII (fails SC-006); switching renderer (unnecessary).

## 8. Headless Chromium in local and CI environments

- **Decision**: Commit a `puppeteer-config.json` that launches Chromium with
  `--no-sandbox` and `--disable-setuid-sandbox` for containerized CI, and support
  the `PUPPETEER_EXECUTABLE_PATH` environment variable to reuse an existing Chrome
  installation. Puppeteer downloads a compatible Chromium during `npm ci` by
  default.
- **Rationale**: Keeps local use simple while making CI reliable in containers.
  No secrets or network calls happen at render time.
- **Alternatives considered**: Requiring a system Chrome always (fragile across
  OSes); running without a sandbox flag (fails in containers).

## 9. Testing strategy

- **Decision**: Use `pytest` with three layers:
  - Unit tests for discovery, normalization, deduplication, naming/collisions,
    manifest validation, and report formatting (fully mocked renderer).
  - Contract tests that assert the `--json` report matches
    `contracts/report.schema.json`, the manifest matches
    `contracts/manifest.schema.json`, and documented exit codes are returned.
  - An opt-in integration test (`-m render`) that renders a tiny fixture diagram
    with the real `mmdc` at scale 1 and scale 2, asserting a valid PNG signature
    and a 2x width/height ratio within documented renderer rounding tolerance.
- **Rationale**: Meets Constitution IV, keeps the default suite fast and
  deterministic (no browser), and still proves the real rendering path.
- **Alternatives considered**: Browser rendering in every test (slow, flaky in CI);
  no integration test (leaves the renderer boundary unverified).

## 10. Performance

- **Decision**: Render sequentially with a 30 s per-diagram timeout and an overall
  budget check. The benchmark records the discovery-derived count, platform,
  renderer versions, and elapsed time; it fails above two minutes or when the
  result regresses by more than 20% from the recorded baseline. Parallel rendering
  is unnecessary complexity for the current tens-of-diagrams scope.
- **Rationale**: Simplicity, predictable memory use, and clear per-diagram error
  attribution. Revisit only if the diagram count grows by an order of magnitude.
- **Alternatives considered**: Parallel rendering via `p-limit` (faster but adds
  process contention and complicates error reporting); a persistent browser
  session through the Node API (faster but a larger implementation surface).
