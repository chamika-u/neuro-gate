# Tasks: Mermaid Diagram PNG Export

**Input**: Design documents from `/neuro-gate/specs/002-mermaid-png-export/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included because the project constitution mandates test-first development
(Principle IV: >= 90% line coverage, 100% branch coverage on boundary modules).
Write each test task first and confirm it fails before implementing the paired task.

**Organization**: Tasks are grouped by user story so each story can be implemented,
tested, and demonstrated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Tool root: `neuro-gate/tools/diagram-export/`
Output root: `neuro-gate/diagrams/`
Sources (read-only): `neuro-gate/docs/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and tool skeleton

- [X] T001 Create the tool directory tree under `neuro-gate/tools/diagram-export/`: `diagram_export/`, `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/fixtures/docs/`
- [X] T002 Create `neuro-gate/tools/diagram-export/pyproject.toml` with Python 3.11+ metadata, `pydantic>=2,<3`, dev extras (`pytest`, `pytest-cov`, `ruff`, `mypy`), and ruff/mypy/pytest/coverage configuration
- [ ] T003 [P] Create `neuro-gate/tools/diagram-export/package.json` pinning `@mermaid-js/mermaid-cli@12.2.0` and `puppeteer@25.16.0`, commit the lockfile, and verify with `npm ci`
- [X] T004 [P] Create `neuro-gate/tools/diagram-export/puppeteer-config.json` with headless Chromium `--no-sandbox` arguments and document `PUPPETEER_EXECUTABLE_PATH` support
- [X] T005 [P] Create `neuro-gate/tools/diagram-export/mermaid-fonts.css` with Noto Sans Sinhala/Tamil fallback fonts for `--cssFile`
- [X] T006 [P] Create `neuro-gate/tools/diagram-export/.gitignore` covering `node_modules/`, `.venv/`, and coverage artifacts while leaving generated PNGs trackable
- [X] T007 Create `neuro-gate/tools/diagram-export/diagram_export/__init__.py` with `__version__` and package docstring
- [ ] T008 [P] Create fixture docs under `neuro-gate/tools/diagram-export/tests/fixtures/docs/`: one standalone `.mmd`, one inline-only diagram, one duplicate inline copy, one invalid diagram, and one non-ASCII label diagram
- [X] T009 [P] Create shared pytest fixtures and the `render` marker in `neuro-gate/tools/diagram-export/tests/conftest.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared models, errors, CLI shell, and reporting that every user story needs

**âš ï¸ CRITICAL**: No user story work can begin until this phase is complete

### Tests first

- [ ] T010 [P] Write failing tests for Pydantic model fields and invariants in `neuro-gate/tools/diagram-export/tests/unit/test_models.py`
- [X] T011 Implement the Pydantic v2 models (`DiagramSource`, `RenderedDiagram`, `ExportReport`, `ManifestEntry`, `Manifest`) in `neuro-gate/tools/diagram-export/diagram_export/models.py`
- [ ] T012 [P] Write failing JSON-schema contract tests for the report and manifest in `neuro-gate/tools/diagram-export/tests/contract/test_schemas.py`
- [X] T013 Add contract fixtures and a JSON-schema validation helper in `neuro-gate/tools/diagram-export/tests/contract/conftest.py`
- [ ] T014 [P] Write failing tests for error types and exit-code mapping in `neuro-gate/tools/diagram-export/tests/unit/test_errors.py`
- [X] T015 Implement error types and the `0/1/2` exit-code mapping in `neuro-gate/tools/diagram-export/diagram_export/errors.py`
- [ ] T016 [P] Write failing tests for CLI argument parsing, defaults, and usage errors in `neuro-gate/tools/diagram-export/tests/unit/test_cli_args.py`
- [X] T017 Implement the argparse CLI skeleton and entry point in `neuro-gate/tools/diagram-export/diagram_export/cli.py` and `neuro-gate/tools/diagram-export/export_diagrams.py`
- [ ] T018 [P] Write failing tests for human and `--json` report formatting in `neuro-gate/tools/diagram-export/tests/unit/test_report.py`
- [X] T019 Implement report formatting in `neuro-gate/tools/diagram-export/diagram_export/report.py`

**Checkpoint**: Models, errors, CLI shell, and reporting are ready; user stories can begin.

---

## Phase 3: User Story 1 - Export all diagram sources to images (Priority: P1) ðŸŽ¯ MVP

**Goal**: Discover every standalone `.mmd` source, render it at 2x scale, and publish
the PNG set to `neuro-gate/diagrams/`.

**Independent Test**: Run the export against the current docs and confirm every
standalone `.mmd` source is represented by a traceable PNG.

### Tests for User Story 1 âš ï¸

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T020 [P] [US1] Write failing tests for standalone `.mmd` discovery and deterministic ordering in `neuro-gate/tools/diagram-export/tests/unit/test_discovery_standalone.py`
- [X] T021 [US1] Implement standalone `.mmd` discovery in `neuro-gate/tools/diagram-export/diagram_export/discovery.py`
- [ ] T022 [P] [US1] Write failing tests for standalone naming, slug generation, and collision suffixes in `neuro-gate/tools/diagram-export/tests/unit/test_naming.py`
- [X] T023 [US1] Implement deterministic naming helpers in `neuro-gate/tools/diagram-export/diagram_export/naming.py`
- [ ] T024 [P] [US1] Write failing tests for the `mmdc` subprocess wrapper, timeout, and staging cleanup in `neuro-gate/tools/diagram-export/tests/unit/test_render.py`
- [X] T025 [US1] Implement the renderer wrapper, per-diagram timeout, and temporary staging in `neuro-gate/tools/diagram-export/diagram_export/render.py`
- [X] T026A [P] [US1] Write failing tests for the standalone discovery â†’ naming â†’ render â†’ publish flow in `neuro-gate/tools/diagram-export/tests/contract/test_cli_flow.py`
- [X] T026 [US1] Wire the standalone discovery â†’ naming â†’ render â†’ publish flow in `neuro-gate/tools/diagram-export/diagram_export/cli.py` after T026A fails
- [X] T027 [P] [US1] Write contract tests for human CLI output, `--json` output, and exit codes in `neuro-gate/tools/diagram-export/tests/contract/test_cli_output.py`
- [ ] T028 [US1] Write the opt-in real-render integration test marked `render` in `neuro-gate/tools/diagram-export/tests/integration/test_render_real.py`
- [ ] T029 [US1] Validate US1 by running the export and confirming ten standalone PNGs plus a valid manifest appear in `neuro-gate/diagrams/`

**Checkpoint**: US1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - Include diagrams that exist only inside documents (Priority: P2)

**Goal**: Discover inline fenced Mermaid blocks, deduplicate identical content, and
render the inline-only diagram so the image set is complete.

**Independent Test**: Run discovery and confirm the report's measured definition
and unique counts, verify inline-only diagrams are rendered, and verify identical
content is rendered once.

### Tests for User Story 2 âš ï¸

- [X] T030 [P] [US2] Write failing tests for inline fenced-block discovery, heading tracking, and block ordering in `neuro-gate/tools/diagram-export/tests/unit/test_discovery_inline.py`
- [X] T031 [US2] Extend `neuro-gate/tools/diagram-export/diagram_export/discovery.py` to parse fenced `mermaid` blocks and record their nearest heading
- [X] T032 [P] [US2] Write failing tests for normalization, SHA-256 identity, dedup, and standalone precedence in `neuro-gate/tools/diagram-export/tests/unit/test_dedup.py`
- [X] T033 [US2] Implement content normalization, hashing, deduplication, and canonical-source precedence in `neuro-gate/tools/diagram-export/diagram_export/discovery.py`
- [X] T034 [US2] Implement inline-only heading-slug naming (for example `05-failure-handling.png`) in `neuro-gate/tools/diagram-export/diagram_export/naming.py`
- [X] T035 [US2] Extend report and CLI flow to count skipped duplicates and show inline origins in `neuro-gate/tools/diagram-export/diagram_export/report.py` and `neuro-gate/tools/diagram-export/diagram_export/cli.py`
- [ ] T036 [P] [US2] Add a non-ASCII fixture and rendering assertion in `neuro-gate/tools/diagram-export/tests/fixtures/docs/` and `neuro-gate/tools/diagram-export/tests/integration/test_non_ascii.py`
- [ ] T037 [US2] Validate US2: confirm discovery-derived counts, inline-only PNGs, and duplicate hashes are represented once in `neuro-gate/diagrams/`

**Checkpoint**: US1 and US2 both work independently.

---

## Phase 5: User Story 3 - Refresh the image set safely (Priority: P3)

**Goal**: Make the export repeatable and idempotent, remove stale generated PNGs,
support `--check`, and guarantee that a failed render never corrupts the published set.

**Independent Test**: Rerun unchanged, edit one source, introduce invalid syntax, and
run `--check`; the output set stays consistent and failures leave prior PNGs intact.

### Tests for User Story 3 âš ï¸

- [X] T038 [P] [US3] Write failing tests for manifest load/validate/write and orphan reconciliation in `neuro-gate/tools/diagram-export/tests/unit/test_manifest.py`
- [X] T039 [US3] Implement manifest read/validate/write and stale-entry reconciliation in `neuro-gate/tools/diagram-export/diagram_export/manifest.py`
- [X] T040 [P] [US3] Write failing tests for atomic publish and no-write-on-failure in `neuro-gate/tools/diagram-export/tests/unit/test_publish.py`
- [X] T041 [US3] Implement two-phase staging and directory-swap publication with rollback in `neuro-gate/tools/diagram-export/diagram_export/cli.py`
- [X] T042 [P] [US3] Write failing tests for `--check` freshness mode and no-write guarantees in `neuro-gate/tools/diagram-export/tests/contract/test_check_mode.py`
- [X] T043 [US3] Implement the `--check` freshness mode without writes in `neuro-gate/tools/diagram-export/diagram_export/cli.py`
- [ ] T044 [US3] Write the integration test for invalid syntax â†’ exit `1` with unchanged outputs in `neuro-gate/tools/diagram-export/tests/integration/test_failure_atomic.py`
- [X] T045 [US3] Implement removal of previously generated PNGs that are no longer expected in `neuro-gate/tools/diagram-export/diagram_export/manifest.py`
- [ ] T046 [US3] Validate US3 scenarios V5â€“V8 (idempotent rerun, edit refresh, failure atomicity, `--check`) against `neuro-gate/docs/` and `neuro-gate/diagrams/`, using `neuro-gate/tools/diagram-export/tests/integration/test_failure_atomic.py`

**Checkpoint**: All three user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, quality gates, and end-to-end validation

- [X] T047 [P] Write `neuro-gate/tools/diagram-export/README.md` with setup, run, and troubleshooting steps
- [X] T048 [P] Verify `neuro-gate/tools/diagram-export/.gitignore` keeps generated PNGs and `manifest.json` trackable; check with `git status`
- [X] T049 Run `ruff format --check`, `ruff check`, and `mypy --strict` on `neuro-gate/tools/diagram-export/` and fix all findings
- [ ] T050 Run `pytest --cov --cov-branch` in `neuro-gate/tools/diagram-export/` and close gaps to >= 90% line coverage and 100% branch coverage on discovery, naming, and manifest modules in `neuro-gate/tools/diagram-export/diagram_export/`
- [X] T051 Add `.github/workflows/diagram-export.yml` to run `npm ci`, Python tests, lint, formatting, strict typing, and the renderer integration job with committed lockfile verification
- [ ] T052 Execute quickstart validation scenarios V1â€“V11 from `neuro-gate/specs/002-mermaid-png-export/quickstart.md` against `neuro-gate/diagrams/` and fix any failures
- [ ] T053 Measure a full export wall-clock time against `neuro-gate/diagrams/`, record environment and diagram count, and fail above two minutes or beyond the approved 20% regression threshold
- [ ] T054 Final check: confirm no files under `neuro-gate/docs/` were modified, then commit the PNGs and `manifest.json` in `neuro-gate/diagrams/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **US1 (Phase 3)**: Depends on Foundational.
- **US2 (Phase 4)**: Depends on Foundational and builds on US1 discovery/render modules.
- **US3 (Phase 5)**: Depends on Foundational and builds on US1/US2 rendering pipeline.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: No dependency on other stories. Delivers the MVP.
- **US2 (P2)**: Extends US1's discovery and naming; independently testable once US1 exists.
- **US3 (P3)**: Extends US1/US2's publish pipeline; independently testable once rendering exists.

