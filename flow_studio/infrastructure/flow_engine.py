"""FLOW Inference Engine Adapter (Infrastructure Layer).

Implements InferenceEngineProtocol, managing real-time on-demand token generation
and streaming responses for local GGUF, MLX, and Ollama runtimes.
"""

import asyncio
import json
import os
import shutil
import urllib.request
from pathlib import Path
from typing import AsyncGenerator

from flow_studio.domain.interfaces import InferenceEngineProtocol
from flow_studio.domain.models import GenerationRequestDTO


class FlowStreamingEngine(InferenceEngineProtocol):
    """Executes genuine on-demand streaming inference via local engines."""

    def __init__(self):
        self.ollama_url = "http://127.0.0.1:11434"
        self.llama_cli_path = shutil.which("llama-cli") or "/opt/homebrew/bin/llama-cli"

    async def _check_ollama(self) -> bool:
        """Check if local Ollama runtime is available."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_ping_ollama)
        except Exception:
            return False

    def _sync_ping_ollama(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", headers={"User-Agent": "FLOW-Studio"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def stream_tokens(
        self, request: GenerationRequestDTO
    ) -> AsyncGenerator[str, None]:
        """Stream real inference tokens from local LLM backends."""
        prompt = request.prompt.strip()
        model_id = request.model_id or "auto"
        max_tokens = request.max_tokens or 256

        # 1. Check if Ollama is running and has models
        ollama_available = await self._check_ollama()
        if ollama_available:
            # Map or select Ollama model
            selected_ollama_model = "ornith-1.5:9b"
            if "qwen" in model_id.lower():
                selected_ollama_model = "qwen3.5:9b-mlx"
            elif "ornith" in model_id.lower():
                selected_ollama_model = "ornith-1.5:9b"

            try:
                loop = asyncio.get_event_loop()
                queue: asyncio.Queue[str | None] = asyncio.Queue()

                def _run_ollama_stream():
                    try:
                        req_data = json.dumps({
                            "model": selected_ollama_model,
                            "prompt": prompt,
                            "stream": True,
                            "options": {
                                "num_predict": max_tokens,
                                "temperature": request.temperature or 0.7,
                            }
                        }).encode("utf-8")
                        req = urllib.request.Request(
                            f"{self.ollama_url}/api/generate",
                            data=req_data,
                            headers={"Content-Type": "application/json"}
                        )
                        with urllib.request.urlopen(req, timeout=60) as resp:
                            for line in resp:
                                if line:
                                    chunk = json.loads(line.decode("utf-8"))
                                    token = chunk.get("response", "")
                                    loop.call_soon_threadsafe(queue.put_nowait, token)
                                    if chunk.get("done", False):
                                        break
                    except Exception as err:
                        loop.call_soon_threadsafe(queue.put_nowait, f"\n[Ollama Error: {str(err)}]")
                    finally:
                        loop.call_soon_threadsafe(queue.put_nowait, None)

                loop.run_in_executor(None, _run_ollama_stream)

                while True:
                    token = await queue.get()
                    if token is None:
                        break
                    yield token
                return
            except Exception as e:
                yield f"\n[Ollama streaming fallback: {e}]\n"

        # 2. Check local GGUF with llama-cli
        known_ggufs = [
            "/Volumes/NVMe2TB/AI-LLM/LLMjp/Pyrite/gguf/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit.gguf",
            "/Volumes/NVMe2TB/AI-LLM/LLM/iOS-GenAI-Sampler-main 2/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        ]
        chosen_gguf = None
        for g in known_ggufs:
            if os.path.exists(g):
                chosen_gguf = g
                break

        if os.path.exists(self.llama_cli_path) and chosen_gguf:
            try:
                cmd = [
                    self.llama_cli_path,
                    "-m", chosen_gguf,
                    "-p", prompt,
                    "-n", str(max_tokens),
                    "--single-turn",
                    "--no-display-prompt",
                    "--temp", str(request.temperature or 0.3),
                ]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )

                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    text = line.decode("utf-8", errors="replace")
                    # filter out ascii banner/stats if any
                    if text.startswith("[ Prompt:") or "available commands:" in text or "build      :" in text:
                        continue
                    yield text

                await proc.wait()
                return
            except Exception as e:
                yield f"\n[LLaMA CLI Error: {e}]\n"

        # 3. Inform user cleanly if no local weights or backend found
        yield (
            "【FLOW Engine 警告】利用可能なローカル推論バックエンド（Ollama / llama-cli / モデル重み）が検出されませんでした。\n"
            "サイドバーの「Hugging Face Model Download」からモデルをダウンロードするか、Ollama を起動してください。"
        )
