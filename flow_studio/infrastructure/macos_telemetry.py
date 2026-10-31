"""macOS Hardware Telemetry Provider (Infrastructure Layer).

Queries kernel memory management state via native sysctl and vm_stat binaries.
Zero dependencies on external C-extension packages like psutil.
"""

import subprocess
from typing import Dict

from flow_studio.constants import (
    BYTES_PER_GIBIBYTE,
    FALLBACK_TOTAL_GB,
    FALLBACK_USED_GB,
    FALLBACK_PERCENT,
    MACOS_PAGE_SIZE_BYTES,
    PERCENT_MULTIPLIER,
)
from flow_studio.domain.interfaces import TelemetryProviderProtocol
from flow_studio.domain.models import MemoryTelemetry


class NativeMacOSTelemetryProvider(TelemetryProviderProtocol):
    """Interrogates Darwin kernel subsystem for Unified RAM state."""

    def get_memory_telemetry(self) -> MemoryTelemetry:
        try:
            # 1. Total Physical Unified Memory
            hw_raw = subprocess.check_output(
                ["sysctl", "-n", "hw.memsize"], stderr=subprocess.DEVNULL
            )
            total_bytes = int(hw_raw.decode("utf-8").strip())

            # 2. Virtual Memory Page Statistics
            vm_raw = subprocess.check_output(["vm_stat"], stderr=subprocess.DEVNULL)
            stats: Dict[str, int] = {}
            for line in vm_raw.decode("utf-8").split("\n")[1:]:
                if ":" in line:
                    key, val = line.split(":", 1)
                    stats[key.strip()] = int(val.strip().rstrip("."))

            # 3. Calculate unallocated and speculative memory
            pages_free = stats.get("Pages free", 0)
            pages_speculative = stats.get("Pages speculative", 0)
            free_bytes = (pages_free + pages_speculative) * MACOS_PAGE_SIZE_BYTES

            used_bytes = max(0, total_bytes - free_bytes)
            used_gb = used_bytes / BYTES_PER_GIBIBYTE
            total_gb = total_bytes / BYTES_PER_GIBIBYTE
            utilization_pct = (used_bytes / total_bytes) * PERCENT_MULTIPLIER

            return MemoryTelemetry(
                used_gb=used_gb,
                total_gb=total_gb,
                utilization_percent=utilization_pct,
            )

        except Exception:
            # Safe defensive fallback matching documented baseline
            return MemoryTelemetry(
                used_gb=float(FALLBACK_USED_GB),
                total_gb=float(FALLBACK_TOTAL_GB),
                utilization_percent=float(FALLBACK_PERCENT),
            )

