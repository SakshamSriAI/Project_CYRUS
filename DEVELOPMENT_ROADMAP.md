# CYRUS Master Development Roadmap
## Strict Phase-by-Phase Execution Plan

> **Cardinal Rule**: Never implement multiple phases at once. Never proceed to the next phase without explicit user approval. At each phase completion: Stop, summarize, explain code, run tests, demonstrate working functionality, and ask:
> *"Phase [N] is complete. Would you like me to proceed to Phase [N+1]?"*

---

### Phase 0: Environment Inspection & System Architecture *(Current Phase)*
- **Objectives**:
  - Inspect MacBook Air hardware (Apple M5, RAM, storage, macOS version).
  - Verify installed developer toolchains (Python, Node.js, Git, Ollama).
  - Select optimal local open-weight model for 16 GB unified RAM.
  - Formulate end-to-end modular architecture (CORE, GUARDIAN, MEMORY, AGENTS, CONNECT).
  - Design session persistence, Pause, Full Shutdown, Resume, and Exam Mode mechanisms.
  - Define language architecture (multilingual input understanding with strict English response enforcement).
  - Prepare foundational project specifications and configuration blueprints.
- **Deliverables**: Complete documentation suite (`README.md`, `ARCHITECTURE.md`, `SECURITY.md`, `DEVELOPMENT_ROADMAP.md`, `PHASE_STATUS.md`, `CHANGELOG.md`, `.env.example`).
- **Gate**: Stop and ask for Saksham's approval before creating Phase 1 code.

---

### Phase 1: Foundation & Project Structure
- **Objectives**:
  - Initialize project directory hierarchy for backend and frontend.
  - Set up Python virtual environment (`venv`) and FastAPI backend skeleton.
  - Set up React + TypeScript frontend using Vite with dark futuristic styling baseline.
  - Implement SQLite database initialization with WAL mode and schema tables.
  - Implement centralized configuration management via `pydantic-settings` and `.env`.
  - Establish process ownership registry foundation (`process_manager.py`).
  - Create `/api/v1/health` and basic system info endpoints.
- **Deliverables**: Clean runnable foundation where backend and frontend communicate via health checks.
- **Verification**: Pytest test suite passing; frontend dev server verifies backend connectivity.

---

### Phase 2: CYRUS CORE & Local AI Integration
- **Objectives**:
  - Guide or verify Ollama installation on MacBook Air.
  - Pull and test recommended model (Qwen 2.5 7B Instruct / Llama 3.1 8B).
  - Implement backend `llm_client.py` and `orchestrator.py`.
  - Build **Centralized Language Gate**:
    - Automatic input language detection (Hindi, Hinglish, English).
    - Preserves semantic intent and technical terms.
    - Centrally guarantees output is 100% English.
  - Connect Chat UI with streaming text responses.
  - Implement conversation persistence to SQLite.
- **Deliverables**: Functional text-based AI assistant running locally on MacBook Air.
- **Verification**: Test with Hindi input ("aaj kya plan hai?"), Hinglish ("mujhe code explain karo"), and English. Verify 100% of responses are in English.

---

### Phase 3: CYRUS GUARDIAN Security Subsystem
- **Objectives**:
  - Implement backend permission engine with L1 to L4 permission tiers.
  - Build Tool Call Authorization Layer (prevents direct shell access).
  - Implement interactive user approval workflow for L4 actions.
  - Implement append-only Audit Logging table (`audit_logs`).
  - Build Emergency Stop (`CYRUS STOP`) mechanism.
  - Create Security Center UI tab (view permissions, audit logs, active sessions).
- **Deliverables**: Secure sandbox environment where unauthorized or high-risk actions are blocked by code.
- **Verification**: Test unauthorized path traversal, arbitrary bash execution, and prompt-injection bypass attempts.

---

### Phase 4: CYRUS Persistent Memory
- **Objectives**:
  - Implement Personal, Business, and Working Memory subsystems in SQLite.
  - Support memory CRUD operations (view, add, edit, delete, inspect confidence).
  - Implement semantic context injection for relevant conversation turns.
  - Implement incremental state checkpoints for conversational resilience.
  - Build Memory Center UI tab (interactive memory browser and editor).
  - Implement Session Recovery flow (displays last session summary upon reload).
- **Deliverables**: System remembers facts across restarts, separates personal and business data, and recovers context.
- **Verification**: Store a preference, restart backend, verify CYRUS remembers and cites the fact accurately.

---

