# CYRUS Changelog
All notable changes to PROJECT CYRUS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.5.0] - Phase 4: CYRUS Persistent Memory Subsystem - 2026-11-05

### Added
- **Three-Tier Persistent Memory Engine**:
  - `backend/app/memory/models.py`: Definitions for `MemoryCategory` (Personal, Business, Working) and `FactType` (Verified Fact, Preference, Routine, Assumption, Task Goal).
  - `backend/app/memory/memory_store.py`: SQLite persistence supporting upsert, soft/hard deletion, multi-tenant isolation, and confidence scoring.
- **Context Injection & Auto-Extraction Engine**:
  - `backend/app/memory/context_manager.py`: Formulates dynamic context blocks for prompts and auto-extracts explicit memory statements from chat ("Remember that...").
- **Session Persistence & Crash Recovery**:
  - `backend/app/memory/session_recovery.py`: Incremental state checkpoints, dirty-exit detection, and JARVIS-inspired session recovery briefings.
- **Memory REST API**:
  - `backend/app/api/v1/memory.py`: Endpoints for querying memories, saving facts, deleting entries, and retrieving recovery reports.
- **Frontend Memory Center**:
  - `frontend/src/components/Memory/MemoryCenter.tsx`: Category tabs (Personal, Business, Working), search, add form, delete controls, and recovery briefing banner.
- **Testing & Verification**:
  - `backend/tests/test_phase4_memory.py`: 7 automated tests covering CRUD, multi-tenant isolation, auto-extraction, and crash recovery.
  - All 33 automated tests passing with a 100% pass rate.

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
