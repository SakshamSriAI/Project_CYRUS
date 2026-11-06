# CYRUS Changelog
All notable changes to PROJECT CYRUS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.10.0] - Phase 9: CYRUS SENTINEL & Proactive Local Monitoring - 2026-11-06

### Added
- **Surveillance & Incident Database Schema**:
  - `backend/app/database.py`: Added normalized tables for `sentinel_monitors` (endpoints, check intervals, expected status codes, current state `UP`/`DOWN`/`DEGRADED`, and latency) and `sentinel_events` (event log classified into 3 severity levels `INFO`, `IMPORTANT`, `CRITICAL` with Telegram dispatch tracking).
- **Proactive Background Health Watcher**:
  - `backend/app/sentinel/watcher.py`: Lightweight asynchronous HTTP ping engine measuring real millisecond latency without event loop blocking.
  - 3-tier event severity classification: Level 1 (Info), Level 2 (Important - high latency or single failure), and Level 3 (Critical - confirmed consecutive downtime).
  - Lifecycle integration: auto-suspension during `PAUSED`, `EXAM_MODE`, or `SHUTDOWN` states.
  - Acceptance Criteria Verification: `simulate_downtime()` simulates mock service failures, verifying that SENTINEL detects downtime and dispatches a Level 3 Critical alert in under 30 seconds (< 30s threshold).
  - Explicit notification of Apple Silicon local sleep and display lid closure monitoring boundaries.
- **Free-Tier Telegram Bot Alert Dispatcher**:
  - `backend/app/sentinel/telegram_notifier.py`: Proactive incident alert dispatch supporting live Telegram Bot API and simulated zero-cost delivery mode.
  - Structured alert templates addressing the user as "Sir" with target name, status code, latency, and timestamp.
- **Specialist Agent Integration (CYRUS SENTINEL)**:
  - `backend/app/agents/sentinel_agent.py`: Created and registered `CYRUS_SENTINEL` into `agent_registry.py` (now 6 active specialist agents).
  - Provides real-time surveillance summaries, runs downtime drills, and explains local MacBook sleep/shutdown boundaries.
- **Sentinel REST API**:
  - `backend/app/api/v1/sentinel.py`: Endpoints for `/status`, `/monitors`, `/monitors/{id}/check-now`, `/events`, `/simulate-downtime`, and `/telegram/test`.
  - Mounted under `/api/v1/sentinel` in `backend/app/main.py`.
- **Frontend Sentinel Surveillance Center**:
  - `frontend/src/components/Sentinel/SentinelCenter.tsx`: Interactive monitoring center with live daemon status pill, Apple Silicon sleep boundary notice, summary metric cards, 1-click downtime drill button (<30s verification), monitored services cards with latency indicators, and live event ledger.
  - Integrated into `frontend/src/App.tsx`.
- **Testing & Verification**:
  - `backend/tests/test_phase9_sentinel.py`: 11 comprehensive unit tests verifying monitor seeding, daemon status, Level 2 Important warnings, Level 3 Critical alerts, downtime detection in <30s, Telegram formatting, simulated dispatch, lifecycle pause suspension, exam mode suspension, Sentinel agent telemetry, and sleep limitations explanation.
  - All 94 automated architectural unit tests passing with 100% pass rate in 0.370s.

---

## [0.9.0] - Phase 8: Business Intelligence & Integrations - 2026-11-06

### Added
- **Multi-Tenant Business Database Schema**:
  - `backend/app/database.py`: Added normalized tables for `business_clients`, `business_invoices`, and `business_projects` with foreign keys and performance indices (`idx_business_clients_tenant`, `idx_business_invoices_tenant_status`, `idx_business_projects_tenant`).
- **Multi-Tenant Business Store**:
  - `backend/app/business/business_store.py`: ACID-compliant multi-tenant store with strict tenant boundary isolation.
  - Automated seeding of enterprise demonstration accounts: Apex Consulting Services (`apex_corp`), Nexus AI Systems (`nexus_tech`), and Solaris Digital Media (`solaris_media`).
  - Days overdue computation based on current timestamp and due dates.
  - Algorithmic Financial Health Score (0-100) and collection realization ratio telemetry.
  - Executive financial health briefing generator addressed to the user as "Sir".
- **Specialist Agent Integration (CYRUS BUSINESS)**:
  - `backend/app/agents/business_agent.py`: Direct connection to the SQLite business store, answering "Which invoices are overdue?" factually with zero hallucination.
  - Returns factual breakdown of `INV-2026-003` (₹60,000) and `INV-2026-004` (₹45,000) totaling ₹1,05,000 with days past due.
  - Full support for revenue reporting, client CRM rosters, and project milestones.
