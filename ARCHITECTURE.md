# CYRUS System Architecture Specification
## Document Version: 1.0.0 (Phase 0 Baseline)

---

## 1. Architectural Philosophy

CYRUS (**Cybernetic Yet Responsive Unified System**) is designed around four foundational architectural principles:

1. **Local Independence & Zero-Cost Baseline**:
   All core intelligence, storage, orchestration, and lifecycle persistence operate locally on the developer's MacBook Air (Apple M5, 16 GB Unified RAM) without mandatory internet connectivity or paid cloud services.
2. **Deterministic Security Separation (CYRUS GUARDIAN)**:
   Intelligence and execution are strictly decoupled. LLM agents never execute operating system tools, file modifications, or network operations directly. All tool execution passes through a code-enforced security gateway with structured permission gates.
3. **Session Durability & Clean Lifecycle State Transitions**:
   The system supports state checkpoints at atomic boundaries. When closed or shut down, all active context, unfinished tasks, and pending approvals are persisted to an ACID-compliant local SQLite database. On restart, the system resumes state seamlessly without orphaned processes or ghost background tasks.
4. **Centralized Language Governance**:
   Input comprehension supports multilingual understanding (Hindi, Hinglish, English) while output generation is centrally constrained to clear, professional English across all response pipelines (text, streaming, voice, alerts).

```
                      +---------------------------------------+
                      |       USER (Saksham)                  |
                      |  [English / Hindi / Hinglish Input]   |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |     CYRUS FRONTEND (React + TS)       |
                      |   - Dashboard       - Conversation    |
                      |   - Agent Center    - Memory Center   |
                      |   - Security View   - Lifecycle Hub   |
                      +-------------------+-------------------+
                                          | HTTP REST / WebSocket
                                          v
                      +---------------------------------------+
                      |      CYRUS BACKEND (FastAPI API)      |
                      |   - Lifecycle / Process Controller    |
                      |   - Language Policy Enforcement Gate  |
                      |   - Session & Recovery Manager        |
                      +-------------------+-------------------+
                                          |
                      +-------------------+-------------------+
                      |                                       |
                      v                                       v
         +------------------------+              +------------------------+
         |      CYRUS CORE        |              |     CYRUS GUARDIAN     |
         |  - Intent Parser       |              |  - Permission Gates    |
         |  - Local LLM Gateway   |<------------>|  - Tool Approvals      |
         |  - Specialist Router   | Request Tool |  - Audit Log Ledger    |
         |  - Memory Injector     |  Validation  |  - Emergency Halt      |
         +-----------+------------+              +-----------+------------+
                     |                                       |
        +------------+------------+                          | Authorized
        |                         |                          | Execution
        v                         v                          v
+---------------+         +---------------+          +---------------+
| CYRUS AGENTS  |         | CYRUS MEMORY  |          | CYRUS CONNECT |
| - Personal    |         | - Personal    |          | - Local Files |
| - Business    |         | - Business    |          | - Git/GitHub  |
| - Dev / Sent. |         | - Working     |          | - Integrations|
+---------------+         +---------------+          +---------------+
                                  |
                                  v
                      +------------------------+
                      | SQLite Local Database  |
                      | (WAL Mode, Encrypted)  |
                      +------------------------+
```

---

## 2. Hardware Profile & Local Inference Sizing

From the Phase 0 environment inspection:
- **Processor**: Apple M5 (ARM64 Architecture)
- **RAM**: 16 GB Unified Memory
- **Disk Storage**: 359 GB available SSD
- **OS**: macOS Darwin 26.5.1
- **Toolchain**: Python 3.14.8, Node.js v24.21.0, Git 2.50.1

### Local Model Feasibility Matrix

Apple's unified memory is shared between the CPU, GPU (Metal), and the operating system.

