"""macOS Hardware Telemetry Provider (Infrastructure Layer).

Queries kernel memory management state via native sysctl and vm_stat binaries.
Zero dependencies on external C-extension packages like psutil.
"""

import re
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
    """Interrogates Darwin kernel subsystem for Unified RAM state.
    
    Calculates memory strictly identical to macOS Activity Monitor:
    Memory Used = App Memory + Wired Memory + Compressed Memory
    (Excluding file-backed disk cache / cached files)
    """

    def get_memory_telemetry(self) -> MemoryTelemetry:
        try:
            # 1. Total Physical Unified Memory
            hw_raw = subprocess.check_output(
                ["sysctl", "-n", "hw.memsize"], stderr=subprocess.DEVNULL
            )
            total_bytes = int(hw_raw.decode("utf-8").strip())

            # 2. Virtual Memory Page Statistics
            vm_raw = subprocess.check_output(["vm_stat"], stderr=subprocess.DEVNULL).decode("utf-8")
            lines = vm_raw.splitlines()

            # Dynamic page size detection (Apple Silicon = 16384 bytes, Intel = 4096 bytes)
            page_size = MACOS_PAGE_SIZE_BYTES
            if lines and "page size of" in lines[0]:
                m = re.search(r"page size of (\d+) bytes", lines[0])
                if m:
                    page_size = int(m.group(1))

            stats: Dict[str, int] = {}
            for line in lines[1:]:
                if ":" in line:
                    key, val = line.split(":", 1)
                    stats[key.strip()] = int(val.strip().rstrip("."))

            anon = stats.get("Anonymous pages", 0)
            purgeable = stats.get("Pages purgeable", 0)
            wired = stats.get("Pages wired down", 0)
            compressed = stats.get("Pages occupied by compressor", 0)
            file_backed = stats.get("File-backed pages", 0)

            # macOS Activity Monitor standard calculation:
            # - App Memory: anonymous memory minus purgeable
            # - Wired Memory: pinned kernel/framework memory
            # - Compressed: pages occupied by the memory compressor
            # - Memory Used = App Memory + Wired Memory + Compressed Memory
            # (Note: Cached files = file_backed + purgeable pages, which is NOT counted as used memory)
            app_bytes = max(0, anon - purgeable) * page_size
            wired_bytes = wired * page_size
            compressed_bytes = compressed * page_size
            used_bytes = app_bytes + wired_bytes + compressed_bytes
            cached_bytes = (file_backed + purgeable) * page_size

            used_gb = used_bytes / BYTES_PER_GIBIBYTE
            total_gb = total_bytes / BYTES_PER_GIBIBYTE
            utilization_pct = (used_bytes / total_bytes) * PERCENT_MULTIPLIER

            return MemoryTelemetry(
                used_gb=used_gb,
                total_gb=total_gb,
                utilization_percent=utilization_pct,
                app_gb=app_bytes / BYTES_PER_GIBIBYTE,
                wired_gb=wired_bytes / BYTES_PER_GIBIBYTE,
                compressed_gb=compressed_bytes / BYTES_PER_GIBIBYTE,
                cached_gb=cached_bytes / BYTES_PER_GIBIBYTE,
            )

        except Exception:
            # Safe defensive fallback matching documented baseline
            return MemoryTelemetry(
                used_gb=float(FALLBACK_USED_GB),
                total_gb=float(FALLBACK_TOTAL_GB),
                utilization_percent=float(FALLBACK_PERCENT),
            )

