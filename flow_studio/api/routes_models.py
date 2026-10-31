"""Model Management & Hugging Face Hub Downloader Router.

Allows downloading models directly from Hugging Face into the local FLOW runtime,
querying local model availability and paths, and manually purging memory.
"""

import asyncio
import gc
import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from huggingface_hub import HfApi, hf_hub_download, snapshot_download

router = APIRouter(prefix="/api/models", tags=["Models"])

MODELS_DIR = Path.home() / ".cache" / "flow_models"
PROJECT_MODELS_DIR = Path(__file__).resolve().parents[2] / "models"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
PROJECT_MODELS_DIR.mkdir(parents=True, exist_ok=True)


class DownloadRequest(BaseModel):
    repo_id: str = Field(..., description="Hugging Face repository ID (e.g. masahiroid/DeepSeek-Coder-V2-Lite-FLOW)")
    filename: Optional[str] = Field(None, description="Optional specific filename to download (e.g. *.gguf or *.flow)")


class DownloadStatusResponse(BaseModel):
    status: str
    message: str
    local_path: Optional[str] = None


@router.get("")
async def list_available_models():
    """List all models detected locally and presets with search path details."""
    models = [
        {"id": "auto", "name": "Auto Detect (Local FLOW / GGUF)", "source": "system", "resolved_path": "Auto-selected"},
    ]

    seen = set()

    for search_dir in [PROJECT_MODELS_DIR, MODELS_DIR]:
        if not search_dir.exists():
            continue
        for p in search_dir.iterdir():
            if p.is_file() or p.is_symlink():
                resolved = p.resolve()
                if resolved.exists() and resolved not in seen:
                    seen.add(resolved)
                    size_gb = round(resolved.stat().st_size / (1024**3), 2)
                    name = p.name
                    if ".flow" in name:
                        label = f"[FLOW Streaming] {name} ({size_gb} GB)"
                    else:
                        label = f"[Pyrite 2-bit GGUF] {name} ({size_gb} GB)"
                    models.append({
                        "id": str(p),
                        "name": label,
                        "source": "local",
                        "resolved_path": str(resolved),
                        "search_dir": str(search_dir),
                        "is_symlink": p.is_symlink(),
                    })

    # Sort so runnable GGUF is at the top of local models
    models.sort(key=lambda m: (0 if "gguf" in m["id"] else 1 if "flow" in m["id"] else 2))

    # Ollama options
    models.extend([
        {"id": "qwen3.5:9b-mlx", "name": "[Ollama] Qwen-3.5-9B", "source": "ollama", "resolved_path": "Ollama Service"},
        {"id": "ornith-1.5:9b", "name": "[Ollama] Ornith-1.5-9B", "source": "ollama", "resolved_path": "Ollama Service"},
    ])

    return {
        "models": models,
        "search_paths": [
            {"path": str(PROJECT_MODELS_DIR), "type": "Project Models Directory"},
            {"path": str(MODELS_DIR), "type": "Global Cache Directory"},
            {"path": "http://127.0.0.1:11434", "type": "Local Ollama Endpoint"},
        ]
    }


@router.post("/unload")
async def unload_models():
    """Manually unload all active models and free GPU/Unified Memory."""
    freed_actions = []

    # 1. Stop Ollama running models if Ollama is present
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/ps", headers={"User-Agent": "FLOW-Studio"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            data = json.loads(resp.read().decode())
            for m in data.get("models", []):
                mname = m.get("name")
                if mname:
                    subprocess.run(["ollama", "stop", mname], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    freed_actions.append(f"Stopped Ollama model: {mname}")
    except Exception:
        pass

    # 2. Terminate any orphan llama-cli / llama-server processes
    try:
        subprocess.run(["pkill", "-f", "llama-cli"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        freed_actions.append("Terminated active llama-cli instances")
    except Exception:
        pass

    # 3. Force garbage collection
    gc.collect()

    return {
        "status": "success",
        "message": "Memory successfully released and all models unloaded.",
        "actions": freed_actions,
    }


@router.post("/download", response_model=DownloadStatusResponse)
async def download_hf_model(req: DownloadRequest):
    """Download a model or specific weight file from Hugging Face Hub."""
    repo = req.repo_id.strip()
    if not repo:
        raise HTTPException(status_code=400, detail="Repository ID is required.")

    try:
        loop = asyncio.get_event_loop()
        target_dir = PROJECT_MODELS_DIR / repo.replace("/", "_")
        target_dir.mkdir(parents=True, exist_ok=True)

        if req.filename:
            local_file = await loop.run_in_executor(
                None,
                lambda: hf_hub_download(
                    repo_id=repo,
                    filename=req.filename,
                    local_dir=str(target_dir),
                )
            )
            return DownloadStatusResponse(
                status="success",
                message=f"Successfully downloaded {req.filename}",
                local_path=local_file
            )
        else:
            local_dir = await loop.run_in_executor(
                None,
                lambda: snapshot_download(
                    repo_id=repo,
                    local_dir=str(target_dir),
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
