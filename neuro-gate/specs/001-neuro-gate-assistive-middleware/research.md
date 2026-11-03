# Phase 0 Research — NeuroGate

Every open technical question from Technical Context is resolved here. Each entry
records the decision, why it was chosen, and what was rejected.

---

## R1. Biosignal transport and hardware-free operation

**Decision**: Lab Streaming Layer (LSL) via `pylsl` is the sole ingest contract. Two
inlet implementations sit behind one interface: `LiveLslInlet` (vendor driver
outlet) and `ReplayLslOutlet` (dataset replay plus a synthetic sEMG envelope
generator).

**Rationale**: LSL is the de facto standard for biosignal time series and is
supported by OpenBCI, BrainFlow bridges, Muse, and most research rigs. It gives
timestamps and clock correction for free. Making replay an outlet rather than a
special code path means the DSP, FSM, and everything downstream are byte-identical
in demo and hardware runs, which is both an honesty requirement for the demo and a
testability requirement.

**Alternatives considered**:

| Alternative | Rejected because |
|-------------|------------------|
| Vendor SDKs directly (BrainFlow native, OpenBCI) | Couples the system to one vendor; violates FR-001 |
| CSV/parquet file playback | No timestamps, no real-time pacing, no live path |
| Custom WebSocket protocol | Reinvents LSL without the ecosystem |
| Mock sensor object in tests | Tests would not exercise the real serialization edge |

**Replay corpus**: PhysioNet EEG Motor Imagery Dataset for realistic EEG
statistics (it is open and redistributable with attribution), plus
scripted sEMG envelopes with known onset times. Scripted cases carry ground-truth
intent text so evaluation can compute precision/recall rather than eyeball output.

---

## R2. Intent gating engine

**Decision**: A hand-written deterministic finite-state machine implemented as an
explicit transition table (state × event → state + side-effect tag), not a graph
framework.

**Rationale**: The gate is a safety boundary. Its behaviour must be provable and
fully branch-covered. A transition table is enumerable — every cell can be
asserted, and `hypothesis` can fuzz event sequences looking for illegal states.
The constitution's Principle IV requires 100% branch coverage on boundary
modules; a table is the only shape where that claim is verifiable.

**Alternatives considered**:

| Alternative | Rejected because |
|-------------|------------------|
| LangGraph (listed in the competition stack) | Adds a runtime dependency and implicit behaviour for a 10-state machine; state persistence semantics conflict with the RAM-only rule by default |
| `transitions` library | Convenient, but callbacks hide the transition table from static inspection and from `hypothesis` fuzzing |
| LLM decides whether to speak | Hallucinated triggers are the exact failure mode being fixed |
| Rules scattered across `if` statements | Not enumerable, not coverable |

**Note**: LangGraph remains a legitimate alternative if the FSM later grows
concurrent branches (multi-agent clarification). It is not needed for v1 and its
default persistence must be explicitly disabled before adoption.

---

## R3. Semantic sanitizer model and prompting

**Decision**: Ollama serving a quantized 3B-class model (`llama3.2:3b` primary,
`phi3:mini` fallback), called over loopback with a JSON-constrained response. The
prompt embeds: (a) a per-language noise lexicon, (b) the fixed output schema, and
(c) three few-shot examples per language.

**Rationale**: The sanitizer needs cross-lingual semantic judgement, not
classification of fixed phrases; a 3B model is the largest that stays inside the
8–16 GB reference envelope while leaving room for DSP buffers and the dashboard.
Ollama gives local model lifecycle without shipping Python bindings into the
critical path, and its `format: json` mode plus Pydantic validation makes the
output contract enforceable.

**Alternatives considered**:

| Alternative | Rejected because |
|-------------|------------------|
| Hosted LLM (GPT/Claude) | Sends private thought content off-device; violates the project's core privacy claim |
| Fine-tuned tiny classifier | Fast and cheap, but cannot generalize to unseen phrasings in three languages with the data available |
| Rule-based stopword stripping | Brittle; removes content words in agglutinative Sinhala/Tamil |
| Two-model ensemble | Doubles latency for unproven gain in v1; kept as a research option |

### R3.1 Confidence calibration (resolves the spec's undefined "confidence")

