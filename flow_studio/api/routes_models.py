"""Model Management & Hugging Face Hub Downloader Router.

Allows downloading models directly from Hugging Face into the local FLOW runtime,
and querying local model availability.
"""

import asyncio
import os
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from huggingface_hub import HfApi, hf_hub_download, snapshot_download

router = APIRouter(prefix="/api/models", tags=["Models"])

MODELS_DIR = Path.home() / ".cache" / "flow_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


class DownloadRequest(BaseModel):
    repo_id: str = Field(..., description="Hugging Face repository ID (e.g. masahiroid/DeepSeek-Coder-V2-Lite-FLOW)")
    filename: Optional[str] = Field(None, description="Optional specific filename to download (e.g. *.gguf or *.flow)")


class DownloadStatusResponse(BaseModel):
    status: str
    message: str
    local_path: Optional[str] = None


@router.get("")
async def list_available_models():
    """List all models detected locally and presets."""
    models = [
        {"id": "auto", "name": "Auto Detect (Local Ollama / LLaMA / MLX)", "source": "system"},
        {"id": "deepseek-flow", "name": "DeepSeek-Coder-V2-Lite-FLOW (15.7B Streaming)", "source": "flow"},
        {"id": "llama-3.2-3b", "name": "Llama-3.2-3B-Instruct (GGUF)", "source": "local"},
        {"id": "qwen3.5:9b-mlx", "name": "Qwen-3.5-9B (Ollama)", "source": "ollama"},
        {"id": "ornith-1.5:9b", "name": "Ornith-1.5-9B (Ollama)", "source": "ollama"},
    ]

    # Scan ~/.cache/flow_models
    for p in MODELS_DIR.glob("**/*"):
        if p.is_file() and (p.suffix in [".flow", ".gguf", ".safetensors"] or p.name.endswith(".gguf.flow")):
            models.append({
                "id": str(p),
                "name": f"{p.name} ({round(p.stat().st_size / (1024**3), 2)} GB)",
                "source": "downloaded"
            })

    return {"models": models}


@router.post("/download", response_model=DownloadStatusResponse)
async def download_hf_model(req: DownloadRequest):
    """Download a model or specific weight file from Hugging Face Hub."""
    repo = req.repo_id.strip()
    if not repo:
        raise HTTPException(status_code=400, detail="Repository ID is required.")

    try:
        loop = asyncio.get_event_loop()
        if req.filename:
            # Download specific file
            local_file = await loop.run_in_executor(
                None,
                lambda: hf_hub_download(
                    repo_id=repo,
                    filename=req.filename,
                    local_dir=str(MODELS_DIR / repo.replace("/", "_")),
                )
            )
            return DownloadStatusResponse(
                status="success",
                message=f"Successfully downloaded {req.filename}",
                local_path=local_file
            )
        else:
            # Snapshot download of model repository
            local_dir = await loop.run_in_executor(
                None,
                lambda: snapshot_download(
                    repo_id=repo,
                    local_dir=str(MODELS_DIR / repo.replace("/", "_")),
                    max_workers=4,
                )
            )
            return DownloadStatusResponse(
                status="success",
                message=f"Successfully downloaded repository {repo}",
                local_path=local_dir
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download model from Hugging Face: {str(e)}")
