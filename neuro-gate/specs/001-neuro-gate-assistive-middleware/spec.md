# Feature Specification: NeuroGate — Intent-Gated Assistive Communication Middleware

**Feature Branch**: `001-neuro-gate-assistive-middleware`

**Created**: 2026-11-03

**Status**: Draft

**Input**: User description: "Create project docs and Mermaid architecture diagrams for the NeuroGate assistive communication middleware; docs live in `docs/`, README at the project root, project root is `neuro-gate/`."

## Clarifications

### Session 2026-11-03

- Q: When the confirmation window expires with no user response, should the utterance be spoken automatically or withheld? → A: Auto-speak on timeout; cancelling is the opt-out.
- Q: How many simultaneous users must a single deployment support? → A: One active user per device; multiple devices are independent.
- Q: How should the spoken language be chosen when the user mixes Sinhala, Tamil and English in one utterance? → A: A session-primary language set at session start drives the voice; mixed-script text renders as-is with no mid-sentence voice switching.
- Q: Who is authorized to start a session and record consent before sensor capture begins? → A: A named operator opens the session and records informed consent; the user retains all utterance decisions.
- Q: Which accessibility conformance level must the subtitle display and the cancel control meet? → A: WCAG 2.1 AA for the subtitle surface, plus a cancel control operable without fine motor precision.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Deliberate utterance is spoken, noise is not (Priority: P1)