| Model Tier | Model Example | Quantization | RAM Required | Feasibility & Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Lightweight (3B)** | Qwen 2.5 3B / Llama 3.2 3B | Q4_K_M | ~2.0 - 2.5 GB | **Instant / Ultra-Fast**: Excellent for quick intent routing, testing, and low-resource tasks. |
| **Balanced (7B - 8B)** | **Qwen 2.5 7B Instruct** | **Q4_K_M** | **~4.7 - 5.2 GB** | **PRIMARY RECOMMENDATION**: Best overall balance for 16 GB RAM. Superb multilingual comprehension (Hindi/Hinglish), strong tool calling, accurate code generation, and leaves ~10 GB RAM for macOS, IDE, and apps. |
| **Heavy (9B - 14B)** | Gemma 2 9B / Qwen 2.5 14B | Q4_K_M | ~6.0 - 10.5 GB | **Usable with caution**: 9B works well; 14B will consume ~65% of RAM, risking disk swap when running heavy IDEs or compilers simultaneously. |
| **Extreme (32B - 70B)**| Qwen 2.5 32B / Llama 3.3 70B | Any | 20 GB - 45 GB | **NOT FEASIBLE**: Exceeds hardware limit (16 GB). |

---

## 3. Core Component Breakdown

### 3.1 CYRUS CORE (Central Intelligence)
- **Responsibility**: Interprets user intent, injects working memory and persistent context, talks to Ollama via local API, formulates multi-step reasoning plans, and routes tasks to specialist agents.
- **Language Policy Gate**: Intercepts user inputs, detects language family, and ensures system prompts strictly prohibit any non-English response. An output validation guard inspects responses before returning to the UI.
- **Independence from Direct Execution**: CORE cannot invoke OS tools or write files directly; it emits structured action requests (`ActionRequest`) that must be validated by GUARDIAN.

### 3.2 CYRUS GUARDIAN (Security Subsystem)
- Enforces an application-level security boundary (not prompt-dependent).
- **Four Permission Tiers**:
  1. *Level 1 (Read)*: Read approved project files, check system status.
  2. *Level 2 (Prepare)*: Draft code, formulate plans, prepare calendar entries (no state change).
  3. *Level 3 (Execute)*: Run unit tests, write to designated project directories, create reminders.
  4. *Level 4 (Restricted)*: Delete files, modify system settings, access external networks, financial records. **Requires explicit human modal confirmation with an explanation of consequences**.
- **Audit Logging**: Every action request, evaluation, approval, and execution output is recorded to an append-only audit log table.
- **Emergency Stop (CYRUS STOP)**: An immediate software-level kill switch that aborts all running tasks, revokes temporary tokens, and transitions the system to a safe lock state.

### 3.3 CYRUS MEMORY (Knowledge & Context)
Persistent memory uses an ACID-compliant local SQLite database with write-ahead logging (WAL) enabled:
- **Personal Memory**: Personal routines, preferences, study goals, reminders.
- **Business Memory**: Multi-tenant client data, project milestones, invoices, revenue metrics (strict tenant isolation).
- **Working Memory**: Active session state, conversation context window, in-flight goals, pending approvals.
- **Semantic Vector Storage**: Fast local vector search (using SQLite with `sqlite-vec` or `chromadb` local embeddings) introduced when retrieval volume justifies it.

### 3.4 CYRUS AGENTS (Specialist Intelligence)
1. **CYRUS PERSONAL**: Daily schedule, study planning, routines, personal knowledge management.
2. **CYRUS BUSINESS**: Client CRM tracking, project deliverables, invoice status, operational summaries.
3. **CYRUS DEV**: Codebase indexing, bug diagnosis, automated testing, Git/GitHub assistant.
4. **CYRUS RESEARCH**: Structured internet research, document synthesis, fact-checking with cited sources.
5. **CYRUS EXECUTIVE**: High-level task coordinator, daily briefing compiler, bottleneck resolver.
6. **CYRUS SENTINEL**: Local health checks, website availability pings, error alerting.

### 3.5 CYRUS CONNECT (Integrations & OS Bridge)
- Controlled bridges to external APIs, filesystem directories, Git binaries, and local scripts.
- Sandboxed execution ensures commands execute only in explicitly authorized directories (`~/Downloads/CYRUS` and authorized test sandboxes).

---

## 4. Lifecycle & Session Persistence Architecture

The system is designed so that Saksham can shut down CYRUS for hours or days, use the MacBook normally, reopen CYRUS, and continue seamlessly.

