"""FLOW Studio Inference Application Service.

Encapsulates prompt execution, model registry lookups, and token streaming workflows.
"""

from typing import AsyncGenerator, List, Optional
from flow_studio.domain.interfaces import InferenceEngineProtocol
from flow_studio.domain.models import CATALOG_MODELS, GenerationRequestDTO, ModelMetadata


class InferenceService:
    """Application service for language model inference."""

    def __init__(self, engine: InferenceEngineProtocol) -> None:
        self._engine = engine

    def get_available_models(self) -> List[ModelMetadata]:
        return list(CATALOG_MODELS)

    def find_model(self, model_id: str) -> Optional[ModelMetadata]:
        for m in CATALOG_MODELS:
            if m.id == model_id or m.name.lower() == model_id.lower():
                return m
        return None

    async def execute_stream(
        self, request: GenerationRequestDTO
    ) -> AsyncGenerator[str, None]:
        async for token in self._engine.stream_tokens(request):
            yield token

