# Implementation Plan: NeuroGate — Intent-Gated Assistive Communication Middleware

**Branch**: `001-neuro-gate-assistive-middleware` | **Date**: 2026-11-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/neuro-gate/specs/001-neuro-gate-assistive-middleware/spec.md`

## Summary

Build a hardware-agnostic, offline assistive middleware that converts a continuous
EEG/sEMG biosignal stream into a small number of confirmed, noise-free utterances.
The technical approach is a four-tier pipeline: LSL ingest and bounded ring buffers,
deterministic DSP with an SNR gate, a deterministic finite-state intent gatekeeper,
and a local small language model that separates deliberate content from affective
noise. A human confirmation window precedes every audio emission, and a local TTS
adapter speaks the sanitized text with the session-primary voice.

Everything runs on one edge device. No cloud inference, no persistence, no
actuation tools. A replayed biosignal source is a first-class input so the entire
system is testable and demonstrable without a physical headband.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pylsl` (biosignal transport), `numpy` + `scipy` (DSP),
`pydantic` v2 (boundary contracts), `httpx` (loopback client for the local model
runtime), Ollama with `llama3.2:3b` / `phi3:mini` quantized weights (semantic
sanitizer), `streamlit` (operator/debug dashboard), `eSpeak NG` or `pyttsx3`
(offline TTS backend), `pytest` + `hypothesis` (tests), `ruff` + `mypy` (quality
gates)

**Storage**: No business-data store — RAM-only ring buffers and session-scoped objects; no
database, no durable business-data writes. The only on-disk artifact is the static,
read-only configuration file (`config/default.toml`). See
[ADR 0002](../../docs/adr/0002-ephemeral-state.md).

**Testing**: `pytest` with a fake LSL source and an in-process fake sanitizer.
`hypothesis` for the FSM transition table and contract validation boundaries.
No network access in tests; no model invocation in unit tests.

**Target Platform**: Single edge device — Windows, Linux, or macOS on x86-64, or an
ARM64 device with equivalent memory. Browser is required only for the optional
Web Speech API TTS path.

**Project Type**: Single project — an installable Python library plus a thin CLI and
a local dashboard.

**Performance Goals**: End of subvocal attempt to audio start under 5 s at p95 on
the reference device (target p50 ≈ 2.5 s). DSP feature extraction ≤ 25 ms p95 per
frame. FSM transition ≤ 2 ms p95. Sanitizer call ≤ 2.5 s p95 (warm model).

**Constraints**: Offline at runtime; single active user per device; 8–16 GB RAM;
no irreversible actions; no thought content written to disk; all inference on the
edge; WCAG 2.1 AA subtitle surface; session-primary language never switched
mid-sentence.

**Scale/Scope**: One user, one sensor stream, one session at a time. Roughly 8 EEG
channels and 4 sEMG channels at 1000 Hz. Prototype scope is three languages
(Sinhala, Tamil, English) and one dashboard.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status | Notes |
|-----------|------|--------|-------|
| I. Stateless by Design (NON-NEGOTIABLE) | No durable store, no cross-request state in business outcomes | **PASS (constitution v1.1.0)** | Thought content never leaves the cycle and never touches disk. Two bounded, content-free session values (calibration baseline, rolling gate threshold) influence thresholds only, under the bounded session exception added in constitution v1.1.0 and recorded in [ADR 0002](../../docs/adr/0002-ephemeral-state.md). |
| II. Pydantic-Validated Data Contracts | Every boundary crossing is a validated model; no raw dicts | **PASS** | Contract set defined in [data-model.md](./data-model.md); enforced at LSL edge, sanitizer edge, TTS edge, and event-stream edge. |
| III. Code Quality & Maintainability | Typed public API, lint + format + type-check clean, docstrings, no dead code | **PASS** | `ruff format` + `ruff check` + `mypy --strict` on `src/neurogate`. |
| IV. Test-First with Mandatory Edge-Case Coverage (NON-NEGOTIABLE) | Tests precede implementation; ≥90% line coverage; 100% branch on validation/boundary modules | **PASS** | Boundary modules are exactly the FSM transition table and the contract validators, which are fully enumerable. Red-Green-Refactor enforced per task. |
| V. UX Consistency & Performance | Single envelope/error schema, one pagination/timestamp convention, p95 300 ms interactive read budget, validation < 10 ms | **PASS (constitution v1.1.0)** | Error envelope and timestamp convention apply. The 300 ms budget applies to interactive reads; the local SLM generative path uses the generation budget added in constitution v1.1.0 (4.5 s p95 end to end, see [docs/02](../../docs/02-agent-decision-loop.md) §3). Validation overhead target is ≤ 10 ms and is measured per frame. |
| Additional constraints | Python 3.11+, Pydantic v2 only, no external DB, secrets from env, secrets never logged, no durable business writes | **PASS** | Model names and paths from env/config; no secret is required at runtime. |

**Verdict**: PROCEED. Two deviations are documented, bounded, and justified in
Complexity Tracking; neither weakens the privacy or validation guarantees.

## Project Structure

### Documentation (this feature)