**Decision**: Confidence is a **composite**, not the model's self-report:

```
confidence = 0.5 * schema_and_contradiction_score
           + 0.3 * language_consistency_score
           + 0.2 * model_reported_score
```

`schema_and_contradiction_score` is 1.0 only when the JSON is valid, `sanitized_text`
is non-empty, and it does not appear inside `rejected_noise`. `language_consistency`
is 1.0 when the script of `sanitized_text` is compatible with the session-primary
language. Only the last term depends on the model.

**Rationale**: LLM self-reported confidence is poorly calibrated, especially for
low-resource languages. Weighting it at 20% means a fluent-sounding hallucination
cannot clear the 0.75 floor on its own, while a deterministic schema failure
immediately halves the score. The weights and the 0.75 floor are configuration, and
will be tuned on the evaluation set rather than hard-coded.

**Open research item**: the exact weight vector is calibrated on the multilingual
evaluation corpus in M9; v1 ships the values above as defaults.

---

## R4. Offline multilingual text-to-speech

**Decision**: A `TextToSpeech` protocol with three backends in preference order:
(1) Web Speech API in the optional browser surface, (2) eSpeak NG invoked as a
local process, (3) subtitle-only fallback. The backend is chosen at session start
and never switched mid-sentence.

**Rationale**: FR-013 forbids network access, which rules out `gTTS` and every
cloud TTS. eSpeak NG is small, offline, permissively licensed, and provides both
Sinhala (`si`) and Tamil (`ta`) voices — the only widely available offline engine
that covers both. Its output is robotic, which is acceptable for a prototype whose
guaranteed channel is text. The protocol keeps the rest of the system ignorant of
which backend exists.

**Alternatives considered**:

| Alternative | Rejected because |
|-------------|------------------|
| `gTTS` | Requires network; violates FR-013 |
| Windows SAPI / `pyttsx3` alone | Usually lacks `si-LK` and `ta-LK` voices; platform-dependent |
| Piper neural TTS | Better quality, but Sinhala/Tamil voice coverage is incomplete and per-language model sizes complicate the 8 GB envelope |
| Cloud TTS with a cached-audio workaround | Still a network dependency and a privacy surface |

**Constraint recorded**: audio is best-effort. If no voice covers the session-primary
language, the system renders subtitles and shows a visible banner (FR-010, SC-007).

---

## R5. Dashboard and process split

**Decision**: Streamlit runs as a separate process that subscribes to a
newline-delimited JSON event stream published by the core session on loopback. The
core session owns the FSM and never imports Streamlit.

**Rationale**: Streamlit reruns the script on every interaction. Hosting the FSM in
that process would make state transitions depend on UI timing, destroying
determinism and the ability to test the FSM headlessly. A one-way event stream also
gives the dashboard no way to push content back into the intent loop, which keeps
the human gate honest.

**Alternatives considered**:

| Alternative | Rejected because |
|-------------|------------------|
| FSM inside Streamlit | Rerun semantics corrupt state timing |
| Gradio | Same rerun model, less mature for multi-panel time-series rendering |
| Custom web UI (Next.js) | More surface area to build and test than the prototype needs |
| Log file the dashboard tails | Would write thought content to disk; violates FR-012 |

**Event payload rule**: the stream carries state names, timings, scores, language
tags, and sanitized text — never raw biosignals and never rejected-noise content
beyond a count.

---

## R6. DSP parameters and calibration

**Decision**: 50 Hz notch; sEMG 20–250 Hz 4th-order Butterworth (zero-phase
`sosfiltfilt`); EEG 1–45 Hz; 50 ms RMS envelope; 1 s Welch PSD at 50% overlap.
Trigger threshold derived from a guided calibration:

```
threshold = p95(rest) + k * (median(guided_attempts) - p95(rest)),  k = 0.6
```

**Rationale**: Values are standard for subvocal sEMG and dry-electrode EEG. The
calibration formula is deliberately conservative: anchoring to the noise floor
rather than the attempt amplitude prevents a user who speaks loudly from producing
constant triggers. `k` stays in configuration because electrode impedance varies.
Zero-phase filtering is used so onset latency is not shifted, which matters for the
hold-time test.

