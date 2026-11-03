---
description: "Task list for NeuroGate — Intent-Gated Assistive Communication Middleware"
---

# Tasks: NeuroGate — Intent-Gated Assistive Communication Middleware

**Input**: Design documents from `/neuro-gate/specs/001-neuro-gate-assistive-middleware/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: **REQUIRED** for this feature. The project constitution (Principle IV,
NON-NEGOTIABLE) mandates test-first development: write the failing test, then the
implementation. Coverage gates: ≥90% line overall; 100% branch on
`fsm/machine.py`, `sanitize/validate.py`, `sanitize/confidence.py`.

**Organization**: Tasks are grouped by user story so each story is independently
implementable, testable, and demoable.

**Path convention**: All paths are relative to the project root `neuro-gate/`.
Documentation paths are relative to the feature directory.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: `US1`–`US5`, mapped to the user stories in `spec.md`
- Every task names the exact file(s) it produces or changes

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the project skeleton, tooling, and static configuration.

- [ ] T001 Create the package and test directory tree exactly as specified in `plan.md` (Project Structure), with `src/neurogate/__init__.py` and empty `__init__.py` files for `contracts/`, `ingest/`, `dsp/`, `fsm/`, `sanitize/`, `output/`, `output/tts/`, `telemetry/`, plus `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/fixtures/`
- [ ] T002 Create `pyproject.toml` with `requires-python = ">=3.11"`, dependencies (`pylsl`, `numpy`, `scipy`, `pydantic>=2`, `httpx`, `streamlit`, `tomli` fallback not needed), dev dependencies (`pytest`, `pytest-cov`, `hypothesis`, `ruff`, `mypy`, `jsonschema`), and the console script `neurogate = "neurogate.cli:main"`
- [ ] T003 [P] Create `ruff.toml` with target `py311`, line length 100, rules `E,F,I,UP,B,SIM`, and formatter settings
- [ ] T004 [P] Create `mypy.ini` enabling `strict = True` for `src/neurogate`, `warn_unreachable`, and `disallow_any_generics`
- [ ] T005 [P] Create `config/default.toml` whose parsed shape validates against `contracts/config.schema.json` (mains 50 Hz, sEMG 20–250 Hz, EEG 1–45 Hz, RMS 50 ms, PSD 1 s, confirmation 1500 ms, confidence 0.75, fault budget 5, event port 49152)
- [ ] T006 [P] Create `config/noise_lexicon.si.toml`, `config/noise_lexicon.ta.toml`, and `config/noise_lexicon.en.toml` with the fatigue/pain/filler examples from `docs/08-multilingual-support.md` §4
- [ ] T007 Install the package in editable mode (`pip install -e ".[dev]"`) and verify `python -c "import neurogate"` resolves `src/neurogate/__init__.py` and exits 0

**Checkpoint**: Package imports, tooling runs, config parses.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Contracts, telemetry, FSM, calibration, and fixtures that every user
story depends on.

**⚠️ CRITICAL**: No user story work may begin until this phase is complete.

### Contract models (constitution Principle II)

- [ ] T008 [P] Create `src/neurogate/contracts/signals.py` with `ChannelKind`, `Band`, `BiosignalFrame`, and `FeatureFrame` including the field constraints in `data-model.md` §1–2
- [ ] T009 [P] Create `src/neurogate/contracts/intents.py` with `TriggerKind`, `Language`, `Decision`, `OutputChannel`, `TriggerEvent`, `ThoughtBuffer`, `SanitizedIntent`, `ConfirmationDecision`, `OutputEvent`, and `TimingRecord` per `data-model.md` §3–8
- [ ] T010 [P] Create `src/neurogate/contracts/events.py` with the event envelope and `EventType` enum mirroring `contracts/event-stream.schema.json`
- [ ] T011 [P] Write `tests/contract/test_signals.py` covering round-trip, NaN/Inf rejection, sample-length bound, and rate range — **must fail before T008 lands**
- [ ] T012 [P] Write `tests/contract/test_intents.py` covering every validation rule in `data-model.md` §5 and the `TIMEOUT`-is-approval invariant from §6 — **must fail first**
- [ ] T013 [P] Write `tests/contract/test_events.py` validating emitted envelopes against `contracts/event-stream.schema.json` with `jsonschema`

### Configuration, errors, telemetry

- [ ] T014 Create `src/neurogate/config.py` that loads TOML, validates against `contracts/config.schema.json`, and exposes an immutable `NeuroGateConfig` Pydantic model
- [ ] T015 Create `tests/contract/test_config.py` covering valid config, missing section, wrong enum, and out-of-range values (`CONFIG_INVALID`)
- [ ] T016 Create `src/neurogate/errors.py` with the stable error-code enum and the shared error envelope from `contracts/README.md`
- [ ] T017 Create `src/neurogate/telemetry/logging.py` — structured logs with an explicit deny-list that forbids payload text, plus a `redact` helper used by every log call
- [ ] T018 Create `src/neurogate/telemetry/publisher.py` — newline-delimited JSON publisher on loopback, validating each event against `contracts/event-stream.schema.json` before send
- [ ] T019 Create `tests/unit/test_publisher.py` asserting schema validation, per-`event_type` required fields (a `fault` event without `fault_code` and a `state_changed` without `state` are rejected), rejection of content-bearing fields, and that no file is ever written

### FSM and calibration

- [ ] T020 Create `src/neurogate/fsm/states.py` with `State` and `Event` enums (10 states, event set from `data-model.md` State machine)
- [ ] T021 Create `src/neurogate/fsm/machine.py` with the exhaustive `TRANSITIONS: dict[tuple[State, Event], State]` table, a `transition()` that raises on illegal pairs, and the four invariants from `data-model.md`
- [ ] T022 Write `tests/unit/test_fsm_machine.py` enumerating **every** table cell, every illegal pair, `FAULT` having no event-based exit, and `SPEAKING` reachable only via `AWAITING_CONFIRMATION` — **must fail first**
- [ ] T023 Write `tests/unit/test_fsm_properties.py` using `hypothesis` to fuzz event sequences and assert no illegal state and no `SPEAKING` without a preceding `AWAITING_CONFIRMATION`
- [ ] T024 Create `src/neurogate/fsm/calibration.py` implementing `threshold = p95(rest) + k * (median(attempts) - p95(rest))` with `k` configurable and an explicit `CalibrationError` when separation is insufficient
- [ ] T025 Create `tests/unit/test_calibration.py` covering insufficient separation, exactly-at-floor, one-below, one-above, zero samples, and empty input

### Ingest buffer, consent, CLI skeleton, fixtures

- [ ] T026 Create `src/neurogate/ingest/ring_buffer.py` — bounded by duration and by max samples, with `snapshot()` and `discard()`; must drop oldest samples, never grow
- [ ] T027 Create `tests/unit/test_ring_buffer.py` covering empty, exactly-full, one-over-full, and post-discard reuse
- [ ] T028 Create `src/neurogate/session.py` with `SessionConfig` (operator id, consent flag, primary language, thresholds) and a startup guard that raises `CONSENT_MISSING` before any inlet opens
- [ ] T029 Create `src/neurogate/cli.py` with `main()`, a `doctor` subcommand (Python version, model presence, TTS backend + declared locales, config validity) and a `reset` subcommand stub
- [ ] T030 [P] Create `tests/fixtures/scripted/` cases: `si-water-glass.json`, `ta-water-glass.json`, `en-water.json`, `jaw-clench.json`, `blink.json`, `cough.json`, `movement.json`, `silence-only.json`, `mixed-script.json` — each with `raw_thought_buffer`, `rejected_noise`, `intended_sentence`, `language`, `duration_ms`
- [ ] T091 [P] Create `tests/fixtures/replay/` with a PhysioNet-derived EEG statistics descriptor, a synthetic sEMG envelope descriptor, and `tests/fixtures/replay/loader.py`; add `tests/unit/test_replay_loader.py` covering missing descriptor, wrong channel count, and rate out of range (FR-015, used by T076 and quickstart scenario 5)
- [ ] T031 [P] Create `tests/fixtures/fake_sanitizer.py` returning the scripted corpus of valid, malformed, contradictory, and low-confidence responses, usable as an in-process replacement for the model client
- [ ] T090 Create bounded transition history in `src/neurogate/fsm/machine.py` (FIFO, 200 entries, no payload text) and publish each transition via `src/neurogate/telemetry/publisher.py`; add `tests/unit/test_transition_history.py` asserting FIFO eviction at exactly 200, one over, and that history is cleared at session end (FR-016)
- [ ] T092 Create `tests/integration/test_no_irreversible_action.py` asserting the orchestrator exposes no mutating capability and that `sanitize/`, `fsm/`, and `output/` import no filesystem-write, network, or actuation API (AST scan), proving FR-018
- [ ] T093 Enforce one active session in `src/neurogate/session.py` (a second open raises `SESSION_ACTIVE`) and add `tests/unit/test_single_session.py` covering duplicate open, close-then-reopen, and no interleaved buffers (FR-019)
- [ ] T094 Add per-stage timeout keys for `dsp`, `fsm`, and `tts` under `stage_timeouts_ms` (the sanitizer already has `sanitizer.timeout_ms`) to `config/default.toml` and `contracts/config.schema.json`, enforce them in the orchestrator, and extend `tests/unit/test_config.py` with a missing-key and a zero-timeout case (FR-017)
- [ ] T095 Write `tests/integration/test_consent_gate.py` — opening without a named operator or consent record raises `CONSENT_MISSING` before any inlet opens; recording consent then opening succeeds (FR-020)

**Checkpoint**: Contracts validate, FSM is provable, config loads, fixtures exist.

---

## Phase 3: User Story 1 — Deliberate utterance is spoken, noise is not (Priority: P1) 🎯 MVP

**Goal**: Filter affective noise out of a buffer, stage the sanitized sentence, and
deliver it as text after the confirmation window resolves.

**Independent Test**: `neurogate replay --case fixtures/scripted/si-water-glass.json
--language si --tts none` delivers exactly the intended sentence, reports two
rejected fragments, and emits no audio.

### Tests for User Story 1 (write first, watch them fail) ⚠️

- [ ] T032 [P] [US1] Write `tests/contract/test_sanitized_intent.py` — accept valid payloads, reject missing fields, reject `additionalProperties`, reject actionable-with-empty-text, reject non-actionable-with-text
- [ ] T033 [P] [US1] Write `tests/unit/test_confidence.py` — composite weights, schema failure halves the score, model self-report alone cannot clear 0.75, boundary at exactly 0.75
- [ ] T034 [P] [US1] Write `tests/unit/test_validate.py` — contradiction detection (`sanitized_text` inside `rejected_noise`), language/script mismatch, empty actionable text
- [ ] T035 [P] [US1] Write `tests/integration/test_us1_delivery.py` — replay → subtitle output, asserting the delivered text equals `intended_sentence`, `rejected_count == 2`, and the local rejection audit list contains both rejected fragment strings (FR-011)
- [ ] T036 [P] [US1] Write `tests/integration/test_us1_passive_noise.py` — `silence-only.json` and a noise-only buffer produce zero output events

### Implementation for User Story 1

- [ ] T037 [P] [US1] Implement `src/neurogate/sanitize/client.py` — loopback Ollama client over `httpx` with `format: json`, per-request timeout, at most one retry, and typed failure results (no exceptions out)
- [ ] T038 [P] [US1] Implement `src/neurogate/sanitize/prompts.py` — per-language system prompt builder embedding the schema, the lexicon file contents, and three few-shot examples
- [ ] T039 [P] [US1] Implement `src/neurogate/sanitize/validate.py` — parse into `SanitizedIntent`, apply the five rules from `data-model.md` §5, return the error code on failure
- [ ] T040 [P] [US1] Implement `src/neurogate/sanitize/confidence.py` — composite score from `research.md` R3.1 with configurable weights
- [ ] T041 [US1] Implement `src/neurogate/dsp/filters.py` — 50 Hz notch and zero-phase Butterworth bandpass via `scipy.signal.sosfiltfilt`
- [ ] T042 [US1] Implement `src/neurogate/dsp/features.py` — 50 ms RMS envelope and Welch band power for the four bands
- [ ] T043 [US1] Implement `src/neurogate/dsp/quality.py` — per-modality SNR estimate and `artifact_flagged` derivation
- [ ] T044 [US1] Implement `src/neurogate/ingest/lsl_inlet.py` — resolve streams, validate metadata against `contracts/lsl-stream.md`, normalize to `BiosignalFrame`
- [ ] T045 [US1] Implement `src/neurogate/ingest/replay_source.py` — paced replay of a scripted case into the same `BiosignalFrame` stream, including the synthesized sEMG envelope
- [ ] T046 [US1] Implement the orchestration loop in `src/neurogate/session.py` wiring ingest → DSP → FSM → sanitize → confirmation → output, with one intent cycle per gate pass
- [ ] T047 [US1] Implement `src/neurogate/output/subtitles.py` — UTF-8 payload plus the local rejection audit list (text stays local, counts go to telemetry)
- [ ] T048 [US1] Implement `src/neurogate/output/tts/base.py` (`TextToSpeech` protocol, `SpeakResult`), `espeak.py` (subprocess backend), and `none.py` (subtitle-only)
- [ ] T049 [US1] Implement the confirmation gate in `src/neurogate/session.py` — 1.5 s window, expiry counts as `TIMEOUT`/approval, only `CANCELLED`/`NO_RESPONSE` suppress output
- [ ] T050 [US1] Implement the `replay` subcommand in `src/neurogate/cli.py` with `--case`, `--language`, and `--tts` flags
- [ ] T051 [US1] Publish `rejected_count` (never the text) on `intent_staged` events in `src/neurogate/telemetry/publisher.py`
- [ ] T052 [US1] Run `pytest tests/unit/test_validate.py tests/unit/test_confidence.py tests/contract/test_sanitized_intent.py tests/integration/test_us1_delivery.py --cov-branch` and confirm 100% branch coverage on `sanitize/validate.py` and `sanitize/confidence.py`

**Checkpoint**: MVP complete — noise is filtered, intent is delivered as text, no audio without confirmation.

---

## Phase 4: User Story 2 — User cancels an unintended utterance (Priority: P1)

**Goal**: A staged utterance can be cancelled before playback and aborted during it,
with no audio ever emitted for a cancelled intention.

**Independent Test**: `neurogate replay --case fixtures/scripted/en-water.json
--cancel-at-ms 600 --tts none` resolves as `CANCELLED` with zero output events.

### Tests for User Story 2 (write first) ⚠️

- [ ] T053 [P] [US2] Write `tests/unit/test_confirmation.py` — cancel before expiry suppresses output, expiry approves, double-resolve is rejected
- [ ] T054 [P] [US2] Write `tests/integration/test_us2_cancel.py` — injected cancel at 600 ms yields `CANCELLED`, zero output, and a cancelled indication

### Implementation for User Story 2

- [ ] T055 [US2] Add a thread-safe `CancellationSignal` to `src/neurogate/session.py` and make the gate resolve exactly once
- [ ] T056 [US2] Implement `abort()` in `src/neurogate/output/tts/base.py` and `espeak.py`, terminating audio within 100 ms
- [ ] T057 [US2] Implement `--cancel-at-ms` injection in the `replay` subcommand in `src/neurogate/cli.py`
- [ ] T058 [US2] Render the cancelled indication (and abort confirmation) in `src/neurogate/output/subtitles.py`
- [ ] T059 [US2] Extend `tests/unit/test_fsm_properties.py` with the ordering property: no `output_delivered` event may precede its `confirmation_resolved`

**Checkpoint**: US1 and US2 both pass independently.

---

## Phase 5: User Story 3 — Low-quality signal produces silence, not guesses (Priority: P2)

**Goal**: Degraded signal causes refusal with a clear message, and repeated faults
block output until an operator resets.

**Independent Test**: `neurogate replay --case fixtures/scripted/en-water.json
--snr-override -12` emits zero output events and shows the sensor-contact status.

### Tests for User Story 3 (write first) ⚠️

- [ ] T060 [P] [US3] Write `tests/unit/test_quality_gate.py` — frames below the floor are discarded, no sanitizer call occurs, incident counter increments, budget crossing → `FAULT`, and `FAULT` blocks all output
- [ ] T061 [P] [US3] Write `tests/integration/test_us3_degraded.py` — `--snr-override -12` produces zero output plus a visible status; `--fault-budget 1` with sustained drop reaches `FAULT`; over the full artifact corpus (`jaw-clench`, `blink`, `cough`, `movement`) at least 95% are rejected with no output (SC-002)

### Implementation for User Story 3

- [ ] T062 [US3] Wire the SNR floor and artifact flags into the orchestration loop in `src/neurogate/session.py`, before the FSM gate
- [ ] T063 [US3] Implement the fault budget and `FAULT` entry/exit in `src/neurogate/fsm/machine.py` and `session.py`, including the operator-only reset path
- [ ] T064 [US3] Implement the sensor-lost banner in `src/neurogate/output/subtitles.py` and the working `reset` subcommand in `src/neurogate/cli.py`
- [ ] T065 [US3] Implement `--snr-override` and `--fault-budget` flags in the `replay` subcommand in `src/neurogate/cli.py`

**Checkpoint**: Degradation refuses rather than guesses; recovery is operator-controlled.

---

## Phase 6: User Story 4 — Multilingual use in Sinhala, Tamil or English (Priority: P2)

**Goal**: Render the original script, speak with the session-primary voice, and
degrade to subtitles with a visible notice — never swapping language silently.

**Independent Test**: The same intent case in `si`, `ta`, and `en` renders the
correct script and selects the matching session-primary voice; with `--tts none`
only a subtitle event with `voice_locale: null` is emitted.

### Tests for User Story 4 (write first) ⚠️

- [ ] T066 [P] [US4] Write `tests/unit/test_language.py` — script-range detection for pure Sinhala (U+0D80–U+0DFF), pure Tamil (U+0B80–U+0BFF), English, mixed-script, and empty input → `UNKNOWN`
- [ ] T067 [P] [US4] Write `tests/unit/test_tts_router.py` — locale compatibility, unsupported locale yields subtitle-only, and no backend ever receives a different language
- [ ] T068 [P] [US4] Write `tests/integration/test_us4_multilingual.py` — three language runs plus `mixed-script.json`, asserting no mid-sentence `voice_locale` change in the event stream

### Implementation for User Story 4

- [ ] T069 [US4] Implement `src/neurogate/sanitize/language.py` — deterministic script-range detection plus the two-pass resolution from `research.md` R9, including `UNKNOWN`
- [ ] T070 [US4] Implement `src/neurogate/output/tts/router.py` — backend selection at session start, `supported_locales` check, and subtitle-only degradation
- [ ] T071 [US4] Make `src/neurogate/output/subtitles.py` script-aware: script-appropriate fallback font chain, script-aware line breaking, and no latin-1 transcode at any point
- [ ] T072 [US4] Emit the subtitle-only banner and `voice_locale: null` output events in `src/neurogate/output/subtitles.py`; never create a `TTS` event with a mismatched locale
- [ ] T073 [US4] Verify per-language lexicon selection in `src/neurogate/sanitize/prompts.py` by extending `tests/unit/test_prompts.py` to assert the correct lexicon is injected for each detected language — no new prompt-building code; T038 owns it
- [ ] T074 [US4] Add an assertion in `tests/integration/test_us4_multilingual.py` that the event stream contains zero locale changes within a single intent

**Checkpoint**: All three languages work; audio is best-effort and visibly labeled.

---

## Phase 7: User Story 5 — Operator runs a hardware-free demonstration (Priority: P3)

**Goal**: Run the entire pipeline from a replayed LSL stream with ground truth shown
beside the delivered output.

**Independent Test**: `neurogate serve` plus `neurogate replay --case ...` with no
headband produces identical pipeline behaviour to a live session.

### Tests for User Story 5 (write first) ⚠️

- [ ] T075 [P] [US5] Write `tests/unit/test_replay_outlet.py` — replay metadata satisfies `contracts/lsl-stream.md`, including `desc.replay = true` and paced timestamps
- [ ] T076 [P] [US5] Write `tests/integration/test_us5_replay_equivalence.py` — the replay path and a recorded live-frame fixture produce the same FSM state sequence

### Implementation for User Story 5

- [ ] T077 [US5] Implement the LSL outlet pacing and descriptor loader in `src/neurogate/ingest/replay_source.py` so replay is indistinguishable at the inlet
- [ ] T078 [US5] Implement `dashboards/app.py` as a 3-panel Streamlit view (raw signal, engine log, output) subscribing to the event stream; the FSM must stay in the core process
- [ ] T079 [US5] Implement the ground-truth comparator output (PASS / correctly rejected) in `src/neurogate/cli.py`
- [ ] T080 [US5] Write `docs/10-demo-runbook.md` — exact demo sequence, fallback video plan, and the "no hardware" judge answer

**Checkpoint**: Full hardware-free demo runs end to end.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Evidence, gates, and documentation accuracy.

- [ ] T081 [P] Implement `src/neurogate/bench.py` and the `bench` subcommand asserting the budgets in `research.md` R8
- [ ] T082 [P] Configure coverage gates in `pyproject.toml` (fail under 90% line) and add a CI step for the 100% branch requirement
- [ ] T083 [P] Write `tests/integration/test_accessibility.py` — contrast ratio check on the subtitle palette and a coarse-target assertion for the cancel control (SC-010)
- [ ] T084 [P] Write `tests/integration/test_no_retention.py` — run a marked utterance, then assert the marker is absent from the working directory, temp directory, and any spooled event file (SC-009)
- [ ] T085 [P] Update `README.md` — real install/run commands, current status table, and third-party acknowledgements (PhysioNet, Ollama model licence, eSpeak NG)
- [ ] T086 [P] Reconcile `docs/01-system-architecture.md`, `docs/02-agent-decision-loop.md`, and `docs/04-technical-stack.md` with any implementation deltas found during Phases 3–7
- [ ] T087 Run all nine scenarios in `quickstart.md` and record pass/fail with observed timing per scenario
- [ ] T088 [P] Write `tests/integration/test_network_guard.py` (blocked sockets, proving FR-013) plus `tests/unit/test_logging_redaction.py` confirming no payload text or secret reaches a log record
- [ ] T089 Final gate: `ruff check .`, `ruff format --check .`, `mypy --strict src/neurogate`, and the full `pytest` suite with branch coverage must all pass, with results recorded in `quickstart.md` and `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup — **BLOCKS all user stories**
- **User Stories (Phases 3–7)**: depend on Foundational; US1 is the MVP and should finish first
- **Polish (Phase 8)**: depends on the user stories it verifies (T081–T084 can start after US1; T085–T089 need all stories)

