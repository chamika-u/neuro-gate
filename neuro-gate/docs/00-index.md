# NeuroGate — Documentation Index

NeuroGate is an **intent-gated edge middleware** that sits between non-invasive
biosignal sensors (EEG + sEMG) and assistive output devices (subtitles, local
text-to-speech). It filters cognitive and physiological noise out of a
continuous thought stream so that only *deliberate* communication intent ever
reaches a display or a speaker.

- **Competition domain**: Domain B — Education & Human Capability (Accessibility)
- **Team**: Sabradox, Sabaragamuwa University of Sri Lanka
- **Project root**: `neuro-gate/` (this directory)

---

## Reading order

| # | Document | What it answers |
|---|----------|-----------------|
| 00 | [Docs index](00-index.md) | This page. Map of the documentation set. |
| 01 | [System architecture](01-system-architecture.md) | What the system is, its boundaries, its four tiers. |
| 02 | [Agent decision loop](02-agent-decision-loop.md) | Perceive → Decide → Act → Loop, and the FSM that enforces it. |
| 03 | [Signal processing](03-signal-processing.md) | How raw EEG/sEMG becomes a trustworthy feature frame. |
| 04 | [Technical stack](04-technical-stack.md) | Components, models, protocols, cost and deployment. |
| 05 | [Safety, ethics & responsible AI](05-safety-and-ethics.md) | Human oversight, failure modes, privacy, disclaimers. |
| 06 | [User scenarios](06-user-scenarios.md) | End-to-end walkthroughs, including cancels and failures. |
| 07 | [Data contracts](07-data-contracts.md) | Pydantic-validated models crossing every boundary. |
| 08 | [Multilingual support](08-multilingual-support.md) | Sinhala, Tamil and English paths end to end. |
| 09 | [Roadmap & risk register](09-roadmap-and-risks.md) | Milestones, open research questions, risks. |

## Diagram sources

Every Mermaid diagram is stored twice: inline in its document, and as a
standalone `.mmd` file under [`diagrams/`](diagrams/) so it can be rendered,
diffed, or exported without parsing Markdown.

| Diagram | File | Used by |
|---------|------|---------|
| System context | [`01-system-context.mmd`](diagrams/01-system-context.mmd) | 01 |
| Four-tier pipeline | [`02-layered-pipeline.mmd`](diagrams/02-layered-pipeline.mmd) | 01 |
| FSM state machine | [`03-fsm-state-machine.mmd`](diagrams/03-fsm-state-machine.mmd) | 02 |
| Decision loop | [`04-agent-decision-loop.mmd`](diagrams/04-agent-decision-loop.mmd) | 02 |
| DSP path | [`05-dsp-pipeline.mmd`](diagrams/05-dsp-pipeline.mmd) | 03 |
| Happy path sequence | [`06-sequence-happy-path.mmd`](diagrams/06-sequence-happy-path.mmd) | 06 |
| Cancel / failure sequence | [`07-sequence-cancel-and-failure.mmd`](diagrams/07-sequence-cancel-and-failure.mmd) | 05, 06 |
| Edge deployment | [`08-edge-deployment.mmd`](diagrams/08-edge-deployment.mmd) | 04 |
| Data contracts | [`09-data-contracts.mmd`](diagrams/09-data-contracts.mmd) | 07 |
| Multilingual routing | [`10-multilingual-routing.mmd`](diagrams/10-multilingual-routing.mmd) | 08 |

## Architecture decision records

| ADR | Decision |
|-----|----------|
| [0001](adr/0001-edge-only-inference.md) | All inference runs on-device; no biometric egress. |
| [0002](adr/0002-ephemeral-state.md) | Session state is RAM-only and expires per intent cycle. |
