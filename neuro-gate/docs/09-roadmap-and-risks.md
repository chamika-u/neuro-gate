# 09 — Roadmap & Risk Register

## 1. Milestones

Two tracks run in parallel. The prototype track is time-boxed by the competition;
the research track is longer and takes the prototype as its artifact.

| # | Milestone | Target | Deliverable | Track |
|---|-----------|--------|-------------|-------|
| M0 | Specification + architecture | done | this document set | both |
| M1 | LSL replay simulator + DSP | Phase 2 window | replayable EEG/sEMG stream, feature frames, SNR gate | prototype |
| M2 | FSM intent gatekeeper | Phase 2 window | deterministic state machine + transition tests | prototype |
| M3 | Local SLM sanitizer | Phase 2 window | Ollama client, strict JSON contract, confidence floor | prototype |
| M4 | Output layer | Phase 2 window | subtitle renderer + TTS with locale selection | prototype |
| M5 | Demo dashboard + video | Phase 2 deadline | 3-panel dashboard, 10-minute demo recording, README | prototype |
| M6 | Competition submission | Phase 2 deadline | runnable repo + status report | prototype |
| M7 | Confirmation gate + safety tests | Grand Finale | cancellable utterances, fault-injection tests | both |
| M8 | Benchmark suite v1 | +2 months | ground-truth corpus, false-activation and over-filter metrics | research |
| M9 | Multilingual evaluation | +4 months | si/ta/en noise rejection and intent-retention results | research |
| M10 | Open-source library release | +6 months | modular package, docs, examples | research |
| M11 | Paper submission | +6–12 months | empirical evaluation, IEEE venue | research |

Timeline dates for M1–M6 come from the published competition schedule; they are
not commitments made by this document.

## 2. Research questions

| # | Question | Why it matters | Instrument |
|---|----------|----------------|------------|
| RQ1 | Can a deterministic FSM meaningfully reduce false activations compared with a signal→text baseline? | The core claim | false activations per minute at matched recall |
| RQ2 | Does a small local SLM strip affective noise without removing genuine intent? | The privacy/dignity value | precision/recall on a labelled noise corpus |
| RQ3 | How much does multilingual noise differ from English noise? | Localization claim | per-language error breakdown |
| RQ4 | What confirmation delay is acceptable before users abandon the device? | Product viability | user study, time-to-speak |
| RQ5 | Is on-device SLM latency acceptable end to end? | Deployability | p50/p95 per stage |

## 3. Risk register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| K1 | No physical headband available for validation | high | high | LSL replay simulator as a first-class path; hardware-agnostic contract |
| K2 | sEMG trigger thresholds are user-specific and unstable | high | high | mandatory calibration gate; rolling baseline; refuse when SNR is low |
| K3 | Sinhala/Tamil SLM quality too weak for reliable filtering | medium | high | per-language noise lexicons; evaluate a dedicated classifier before the SLM |
| K4 | Latency makes conversation feel broken | medium | high | DSP is cheap; only SLM is slow; stage output during the confirmation window |
| K5 | Over-filtering removes genuine intent | medium | high | rejected fragments visible locally; retry prompt; tunable lexicon |
| K6 | Scope creep toward actuation | medium | high | explicit non-goals; no irreversible tools; ADR required to add one |
| K7 | Competition IP exposure | medium | medium | reference architecture documented, implementation repo access controlled |
| K8 | "Mind reading" overclaim in pitch or paper | medium | high | fixed, narrow claims in every artefact: gating and sanitization only |
| K9 | TTS voice missing on target platform | medium | medium | subtitles are the guaranteed channel; visible fallback banner |
| K10 | Privacy incident from logging | low | high | fault logs carry codes only; ADR 0001 and ADR 0002 |

## 4. Out of scope for v1

- Custom electrode or headband design.
- Training a neural decoder from scratch.
- Clinical validation or regulatory submission.
- Any cloud service, account system, or multi-device sync.
- Emergency calling or any irreversible action.
- Languages beyond Sinhala, Tamil, English.

## 5. Definition of done (prototype)

- [ ] Replayed LSL stream drives the full pipeline with no hardware.
- [ ] FSM transition table is fully covered by tests, including every rejection
      path and both fault paths.
- [ ] Sanitizer returns schema-valid JSON or produces a silent drop; never
      passes raw model output through.
- [ ] Confirmation gate can be cancelled in practice, not just in theory.
- [ ] All three languages render and speak, or degrade to subtitles with a
      visible banner.
- [ ] No code path writes thought content to disk.
- [ ] README reproduction steps work on a clean machine with a documented
      hardware profile.