### User Story Dependencies

| Story | Depends on | Integrates with |
|-------|-----------|-----------------|
| US1 (P1) | Foundational | — |
| US2 (P1) | Foundational | US1's confirmation gate (replaces stub with real cancel) |
| US3 (P2) | Foundational | US1's orchestration loop (inserts pre-gate quality check) |
| US4 (P2) | Foundational | US1's output layer (replaces fixed locale with router) |
| US5 (P3) | Foundational | US1's ingest + CLI (adds outlet pacing and dashboard) |

US2–US5 may proceed in parallel once US1's checkpoint is reached, because each
touches a different module set except `session.py` (US2, US3) and `cli.py`
(US4, US5). Serialize edits to those two files if working concurrently.

### Within Each User Story

Tests (failing) → models/contracts → core service → wiring → integration → coverage check.

---

## Parallel Opportunities

**Setup**: T003, T004, T005, T006 are independent files and fully parallel.

**Foundational**: two parallel tracks —
`T008/T009/T010 → T011/T012/T013` (contracts) and
`T020/T021/T024/T026 → T022/T023/T025/T027` (FSM, calibration, buffer).
T014–T019 (config, telemetry) and T030/T031/T091 (fixtures) are independent of both.
T090 (transition history) extends `fsm/machine.py`, so it starts after T021.
T092–T095 are safety invariants over existing modules and can follow T028/T029.
`tests/unit/test_fsm_properties.py` is extended by T059; serialize T023 → T059.

