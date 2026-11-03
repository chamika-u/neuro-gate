# Contract: LSL Biosignal Stream

**Boundary**: sensor or replay outlet → NeuroGate ingest
**Direction**: inbound only
**Transport**: Lab Streaming Layer (LSL), one stream per modality

## Required stream shape

Two logical streams are expected. They may be published by one device or two.

| Stream | `type` | Channels | Rate | Channel format |
|--------|--------|----------|------|----------------|
| EEG | `EEG` | 8 nominal | 1000 Hz nominal | `float32` |
| sEMG | `EMG` | 4 nominal | 1000 Hz nominal | `float32` |

A single combined stream is also acceptable if its channel metadata declares the
modality per channel; the inlet must not guess from channel count.

## Metadata requirements

| Field | Required | Rule |
|-------|----------|------|
| `name` | yes | stable per session; used as `stream_id` |
| `type` | yes | `EEG` or `EMG` |
| `channel_count` | yes | 1–32 |
| `nominal_srate` | yes | 100–2000 Hz |
| `channel_format` | yes | `float32` |
| `source_id` | recommended | used to disambiguate two devices |
| `desc` | recommended | units and electrode labels when available |

## Timing rules

1. LSL timestamps are authoritative. Wall-clock time is never used for alignment.
2. Frames whose timestamp is not strictly greater than the previous frame for the
   same stream are dropped and counted as `TIMESTAMP_DESYNC`.
3. Clock offset correction is enabled; a residual offset above 50 ms raises
   `TIMESTAMP_DESYNC` and blocks sanitization until resolved.
4. A gap longer than 250 ms discards the in-progress buffer.

## Failure behaviour

| Condition | Behaviour |
|-----------|-----------|
| Stream disappears for > 1 s | FSM → `FAULT`; dashboard shows sensor-lost banner |
| NaN or Inf sample | frame dropped, counter incremented |
| Channel count changes mid-session | `CONFIG_INVALID`; session must restart |
| Rate below 100 Hz or above 2000 Hz | stream rejected at discovery |
| No EEG stream, only sEMG | permitted; affect features unavailable, SNR gate uses sEMG only |

## Replay outlet

The replay source publishes a stream satisfying this contract exactly, using a
recorded descriptor plus a paced timer. It must be indistinguishable from hardware
at the inlet. Replay metadata additionally sets `desc.replay = true`, which the
dashboard displays and which never affects processing behaviour.
