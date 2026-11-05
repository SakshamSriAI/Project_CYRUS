"""Tests for CYRUS SQLite Database Management and WAL mode."""

import pytest
from backend.app.database import check_db_health, execute_query, execute_write, init_db


@pytest.mark.asyncio
async def test_database_initialization_and_wal():
    db_info = await init_db()
    assert db_info["journal_mode"].upper() == "WAL"
    assert db_info["table_count"] >= 7

    health = await check_db_health()
    assert health["healthy"] is True
    assert health["journal_mode"].upper() == "WAL"


@pytest.mark.asyncio
async def test_database_crud_operations():
    # Insert a dummy session
    await execute_write(
        "INSERT INTO sessions (id, started_at, status, last_heartbeat) VALUES (?, ?, ?, ?)",
        ("test-sess-1", "2026-11-05T00:00:00Z", "ACTIVE", "2026-11-05T00:00:00Z"),
    )

    rows = await execute_query("SELECT * FROM sessions WHERE id = ?", ("test-sess-1",))
    assert len(rows) == 1
    assert rows[0]["id"] == "test-sess-1"
    assert rows[0]["status"] == "ACTIVE"

    # Clean up
    await execute_write("DELETE FROM sessions WHERE id = ?", ("test-sess-1",))
