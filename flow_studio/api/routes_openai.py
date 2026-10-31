"""OpenAI & Ollama Compatible Protocol Router (/v1).

Exposes standard /v1/models and /v1/chat/completions endpoints,
allowing external tools (Cursor, VSCode Continue, Obsidian, OpenWebUI)
to utilize FLOW as a drop-in local inference backend.
"""

import json
import time
from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from flow_studio.config import settings
from flow_studio.constants import (
    MIME_APPLICATION_JSON,
    MIME_TEXT_EVENT_STREAM,
    SSE_DATA_PREFIX,
    SSE_DONE_MESSAGE,
)
from flow_studio.domain.models import GenerationRequestDTO
from flow_studio.infrastructure.flow_engine import FlowStreamingEngine
from flow_studio.services.inference_service import InferenceService

router = APIRouter(prefix="/v1", tags=["OpenAI Compatibility"])


class OpenAIChatMessage(BaseModel):
    role: str
    content: str


class OpenAIChatCompletionRequest(BaseModel):
    model: str = Field(default="deepseek")
    messages: List[OpenAIChatMessage]
    max_tokens: Optional[int] = Field(default=settings.default_max_tokens)
    temperature: Optional[float] = Field(default=settings.default_temperature)
    stream: Optional[bool] = Field(default=False)


def get_inference_service() -> InferenceService:
    engine = FlowStreamingEngine()
    return InferenceService(engine)


@router.get("/models")
async def list_models(service: InferenceService = Depends(get_inference_service)):
    models = service.get_available_models()
    return {
        "object": "list",
        "data": [
            {
                "id": m.name,
                "object": "model",
                "owned_by": m.owned_by,
                "metadata": {
                    "architecture": m.architecture.value,
                    "streaming_mode": m.streaming_mode.value,
                    "format": m.primary_format.value,
                    "active_ram_gb": m.active_ram_gb,
                },
            }
            for m in models
        ],
    }


@router.post("/chat/completions")
async def chat_completions(
    req: OpenAIChatCompletionRequest,
    service: InferenceService = Depends(get_inference_service),
):
    user_prompt = ""
    for msg in req.messages:
        if msg.role == "user":
            user_prompt = msg.content

    dto = GenerationRequestDTO(
        prompt=user_prompt,
        model_id=req.model,
        max_tokens=req.max_tokens or settings.default_max_tokens,
        temperature=req.temperature or settings.default_temperature,
    )
    created_timestamp = int(time.time())

    if req.stream:
        async def stream_event_source():
            chunk_index = 0
            async for token in service.execute_stream(dto):
                payload = {
                    "id": f"chatcmpl-{created_timestamp}",
                    "object": "chat.completion.chunk",
                    "created": created_timestamp,
                    "model": req.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": token},
                            "finish_reason": None,
                        }
                    ],
                }
                yield f"{SSE_DATA_PREFIX}{json.dumps(payload)}\n\n"
                chunk_index += 1

            # Final stop chunk
            stop_payload = {
                "id": f"chatcmpl-{created_timestamp}",
                "object": "chat.completion.chunk",
                "created": created_timestamp,
                "model": req.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }
                ],
            }
            yield f"{SSE_DATA_PREFIX}{json.dumps(stop_payload)}\n\n"
            yield SSE_DONE_MESSAGE

        return StreamingResponse(stream_event_source(), media_type=MIME_TEXT_EVENT_STREAM)

    else:
        full_tokens: List[str] = []
        async for token in service.execute_stream(dto):
            full_tokens.append(token)
        response_text = "".join(full_tokens)

        return JSONResponse(
            status_code=200,
            content={
                "id": f"chatcmpl-{created_timestamp}",
                "object": "chat.completion",
                "created": created_timestamp,
                "model": req.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": response_text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": len(user_prompt.split()),
                    "completion_tokens": len(response_text.split()),
                    "total_tokens": len(user_prompt.split()) + len(response_text.split()),
                },
            },
        )

