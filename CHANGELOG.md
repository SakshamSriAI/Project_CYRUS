# CYRUS Changelog
All notable changes to PROJECT CYRUS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.6.1] - Phase 5 Extension: Kokoro TTS & Puck Voice Configuration - 2026-11-06

### Added
- **Kokoro TTS Neural Engine with Puck Default Voice (`am_puck`)**:
  - `backend/app/voice/kokoro_service.py`: Local neural TTS inference engine outputting studio-grade 24 kHz audio.
  - Puck (`am_puck`) configured as CYRUS default voice: American English masculine, warm, conversational, articulate, intelligent, composed, subtly witty, zero robotic cadence.
  - Jessica (`af_jessica`) configured as alternative feminine voice.
- **Natural Speech Text Preprocessor**:
  - `backend/app/voice/text_preprocessor.py`: Strips markdown formatting, code blocks, and URLs; phonetically expands technical abbreviations (`API` -> `A P I`, `SQLite` -> `S Q L lite`, `WAL` -> `W A L`, `RAM` -> `R A M`, `GB` -> `gigabytes`, `B.Tech` -> `B Tech`); chunks text for natural breathing pauses.
- **Persistent Voice Preferences**:
  - `backend/app/voice/voice_preferences.py`: Persistent storage of voice preferences (voice ID, speech speed, voice enabled/disabled) in SQLite under `MemoryCategory.PERSONAL`, surviving full system shutdowns and reboots.
- **Dedicated CYRUS Voice Studio**:
  - `frontend/src/components/Voice/VoiceStudio.tsx`: Full Voice Studio UI with default voice selector, Puck signature preview button, custom text auditioning, play/pause/stop controls, speech speed slider (0.75x–1.5x), live microphone volume testing, and engine status monitor.
- **Voice Studio REST Endpoints**:
  - `backend/app/api/v1/voice.py`: Added `/studio/config`, `/studio/preview`, `/studio/audition`, and `/audio/{filename}` audio streaming.
- **Test Suite**:
  - `backend/tests/test_phase5_kokoro_puck.py`: 6 tests verifying preprocessor acronym expansion, preference persistence across SQLite reloads, 24kHz audio synthesis, Puck signature preview, custom text auditioning, and English output enforcement.
  - All 45 automated tests passing with 100% pass rate.

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
