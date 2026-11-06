"""CYRUS Local Database Management.

Provides asynchronous SQLite access with Write-Ahead Logging (WAL) enabled.
Creates and manages normalized tables for sessions, messages, memory,
agent tasks, security permissions, audit logs, and process registry.
"""

import asyncio
import logging
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
from backend.app.config import settings

logger = logging.getLogger("cyrus.database")

SCHEMA_SQL = """
-- 1. Sessions Table: Tracks lifecycle states and session persistence
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'PAUSED', 'SHUTDOWN', 'CRASHED', 'EXAM_MODE')),
    last_heartbeat TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}'
);

-- 2. Messages Table: Conversation history with language tracking
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    raw_input TEXT,
    detected_language TEXT DEFAULT 'English',
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- 3. Memory Items Table: Persistent memory (Personal, Business, Working)
CREATE TABLE IF NOT EXISTS memory_items (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL CHECK(category IN ('personal', 'business', 'working')),
    tenant_id TEXT DEFAULT 'default',
    memory_key TEXT NOT NULL,
    memory_value TEXT NOT NULL,
    fact_type TEXT DEFAULT 'VERIFIED_FACT',
    confidence REAL DEFAULT 1.0,
    source TEXT DEFAULT 'user_explicit',
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(category, tenant_id, memory_key)
);

-- 4. Agent Tasks Table: Task status and state checkpoints
CREATE TABLE IF NOT EXISTS agent_tasks (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    task_description TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PENDING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED')),
    checkpoint_state_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- 5. Guardian Permissions Table: Authorization rules
CREATE TABLE IF NOT EXISTS guardian_permissions (
    id TEXT PRIMARY KEY,
    resource_path TEXT NOT NULL UNIQUE,
    permission_level INTEGER NOT NULL CHECK(permission_level BETWEEN 1 AND 4),
    requires_approval INTEGER DEFAULT 0,
    granted_at TEXT NOT NULL,
    granted_until TEXT
);

-- 6. Audit Logs Table: Immutable append-only security log
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target_resource TEXT NOT NULL,
    risk_level INTEGER NOT NULL CHECK(risk_level BETWEEN 1 AND 4),
    decision TEXT NOT NULL CHECK(decision IN ('ALLOWED', 'DENIED', 'AWAITING_APPROVAL', 'APPROVED_BY_USER', 'HALTED')),
    details_json TEXT DEFAULT '{}'
);

-- 7. Process Registry Table: Tracks process ownership to eliminate orphans
CREATE TABLE IF NOT EXISTS process_registry (
    pid INTEGER PRIMARY KEY,
    process_name TEXT NOT NULL,
    purpose TEXT NOT NULL,
    owned_by_cyrus INTEGER NOT NULL DEFAULT 1,
    started_at TEXT NOT NULL,
    stopped_at TEXT,
    status TEXT NOT NULL CHECK(status IN ('RUNNING', 'STOPPED', 'TERMINATED', 'FAILED'))
);

-- 8. Approval Requests Table: Human-in-the-loop approval workflow for Level 4 actions
CREATE TABLE IF NOT EXISTS approval_requests (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    action_type TEXT NOT NULL,
    target_resource TEXT NOT NULL,
    risk_level INTEGER NOT NULL CHECK(risk_level BETWEEN 1 AND 4),
    consequence_summary TEXT NOT NULL,
    payload_json TEXT DEFAULT '{}',
    status TEXT NOT NULL CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    resolved_at TEXT,
    resolved_by TEXT
);

-- 9. Business Clients Table: Multi-tenant CRM portfolios
CREATE TABLE IF NOT EXISTS business_clients (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    client_name TEXT NOT NULL,
    contact_email TEXT,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'INACTIVE', 'LEAD')),
    created_at TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}'
);

-- 10. Business Invoices Table: Accounts receivable and payment tracking
CREATE TABLE IF NOT EXISTS business_invoices (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    invoice_number TEXT NOT NULL UNIQUE,
    amount_inr REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('DRAFT', 'ISSUED', 'PAID', 'OVERDUE', 'CANCELLED')),
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    paid_date TEXT,
    description TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES business_clients(id) ON DELETE CASCADE
);

-- 11. Business Projects Table: Deliverables, budget, and milestone progress
CREATE TABLE IF NOT EXISTS business_projects (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PLANNING', 'IN_PROGRESS', 'BLOCKED', 'COMPLETED')),
    budget_inr REAL NOT NULL,
    progress_percent INTEGER DEFAULT 0,
    deadline TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES business_clients(id) ON DELETE CASCADE
);

-- 12. Sentinel Monitors Table: Targets for proactive health-checks
CREATE TABLE IF NOT EXISTS sentinel_monitors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    target_url TEXT NOT NULL,
    check_type TEXT NOT NULL CHECK(check_type IN ('HTTP_PING', 'TCP_PORT', 'LOCAL_PROCESS')),
    interval_seconds INTEGER DEFAULT 30,
    timeout_seconds REAL DEFAULT 5.0,
    expected_status_code INTEGER DEFAULT 200,
    is_active INTEGER DEFAULT 1,
    current_status TEXT NOT NULL CHECK(current_status IN ('UP', 'DOWN', 'DEGRADED', 'UNKNOWN')),
    last_checked_at TEXT,
    last_latency_ms REAL,
    consecutive_failures INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

-- 13. Sentinel Events Table: Alert notifications and event history
CREATE TABLE IF NOT EXISTS sentinel_events (
    id TEXT PRIMARY KEY,
    monitor_id TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('INFO', 'IMPORTANT', 'CRITICAL')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    latency_ms REAL,
    status_code INTEGER,
    is_resolved INTEGER DEFAULT 0,
    telegram_dispatched INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (monitor_id) REFERENCES sentinel_monitors(id) ON DELETE CASCADE
);

-- Indices for rapid query retrieval
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_memory_category ON memory_items(category, tenant_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON agent_tasks(session_id, status);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_process_status ON process_registry(status, owned_by_cyrus);
CREATE INDEX IF NOT EXISTS idx_approval_status ON approval_requests(status, expires_at);
CREATE INDEX IF NOT EXISTS idx_business_clients_tenant ON business_clients(tenant_id);
CREATE INDEX IF NOT EXISTS idx_business_invoices_tenant_status ON business_invoices(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_business_projects_tenant ON business_projects(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sentinel_monitors_active ON sentinel_monitors(is_active, current_status);
CREATE INDEX IF NOT EXISTS idx_sentinel_events_created ON sentinel_events(created_at, severity);
"""


