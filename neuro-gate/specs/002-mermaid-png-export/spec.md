# Feature Specification: Mermaid Diagram PNG Export

**Feature Branch**: `002-mermaid-png-export`

**Created**: 2026-11-03

**Status**: Draft

**Input**: User description: "i want to create another directory called digrams in nerou-gate direcory and save all the current digrams in mermaid into png files on that directory"

## Clarifications

### Session 2026-11-03

- Q: Should the deliverable be a repeatable export command or a one-time snapshot? → A: A repeatable export command that regenerates all PNGs on demand.
- Q: Should the generated PNGs be committed or excluded as build artifacts? → A: Commit the generated PNGs to version control.
- Q: What minimum output resolution should the PNGs meet? → A: High-DPI rendering at 2x scale.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export all diagram sources to images (Priority: P1)

A maintainer wants a single, predictable place where every Mermaid diagram in the
NeuroGate documentation set exists as a ready-to-view image, so diagrams can be
shared in slides, reviews, and reports without copying source text or rendering
each one by hand.

**Why this priority**: This is the core value of the request. Without a complete,
predictable image set the feature delivers nothing.

**Independent Test**: Run the documented export action, then confirm that
`neuro-gate/diagrams/` exists and contains one PNG for every standalone Mermaid
diagram source under `neuro-gate/docs/diagrams/`.

**Acceptance Scenarios**:

1. **Given** the project contains ten standalone Mermaid source files, **When**
   the maintainer runs the export, **Then** `neuro-gate/diagrams/` contains ten
   PNG files with names that clearly correspond to their sources.
2. **Given** the output directory does not yet exist, **When** the export runs,
   **Then** the directory is created automatically and the export succeeds.
3. **Given** the export has completed, **When** the maintainer opens any produced
   PNG, **Then** the full diagram is visible with all nodes, labels, and arrows
   present and legible.

---

### User Story 2 - Include diagrams that exist only inside documents (Priority: P2)

A maintainer wants every diagram that appears in the documentation rendered,
including the one that is currently only embedded inside a document and has no
standalone source file, so the image set is truly complete.

**Why this priority**: Missing even one diagram undermines trust in the exported
set and forces manual follow-up.

**Independent Test**: Compare the set of unique Mermaid diagrams discoverable in
the documentation against the PNGs produced; every unique diagram is represented
exactly once.

**Acceptance Scenarios**:

1. **Given** a diagram exists only as an inline fenced Mermaid block in a
   document, **When** the export runs, **Then** that diagram is also rendered to
   PNG in the output directory.
2. **Given** the same diagram content appears in two documents, **When** the
   export runs, **Then** it produces a single PNG rather than duplicate images.
3. **Given** the exported PNG set, **When** a maintainer inspects the file names,
   **Then** each PNG can be traced back to the document or source that defined it.

---

### User Story 3 - Refresh the image set safely (Priority: P3)

A maintainer updates a diagram source and wants to regenerate the images without
manually deleting old files, while being confident that a broken diagram cannot
leave the image set in a corrupted or half-written state.

**Why this priority**: Diagrams change over time; a repeatable, safe refresh is
what keeps the image set trustworthy after the first export.

**Independent Test**: Edit one diagram, rerun the export, and confirm the affected
PNG changes while all other PNGs remain valid; then introduce a deliberate syntax
error and confirm the failure is reported and no valid PNG is corrupted.

**Acceptance Scenarios**:

1. **Given** an existing complete PNG set, **When** the export is rerun unchanged,
   **Then** the same set of PNGs is produced with no leftover or orphaned files.
2. **Given** one diagram has been edited, **When** the export is rerun, **Then**
   that diagram's PNG reflects the change and the other PNGs remain valid.
3. **Given** one diagram contains invalid Mermaid syntax, **When** the export runs,
   **Then** the failing diagram is identified by name, the overall result is
   reported as a failure, and previously valid PNGs are left intact.

---

### Edge Cases

- When a diagram contains non-ASCII labels (for example Sinhala, Tamil, or
  punctuation such as em dashes), the rendered PNG must show the characters
  legibly rather than as missing glyphs or replacement characters.
- When a diagram is very tall or very wide, the rendered PNG must contain the
  whole diagram rather than a clipped or cropped view.
- When the export discovers no diagrams, it must complete with a clear notice
  that zero diagrams were exported rather than appearing to succeed silently.
- When two diagrams have identical content, only one PNG is produced and the
  shared source is not counted as a failure.
- When a source file name contains spaces or special characters, the produced PNG
  name must remain valid and clearly associated with that source.
