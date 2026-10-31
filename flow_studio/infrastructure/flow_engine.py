"""FLOW Inference Engine Adapter (Infrastructure Layer).

Implements InferenceEngineProtocol, managing real-time on-demand token generation
and streaming responses for local FLOW, GGUF, MLX, and Ollama runtimes.
"""

import asyncio
import json
import os
import shutil
import sys
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
        self.project_root = Path(__file__).resolve().parents[2]
        self.models_dir = self.project_root / "models"
        self.cache_dir = Path.home() / ".cache" / "flow_models"

    def _find_model_path(self, model_id: str) -> str | None:
        """Locate runnable model path, resolving .flow containers to their GGUF counterparts."""
        if not model_id:
            model_id = "auto"

        # 1. If exact path exists
        if os.path.exists(model_id):
            p = Path(model_id).resolve()
            # If it's a directory with config.json (MLX model)
            if p.is_dir() and (p / "config.json").exists():
                return str(p)
            # If it's a .gguf
            if p.suffix == ".gguf":
                return str(p)
            # If it's a .flow, check for counterpart .gguf
            if str(p).endswith(".flow"):
                candidate_names = [
                    str(p).replace(".gguf.flow", ".gguf"),
                    str(p).replace(".flow", ""),
                    Path(p.name).stem,
                ]
                if "deepseek" in p.name.lower():
                    candidate_names.append("DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit.gguf")

                for search_dir in [self.models_dir, self.cache_dir, Path("/Volumes/NVMe2TB/AI-LLM/LLMjp/Pyrite/gguf"), Path("/Volumes/NVMe2TB/AI-LLM/models")]:
                    for cname in candidate_names:
                        cand = (search_dir / Path(cname).name).resolve()
                        if cand.exists() and cand.suffix == ".gguf":
                            return str(cand)

        # 2. If model_id points to a .flow file
        if str(model_id).endswith(".flow"):
            candidate_names = [
                str(model_id).replace(".gguf.flow", ".gguf"),
                str(model_id).replace(".flow", ""),
                Path(model_id).name.replace(".flow", ""),
            ]
            if "deepseek" in model_id.lower():
                candidate_names.append("DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit.gguf")

            for search_dir in [self.models_dir, self.cache_dir, Path("/Volumes/NVMe2TB/AI-LLM/LLMjp/Pyrite/gguf"), Path("/Volumes/NVMe2TB/AI-LLM/models")]:
                for cname in candidate_names:
                    cand = (search_dir / Path(cname).name).resolve()
                    if cand.exists() and cand.suffix == ".gguf":
                        return str(cand)

        # 3. Search directories for any valid GGUF or MLX
        search_dirs = [self.models_dir, self.cache_dir, Path("/Volumes/NVMe2TB/AI-LLM/LLMjp/Pyrite/gguf"), Path("/Volumes/NVMe2TB/AI-LLM/models")]
        for candidate_dir in search_dirs:
            if not candidate_dir.exists():
                continue
            for cand in candidate_dir.glob("*.gguf"):
                resolved = cand.resolve()
                if resolved.exists():
                    return str(resolved)
            for cand in candidate_dir.iterdir():
                if cand.is_dir() and (cand / "config.json").exists():
                    return str(cand.resolve())

        return None

    async def stream_tokens(
        self, request: GenerationRequestDTO
    ) -> AsyncGenerator[str, None]:
        """Stream real inference tokens from local LLM backends."""
        prompt = request.prompt.strip()
        model_id = (request.model_id or "auto").lower()
        max_tokens = request.max_tokens or 256

        # 1. If explicit Ollama model selected
        if "qwen" in model_id or "ornith" in model_id:
            selected_ollama = "qwen3.5:9b-mlx" if "qwen" in model_id else "ornith-1.5:9b"
            async for token in self._stream_ollama(prompt, selected_ollama, max_tokens, request.temperature):
                yield token
            return

        # 2. Local Model (GGUF, FLOW, or MLX)
        target_model = self._find_model_path(request.model_id)

        # Check if MLX Directory
        if target_model and os.path.isdir(target_model) and (Path(target_model) / "config.json").exists():
            async for token in self._stream_mlx(prompt, target_model, max_tokens, request.temperature):
                yield token
            return

        # Check if GGUF / FLOW file
        if target_model and os.path.exists(self.llama_cli_path):
            if "deepseek" in target_model.lower():
                formatted_prompt = f"<｜User｜>{prompt}\n\n（日本語で分かりやすく簡潔に回答してください）<｜Assistant｜>"
            else:
                formatted_prompt = f"User: {prompt}\n\nAssistant: "

            try:
                cmd = [
                    self.llama_cli_path,
                    "-m", target_model,
                    "-p", formatted_prompt,
                    "-n", str(max_tokens),
                    "-c", "512",
                    "--simple-io",
                    "--single-turn",
                    "-ngl", "0",  # Safe mode on 16GB Macs under high memory pressure
                    "--repeat-penalty", "1.18",
                    "--repeat-last-n", "64",
                    "--temp", str(request.temperature or 0.6),
                ]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                started = False
                tokens_emitted = 0

                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    text = line.decode("utf-8", errors="replace")

                    if not started:
                        if "<｜Assistant｜>" in text:
                            started = True
                            after_token = text.split("<｜Assistant｜>")[-1]
                            if after_token.strip():
                                tokens_emitted += 1
                                yield after_token
                            continue
                        elif "Assistant:" in text:
                            started = True
                            after_token = text.split("Assistant:")[-1]
                            if after_token.strip():
                                tokens_emitted += 1
                                yield after_token
                            continue
                        elif text.startswith(">"):
                            started = True
                            continue
                        continue

                    if text.startswith("[ Prompt:"):
                        break

                    # Guard against repeating prompt leaks
                    if "（日本語で分かりやすく簡潔に回答してください）" in text or "<｜Assistant｜>" in text or "Assistant:" in text:
                        continue

                    tokens_emitted += 1
                    yield text

                await proc.wait()
                if tokens_emitted == 0 and proc.returncode != 0:
                    err_bytes = await proc.stderr.read()
                    err_msg = err_bytes.decode("utf-8", errors="replace")
                    yield f"【推論エラー】モデル実行に失敗しました (exit code {proc.returncode}):\n{err_msg[-300:]}"
                return
            except Exception as e:
                yield f"\n[FLOW LLaMA Error: {e}]\n"

        # 3. Fallback to Ollama if running
        ollama_available = await self._check_ollama()
        if ollama_available:
            async for token in self._stream_ollama(prompt, "ornith-1.5:9b", max_tokens, request.temperature):
                yield token
            return

        # 4. Inform user
        yield (
            "【FLOW Engine】利用可能なモデルファイルが検出されませんでした。\n"
            f"models/ ディレクトリ ({self.models_dir}) またはサイドバーの「任意のパスから追加」でモデルを指定してください。"
        )

    async def _stream_mlx(
        self, prompt: str, model_path: str, max_tokens: int, temperature: float | None
    ) -> AsyncGenerator[str, None]:
        """Stream inference from MLX model directory (e.g. Mixtral, Qwen MLX)."""
        cmd = [
            sys.executable,
            "-m", "mlx_lm.generate",
            "--model", model_path,
            "--prompt", prompt,
            "--max-tokens", str(max_tokens),
            "--temp", str(temperature or 0.6),
            "--verbose", "False"
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace")
                if "Prompt:" in text or "Generation:" in text or "Peak memory:" in text:
                    continue
                yield text
            await proc.wait()
        except Exception as e:
            yield f"\n[MLX Inference Error: {e}]\n"

    async def _check_ollama(self) -> bool:
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

    async def _stream_ollama(
        self, prompt: str, model_name: str, max_tokens: int, temperature: float | None
    ) -> AsyncGenerator[str, None]:
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def _worker():
            try:
                req_data = json.dumps({
                    "model": model_name,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature or 0.7,
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

        loop.run_in_executor(None, _worker)
        while True:
            token = await queue.get()
            if token is None:
                break
            yield token
