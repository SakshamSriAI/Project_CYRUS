# CYRUS Changelog
All notable changes to PROJECT CYRUS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.6.0] - Phase 5: CYRUS Local Voice Interaction Subsystem - 2026-11-05

### Added
- **Speech-to-Text (STT) Engine**:
  - `backend/app/voice/stt_service.py`: Multilingual speech recognition for English, Hindi, and Hinglish.
  - Wake-word parsing (`"Hey CYRUS"`, `"CYRUS"`).
- **Text-to-Speech (TTS) Engine**:
  - `backend/app/voice/tts_service.py`: Zero-cost local voice synthesis using macOS native `say` and browser Web Speech API.
  - Curated English voices (Daniel UK, Samantha US, Karen AU).
  - Post-generation speech sanitizer guaranteeing 100% English speech.
  - Speech interruptibility.
- **End-to-End Voice Pipeline**:
  - `backend/app/voice/voice_pipeline.py`: Coordinates STT -> CORE -> GUARDIAN -> MEMORY -> TTS.
  - Automatic microphone release on Exam Mode and Emergency Stop.
- **Voice REST API**:
  - `backend/app/api/v1/voice.py`: Endpoints for voice status, full turn interaction, text synthesis, and speech interruption.
- **Frontend Voice Center**:
  - `frontend/src/components/Voice/VoiceCenter.tsx`: Circular animated visualizer orb, Push-to-Talk, voice selector dropdown, and quick simulation buttons.
- **CLI Voice Tool**:
  - `scripts/cyrus_ctl.sh voice`: Direct command-line voice testing with local macOS speaker playback.
- **Testing & Verification**:
  - `backend/tests/test_phase5_voice.py`: 6 automated tests covering wake-words, multilingual parsing, English speech enforcement, Exam Mode lock, and speech interruption.
  - All 39 automated tests passing with a 100% pass rate.

---

## [0.5.0] - Phase 4: CYRUS Persistent Memory Subsystem - 2026-11-05

### Added
- Three-tier memory engine (Personal, Business, Working), multi-tenant isolation, context manager prompt injection, auto-extraction, and session recovery briefings.

---

## [0.4.0] - Phase 3: CYRUS GUARDIAN Deep Security Subsystem - 2026-11-05

### Added
- 4-tier permission model, interactive approval workflow, prompt-injection defense, CYRUS STOP kill switch, and audit ledger.

---

## [0.3.0] - Phase 2: CYRUS CORE & Local AI Integration - 2026-11-05

### Added
- Conversational orchestrator, Ollama interface, language policy guard, and chat API.

---

## [0.2.0] - Phase 1: Foundation and Project Structure - 2026-11-05

### Added
- Modular architecture, SQLite WAL engine, lifecycle state machine, and CLI controller.

---

## [0.1.0] - Phase 0: Environment Inspection & System Architecture - 2026-11-05

### Added
- Hardware inspection of Apple M5, 16 GB RAM, 359 GB storage.
- Architecture specification, security blueprint, and 14-phase roadmap.