- When the output directory already contains PNGs from an earlier run, the export
  must replace them deterministically and must not accumulate stale duplicates.
- When the rendering tool is unavailable or cannot run in the current
  environment, the export must fail with an actionable message and must not
  create partial or empty PNG files.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a dedicated output directory at
  `neuro-gate/diagrams/` for rendered diagram images.
- **FR-002**: The system MUST discover every Mermaid diagram currently defined in
  the NeuroGate documentation set, including standalone `.mmd` sources and fenced
  Mermaid blocks embedded in Markdown documents.
- **FR-003**: The system MUST produce a PNG image for each unique discovered
  diagram.
- **FR-004**: The system MUST deduplicate diagrams whose content is identical so
  that each unique diagram yields exactly one PNG.
- **FR-005**: The system MUST name each PNG so that it can be unambiguously
  associated with its originating diagram source.
- **FR-006**: The system MUST create the output directory automatically when it
  does not exist.
- **FR-007**: The system MUST replace existing PNGs on rerun so the output set
  always reflects the current diagram sources.
- **FR-008**: The system MUST report, for each diagram, whether rendering
  succeeded or failed, and MUST provide an overall summary of exported, skipped,
  and failed counts.
- **FR-009**: The system MUST return a failure result when any discovered diagram
  cannot be rendered, identifying the failing diagram.
- **FR-010**: The system MUST NOT corrupt or delete an existing valid PNG when a
  render for that diagram fails.
- **FR-011**: The system MUST preserve non-ASCII diagram labels in the rendered
  images.
- **FR-012**: The system MUST render complete diagrams without cropping, scaling
  down to illegibility, or truncating any nodes or edges.
- **FR-013**: The system MUST operate without requiring manual per-diagram steps
  beyond invoking the documented export action.
- **FR-014**: The system MUST NOT modify the source diagram files or documentation
  during export.
- **FR-015**: The system MUST provide a repeatable export command that regenerates
  all PNGs on demand from the current diagram sources, rather than a one-time
  snapshot.
- **FR-016**: The generated PNGs MUST be committed to version control so they are
  available to repository viewers without running the export.
- **FR-017**: The system MUST render each PNG at a minimum of 2x scale relative to
  the diagram's native size.

### Key Entities *(include if data involved)*

- **Diagram Source**: A Mermaid diagram definition. Key attributes: source path,
  origin type (standalone source file or inline document block), content, and a
  stable identity derived from its content for deduplication.
- **Rendered Diagram**: A PNG output. Key attributes: file name, source diagram
  it represents, rendered dimensions, and success state.
- **Export Report**: The outcome of one export run. Key attributes: total
  discovered, exported, skipped (duplicate), failed, and the list of failures
  with their sources.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of unique Mermaid diagrams in the documentation set are
  represented by a PNG in the output directory after a successful export.
- **SC-002**: A maintainer can run the complete export with one documented action
  and no per-diagram manual work.
- **SC-003**: A full export of the current diagram set completes in under two
  minutes on a standard development machine.
- **SC-004**: Rerunning the export after changing a single diagram updates that
  diagram's PNG while leaving zero invalid or orphaned PNGs.
- **SC-005**: When any diagram fails to render, the failure names the source and
  the number of corrupted output files is zero.
- **SC-006**: 100% of diagrams containing non-ASCII labels render those labels
  legibly in the produced images.
- **SC-007**: Identical diagrams produce exactly one image (zero duplicates).
- **SC-008**: Every produced PNG is rendered at a minimum of 2x scale relative to
  the diagram's native size, keeping labels legible on high-DPI displays.

## Assumptions

- The user's spelling "digrams" and "nerou-gate" refer to "diagrams" and the
  existing `neuro-gate/` project directory.
- The requested output directory is `neuro-gate/diagrams/` at the project root.
  The pre-existing `neuro-gate/docs/diagrams/` holds canonical `.mmd` sources and
  remains the source location; the new directory holds rendered PNGs only.
- "All current diagrams" means every unique Mermaid diagram currently present:
  the ten standalone `.mmd` sources plus the inline-only failure-handling diagram
  in the safety document, with duplicate inline copies collapsed to one image.
- PNG is the only required output format; no SVG, PDF, or other formats are in
  scope.
- PNGs are rendered at a minimum of 2x scale relative to the diagram's native
  size, as confirmed during clarification.
- The diagram set is static documentation content; diagrams generated at runtime
  from live data are out of scope.
- Only documentation under `neuro-gate/docs/` is in scope for discovery.
- A headless rendering tool can be installed and run locally as part of the
  documented setup; no hosted rendering service is required.
