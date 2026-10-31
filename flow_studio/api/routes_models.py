"""Model Management & Hugging Face Hub Downloader Router.

Allows downloading models directly from Hugging Face into the local FLOW runtime,
scanning arbitrary directories for GGUF/FLOW/MLX models, querying local model availability,
and manually purging memory.
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

# Dynamic scanned directories list
CUSTOM_DIRS: List[Path] = [
    PROJECT_MODELS_DIR,
    MODELS_DIR,
    Path("/Volumes/NVMe2TB/AI-LLM/models"),
    Path("/Volumes/NVMe2TB/AI-LLM/LLMjp/Pyrite/gguf"),
    Path("/Volumes/NVMe2TB/AI-LLM/LLM/iOS-GenAI-Sampler-main 2"),
]


class DownloadRequest(BaseModel):
    repo_id: str = Field(..., description="Hugging Face repository ID (e.g. masahiroid/DeepSeek-Coder-V2-Lite-FLOW)")
    filename: Optional[str] = Field(None, description="Optional specific filename to download (e.g. *.gguf or *.flow)")


class ScanRequest(BaseModel):
    directory: str = Field(..., description="Absolute path of directory or file to scan")


class DownloadStatusResponse(BaseModel):
    status: str
    message: str
    local_path: Optional[str] = None


def _format_model_entry(p: Path, search_dir: Path) -> Dict[str, Any]:
    resolved = p.resolve()
    size_gb = round(resolved.stat().st_size / (1024**3), 2) if resolved.is_file() else 0.0
    name = p.name

    if ".flow" in name:
        label = f"[FLOW Streaming] {name} ({size_gb} GB)"
        category = "flow"
    elif name.endswith(".gguf"):
        label = f"[GGUF] {name} ({size_gb} GB)"
        category = "gguf"
    elif p.is_dir() and (p / "config.json").exists():
        label = f"[MLX / HF] {name}"
        category = "mlx"
    else:
        label = f"[Weight] {name} ({size_gb} GB)"
        category = "generic"

    return {
        "id": str(p),
        "name": label,
        "source": "local",
        "category": category,
        "resolved_path": str(resolved),
        "search_dir": str(search_dir),
        "is_symlink": p.is_symlink(),
        "size_gb": size_gb,
    }


@router.get("")
async def list_available_models():
    """List all models detected across standard and custom directories."""
    models = []
    seen = set()

    # 1. Scan registered directories
    for search_dir in CUSTOM_DIRS:
        if not search_dir.exists():
            continue
        try:
            # Check directory items
            for p in search_dir.iterdir():
                # Direct model files or symlinks
                if p.is_file() or p.is_symlink():
                    resolved = p.resolve()
                    if resolved.exists() and resolved not in seen:
                        if resolved.suffix in [".gguf", ".flow"] or ".gguf.flow" in resolved.name:
                            seen.add(resolved)
                            models.append(_format_model_entry(p, search_dir))
                # Subdirectories (e.g. MLX model directories or nested models)
                elif p.is_dir():
                    if (p / "config.json").exists() and p.resolve() not in seen:
                        seen.add(p.resolve())
                        models.append(_format_model_entry(p, search_dir))
                    else:
                        for sub_p in p.glob("*.gguf"):
                            if sub_p.resolve() not in seen:
                                seen.add(sub_p.resolve())
                                models.append(_format_model_entry(sub_p, search_dir))
        except Exception:
            continue

    # Sort: DeepSeek / Pyrite first, then other GGUF/FLOW, then MLX
    models.sort(key=lambda m: (
        0 if "deepseek" in m["id"].lower() and "gguf" in m["id"].lower()
        else 1 if "flow" in m["id"].lower()
        else 2 if "gguf" in m["id"].lower()
        else 3
    ))

    # Add Ollama models
    models.extend([
        {"id": "qwen3.5:9b-mlx", "name": "[Ollama] Qwen-3.5-9B (Fast Japanese)", "source": "ollama", "resolved_path": "Ollama Service: qwen3.5:9b-mlx", "category": "ollama"},
        {"id": "ornith-1.5:9b", "name": "[Ollama] Ornith-1.5-9B (Qwen Reasoning)", "source": "ollama", "resolved_path": "Ollama Service: ornith-1.5:9b", "category": "ollama"},
    ])

    return {
        "models": models,
        "search_paths": [{"path": str(d), "type": "Scanned Directory"} for d in CUSTOM_DIRS if d.exists()]
    }


@router.post("/scan")
async def scan_custom_directory(req: ScanRequest):
    """Scan and add any arbitrary user-specified directory or file."""
    path_str = req.directory.strip()
    if not path_str:
        raise HTTPException(status_code=400, detail="Path is required.")

    target = Path(path_str).expanduser().resolve()
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Path does not exist: {path_str}")

    if target.is_dir():
        if target not in CUSTOM_DIRS:
            CUSTOM_DIRS.insert(0, target)
    elif target.is_file():
        parent_dir = target.parent
        if parent_dir not in CUSTOM_DIRS:
            CUSTOM_DIRS.insert(0, parent_dir)

    return await list_available_models()


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
