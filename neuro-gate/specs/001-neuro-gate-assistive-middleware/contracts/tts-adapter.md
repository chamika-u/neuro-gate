# Contract: Text-to-Speech Adapter

**Boundary**: core → speech backend
**Direction**: outbound
**Form**: Python `Protocol` in `output/tts/base.py`

## Protocol

```
TextToSpeech
  name: str
  supported_locales: frozenset[str]
  def speak(text: str, locale: str) -> SpeakResult
  def abort() -> None
  def available() -> bool
```

`SpeakResult` reports `delivered: bool`, `aborted: bool`, and `error_code: str | None`.

## Rules

1. `speak` MUST return only after playback completes or is aborted. It MUST NOT
   return optimistically before audio starts.
2. `abort` MUST be safe to call from another thread and MUST stop audio within
   100 ms.
3. `supported_locales` is declared up front. The core never asks a backend to speak
   a locale it does not declare.
4. A backend MUST NOT fall back to another language internally. If it cannot speak
   the requested locale, it reports `LANGUAGE_UNSUPPORTED`.
5. A backend MUST NOT contact the network. This is a hard requirement of FR-013.
6. Failures are reported as `error_code`, never raised as unhandled exceptions.

## Backends

| Backend | Selection order | Locales declared | When chosen |
|---------|----------------|------------------|-------------|
| `webspeech` | 1 | depends on OS voices, queried at start | only in a browser surface |
| `espeak` | 2 | `si-LK`, `ta-LK`, `ta-IN`, `en-US`, `en-GB` | default offline path |
| `none` | 3 | — | no backend available; subtitle-only |

## Degradation contract

If the resolved backend does not declare the session-primary locale:

- the system emits a `SUBTITLE` output only,
- `OutputEvent.voice_locale` is `null`,
- the dashboard shows a visible subtitle-only banner,
- no `TTS` output event is ever created with a mismatched locale.

This is the mechanism that satisfies FR-010 and SC-007. Switching voice mid-sentence
is not expressible in this contract by design.
