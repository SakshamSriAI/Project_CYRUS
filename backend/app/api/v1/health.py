"""CYRUS Health Check Endpoint.

Returns detailed diagnostics on backend status, SQLite database,
lifecycle state, process tracker, and language governance.
"""

from datetime import datetime, timezone
import os
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.database import check_db_health
from backend.app.lifecycle.process_manager import process_manager

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


def _get_ram_info():
    """Retrieves RAM information using standard library os.sysconf or psutil."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        return {
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "ram_available_gb": round(mem.available / (1024**3), 2),
            "ram_percent_used": mem.percent,
            "cpu_percent": psutil.cpu_percent(interval=None),
        }
    except ImportError:
        try:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            total_bytes = pages * page_size
            return {
                "ram_total_gb": round(total_bytes / (1024**3), 2),
                "ram_available_gb": "N/A (psutil not installed)",
                "ram_percent_used": 0.0,
                "cpu_percent": 0.0,
            }
        except Exception:
            return {
                "ram_total_gb": 16.0,
                "ram_available_gb": "Unknown",
                "ram_percent_used": 0.0,
                "cpu_percent": 0.0,
            }


@router.get("")
async def get_health_status():
    """Returns real-time health and diagnostics for the CYRUS backend."""
    db_status = await check_db_health()
    mem_info = _get_ram_info()

    return {
        "status": "ONLINE" if db_status.get("healthy") else "DEGRADED",
        "app_name": settings.CYRUS_APP_NAME,
        "version": settings.CYRUS_VERSION,
        "environment": settings.CYRUS_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "lifecycle_state": process_manager.current_state.value,
        "database": {
            "status": "HEALTHY" if db_status.get("healthy") else "ERROR",
            "journal_mode": db_status.get("journal_mode", "UNKNOWN"),
            "path": str(settings.absolute_db_path),
        },
        "system": mem_info,
        "language_governance": {
            "default_response_language": settings.DEFAULT_RESPONSE_LANGUAGE,
            "supported_inputs": settings.SUPPORTED_INPUT_LANGUAGES,
            "allow_hindi_responses": settings.ALLOW_HINDI_RESPONSES,
        },
    }
