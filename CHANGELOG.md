# CYRUS Changelog
All notable changes to PROJECT CYRUS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.0] - Phase 3: CYRUS GUARDIAN Deep Security Subsystem - 2026-11-05

### Added
- **4-Tier Permission Model & Sandbox Boundaries**:
  - `backend/app/guardian/permissions.py`: Code-enforced L1 Read, L2 Prepare, L3 Execute, L4 Restricted gating.
- **Human-in-the-Loop Approval Workflow**:
  - `backend/app/guardian/approval.py`: Interactive approval requests in SQLite `approval_requests` with consequence disclosures.
  - Automatic 10-minute TTL expiration for unhandled requests.
  - Explicit approval and rejection endpoints.
- **Prompt Injection Defense & Untrusted Context Isolation**:
  - `backend/app/guardian/prompt_injection.py`: Regex pattern scanner neutralizing jailbreak/override attempts.
  - `<untrusted_content>` boundary wrapper isolating external web and document text.
- **Emergency Stop (CYRUS STOP) Kill Switch**:
  - `backend/app/guardian/emergency_stop.py`: Application-level freeze stopping new tasks, terminating child processes, and revoking tokens.
- **Session Authentication & Identity Binding**:
  - `backend/app/guardian/auth.py`: HMAC-SHA256 session token generation and sovereign owner identity bound to Saksham.
- **Security REST API**:
  - `backend/app/api/v1/guardian.py`: Endpoints for status, pending approvals, approve/reject, audit logs, and emergency halt.
- **Frontend Security Center**:
  - `frontend/src/components/Security/SecurityCenter.tsx`: UI for reviewing pending approvals, viewing audit logs, and triggering CYRUS STOP.
- **Testing & Verification**:
  - `backend/tests/test_phase3_guardian.py`: 7 automated tests covering permissions, approvals, expiration, prompt injection, and emergency stops.
  - All 26 tests passing with a 100% pass rate.

---

## [0.3.0] - Phase 2: CYRUS CORE & Local AI Integration - 2026-11-05

### Added
- CYRUS CORE conversational orchestrator, Ollama interface, language policy guard, and chat API.

---

## [0.2.0] - Phase 1: Foundation and Project Structure - 2026-11-05

### Added
- Modular architecture, SQLite WAL engine, lifecycle state machine, and CLI controller.

---

## [0.1.0] - Phase 0: Environment Inspection & System Architecture - 2026-11-05

### Added
- Hardware inspection of Apple M5, 16 GB RAM, 359 GB storage.
- Architecture specification, security blueprint, and 14-phase roadmap.