### Within Each User Story

- Tests MUST be written and FAIL before implementation.
- Models before services; discovery/naming before render wiring.
- Core implementation before integration; validate the checkpoint before the next story.

### Parallel Opportunities

- Setup tasks T003â€“T006, T008â€“T009 are parallel.
- Foundational test-writing tasks T010, T012, T014, T016, T018 are parallel.
- Within each story, all `[P]` test tasks can run in parallel.
- Test-writing for US2/US3 can start once their module interfaces from US1 are stable.

---

## Parallel Example: User Story 1

```bash
# Launch the three unit-test-writing tasks together:
Task: "Write failing discovery tests in tests/unit/test_discovery_standalone.py"
Task: "Write failing naming tests in tests/unit/test_naming.py"
Task: "Write failing render wrapper tests in tests/unit/test_render.py"

# Then implement in dependency order:
Task: "Implement discovery.py"
Task: "Implement naming.py"
Task: "Implement render.py"
Task: "Wire flow in cli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: US1.
4. **STOP and VALIDATE**: ten standalone PNGs render and are traceable.
5. Commit the MVP image set.

### Incremental Delivery

1. Setup + Foundational â†’ tool skeleton ready.
2. US1 â†’ standalone exports (MVP).
3. US2 â†’ inline-only diagram and deduplication complete the set.
4. US3 â†’ repeatable, atomic refresh with `--check`.
5. Polish â†’ documentation, quality gates, and end-to-end validation.

### Parallel Team Strategy

1. Team completes Setup + Foundational together.
2. Then split: Developer A takes US1, Developer B prepares US2 inline discovery,
   Developer C prepares US3 manifest/atomic tests (interfaces agreed first).
3. Integrate and validate each checkpoint independently.

---

## Notes

- `[P]` tasks touch different files and have no incomplete-task dependencies.
- `[Story]` labels provide traceability to spec.md user stories.
- Do not proceed past a checkpoint until its independent test passes.
- Keep `neuro-gate/docs/` read-only throughout.
- Commit after each logical group; the final commit must include the generated PNGs and manifest.
