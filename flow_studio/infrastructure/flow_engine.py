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
        if model_id.startswith("ollama:") or (":" in model_id and "/" not in model_id):
            selected_ollama = model_id.replace("ollama:", "")
            async for token in self._stream_ollama(prompt, selected_ollama, max_tokens, request.temperature):
                yield token
            return

        # 2. Local Model (GGUF, FLOW, or MLX)
        target_model = self._find_model_path(request.model_id)

        # Check if MLX Directory or Mixtral Model (Direct or FLOW container)
        if target_model and (
            (os.path.isdir(target_model) and (Path(target_model) / "config.json").exists())
            or "mixtral" in target_model.lower()
        ):
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

                    if "unknown model architecture" in err_msg:
                        import re
                        m = re.search(r"unknown model architecture: '([^']+)'", err_msg)
                        arch_name = m.group(1) if m else "未対応"
                        yield (
                            f"【非対応アーキテクチャ: '{arch_name}'】\n"
                            f"このモデルファイルはアーキテクチャ '{arch_name}' を使用しているため、llama.cpp 実行エンジンでは読み込めません。\n\n"
                            "💡 解決策:\n"
                            "左側のセレクターから、動作確認済みの対応モデル（[FLOW] DeepSeek-Coder-V2, [FLOW] Llama-3.2, [FLOW] Phi-3 など）を選択して実行してください。"
                        )
                    elif "out of memory" in err_msg.lower() or "metal" in err_msg.lower():
                        yield (
                            "【メモリ不足エラー】Unified Memory の割り当てに失敗しました。\n"
                            "左側の「⚡ Release RAM / メモリ完全開放」ボタンを押して不要なキャッシュを開放してから再度実行してください。"
                        )
                    else:
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
        """Stream inference from MLX model directory (e.g. Mixtral Streaming Engine, Qwen MLX)."""
        is_mixtral = "mixtral" in model_path.lower()
        is_qwen = "qwen" in model_path.lower()

        # Format prompt with conversational chat template if applicable
        if is_qwen:
            formatted_prompt = (
                f"<|im_start|>system\n"
                f"あなたは親切で有能なAIアシスタントです。日本語で直接、簡潔かつ丁寧に回答してください。<|im_end|>\n"
                f"<|im_start|>user\n{prompt}<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )
        elif is_mixtral:
            formatted_prompt = f"[INST] {prompt} [/INST]"
        else:
            formatted_prompt = prompt

        if is_mixtral:
            runner_script = Path("/Volumes/NVMe2TB/AI-LLM/LLMjp/Pyrite/moe_stream/mixtral_runner.py")
            if runner_script.exists():
                cmd = [
                    sys.executable,
                    str(runner_script),
                    model_path,
                    formatted_prompt,
                    str(max_tokens),
                ]
            else:
                cmd = [
                    sys.executable,
                    "-m", "mlx_lm", "generate",
                    "--model", model_path,
                    "--prompt", formatted_prompt,
                    "--max-tokens", str(max_tokens),
                    "--temp", str(temperature or 0.6),
                ]
        else:
            cmd = [
                sys.executable,
                "-m", "mlx_lm", "generate",
                "--model", model_path,
                "--prompt", formatted_prompt,
                "--max-tokens", str(max_tokens),
                "--temp", str(temperature or 0.6),
            ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )
            started = False
            delimiter_count = 0

            while True:
                if started and is_mixtral:
                    chunk = await proc.stdout.read(128)
                    if not chunk:
                        break
                    text = chunk.decode("utf-8", errors="replace")
                    if "Prompt TPS:" in text or "Generation TPS:" in text:
                        break
                    yield text
                    continue

                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace")

                # Mixtral streaming runner specific markers
                if "Streaming generation started:" in text:
                    started = True
                    continue
                if is_mixtral and not started:
                    if "Resident tensors:" in text:
                        yield "【FLOW Engine】常駐テンソルをRAMへ配置完了（~2.3GB / NVMeオフロード 76.7GB）\n"
                    continue

                # Standard mlx_lm delimiters
                if text.strip() == "==========":
                    delimiter_count += 1
                    if delimiter_count == 1:
                        started = True
                        continue
                    elif delimiter_count >= 2:
                        break  # Finished generation text block

                if not started and not is_mixtral:
                    continue

                # Filter internal warnings and MLX profiling logs
                if any(ignored in text for ignored in [
                    "Prompt:", "Generation:", "Peak memory:", "[transformers]",
                    "Calling `python", "The tokenizer you are loading", "This will lead to",
                    "Initializing AntenneFrance", "Architecture:", "Building zero-copy",
                    "Loading resident", "Instantiating base", "Quantizing resident",
                    "Injecting Streaming", "successfully mounted"
                ]):
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
