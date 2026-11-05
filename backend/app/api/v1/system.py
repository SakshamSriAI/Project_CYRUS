"""CYRUS System Information & Lifecycle Control Endpoints."""

import os
import platform
import shutil
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.lifecycle.process_manager import LifecycleState, process_manager

router = APIRouter(prefix="/system", tags=["System & Lifecycle"])


@router.get("/info")
async def get_system_info():
    """Returns detected host specifications and development runtime status."""
    disk = shutil.disk_usage("/")
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "storage": {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent_used": round((disk.used / disk.total) * 100, 1),
        },
        "sandbox_root": settings.CYRUS_SANDBOX_PATH,
        "ollama_endpoint": settings.OLLAMA_BASE_URL,
    }


@router.get("/processes")
async def get_registered_processes():
    """Returns currently tracked subprocesses to verify process ownership."""
    procs = await process_manager.list_registered_processes(only_running=False)
    return {
        "lifecycle_state": process_manager.current_state.value,
        "total_tracked": len(procs),
        "processes": procs,
    }


@router.post("/lifecycle/pause")
async def pause_lifecycle():
    """Pauses task intake and checkpoints active agent states."""
    result = await process_manager.pause_system()
    return result


@router.post("/lifecycle/resume")
async def resume_lifecycle():
    """Resumes active operation from paused state."""
    result = await process_manager.resume_system()
    return result


@router.post("/lifecycle/exam-mode")
async def activate_exam_mode():
    """Engages Exam Mode: stops background tasks, guarantees zero footprint."""
    result = await process_manager.enter_exam_mode()
    return result