```
                      +-------------------+
                      |   ACTIVE RUNNING  |
                      +---------+---------+
                                |
             +------------------+------------------+
             |                                     |
             v                                     v
     [User Selects Pause]               [User Selects Full Shutdown]
             |                                     |
             v                                     v
+-------------------------+             +-------------------------+
|     PAUSED STATE        |             |   SHUTDOWN SEQUENCE     |
| 1. Stop new task queue  |             | 1. Checkpoint tasks     |
| 2. Finish current step  |             | 2. Terminate subprocesses|
| 3. Write checkpoint     |             | 3. Stop background jobs |
| 4. Keep UI alive        |             | 4. Verify 0 processes   |
+------------+------------+             | 5. Close DB safely      |
             |                          +------------+------------+
             | [Resume]                              |
             +----------------->+<-------------------+ [Restart CYRUS]
                                |
                                v
                    +-------------------------+
                    |    SESSION RECOVERY     |
                    | 1. Load last checkpoint |
                    | 2. Re-hydrate context   |
                    | 3. Report pending tasks |
                    | 4. Verify approvals     |
                    +-------------------------+
```

### 4.1 Process Ownership Registry
To avoid accidentally killing unrelated user processes or shared services:
- A `process_registry` table in SQLite stores every subprocess launched by CYRUS with its PID, start timestamp, purpose, and ownership tag (`OWNED_BY_CYRUS = true`).
- A shared daemon like Ollama (if run as a macOS system service) is marked `EXTERNAL_SHARED`. CYRUS will never terminate external shared services without explicit confirmation.
- During Full Shutdown, CYRUS queries only processes tagged `OWNED_BY_CYRUS`, sends `SIGTERM`, waits a grace period (3 seconds), and uses `SIGKILL` only if the process fails to stop cleanly.

### 4.2 Exam Mode
- Triggered by user command or UI button.
- Immediately stops all CYRUS background loops, shuts off microphone polling, kills local LLM inference processes owned by CYRUS, and flushes session state.
- Leaves a pristine 0% CPU and 0% RAM footprint so your MacBook runs completely uninhibited during exams or intensive tasks.

### 4.3 Crash Recovery
- SQLite Write-Ahead Logging (WAL) ensures atomic commits.
- A heartbeat flag `session_active = true` is set during runtime.
- If the app opens and finds `session_active = true` without a clean shutdown record, it detects an unexpected termination or crash. It presents a **Crash Recovery Report**, restores the last valid transaction checkpoint, and prompts before resuming any interrupted action.

---

## 5. Centralized Language Governance

CYRUS enforces language handling at the application layer:

```
User Input ("Aaj mera kya plan hai?")
   |
   v
[Language Gate]
   |--> Detects: Hinglish / Hindi Intent
   |--> Standardizes intent representation
   |--> Appends strict output directive to prompt context
   |
   v
[Local LLM Generation]
   |
   v
[Output Enforcement Guard]
   |--> Validates response is 100% English
   |--> If non-English tokens detected, re-runs or sanitizes
   |
   v
User Response ("You have two study sessions and one project review scheduled for today.")
```

- Configuration parameters:
  - `DEFAULT_RESPONSE_LANGUAGE = "English"`
  - `INPUT_LANGUAGE_DETECTION = "Automatic"`
  - `SUPPORTED_INPUT_LANGUAGES = ["English", "Hindi", "Hinglish"]`
  - `ALLOW_HINDI_RESPONSES = False`

---

## 6. Database Schema Design (SQLite)

The local SQLite database (`cyrus.db`) uses normalized tables for durability:

1. **`sessions`**: `id`, `started_at`, `ended_at`, `status` (`ACTIVE`, `PAUSED`, `SHUTDOWN`, `CRASHED`), `last_heartbeat`, `metadata_json`.
2. **`messages`**: `id`, `session_id`, `role` (`user`, `assistant`, `system`), `raw_input`, `detected_language`, `content`, `timestamp`.
3. **`memory_items`**: `id`, `category` (`personal`, `business`, `working`), `tenant_id`, `key`, `value`, `confidence`, `source`, `created_at`, `updated_at`.
4. **`agent_tasks`**: `id`, `session_id`, `agent_name`, `status` (`PENDING`, `RUNNING`, `PAUSED`, `COMPLETED`, `FAILED`), `checkpoint_state_json`, `created_at`.
5. **`guardian_permissions`**: `id`, `resource`, `permission_level` (1-4), `requires_approval`, `granted_until`.
6. **`audit_logs`**: `id`, `timestamp`, `actor` (`CORE`, `GUARDIAN`, `USER`), `action`, `target_resource`, `risk_level`, `outcome`, `details_json`.
7. **`process_registry`**: `pid`, `process_name`, `owned_by_cyrus`, `started_at`, `status`.

---

## 7. Proposed Directory Structure

```
/Users/sakshamsrivastava/Downloads/CYRUS/
├── .env.example                # Configuration blueprint
├── .gitignore                  # Git ignore rules
├── README.md                   # Project overview
├── ARCHITECTURE.md             # This document
├── SECURITY.md                 # Security & Guardian specifications
├── DEVELOPMENT_ROADMAP.md      # 14-phase roadmap
├── CHANGELOG.md                # Changes log
├── PHASE_STATUS.md             # Live phase dashboard
├── scripts/                    # Management scripts (run, pause, shutdown, verify)
│   ├── cyrus_ctl.sh            # Unified CLI controller
│   └── test_env.py             # Environment verification script
├── backend/                    # FastAPI Backend Application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # Server entrypoint
│   │   ├── config.py           # Environment & settings
│   │   ├── database.py         # SQLite connection & migrations
│   │   ├── core/               # CYRUS CORE orchestrator
│   │   │   ├── orchestrator.py
│   │   │   ├── language_gate.py # Multilingual input / English output
│   │   │   └── llm_client.py   # Ollama interface
│   │   ├── guardian/           # Security subsystem
│   │   │   ├── security_engine.py
│   │   │   ├── permissions.py
│   │   │   └── audit_logger.py
│   │   ├── memory/             # Persistent memory managers
│   │   │   ├── memory_store.py
│   │   │   └── context_manager.py
│   │   ├── agents/             # Specialist agents
│   │   │   ├── base_agent.py
│   │   │   ├── personal_agent.py
│   │   │   └── dev_agent.py
│   │   ├── lifecycle/          # Process tracking, pause, shutdown, resume
│   │   │   ├── process_manager.py
│   │   │   └── session_persistence.py
│   │   └── api/                # REST & WebSocket routes
│   │       ├── v1/
│   │       │   ├── chat.py
│   │       │   ├── lifecycle.py
│   │       │   ├── memory.py
│   │       │   └── guardian.py
│   ├── tests/                  # Automated test suite
│   ├── requirements.txt
│   └── data/                   # SQLite database & checkpoints directory
└── frontend/                   # React + TypeScript + Vite UI
    ├── src/
    │   ├── components/         # Premium dark command-center components
    │   │   ├── Dashboard/
    │   │   ├── Chat/
    │   │   ├── AgentHub/
    │   │   ├── MemoryCenter/
    │   │   ├── GuardianView/
    │   │   └── LifecycleBar/
    │   ├── context/            # State management
    │   ├── services/           # API client
    │   ├── styles/             # Dark navy/electric cyan theme
    │   ├── App.tsx
    │   └── main.tsx
    ├── package.json
    └── vite.config.ts
```

---

## 8. Future Extension Points (Cross-Device & Cloud)

While initial development is strictly local to Saksham's MacBook Air:
- **API Boundary Abstraction**: All frontend-to-backend communication uses standard OpenAPI REST and WebSocket endpoints. Adding an Android app (Phase 11) simply targets the same endpoints via local Wi-Fi or secure WireGuard/Tailscale VPN without changing backend logic.
- **Pluggable LLM Provider**: The `llm_client.py` module defines an abstract interface. It connects to local Ollama by default, but can optionally connect to self-hosted or cloud endpoints in Phase 12 if approved.
- **Tenant Isolation**: Database tables include `tenant_id` from day one, allowing future multi-business or multi-device profile separation without painful schema migrations.