A non-verbal user wearing an EEG/sEMG headband thinks a mix of stray thoughts
("I'm tired", "my head hurts") and one deliberate sentence ("please bring me a
glass of water"). The system identifies the deliberate attempt, strips the
affective noise, shows the cleaned sentence as text, and waits for confirmation
before speaking it aloud.

**Why this priority**: This is the entire product thesis. Without it there is no
system, only a signal recorder.

**Independent Test**: Feed a replayed biosignal stream containing a known noise-plus-
intent buffer; confirm the delivered text contains only the intended sentence and
nothing is emitted before the confirmation window resolves.

**Acceptance Scenarios**:

1. **Given** a calibrated session and a buffer containing one deliberate sentence
   plus fatigue noise, **When** the buffer passes the intent gate, **Then** the
   sanitized output contains the deliberate sentence and the noise fragments are
   listed as rejected.
2. **Given** a sanitized intent awaiting confirmation, **When** the user does not
   cancel within the confirmation window, **Then** the utterance is displayed and
   spoken exactly once.
3. **Given** a buffer that is entirely passive inner monologue, **When** it is
   processed, **Then** nothing is displayed or spoken.

---

### User Story 2 - User cancels an unintended utterance (Priority: P1)

The gate fires on an attempt the user did not intend to broadcast. During the
confirmation window the user cancels, and no audio is ever produced.

**Why this priority**: Dignity and privacy are the product's stated value. A
system that cannot be stopped is not safe to deploy.

**Independent Test**: Trigger an intent, issue a cancel within the window, and
assert that the audio tool was never invoked and a cancelled state was shown.

**Acceptance Scenarios**:

1. **Given** a staged intent, **When** a cancel gesture arrives before the window
   expires, **Then** playback is aborted and the user sees a cancelled indication.
2. **Given** a playback in progress, **When** the user aborts, **Then** audio
   stops and the session returns to passive monitoring.

---

### User Story 3 - Low-quality signal produces silence, not guesses (Priority: P2)

Sensor contact degrades mid-session. Rather than emitting a hallucinated
sentence, the system refuses, tells the user why, and eventually blocks output.

**Why this priority**: Refusing is the difference between an assistive tool and a
liability.

**Independent Test**: Lower the injected SNR below the calibrated floor and
assert zero output events plus a visible, understandable status message.

**Acceptance Scenarios**:

1. **Given** a degraded signal, **When** frames fall below the SNR floor, **Then**
   no intent is attempted and the user sees a sensor-contact message.
2. **Given** repeated degradation, **When** the incident limit is crossed, **Then**
   all output is blocked until an operator resets.

---

### User Story 4 - Multilingual use in Sinhala, Tamil or English (Priority: P2)

A user communicates in Sinhala, Tamil or English, including code-mixed speech.
The original script is rendered, and speech uses the session-primary voice, or the
system degrades to subtitles with a visible notice.

**Why this priority**: An aid that only works in English does not serve the
intended population; the competition also awards bonus marks for localization.

**Independent Test**: Run the same intent buffer in each language and verify
script rendering, noise rejection, and session-primary voice selection independently.

**Acceptance Scenarios**:

1. **Given** a Sinhala buffer with noise and Sinhala as the session-primary language,
   **When** sanitized, **Then** the output is Sinhala text and speech uses the
   Sinhala voice.
2. **Given** the required voice is unavailable, **When** output is emitted, **Then**
   subtitles render and a visible subtitle-only notice appears; the language is
   never silently switched.

---

### User Story 5 - Operator runs a hardware-free demonstration (Priority: P3)

An evaluator with no headband replays a recorded biosignal stream and observes
the full pipeline, with ground truth shown beside the delivered output.

**Why this priority**: Enables validation and demonstration without hardware, and
proves the architecture is genuinely hardware-agnostic.

**Independent Test**: Start the replay source only; confirm the end-to-end output
matches the scripted ground truth.

**Acceptance Scenarios**:

1. **Given** only the replay simulator, **When** the session runs, **Then** the
   full pipeline executes identically to a hardware session.

---

### Edge Cases

- Silence-only or noise-only buffer → silent drop (see US1 acceptance scenario 3).
- A single high-amplitude spike (cough, jaw clench) → rejected as transient.
- Sanitizer returns malformed structured output or prose around it → schema-invalid
  fault, silent drop.
- Sanitizer returns text present verbatim in the rejected-noise list → contradiction,
  drop.
- Confirmation window elapses with no user response → the utterance is emitted
  automatically; only an explicit cancel suppresses it. The window is never
  open-ended.
- Language detection is ambiguous or code-mixed → text renders its original script
  as-is and speech uses the session-primary language; no mid-sentence voice switch.
- Sensor stream stops mid-buffer → buffer discarded, no partial utterance.
- Model runtime unavailable or times out → single retry, then degraded subtitle-only
  mode or fault.
- No operator consent record exists → capture MUST NOT start and the device stays
  silent until an operator creates one.
- Session restarts → no prior state restored; recalibration is required.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ingest multi-channel biosignal data over a standard,
  vendor-neutral streaming protocol without requiring a specific device model.
- **FR-002**: System MUST reject frames that fall below a calibrated signal-quality
  threshold before any semantic processing.
- **FR-003**: System MUST distinguish a volitional communication attempt from a
  transient artifact using a deterministic gating stage.
- **FR-004**: System MUST NOT invoke semantic processing unless the gating stage
  has accepted the attempt.
- **FR-005**: System MUST identify intentional content within a buffer and separate
  affective or non-actionable fragments from it.
- **FR-006**: System MUST return a structured, validated result for every semantic
  step and MUST discard any result that fails validation.
- **FR-007**: System MUST require a resolved human confirmation decision before any
  audio is emitted, where an expired confirmation window counts as approval and
  only an explicit cancel suppresses output.
- **FR-008**: Users MUST be able to cancel a staged utterance before playback starts
  and abort playback in progress.
- **FR-009**: System MUST render the sanitized utterance as text in all cases,
  including when audio is unavailable.
- **FR-010**: System MUST support Sinhala, Tamil and English input. A session-primary
  language, set at session start, MUST drive the spoken voice; the system MUST NOT
  switch voices mid-sentence based on detection and MUST NOT silently substitute a
  different language or voice.
- **FR-011**: System MUST show rejected noise fragments to the user locally so the
  filter is auditable.
- **FR-012**: System MUST retain thought content only in volatile memory scoped to
  a single intent cycle.
- **FR-013**: System MUST operate without network access at runtime.
- **FR-014**: System MUST enter a blocked state after repeated unrecoverable faults
  and require an operator to resume.
- **FR-015**: System MUST accept replayed biosignal streams as a first-class input
  source equivalent to live sensors.
- **FR-016**: System MUST expose the state transition history of the gating stage
  for verification.
- **FR-017**: System MUST bound every processing stage with a timeout and resolve
  stage timeout to silence rather than output. The confirmation window is the sole
  exception: its expiry is an approval (see FR-007).
- **FR-018**: System MUST NOT expose any capability that performs an irreversible
  real-world action.
- **FR-019**: System MUST serve exactly one active user per device instance and MUST
  NOT interleave sensor streams or conversational state between users.
- **FR-020**: System MUST require a named operator to open a session and record
  informed consent before any sensor capture begins, while the user retains every
  utterance-level decision.
- **FR-021**: System MUST meet WCAG 2.1 AA for the subtitle surface (contrast and text
  size) and MUST provide a cancel control operable without fine motor precision.

### Key Entities

- **Biosignal frame**: a timestamped batch of sensor samples from one channel.
- **Feature frame**: derived, quality-scored representation of a time window.
- **Trigger event**: a gating decision recording whether a volitional attempt
  occurred.
- **Thought buffer**: a bounded window of candidate communication content.
- **Sanitized intent**: the validated result of noise separation, with language and
  confidence.
- **Confirmation decision**: the recorded human response to a staged utterance.
- **Output event**: the delivered text and/or speech, with locale and delivery state.

### Terminology

Canonical terms used across spec, plan, tasks and docs. Code identifiers in
parentheses are the only permitted variants.

| Canonical term | Meaning | Not used |
|---|---|---|
| Intent gate | The deterministic gating stage that decides whether a volitional attempt occurred | trigger classifier, FSM (the FSM is only its implementation) |
| Session-primary language | The language chosen at session start that drives rendering and voice | language profile, detected language (code field: `primary_language`) |
| Operator | The named person who records consent and opens the session | admin, supervisor, caregiver |
| Semantic step | Any stage that interprets content and may invoke the local model | SLM call, inference, agent |
| Staged utterance | Sanitized text awaiting the confirmation decision | pending output, draft |
| Transient artifact | A non-volitional signal event (blink, clench, cough) | noise, garbage |

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a scripted evaluation set, at least 90% of deliberate utterances
  are delivered with only the intended content and no noise fragment spoken.
- **SC-002**: At least 95% of transient artifacts (spikes, blinks, clenches) are
  rejected without producing any output.
- **SC-003**: Zero utterances are spoken without a recorded confirmation decision
  (explicit approval or recorded window expiry) in any test run.
- **SC-004**: When signal quality is below the calibrated threshold, the system
  produces no output in 100% of test cases and shows the configured localized
  `low_signal_message` as text within 2 seconds.
- **SC-005**: A user unable to perform fine motor gestures can cancel a staged
  utterance within a 1.5-second window on the first attempt in at least 9 of 10
  trials (single recorded trial protocol, one operator observing).
- **SC-006**: End-to-end delay from end of subvocal attempt to audio start is under
  5 seconds for 95% of utterances on the reference device.
- **SC-007**: Sinhala, Tamil and English each render correctly and speak in the
  session-primary voice, or degrade to subtitles with a visible notice shown for at
  least 3 seconds at AA contrast, in 100% of evaluation cases; no mid-sentence voice
  switch occurs.
- **SC-008**: A new operator can run a complete hardware-free session using only
  the documented steps, without assistance.
- **SC-009**: No thought content is recoverable from the device after the session
  ends.
- **SC-010**: The subtitle surface passes a WCAG 2.1 AA audit for contrast and text
  size, and the cancel control meets a 44 x 44 px minimum target and requires no
  fine-motor gesture (a single coarse press or equivalent).

## Assumptions

- Users are non-verbal or speech-impaired and have consented, through an operator,
  to sensor use for assisted communication.
- A calibration step is acceptable at the start of each session; the device is not
  expected to be accurate out of the box.
- Subtitle output is always acceptable; audio is an enhancement, not a guarantee.
- A consumer laptop with 8–16 GB RAM is the reference device.
- Each deployment serves one active user on one sensor stream; supporting more users
  means additional independent devices, not a shared multi-tenant service.
- The prototype covers three languages; additional languages are out of scope.
- Sensors provide a standard streaming protocol; device-specific drivers are
  external to this system.
- No clinical claim is made; output quality is evaluated as a communication aid,
  not as a medical instrument.
- Persistent user profiles are out of scope and would require a governance
  amendment before implementation.
