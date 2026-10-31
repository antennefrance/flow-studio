"""FLOW Studio Domain Interfaces.

Defines abstract contracts for telemetry providers and inference engines.
Ensures loose coupling and clean unit-testability.
"""

from typing import AsyncGenerator, Protocol
from flow_studio.domain.models import GenerationRequestDTO, MemoryTelemetry


class TelemetryProviderProtocol(Protocol):
    """Abstract contract for hardware memory telemetry."""

    def get_memory_telemetry(self) -> MemoryTelemetry:
        """Query and calculate current physical Unified Memory utilization."""
        ...


class InferenceEngineProtocol(Protocol):
    """Abstract contract for token stream generation."""

    async def stream_tokens(
        self, request: GenerationRequestDTO
    ) -> AsyncGenerator[str, None]:
        """Asynchronously yield generated tokens for a prompt."""
        ...

