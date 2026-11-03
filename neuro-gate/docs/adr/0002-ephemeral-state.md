# ADR 0002 — Session state is RAM-only and expires per intent cycle

- **Status**: Accepted
- **Date**: 2026-11-03
- **Deciders**: Sabradox
- **Related**: [InnovaX Constitution, Principle I — Stateless by Design](../../../.specify/memory/constitution.md)

## Context

The InnovaX constitution mandates a purely stateless system: no external
database, no durable store, and no state persisted between requests. NeuroGate is
a continuous pipeline rather than a request/response service, so it inevitably
has *ephemeral* working state: ring buffers, a calibration baseline, and a
rolling gate threshold.

That is a real deviation from a literal reading of Principle I and must be
recorded rather than quietly ignored.

## Decision

1. All working state lives in **RAM only**, scoped to a session and, for thought
   content, scoped to a **single intent cycle**.
2. No business data is written to disk. No database, no cache file, no log line
   containing decoded text.
3. The rolling baseline and calibration parameters exist as **derived session
   configuration** — they influence thresholds but never carry content.
4. Nothing survives a process restart except what an operator explicitly
   re-enters (consent record, language profile, thresholds).
5. Fault telemetry is limited to stable codes, timestamps, and counters.

## Consequences

**Positive**

- The privacy guarantee is structural, not policy-based.
- The system is horizontally trivially scalable: one FSM instance per session,
  no shared state, no coordination.
- Restart behaviour is predictable: the device is silent until re-calibrated.

**Negative**

- Users must recalibrate after every restart (~5 minutes), which is a real UX
  cost for an assistive device.
- No cross-session personalization; no adaptive improvement over time.
- Persistent user profiles would require a constitution amendment.

## Constitution alignment

| Principle | Reading |
|-----------|---------|
| I — Stateless by Design | Literal request-scoped statelessness is satisfied for thought content. Ephemeral in-memory pipeline state is a documented, bounded deviation: it cannot survive restart and carries no content across cycles. |
| II — Pydantic contracts | Fully satisfied; see `docs/07-data-contracts.md`. |
| III — Code quality | Applies to implementation; this repository is documentation only. |
| IV — Test-first | Applies to implementation; the FSM transition table is the primary test surface. |
| V — UX & performance | The p95 300 ms budget in the constitution was written for HTTP APIs and does not apply to the SLM stage. The project budget in `docs/02-agent-decision-loop.md` supersedes it for this system. |

## Amendment path

If persistent per-user profiles are later required, the change is:

1. a written amendment to Principle I,
2. a data-protection review covering biometric data at rest,
3. a new ADR defining encryption, retention, and deletion semantics,
4. updated contracts and tests.

Until then, persistence is out of scope.