**Alternatives considered**: fixed global thresholds (fail across users); adaptive
LMS filtering (needs a reference channel the headbands do not offer); ICA
artifact removal (requires more channels and a clean reference; deferred to
research).

---

## R7. Testing strategy

**Decision**: Four layers, no network, no model in unit tests.

| Layer | Tool | What it proves |
|-------|------|----------------|
| Contract | `pytest` + JSON schema fixtures | Every model round-trips; malformed input is rejected with the right error code |
| Unit | `pytest` | Filters, features, SNR, confidence composition |
| Property | `hypothesis` | No event sequence can enter an illegal FSM state; no output event lacks a confirmation decision |
| Integration | `pytest` + fakes | Replay descriptor → sanitized output → delivered text, with a fake sanitizer returning scripted JSON |

**Rationale**: Determinism requires that the model never runs in a test. The fake
sanitizer returns a fixed corpus of valid, invalid, contradictory, and low-confidence
responses, which is also the fixture set used to calibrate the confidence floor.

**Coverage targets** (constitution): ≥90% line overall; 100% branch on
`fsm/machine.py`, `sanitize/validate.py`, `sanitize/confidence.py`.

---

## R8. Latency measurement and budgets

**Decision**: Instrument each tier with monotonic timestamps and emit a
`TimingRecord` per intent cycle into the event stream. Budgets are asserted in a
benchmark test on recorded feature frames, not measured by hand.

**Rationale**: SC-006 is an end-to-end claim; the only way to defend it is a
repeatable measurement. Recording per-stage p50/p95 also tells the operator which
stage to blame during a live demo.

**Reference budget** (from [docs/02](../../docs/02-agent-decision-loop.md) §3):
DSP ≤ 25 ms p95, FSM ≤ 2 ms p95, sanitize ≤ 2.5 s p95, validation ≤ 10 ms,
confirmation 1.5 s fixed, total ≤ 4.5 s p95.

---

## R9. Multilingual detection

**Decision**: Two-pass detection — deterministic Unicode script-range check first,
model hint second, session-primary as tiebreaker with `UNKNOWN` reported when the
composite is below the floor.

**Rationale**: Script ranges are exact for pure Sinhala/Tamil/English and cost
nothing. The model is only consulted for code-mixed buffers, where a 3B model is
more reliable than trying to write per-phrase heuristics. `UNKNOWN` never reaches
TTS with a guessed locale; it renders as text only.

**Alternatives considered**: `langdetect`/`lingua` (trained on Latin scripts, poor on
Sinhala), per-token classifier (over-engineering before the corpus exists).

---

## R10. Evaluation corpus

**Decision**: Build a synthetic-but-labelled corpus of triples
`(raw_thought_buffer, noise_fragments[], intended_sentence, language)` with at least
150 entries across the three languages, sourced from bilingual volunteers and
clearly declared as synthetic in the paper.

**Rationale**: No public corpus of *inner monologue with affective noise* exists.
Claiming real-world validity from a synthetic set would be dishonest; instead the
corpus is described as scripted cases with explicit ground truth, and the paper
reports precision/recall on it as an upper bound with a stated limitation.

**Alternatives considered**: collecting real inner-speech data (ethics approval and
consent overhead beyond the project window; also creates a biometric dataset the
project explicitly refuses to retain).

---

## Resolved unknowns

| Technical Context field | Resolution |
|------------------------|------------|
| Language/version | Python 3.11+ (constitution, R2) |
| Primary dependencies | `pylsl`, `numpy`, `scipy`, `pydantic` v2, `httpx`, Ollama, `streamlit`, eSpeak NG, `pytest`, `hypothesis`, `ruff`, `mypy` (R1, R3, R4, R5) |
| Storage | None — RAM only (ADR 0002) |
| Testing | Four-layer `pytest` strategy, no network (R7) |
| Target platform | x86-64 edge device, Windows/Linux/macOS (R4, R5) |
| Project type | Single installable Python project (plan structure) |
| Performance goals | Measured per-stage budgets (R8) |
| Constraints | Offline, single-user, no actuation, no persistence (R1, R4, R5) |
| Scale/scope | 1 user, 12 channels @ 1000 Hz, 3 languages, 1 dashboard (R5) |