- **Business Intelligence REST API**:
  - `backend/app/api/v1/business.py`: Endpoints for `/summary`, `/invoices`, `/invoices/overdue`, `/clients`, `/projects`, `/health-report`, and `/seed-demo-data`.
  - Mounted under `/api/v1/business` in `backend/app/main.py`.
- **Frontend Business Intelligence Center**:
  - `frontend/src/components/Business/BusinessCenter.tsx`: Interactive multi-tenant UI with Tenant Sandbox selector, financial KPI cards (Realized Revenue, Overdue Receivables, Pending Receivables, Health Index), overdue invoices banner with 1-click follow-up reminder generator, and tabs for Invoices Ledger, Client CRM, Projects, and Executive Briefing.
  - Integrated into `frontend/src/App.tsx`.
- **Testing & Verification**:
  - `backend/tests/test_phase8_business.py`: 10 comprehensive unit tests verifying data seeding, multi-tenant isolation, overdue invoice accuracy, tenant filtering, dynamic invoice creation, health score calculation, and CYRUS_BUSINESS specialist agent integration.
  - All 83 automated architectural unit tests passing with 100% pass rate in 0.334s.

---

## [0.8.0] - Phase 7: CYRUS Research & Approved Computer Access - 2026-11-06

### Added
- **Sandboxed Document Reader Subsystem**:
  - `backend/app/research/doc_reader.py`: Secure document reader strictly bounded to `CYRUS_SANDBOX_PATH` with automated path-traversal blocking (`/etc/passwd`, relative directory escaping).
  - Multi-format support: Markdown (`.md`), plain text (`.txt`), code files (`.py`, `.ts`, `.tsx`, `.json`, `.yml`, `.sh`), and PDF streams.
  - Resource safety bounding (100,000 characters limit) for Apple Silicon M5 unified memory.
  - Automatic prompt injection defense wrapping all document excerpts inside `<untrusted_content>` tags.
  - Executive document summarizer and outline extractor addressing the user as "Sir".
- **Zero-Cost Web Research Subsystem**:
  - `backend/app/research/web_researcher.py`: ₹0 recurring cost web research using open, keyless search providers (Wikipedia API, DuckDuckGo Instant Answers, ArXiv).
  - GUARDIAN permission check and SQLite `audit_logs` tracking for every inquiry.
  - Offline scientific synthesis fallback for isolated offline operation.
  - HTML stripping, prompt injection quarantine, and structured citation extraction.
- **Controlled Local Codebase Inspector**:
  - `backend/app/research/code_inspector.py`: Filtered file tree scanner ignoring noisy directories (`.git`, `.venv`, `node_modules`, `__pycache__`) and binary weights.
  - AST-based symbol search for Python classes, functions, and FastAPI routes.
  - Regex symbol scanner for TypeScript interfaces, type aliases, and React components.
  - High-level codebase metrics calculation.
