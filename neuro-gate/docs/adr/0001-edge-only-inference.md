# ADR 0001 — All inference runs on-device

- **Status**: Accepted
- **Date**: 2026-11-03
- **Deciders**: Sabradox

## Context

The system processes decoded inner speech — the user's private thoughts — before
deciding what may be spoken. Two options were available:

1. Send thought buffers to a cloud language model for noise classification.
2. Run a small quantized language model locally.

## Decision

Run **all** inference on the edge device. No biometric signal, feature frame,
thought buffer, or sanitized intent may leave the device at runtime. The SLM
runtime is bound to loopback.

## Consequences

**Positive**

- No biometric egress, which is the only defensible position for this class of
  data.
- Works offline, which matters for a device someone may depend on to communicate.
- Zero marginal inference cost, so per-user cost is not a barrier to access.
- Deterministic privacy story that can be stated on stage in one sentence.

**Negative**

- Model quality is limited to what fits on consumer hardware (3B-class quantized).
- SLM latency becomes a UX constraint that must be designed around.
- No fleet-wide model updates; distribution is per-device.
- Multilingual quality is weaker than a large hosted model.

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Cloud LLM for sanitization | Sends private thought content off-device |
| Hybrid with opt-in upload | Opt-in under social pressure is not consent in practice |
| Larger local model | Exceeds reference hardware envelope |
| On-device tiny classifier only | Insufficient for cross-lingual semantic filtering in v1 |

## Review trigger

Revisit only if an on-device model reaches parity with hosted quality at the
reference hardware profile, or if a formal privacy-preserving compute design
(differential privacy, on-device enclave) is evaluated and approved via a new ADR.
