"""Tests for CYRUS Lifecycle and Process Ownership Manager."""

import os
import pytest
from backend.app.lifecycle.process_manager import (
    LifecycleState,
    process_manager,
)


@pytest.mark.asyncio
async def test_lifecycle_state_transitions():
    process_manager.set_state(LifecycleState.ACTIVE)
    assert process_manager.current_state == LifecycleState.ACTIVE

    pause_res = await process_manager.pause_system()
    assert process_manager.current_state == LifecycleState.PAUSED
    assert pause_res["status"] == "PAUSED"

    resume_res = await process_manager.resume_system()
    assert process_manager.current_state == LifecycleState.ACTIVE
    assert resume_res["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_process_registration_and_listing():
    current_pid = os.getpid()
    await process_manager.register_process(
        pid=current_pid,
        process_name="pytest_runner",
        purpose="automated_testing",
        owned_by_cyrus=True,
    )

    procs = await process_manager.list_registered_processes(only_running=True)
    matching = [p for p in procs if p["pid"] == current_pid]
    assert len(matching) == 1
    assert matching[0]["process_name"] == "pytest_runner"
    assert matching[0]["os_alive"] is True

    await process_manager.unregister_process(current_pid, "STOPPED")
