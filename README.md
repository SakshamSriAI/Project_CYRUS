# PROJECT CYRUS
## Cybernetic Yet Responsive Unified System
### Personal AI Intelligence — Built Locally, Securely, and Modularly

CYRUS is an advanced personal AI intelligence inspired by JARVIS, designed and engineered locally for **Saksham**. Unlike standard chatbots or wrapper UIs, CYRUS is built as a modular personal AI operating system featuring autonomous task handling, persistent context and memory, strict backend security boundaries, and natural multilingual comprehension with strictly enforced English responses.

---

## 🌟 Key Pillars

1. **Local-First & ₹0 Target Budget**: Runs on Apple Silicon (M5 MacBook Air) using local open-weight LLMs via Ollama, local SQLite databases, and native macOS capabilities. No recurring cloud fees required for core functionality.
2. **CYRUS GUARDIAN Security**: Every tool call, agent action, and file interaction is gated by backend application logic with 4 permission levels (Read, Prepare, Execute, Restricted) and human-in-the-loop approvals.
3. **Strict Language Policy**: Full comprehension of **Hindi**, **Hinglish**, and **English** inputs, with centralized, non-negotiable **English-only output enforcement** across all text and voice channels.
4. **Deterministic Lifecycle & Session Persistence**:
   - **Pause**: Suspends agent task queues while keeping the UI and status live.
   - **Full Shutdown**: Gracefully checkpoints all state to SQLite, cancels child processes, verifies zero orphaned background tasks, and exits cleanly.
   - **Resume**: Re-opens instantly with prior context, active tasks, conversation history, and pending approvals intact.
   - **Exam Mode**: Guarantees zero background activity, zero microphone access, and zero CPU/RAM footprint so you can study without distraction.
5. **Specialist Multi-Agent Architecture**: Specialist agents (Personal, Business, Dev, Research, Executive, Sentinel) orchestrated by CYRUS CORE under GUARDIAN supervision.

---

## 💻 System Specifications (Detected)

- **Host Machine**: Apple MacBook Air
- **Processor**: Apple M5 (ARM64)
- **Unified Memory (RAM)**: 16 GB
- **Available Storage**: ~359 GB SSD
- **Runtime Toolchains**:
  - Python 3.14.8 (`venv` + `pip` available)
  - Node.js v24.21.0 & npm
  - Git 2.50.1
  - Local AI Engine: Ollama (Recommended Model: Qwen 2.5 7B Instruct / Llama 3.1 8B)

---

## 📂 Documentation Directory

| Document | Purpose |
| :--- | :--- |
| [ARCHITECTURE.md](file:///Users/sakshamsrivastava/Downloads/CYRUS/ARCHITECTURE.md) | Full system design, component breakdown, database schema, lifecycle state machine, and data flows. |
| [SECURITY.md](file:///Users/sakshamsrivastava/Downloads/CYRUS/SECURITY.md) | GUARDIAN permission tiers, tool authorization rules, prompt injection defenses, and emergency stop. |
| [DEVELOPMENT_ROADMAP.md](file:///Users/sakshamsrivastava/Downloads/CYRUS/DEVELOPMENT_ROADMAP.md) | Strict 14-phase roadmap (Phases 0 to 13) with deliverables and sign-off criteria. |
| [PHASE_STATUS.md](file:///Users/sakshamsrivastava/Downloads/CYRUS/PHASE_STATUS.md) | Live progress tracker, current phase status, hardware inspection results, and test logs. |
| [CHANGELOG.md](file:///Users/sakshamsrivastava/Downloads/CYRUS/CHANGELOG.md) | Chronological log of architecture changes, features, and milestones. |
| [.env.example](file:///Users/sakshamsrivastava/Downloads/CYRUS/.env.example) | Configuration blueprint for system variables, ports, model settings, and security keys. |

---

## 🚀 Development Methodology

Development proceeds strictly **one phase at a time**. After each phase:
1. Work is halted.
2. Architecture, code, and features are explained in beginner-friendly mentor style.
3. Automated tests and manual verification are reported.
4. Explicit sign-off is requested before advancing to the next phase.
