"""FLOW Studio Telemetry Application Service.

Encapsulates memory telemetry business logic and DTO conversions.
"""

from typing import Dict
from flow_studio.domain.interfaces import TelemetryProviderProtocol
from flow_studio.domain.models import MemoryTelemetry


class TelemetryService:
    """Coordinates telemetry sampling and client formatting."""

    def __init__(self, provider: TelemetryProviderProtocol) -> None:
        self._provider = provider

    def get_current_metrics(self) -> MemoryTelemetry:
        return self._provider.get_memory_telemetry()

    def get_metrics_dict(self) -> Dict[str, str]:
        return self.get_current_metrics().to_dict()

