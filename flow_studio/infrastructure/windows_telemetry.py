"""Windows Hardware Memory Telemetry Provider (Infrastructure Layer).

Queries Windows Win32 GlobalMemoryStatusEx via ctypes.
Enables FLOW Studio to run natively on Windows 10/11 with zero external dependencies.
"""

import ctypes
from typing import NamedTuple

from flow_studio.constants import (
    BYTES_PER_GIBIBYTE,
    FALLBACK_TOTAL_GB,
    FALLBACK_USED_GB,
    FALLBACK_PERCENT,
    PERCENT_MULTIPLIER,
)
from flow_studio.domain.interfaces import TelemetryProviderProtocol
from flow_studio.domain.models import MemoryTelemetry


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class WindowsTelemetryProvider(TelemetryProviderProtocol):
    """Interrogates Windows kernel subsystem for physical RAM metrics."""

    def get_memory_telemetry(self) -> MemoryTelemetry:
        try:
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))

            total_bytes = stat.ullTotalPhys
            avail_bytes = stat.ullAvailPhys
            used_bytes = max(0, total_bytes - avail_bytes)

            used_gb = used_bytes / BYTES_PER_GIBIBYTE
            total_gb = total_bytes / BYTES_PER_GIBIBYTE
            utilization_pct = (used_bytes / total_bytes) * PERCENT_MULTIPLIER

            return MemoryTelemetry(
                used_gb=used_gb,
                total_gb=total_gb,
                utilization_percent=utilization_pct,
            )
        except Exception:
            return MemoryTelemetry(
                used_gb=float(FALLBACK_USED_GB),
                total_gb=float(FALLBACK_TOTAL_GB),
                utilization_percent=float(FALLBACK_PERCENT),
            )

