<!--
Sync Impact Report
==================
Version change: (unratified template) → 1.0.0
Bump rationale: Initial ratification. All principles and governance sections are newly
defined; MAJOR classification applies because this is the first adopted constitution.

Modified principles:
- Template principle 1 → I. Stateless by Design (NON-NEGOTIABLE)
- Template principle 2 → II. Pydantic-Validated Data Contracts
- Template principle 3 → III. Code Quality & Maintainability
- Template principle 4 → IV. Test-First with Mandatory Edge-Case Coverage (NON-NEGOTIABLE)
- Template principle 5 → V. UX Consistency & Performance

Added sections:
- Additional Constraints
- Development Workflow & Quality Gates
- Governance (populated)

Removed sections: none

Follow-up TODOs: none. Ratification date recorded as the adoption date of this version.

Amendment 1.1.0 (2026-11-03)
============================
Version change: 1.0.0 → 1.1.0 (MINOR: materially expanded guidance; no principle
removed or redefined).

Modified principles:
- I. Stateless by Design: added the bounded session exception for content-free derived
  values (calibration baseline, rolling gate threshold) held in volatile memory only.
- V. UX Consistency & Performance: split the single p95 300 ms budget into a read budget
  and a generative-path budget recorded in the feature plan.

Rationale: the two exceptions were already documented in ADR 0002 and the NeuroGate
feature plan; recording them here makes compliance verifiable instead of interpretive.
-->

# InnovaX Constitution

## Core Principles

### I. Stateless by Design (NON-NEGOTIABLE)

The system MUST be purely stateless. It MUST NOT write to any external database or any other
external durable store, and it MUST NOT depend on state persisted between requests.

- Every request MUST be processed using only its own input plus immutable configuration.
- No global mutable state, sticky sessions, or cross-request in-memory caches may influence
  business outcomes.
- Any data that must survive a process restart is out of scope; adding persistence requires a
  constitution amendment before implementation.
- Side effects MUST be limited to the response returned to the caller and non-durable,
  observable telemetry that cannot affect behavior.
- **Bounded session exception**: A session MAY hold content-free derived values (calibration
  baseline, rolling gate threshold) that influence processing outcomes, provided they (a) live
  only in volatile memory, (b) are destroyed when the session ends, (c) contain no user content,
  decoded text, or biometric samples, and (d) are documented in an ADR. Values meeting (a)–(d)
  are excluded from the request-scoped statelessness rule above. Any content, persistence, or
  cross-session value requires a separate amendment.

Rationale: Statelessness guarantees horizontal scalability, deterministic behavior, and freedom
from hidden coupling to external infrastructure.

### II. Pydantic-Validated Data Contracts

All data structures MUST be validated with Pydantic before any processing occurs. Raw
dictionaries, untyped JSON, or unvalidated objects MUST NOT cross a function, module, or API
boundary.

- Every inbound payload MUST be parsed into a Pydantic model at the system edge; invalid input
  MUST be rejected before business logic runs.
- Every outbound payload MUST be produced from a Pydantic model with an explicit schema.
- Models MUST declare strict types, explicit optionality, and field-level constraints
  (lengths, ranges, formats) rather than relying on downstream checks.
- Schema changes MUST be treated as contract changes: documented, tested, and reviewed.
- Validation MUST NOT be bypassed in tests or production paths; model construction with
  `model_construct` or equivalent is prohibited for untrusted input.

Rationale: A single validation layer eliminates entire classes of defects and keeps contracts
explicit, discoverable, and testable.

### III. Code Quality & Maintainability

Code MUST be readable, typed, and free of dead or duplicated logic. Quality is a gate, not an
aspiration.

- All Python code MUST include type annotations for public functions and methods and MUST pass
  the project's static type checker with no new errors.
- All code MUST pass the configured linter and formatter before merge.
- Functions MUST have a single responsibility; complexity that cannot be justified in review
  MUST be simplified rather than merged.
- Public modules, classes, and functions MUST have docstrings describing purpose, inputs,
  outputs, and raised errors.
- Dead code, commented-out code, and unused dependencies MUST be removed.
- Dependencies MUST be pinned and justified; adding a dependency requires reviewer approval.

Rationale: Consistent quality standards reduce defect rates, speed up reviews, and keep the
codebase safe to change.