### Phase 5: CYRUS Voice Interaction
- **Objectives**:
  - Integrate local Speech-to-Text (Whisper or Apple Speech API).
  - Integrate local Text-to-Speech (Piper / local TTS).
  - Support spoken Hindi and Hinglish recognition converted to English understanding.
  - Guarantee all spoken responses are exclusively in English.
  - Implement microphone controls with visible indicator and clean hardware release.
  - Support speech interruption / cancellation.
- **Deliverables**: Hands-free natural voice interaction operating locally on macOS.
- **Verification**: Speak in Hinglish; verify CYRUS transcribes, thinks, and speaks back in English.

---

### Phase 6: CYRUS Multi-Agent Specialist Framework
- **Objectives**:
  - Build modular agent orchestration layer.
  - Implement **CYRUS PERSONAL** (daily schedule, habits, personal planning).
  - Implement **CYRUS BUSINESS** (client tracking, business metrics).
  - Implement **CYRUS DEV** (codebase inspection, linting, git assistance).
  - Implement **CYRUS RESEARCH** (structured research with citations).
  - Implement **CYRUS EXECUTIVE** (daily briefings, cross-agent coordination).
  - Enforce GUARDIAN permissions across every specialist agent.
- **Deliverables**: Multi-agent coordinated system routed through CYRUS CORE.
- **Verification**: Delegate specialized tasks to each agent and verify controlled context sharing.

---

### Phase 7: Research & Approved Computer Access
- **Objectives**:
  - Implement web research tool using open/free search APIs with source validation.
  - Implement sandboxed document reader (PDF, Markdown, text).
  - Implement controlled local codebase inspector for designated project directories.
  - Implement safe Git helpers (branch inspection, commit drafting).
- **Deliverables**: CYRUS can read local project files and research online while confined to safety boundaries.
- **Verification**: Ask CYRUS to analyze a repository structure and summarize a research topic.

---

### Phase 8: Business Intelligence & Integrations
- **Objectives**:
  - Implement multi-tenant business data storage with strict tenant boundaries.
  - Support mock/test accounts for CRM, invoices, revenue tracking, and project tasks.
  - Generate automated business summary reports and financial health analysis.
- **Deliverables**: Business intelligence queries answered using real/test structured data without hallucination.
- **Verification**: Query "Which invoices are overdue?" and verify accurate, factual responses from test DB.

---

### Phase 9: CYRUS SENTINEL & Proactive Local Monitoring
- **Objectives**:
  - Implement lightweight background health-check scheduler (pings websites, local servers).
  - Event classification (Level 1 Info, Level 2 Important, Level 3 Critical).
  - Build Telegram bot alert integration (free tier) for critical alerts.
  - Clearly display local monitoring limitations (monitoring stops when MacBook is asleep or shutdown).
- **Deliverables**: Local proactive watcher alerting to downtime or anomalies while running.
- **Verification**: Simulate mock website downtime; verify SENTINEL detects and alerts within 30 seconds.

---

### Phase 10: Advanced Voice & Optional Telephony
- **Objectives**:
  - Explore two-way voice call integrations (Twilio/SIP) for Level 3 emergency escalation.
  - Transparently present cost models before enabling any paid telephony integration.
  - Implement voice-based authorization verification.
- **Deliverables**: Prototype emergency call escalation workflow with zero default cost.
- **Verification**: Verify call simulation and cost-guard boundaries.

---

### Phase 11: Android & Cross-Device PWA Access
- **Objectives**:
  - Build responsive mobile UI / Progressive Web App (PWA).
  - Implement secure local-network and VPN authentication (Tailscale / local Wi-Fi).
  - Support mobile text and voice interaction connected to MacBook host.
  - Maintain English-only response policy across mobile clients.
- **Deliverables**: Access CYRUS seamlessly from Android smartphone within local network.
- **Verification**: Connect phone browser to MacBook server; send voice note; receive English response.

---

### Phase 12: Optional Cloud Infrastructure Evaluation
- **Objectives**:
  - Comprehensive cost-benefit analysis of optional cloud hosting (e.g. Oracle Free Tier, Hetzner, Railway).
  - Architecture plan for always-on background monitoring when MacBook is asleep.
  - Implementation ONLY if explicitly requested and budgeted by Saksham.
- **Deliverables**: Written evaluation and optional deployment scripts.

---

### Phase 13: System Optimization, Hardening & Final Audit
- **Objectives**:
  - Benchmark inference latency and memory utilization on M5 chip.
  - Perform full security penetration test (prompt injection, privilege escalation).
  - Stress test session recovery, crash handling, and Exam Mode transitions.
  - Complete technical documentation and user manual.
- **Deliverables**: Production-grade personal AI operating system operating stably and reliably.
- **Verification**: Comprehensive audit report and final sign-off.
