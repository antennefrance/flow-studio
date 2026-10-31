"""Direct Chat & Prompt Generation Router.

Handles streaming token delivery directly to the FLOW Studio web interface.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from flow_studio.config import settings
from flow_studio.constants import MIME_TEXT_PLAIN
from flow_studio.domain.models import GenerationRequestDTO
from flow_studio.infrastructure.flow_engine import FlowStreamingEngine
from flow_studio.services.inference_service import InferenceService

router = APIRouter(prefix="/api", tags=["Chat"])


class GenerateRequestBody(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: str = Field(default="deepseek")
    max_tokens: int = Field(
        default=settings.default_max_tokens,
        ge=settings.min_token_limit,
        le=settings.max_token_limit,
    )


def get_inference_service() -> InferenceService:
    engine = FlowStreamingEngine()
    return InferenceService(engine)


@router.post("/generate")
async def generate_stream(
    req: GenerateRequestBody,
    service: InferenceService = Depends(get_inference_service),
):
    dto = GenerationRequestDTO(
        prompt=req.prompt,
        model_id=req.model,
        max_tokens=req.max_tokens,
        temperature=settings.default_temperature,
    )

    async def token_stream():
        async for token in service.execute_stream(dto):
            yield token

    return StreamingResponse(token_stream(), media_type=MIME_TEXT_PLAIN)

