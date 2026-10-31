"""Hardware Telemetry Router.

Exposes REST endpoints for querying physical Apple Silicon memory statistics.
"""

import platform
from fastapi import APIRouter, Depends
from flow_studio.infrastructure.macos_telemetry import NativeMacOSTelemetryProvider
from flow_studio.infrastructure.windows_telemetry import WindowsTelemetryProvider
from flow_studio.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/api", tags=["Telemetry"])


def get_telemetry_service() -> TelemetryService:
    """Auto-detects host operating system and injects the proper telemetry provider."""
    current_os = platform.system().lower()
    if current_os == "windows":
        provider = WindowsTelemetryProvider()
    else:
        # macOS / Darwin (and Linux fallback)
        provider = NativeMacOSTelemetryProvider()

    return TelemetryService(provider)


@router.get("/telemetry")
async def read_telemetry(service: TelemetryService = Depends(get_telemetry_service)):
    return service.get_metrics_dict()