### IV. Test-First with Mandatory Edge-Case Coverage (NON-NEGOTIABLE)

Tests MUST be written before implementation and MUST fail before the implementation is added.
The Red-Green-Refactor cycle is mandatory.

- Every new behavior MUST have automated tests covering the happy path and its boundaries.
- Edge cases MUST have dedicated unit tests. At minimum, capacity and limit logic MUST be tested
  at exactly the maximum (for example, registered students exactly equal to maximum capacity),
  one below the maximum, one above the maximum, zero, and empty input.
- Boundary and off-by-one behavior MUST be asserted explicitly, not inferred from happy-path
  tests.
- Validation failures, malformed input, and rejected contracts MUST have dedicated negative
  tests.
- Test suites MUST be deterministic, isolated, and free of network or external-database access.
- Line coverage MUST be at least 90% overall, and validation and boundary-handling modules MUST
  have 100% branch coverage.
- A change MUST NOT be merged with failing or skipped tests; flaky tests MUST be fixed or
  removed with justification.

Rationale: Edge cases at exact limits are where production incidents concentrate; dedicated
tests make those behaviors intentional and regression-proof.

### V. UX Consistency & Performance

User-facing behavior MUST be consistent across endpoints and MUST meet explicit performance
budgets.

- All responses MUST use a single, documented envelope and a single error schema with stable
  error codes and human-readable messages.
- Pagination, filtering, sorting, and timestamp formats MUST follow one project-wide convention.
- Errors MUST be actionable and MUST NOT leak stack traces, secrets, or internal paths.
- Interactive read operations MUST meet a p95 latency budget of 300 ms at the documented
  reference load.
- Generative operations that invoke a local model MUST instead meet the generation budget
  recorded in the feature plan (default: 4.5 s end to end at p95) and MUST be verified by an
  automated benchmark in the same way as read budgets.
- Pydantic validation overhead MUST stay under 10 ms per request payload at the documented
  reference size.
- Performance budgets MUST be verified by automated benchmarks before release; regressions
  beyond 20% of a budget MUST block release.
- Memory usage per request MUST be bounded and MUST NOT grow across sequential requests.

Rationale: Predictable contracts and measurable budgets keep the product trustworthy and
prevent silent performance decay.

## Additional Constraints

- Runtime: Python 3.11 or newer.
- Validation: Pydantic v2 is the only permitted validation framework for boundary contracts.
- Persistence: no external database, no durable file writes for business data, and no reliance
  on external stateful services. Configuration and secrets are injected at runtime.
- Security: secrets MUST come from environment or a secret manager and MUST NOT be logged,
  committed, or embedded in source.
- Observability: structured logs and metrics MAY be emitted but MUST NOT alter business behavior
  or persist user data.
- Portability: the service MUST run identically in local and containerized environments without
  external storage dependencies.

## Development Workflow & Quality Gates

- Every change MUST start from a specification and an approved plan before implementation.
- Pull requests MUST pass lint, static type checking, the full test suite, and performance
  benchmarks in CI.
- Reviewers MUST verify compliance with all five principles; non-compliance MUST block merge.
- Test-first evidence (failing test before implementation) MUST be visible in the change history
  or review notes.
- Performance benchmark results MUST be attached to releases.
- Any deviation from this constitution MUST be documented, justified, and approved through the
  amendment procedure.

## Governance

This constitution supersedes all other development practices. When a practice conflicts with a
principle, the principle wins.

- Amendments MUST be proposed in writing, state the motivation, list affected principles, and
  include a migration plan when behavior changes.
- Amendments MUST be reviewed and approved by the project maintainers before taking effect.
- Versioning follows semantic versioning: MAJOR for incompatible governance or principle
  removals/redefinitions, MINOR for new principles or materially expanded guidance, PATCH for
  clarifications and non-semantic refinements.
- Every pull request and review MUST verify compliance with this constitution; unresolved
  violations block merge.
- Compliance review MUST occur at each release, and exceptions MUST be time-boxed and recorded.
- Runtime development guidance in project documentation MUST remain consistent with this
  constitution.

**Version**: 1.1.0 | **Ratified**: 2026-11-03 | **Last Amended**: 2026-11-03
