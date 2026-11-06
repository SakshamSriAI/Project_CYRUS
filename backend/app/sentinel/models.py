"""CYRUS SENTINEL Models.

Defines telemetry data structures, monitor definitions,
event severity tiers, and daemon status.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EventSeverity(str, Enum):
    INFO = "INFO"            # Level 1: Recoveries, latency recovery, scheduled heartbeats
    IMPORTANT = "IMPORTANT"  # Level 2: High latency (>1500ms), 1st failure, minor degradation
    CRITICAL = "CRITICAL"    # Level 3: Consecutive downtime (2+ failures), connection refused


class MonitorStatus(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


class CheckType(str, Enum):
    HTTP_PING = "HTTP_PING"
    TCP_PORT = "TCP_PORT"
    LOCAL_PROCESS = "LOCAL_PROCESS"


@dataclass
class SentinelMonitor:
    id: str
    name: str
    target_url: str
    check_type: CheckType = CheckType.HTTP_PING
    interval_seconds: int = 30
    timeout_seconds: float = 5.0
    expected_status_code: int = 200
    is_active: bool = True
    current_status: MonitorStatus = MonitorStatus.UNKNOWN
    last_checked_at: Optional[str] = None
    last_latency_ms: Optional[float] = None
    consecutive_failures: int = 0
    created_at: str = ""


@dataclass
class SentinelEvent:
    id: str
    monitor_id: str
    monitor_name: str
    severity: EventSeverity
    title: str
    message: str
    latency_ms: Optional[float] = None
    status_code: Optional[int] = None
    is_resolved: bool = False
    telegram_dispatched: bool = False
    created_at: str = ""


@dataclass
class SentinelDaemonStatus:
    is_running: bool
    lifecycle_state: str
    active_monitors_count: int
    services_up_count: int
    services_down_count: int
    services_degraded_count: int
    last_cycle_timestamp: Optional[str] = None
    limitations_notice: str = ""
