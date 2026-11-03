# Quickstart & Validation Guide — NeuroGate

This is a **validation guide**, not an implementation guide. It describes how to
prove each acceptance scenario from [spec.md](./spec.md) end to end once the code
exists. Commands refer to the planned CLI surface (`neurogate ...`) and the project
layout in [plan.md](./plan.md).

> Status: implementation pending. Nothing here has been executed yet.

## Prerequisites

| Requirement | Minimum | Check |
|-------------|---------|-------|
| Python | 3.11 | `python --version` |
| RAM | 8 GB (16 GB recommended) | — |
| Ollama | running locally | `ollama list` |
| Model | `llama3.2:3b` pulled | `ollama pull llama3.2:3b` |
| Offline TTS | eSpeak NG on `PATH` | `espeak-ng --version` |
| Network | not required at runtime | — |

Install and verify:

```bash
pip install -e ".[dev]"
neurogate doctor
```

`doctor` checks: Python version, model presence, TTS backend availability and
declared locales, config schema validity, and that no network egress path is
configured. Expected: every line `OK`, exit code 0.

## Validation scenario 1 — Noise is filtered, intent is delivered

Proves FR-002, FR-003, FR-005, FR-009, SC-001.

```bash
neurogate replay --case fixtures/scripted/si-water-glass.json --language si --tts none
```

Expected:

- FSM transitions logged: `PASSIVE → TRIGGER_DETECTED → BUFFERING → SANITIZING →
  AWAITING_CONFIRMATION → SPEAKING → PASSIVE`.
- Staged text equals the scripted intended sentence.
- The two noise fragments appear as `rejected_count: 2` in the event stream, and
  their text is visible only in the local rejection panel.
- Subtitle event contains the intended sentence; no TTS event because `--tts none`.
- Ground-truth comparison printed at the end: `PASS`.

## Validation scenario 2 — Transient artifact produces nothing

Proves FR-002, FR-003, SC-002.

```bash
neurogate replay --case fixtures/scripted/jaw-clench.json --tts none
```

Expected: `TRIGGER_DETECTED → PASSIVE` on the transient path; zero `intent_staged`
events; zero output events; ground-truth comparison `PASS (correctly rejected)`.

## Validation scenario 3 — Confirmation window: expiry approves, cancel suppresses

Proves FR-007, FR-008, SC-003, SC-005.

```bash
# Expiry: do not send a cancel, let the 1.5 s window elapse
neurogate replay --case fixtures/scripted/en-water.json --tts none

# Cancel: script injects a cancel at 600 ms
neurogate replay --case fixtures/scripted/en-water.json --cancel-at-ms 600 --tts none
```

Expected:

- Expiry run: exactly one `confirmation_resolved` with `decision: TIMEOUT`, followed
  by one output event.
- Cancel run: `decision: CANCELLED`, **zero** output events, `SILENT_DROP` shown.
- In neither run does an output event precede a `confirmation_resolved` event.

## Validation scenario 4 — Degraded signal refuses instead of guessing

Proves FR-002, FR-014, FR-017, SC-004.

```bash
neurogate replay --case fixtures/scripted/en-water.json --snr-override -12
```

Expected: frames discarded, zero sanitizer calls, zero output events, visible
"sensor contact" status. Repeat with `--fault-budget 1` and a sustained drop to
confirm transition to `FAULT` and that no further output occurs until
`neurogate reset`.

## Validation scenario 5 — Multilingual round trip

Proves FR-010, FR-011, SC-007, and the localization bonus claim.

```bash
neurogate replay --case fixtures/scripted/si-water-glass.json --language si --tts espeak
neurogate replay --case fixtures/scripted/ta-water-glass.json --language ta --tts espeak
neurogate replay --case fixtures/scripted/en-water.json        --language en --tts espeak
```

Expected per language:

- Subtitle renders the correct script (check the rendered payload, not the console
  encoding).
- TTS event carries `voice_locale` matching the session primary.
- Mixed-script case: text renders as-is, voice stays the session primary, and no
  mid-sentence locale change appears in the event stream.
- With `--tts none`: subtitle event only, `voice_locale: null`, visible
  subtitle-only banner.

## Validation scenario 6 — Sanitizer contract rejection

Proves FR-006, and the silent-drop path.

```bash
neurogate replay --case fixtures/scripted/en-water.json --fake-sanitizer malformed
neurogate replay --case fixtures/scripted/en-water.json --fake-sanitizer contradiction
neurogate replay --case fixtures/scripted/en-water.json --fake-sanitizer low-confidence
```

Expected: `SCHEMA_INVALID` (first two) and `SILENT_DROP` without output (all three).
No raw model string is ever forwarded to output.

## Validation scenario 7 — Consent gate

Proves FR-020.

```bash
neurogate replay --case fixtures/scripted/en-water.json --no-consent
```

Expected: startup error `CONSENT_MISSING`, non-zero exit, no stream opened, no
output. Confirm with `neurogate doctor` that no capture process started.

## Validation scenario 8 — No content leaves the device

Proves FR-012, SC-009.

1. Run scenario 1 with a unique marker sentence.
2. After the session exits, grep the working directory, temp directory, and the
   event-stream file for the marker.

Expected: zero matches. The event stream contains `sanitized_text` for the live
display but is in-memory/loopback only; if the dashboard spools it, that buffer must
be verified to be ephemeral and match the retention matrix in
[data-model.md](./data-model.md).

## Validation scenario 9 — Accessibility surface

Proves FR-021, SC-010.

- Run a contrast audit (e.g. axe or a manual ratio check) on the rendered subtitle
  surface at the default and maximum text sizes: expected WCAG 2.1 AA pass for
  normal and large text.
- Operate the cancel control with a coarse input (large hit area, no drag): expected
  success in at least 9 of 10 trials.

## Automated verification

```bash
pytest tests/unit tests/contract            # fast, no model, no network
pytest tests/integration --fake-sanitizer    # replay → output end to end
pytest --cov=src/neurogate --cov-branch
ruff check . && ruff format --check .
mypy --strict src/neurogate
```

Gates (constitution Principle IV): overall line coverage ≥ 90%; 100% branch coverage
for `fsm/machine.py`, `sanitize/validate.py`, `sanitize/confidence.py`.

## Performance check

```bash
neurogate bench --replay fixtures/replay/physionet-sample --iterations 50
```

Expected on the reference device: DSP p95 ≤ 25 ms, FSM p95 ≤ 2 ms, sanitize p95 ≤
2.5 s, validation p95 ≤ 10 ms, end-to-end p95 ≤ 4.5 s (SC-006).

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|-------------|--------|
| `MODEL_UNAVAILABLE` | Ollama not running or model not pulled | `ollama serve`, `ollama pull llama3.2:3b` |
| Sanitizer always times out | Model cold on a slow CPU | Warm the model once at startup; check `timeout_ms` in config |
| All frames rejected | Calibration not run or SNR floor too high | Re-run `neurogate calibrate`, inspect baseline |
| No voices for `si-LK` | eSpeak NG missing or bundle lacks voice | Install eSpeak NG; system degrades to subtitles by design |
| Dashboard shows nothing | Core event port mismatch | Compare `ui.event_port` in config with `neurogate serve` output |
| Constant triggers | Threshold too low for this user | Raise `k`/hold floor; re-calibrate |
