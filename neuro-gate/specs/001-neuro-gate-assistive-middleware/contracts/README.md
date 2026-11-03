# Contracts — NeuroGate

Interface contracts for the three boundaries the system actually exposes, plus the
two internal process boundaries that must stay stable. Each contract states what is
allowed across the boundary and what happens when the other side misbehaves.

| Contract | Boundary | Format | Enforced by |
|----------|----------|--------|-------------|
| [LSL stream](./lsl-stream.md) | sensor → ingest | LSL stream metadata + samples | `ingest/` inlet validation |
| [Sanitizer](./sanitized-intent.schema.json) | core → local model | JSON (Ollama `/api/generate`) | `sanitize/validate.py` |
| [TTS adapter](./tts-adapter.md) | core → speech backend | Python protocol | `output/tts/base.py` |
| [Event stream](./event-stream.schema.json) | core → dashboard | newline-delimited JSON | publisher schema check |
| [Configuration](./config.schema.json) | operator → core | TOML validated as JSON | `contracts/` + startup gate |

## Universal rules

1. **Validate before use.** A payload is parsed into a Pydantic model at the edge.
   Invalid payloads are rejected with a stable error code and never reach logic.
2. **No content in telemetry.** Event-stream and fault payloads carry codes,
   timings, counts, and language tags — never raw biosignals, never rejected-noise
   text, never an unbounded thought buffer.
3. **No silent coercion.** Missing required fields, wrong types, and out-of-range
   numbers are errors, not defaults.
4. **No version negotiation.** A version mismatch between publisher and consumer is
   a startup error, not a best-effort parse.
5. **No durable output.** No contract permits writing to disk at runtime.

## Error envelope

Every rejected boundary crossing reports:

```json
{
  "code": "SCHEMA_INVALID",
  "boundary": "sanitizer",
  "message": "human-readable, no payload content",
  "retryable": false
}
```

Stable codes: `SCHEMA_INVALID`, `LOW_SNR`, `TIMESTAMP_DESYNC`, `SLM_TIMEOUT`,
`MODEL_UNAVAILABLE`, `TTS_UNAVAILABLE`, `LANGUAGE_UNSUPPORTED`, `CONFIG_INVALID`,
`CONSENT_MISSING`, `REPEATED_FAULT`.

## Versioning

Contracts are versioned in the `contract_version` field of each JSON schema
(`"1.0"`). A breaking change to field name, type, or constraint requires a spec
update, a migration note here, and a test that fails against the previous version.