- **Safe Git Assistant**:
  - `backend/app/research/git_assistant.py`: Safe inspection of repository branch, clean/dirty state, staged vs unstaged file changes, and untracked files.
  - Recent commit log viewer (`git log`) and safe staged/unstaged diff viewer.
  - Automated Conventional Commit message drafter (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
  - Destructive command guard: flags and blocks destructive git actions (`git reset --hard`, `git push --force`, `git clean -fd`) under GUARDIAN L4 Restricted tier.
- **Specialist Agent Integration**:
  - Integrated `SandboxedDocReader` and `WebResearcher` into `CYRUS_RESEARCH` (`research_agent.py`).
  - Integrated `SafeGitAssistant` and `CodebaseInspector` into `CYRUS_DEV` (`dev_agent.py`).
- **Research REST API Endpoints**:
  - `backend/app/api/v1/research.py`: Endpoints for `/web-search`, `/document/read`, `/document/list`, `/codebase/tree`, `/codebase/symbols`, `/codebase/overview`, `/git/status`, `/git/commits`, `/git/diff`, and `/git/draft-commit`.
  - Mounted under `/api/v1/research` in `backend/app/main.py`.
- **Frontend Research Center**:
  - `frontend/src/components/Research/ResearchCenter.tsx`: 4-tab UI (Web Research, Doc Reader, Code Inspector, Safe Git Assistant) with interactive inquiry box, preset chips, verified citation cards, document outline chips, path-traversal drill button, codebase metrics, symbol search, and Git commit drafter.
  - Integrated into `frontend/src/App.tsx`.
- **Testing & Verification**:
  - `backend/tests/test_phase7_research.py`: 18 comprehensive unit tests covering document reading, path-traversal prevention, PDF parsing, web research offline fallback, prompt injection quarantine, codebase file tree, Python AST symbol search, TypeScript symbol search, codebase metrics, safe git status, recent commits, destructive git command gating, git diff inspection, Research agent doc delegation, Dev agent git status, and Dev agent codebase overview.
  - All 73 automated architectural unit tests passing with 100% pass rate in 0.295s.

---

## [0.7.0] - Phase 6: CYRUS Specialist Agent Framework - 2026-11-06

### Added
- **Base Specialist Agent Architecture**:
  - `backend/app/agents/base_agent.py`: `BaseAgent` class enforcing universal "Sir" address, 100% English outputs, GUARDIAN security boundary verification, and task lifecycle checkpoints in SQLite `agent_tasks`.
- **Five Core Specialist Agents**:
  - `backend/app/agents/personal_agent.py` (**CYRUS PERSONAL**): Daily agenda management, B.Tech CS study planning, habit tracking, and personal memory recall.
  - `backend/app/agents/business_agent.py` (**CYRUS BUSINESS**): Multi-tenant portfolio isolation, invoice/receivables tracking, pipeline telemetry, and revenue health analysis.
  - `backend/app/agents/dev_agent.py` (**CYRUS DEV**): Codebase architecture review, automated test verification, Git version tracking, and L1-L4 GUARDIAN-gated tool execution.
  - `backend/app/agents/research_agent.py` (**CYRUS RESEARCH**): Structured scientific inquiry, comparative analysis, factual trade-off matrices, and verified citation formatting.
  - `backend/app/agents/executive_agent.py` (**CYRUS EXECUTIVE**): Unified daily morning briefings, end-of-day retrospectives, cross-agent coordination, and system readiness aggregation.
- **Specialist Agent Registry & Intent Router**:
  - `backend/app/agents/agent_registry.py`: Central singleton managing agent listing, semantic intent routing (`route_intent`), direct dispatching, and recent task logging.
- **Specialist Agents REST API**:
  - `backend/app/api/v1/agents.py`: Endpoints for listing agents (`GET /agents`), agent details (`GET /agents/{name}`), direct dispatching (`POST /agents/{name}/dispatch`), auto-delegation (`POST /agents/delegate`), and task history (`GET /agents/tasks/history`).
- **Frontend Agent Center**:
  - `frontend/src/components/Agents/AgentCenter.tsx`: 5 specialist agent cards with status tags, interactive task dispatcher with preset action chips, live task output window, and recent task log table.
- **Testing & Verification**:
  - `backend/tests/test_phase6_agents.py`: 9 unit tests verifying agent listing, personal study planning, business tenant isolation, dev GUARDIAN gating, research citations, executive briefings, multi-agent intent routing, Exam Mode blocking, and Emergency Halt blocking.
  - All 55 automated architectural unit tests passing with 100% pass rate in 0.155s.

---

## [0.6.2] - User Identity & Form of Address Policy: "Sir" - 2026-11-06

### Added & Changed
- **Permanent Form of Address Policy ("Sir")**:
  - Registered User Identity: **Saksham Srivastava**.
  - Form of Address: **"Sir"** across all direct conversations, text interactions, voice responses, greetings, and briefings.
  - Enforced 9 rules: Never casually use first name in address; use "Sir" naturally and contextually; maintain respectful, articulate, JARVIS-like tone; preserve user's legal/account name for internal configuration/documents.
- **System Prompt & Orchestrator Updates**:
  - `backend/app/core/orchestrator.py`: `CYRUS_SYSTEM_PROMPT` updated with mandatory Form of Address policy. Deterministic fallback responses and memory confirmations updated to address the user as "Sir".
  - `backend/app/config.py`: Added `USER_REGISTERED_NAME` and `USER_FORM_OF_ADDRESS`.
  - `backend/app/memory/session_recovery.py`: Clean restore and crash recovery briefings updated to "Welcome back, Sir."
  - `backend/app/voice/kokoro_service.py`: Re-synthesized neural Puck signature preview audio addressing the user as "Sir".
  - `frontend/src/components/Voice/VoiceStudio.tsx`: Default audition texts and presets updated to "Sir".
- **Persistent Memory Seeding**:
  - Stored `preferred_form_of_address` ("Sir") and `user_identity` ("Saksham Srivastava") into SQLite `memory_items` under `MemoryCategory.PERSONAL`, persisting across restarts.
- **Verification**:
  - `test_form_of_address_sir_in_conversational_response` added to `backend/tests/test_phase2_core.py`.
  - All 46 automated unit tests passing with 100% pass rate.

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