**US1**: T032–T036 (tests) all parallel; T037–T040 (sanitizer) parallel; T041–T043
(DSP) parallel; T044/T045 (ingest) parallel; T047/T048 (output) parallel.

**US4**: T066–T068 (tests) parallel; T069 and T070 parallel.

**Polish**: T081–T086 mostly parallel.

### Parallel example — User Story 1 sanitizer track

```bash
Task: "Implement the loopback model client in src/neurogate/sanitize/client.py"
Task: "Implement per-language prompt construction in src/neurogate/sanitize/prompts.py"
Task: "Implement contract validation in src/neurogate/sanitize/validate.py"
Task: "Implement composite confidence scoring in src/neurogate/sanitize/confidence.py"
```

---

## Implementation Strategy

### MVP first (User Story 1 only)

1. Phase 1 → Phase 2 (contracts + FSM must be provable before anything else).
2. Phase 3 → run `neurogate replay --case fixtures/scripted/en-water.json --tts none`.
3. **STOP**: verify noise is removed and no audio is produced without confirmation.
4. This is demoable on its own and satisfies the core research claim.

### Incremental delivery

| Step | Adds | Demo value |
|------|------|-----------|
| Setup + Foundational | contracts, FSM, config | internal confidence |
| + US1 | filtered text delivery | the product thesis |
| + US2 | cancellable output | dignity argument |
| + US3 | refusal on bad signal | trust argument |
| + US4 | si/ta/en | +10 localization bonus |
| + US5 | dashboard + replay demo | competition-ready |
| + Polish | benchmarks, coverage, runbook | submission-ready |

### Team split (3 members, from `docs/09-roadmap-and-risks.md`)

| Member | Owns |
|--------|------|
| Signal/simulation | T041–T045, T060–T065, T075–T077, T091 |
| Middleware/SLM | T020–T025, T037–T040, T053–T059, T066, T069, T073, T090, T092–T095 |
| UI/output | T047–T051, T070–T072, T078–T080, T083–T085 |

---

## Notes

- `[P]` means different files and no dependency on an incomplete task — not merely
  "different task".
- Every test task must fail before its implementation task is started; record the
  failing output in the commit message or PR note (constitution workflow gate).
- Do not add persistence, a cloud call, or an actuation tool at any point — those
  require a constitution amendment, not a task.
- Commit after each logical group; stop at each checkpoint to validate the story
  independently.