```text
neuro-gate/specs/001-neuro-gate-assistive-middleware/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
neuro-gate/
├── pyproject.toml
├── config/
│   ├── default.toml                 # thresholds, windows, budgets
│   ├── noise_lexicon.si.toml        # Sinhala noise examples
│   ├── noise_lexicon.ta.toml        # Tamil noise examples
│   └── noise_lexicon.en.toml        # English noise examples
├── src/neurogate/
│   ├── __init__.py
│   ├── contracts/                   # Pydantic v2 models (the only boundary types)
│   │   ├── signals.py
│   │   ├── intents.py
│   │   └── events.py
│   ├── ingest/
│   │   ├── lsl_inlet.py             # live sensor inlet
│   │   ├── replay_source.py         # dataset replay + synthetic envelope
│   │   └── ring_buffer.py           # bounded, content-expiring
│   ├── dsp/
│   │   ├── filters.py               # notch, bandpass
│   │   ├── features.py              # RMS envelope, Welch band power
│   │   └── quality.py               # SNR estimate, artifact flags
│   ├── fsm/
│   │   ├── states.py                # enums
│   │   ├── machine.py               # deterministic transition table
│   │   └── calibration.py           # baseline + threshold derivation
│   ├── sanitize/
│   │   ├── client.py                # loopback Ollama client
│   │   ├── prompts.py               # per-language system prompts
│   │   ├── validate.py              # schema + contradiction checks
│   │   └── confidence.py            # composite confidence scoring
│   ├── output/
│   │   ├── subtitles.py             # UTF-8 render payload
│   │   └── tts/
│   │       ├── base.py              # TextToSpeech protocol
│   │       ├── espeak.py            # offline backend
│   │       └── webspeech.py         # optional browser backend
│   ├── session.py                   # orchestration + human gate
│   ├── errors.py
│   └── cli.py
├── dashboards/
│   └── app.py                       # Streamlit 3-panel view
└── tests/
    ├── contract/                    # schema round-trips, rejection cases
    ├── integration/                 # replay -> output end to end
    ├── unit/                        # dsp, fsm, validate, confidence
    └── fixtures/
        ├── replay/                  # recorded/anonymised stream descriptors
        └── scripted/                # ground-truth intent + noise cases
```

**Structure Decision**: Single project. The system is one local process tree with
a UI front-end, not a client/server application — there is no backend to separate.
Tiers are expressed as packages (`ingest`, `dsp`, `fsm`, `sanitize`, `output`)
because each is independently testable and the FSM must be provable in isolation.
`contracts/` is a package rather than a module because every tier imports it and
it is the constitution's enforcement point.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Ephemeral session state (calibration baseline, rolling gate threshold) influences behaviour, which a literal reading of Principle I forbids | A trigger threshold that cannot adapt to the individual user produces either constant false activations or constant misses; sEMG amplitude varies widely across users and electrode placement | A truly stateless per-frame gate would have to ship one global threshold, which fails calibration for a large share of users; persisting profiles would be worse and is explicitly out of scope |
| p95 300 ms interactive budget is not met by the SLM stage | Local semantic filtering of a 3B model on CPU takes ~1–2.5 s; there is no cloud round-trip to parallelize and no smaller model that meets multilingual quality | Removing the SLM returns to single-pass decoding, which is the exact failure mode the project exists to fix; splitting into a tiny classifier plus SLM is retained in research as a fallback, not a default |
| One extra process boundary between the dashboard and the core session | The dashboard must not be able to block the intent loop or hold audio state; Streamlit reruns are not compatible with a deterministic state machine | Running the FSM inside the Streamlit process would make transitions depend on UI rerun timing, which breaks determinism and testability |

## Execution Phases

### Phase 0 — Research

Resolve the open technical questions before design: transport and replay strategy,
FSM engine choice, sanitizer prompting and confidence calibration, offline
multilingual TTS, and the test strategy. Output: [research.md](./research.md).

### Phase 1 — Design & Contracts

Produce the validated data model, the interface contracts, and the runnable
validation guide:
[data-model.md](./data-model.md), [contracts/](./contracts/),
[quickstart.md](./quickstart.md).

### Phase 2 — Tasks

Deferred to `/speckit.tasks`. Ordering constraint for task generation: contract
models first, then FSM (fully tested), then DSP, then sanitizer, then output, then
orchestration, then dashboard, because every later tier depends on the earlier
one's contracts.

## Post-Design Constitution Re-check

*Re-evaluated after Phase 1 artifacts were written.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Stateless | PASS (documented deviation) | `data-model.md` marks every entity `session-scoped` or `cycle-scoped`; no `persist` behaviour exists; `contracts/event-stream.schema.json` is PII-free by construction. |
| II. Pydantic contracts | PASS | Every boundary in `contracts/` has an explicit model and rejection rule; `data-model.md` lists a validation rule per field. |
| III. Code quality | PASS | Structure above fixes public module boundaries; `mypy --strict` applies to `src/neurogate` only. |
| IV. Test-first | PASS | `quickstart.md` enumerates the red-first acceptance scenarios; FSM and validators are fully enumerable branch surfaces. |
| V. UX & performance | PASS (documented deviation) | Single error envelope defined in `contracts/event-stream.schema.json`; SLM budget is explicit and measured, not implied. |

No new gate failures. Implementation may proceed.