def _get_raw_connection() -> sqlite3.Connection:
    """Creates a raw SQLite connection configured for high performance and durability."""
    db_path = settings.absolute_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(db_path),
        timeout=30.0,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row

    if settings.CYRUS_DB_WAL_MODE:
        # WAL mode allows concurrent readers and prevents database locking during writes
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


async def init_db() -> Dict[str, Any]:
    """Initializes the database schema and verifies WAL mode."""
    def _init():
        conn = _get_raw_connection()
        try:
            with conn:
                conn.executescript(SCHEMA_SQL)
                # Ensure fact_type column exists in existing tables
                try:
                    conn.execute("ALTER TABLE memory_items ADD COLUMN fact_type TEXT DEFAULT 'VERIFIED_FACT';")
                except sqlite3.OperationalError:
                    pass  # Column already exists
            cur = conn.execute("PRAGMA journal_mode;")
            journal_mode = cur.fetchone()[0]
            cur = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
            table_count = cur.fetchone()[0]
            return {
                "journal_mode": journal_mode,
                "table_count": table_count,
                "db_path": str(settings.absolute_db_path),
            }
        finally:
            conn.close()

    result = await asyncio.to_thread(_init)
    logger.info("CYRUS SQLite database initialized at %s with WAL mode (%d tables)", result["db_path"], result["table_count"])
    return result


async def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """Executes a read query asynchronously and returns a list of dictionaries."""
    def _execute():
        conn = _get_raw_connection()
        try:
            cur = conn.execute(query, params if params is not None else ())
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    return await asyncio.to_thread(_execute)


async def execute_write(query: str, params: Optional[tuple] = None) -> int:
    """Executes a write query within an atomic transaction and returns affected rows."""
    def _execute():
        conn = _get_raw_connection()
        try:
            with conn:
                cur = conn.execute(query, params if params is not None else ())
                return cur.rowcount
        finally:
            conn.close()

    return await asyncio.to_thread(_execute)


async def check_db_health() -> Dict[str, Any]:
    """Performs a lightweight health check on the SQLite database."""
    def _check():
        conn = _get_raw_connection()
        try:
            cur = conn.execute("SELECT 1;")
            result = cur.fetchone()[0]
            cur = conn.execute("PRAGMA journal_mode;")
            mode = cur.fetchone()[0]
            return {"healthy": result == 1, "journal_mode": mode}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
        finally:
            conn.close()

    return await asyncio.to_thread(_check)
