#!/usr/bin/env python3
"""Official llm-jp-eval prompts and metrics with a checkpointed local inference adapter.

Run main in the llm-jp-eval environment. --inference-python runs MLX in its own
compatible environment. No scores or gold answers are passed to the MLX worker.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_MODEL = "masahiroid/llm-jp-4.1-8b-thinking-4bit-mlx"
TASKS = ("marc_ja", "jsts", "jnli", "jsquad", "mgsm")


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
    tmp.replace(path)


def final_answer(text, require_final=False):
    markers = list(re.finditer(r"<\|channel\|>\s*final\s*<\|message\|>", text))
    if markers:
        return re.split(r"<\|(?:return|end|call)\|>", text[markers[-1].end():], maxsplit=1)[0].strip()
    if "</think>" in text:
        return text.rsplit("</think>", 1)[-1].strip()
    if require_final or "<think>" in text or re.search(r"<\|channel\|>\s*analysis", text):
        return ""
    return text.strip()


def worker(a):
    items = [json.loads(x) for x in a.worker_input.read_text().splitlines() if x.strip()]
    # Resume only when the full provenance matches; never reuse outputs from another run.
    done = {}
    if a.worker_output.exists():
        for line in a.worker_output.read_text().splitlines():
            record = json.loads(line)
            if record.get("run_fingerprint") != a.fingerprint:
                raise RuntimeError("Checkpoint belongs to a different model/settings run")
            done[record["prompt_sha256"]] = record
    if a.backend == "mlx":
        import mlx.core as mx
        from mlx_lm import load, stream_generate
        from mlx_lm.sample_utils import make_sampler
        mx.set_cache_limit(a.cache_mb * 1024 * 1024)
        mx.random.seed(a.seed)
        model, tokenizer = load(a.model_path, tokenizer_config={"trust_remote_code": False})
        sampler = make_sampler(temp=0.0)
    with a.worker_output.open("a") as out:
        for i, item in enumerate(items):
            key = hashlib.sha256(item["prompt"].encode()).hexdigest()
            if key in done:
                continue
            started = time.monotonic()
            finish = None
            if a.backend == "mlx":
                prompt = item["prompt"]
                if a.chat_template:
                    prompt = tokenizer.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False,
                                                          add_generation_prompt=True, reasoning_effort=a.reasoning_effort)
                if len(tokenizer.encode(prompt)) > a.max_input_tokens:
                    raise RuntimeError("Input exceeds --max-input-tokens; no silent truncation")
                pieces = []
                count = 0
                for result in stream_generate(model, tokenizer, prompt=prompt, max_tokens=a.max_tokens, sampler=sampler):
                    pieces.append(result.text)
                    count += 1
                    finish = getattr(result, "finish_reason", None)
                raw = "".join(pieces)
                truncated = finish == "length" or count >= a.max_tokens
            else:
                import requests
                endpoint = a.base_url.rstrip("/") + ("/chat/completions" if a.chat_template else "/completions")
                body = {"model": a.model, "temperature": 0, "max_tokens": a.max_tokens, "seed": a.seed}
                body.update({"messages": [{"role": "user", "content": item["prompt"]}]} if a.chat_template else {"prompt": item["prompt"]})
                response = requests.post(endpoint, json=body, timeout=a.timeout)
                response.raise_for_status()
                choice = response.json()["choices"][0]
                raw = choice.get("message", {}).get("content") if a.chat_template else choice.get("text")
                raw = raw or ""
                finish = choice.get("finish_reason")
                count = response.json().get("usage", {}).get("completion_tokens")
                truncated = finish == "length"
            answer = final_answer(raw, require_final=a.require_final)
            record = {"prompt_sha256": key, "run_fingerprint": a.fingerprint, "raw": raw, "answer": answer,
                      "completion_tokens": count, "truncated": truncated, "empty_answer": not bool(answer),
                      "seconds": time.monotonic() - started}
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            done[key] = record
            print(f"inference {i+1}/{len(items)} truncated={truncated} empty={not bool(answer)}", flush=True)


def register_marc(directory):
    from llm_jp_eval.jaster.base import BaseDatasetProcessor, Sample, Split
    from llm_jp_eval.answer_parser import AnswerPatternId

    class MARCJaLocal(BaseDatasetProcessor):
        data_name = "marc_ja"
        # JGLUE/Amazon license is not assumed to permit commercial use.
        is_processed_allowing_commercial_use = False
        splits = [Split.TRAIN, Split.TEST]
        def __init__(self, dataset_dir, version_name):
            super().__init__(dataset_dir, version_name)
            self.output_info.instruction = "レビューの感情をpositiveまたはnegativeで回答してください。"
            self.output_info.output_length = 15
            self.output_info.metrics = ["exact_match"]
            self.output_info.label_list = ["positive", "negative"]
            self.output_info.answer_pattern_id = AnswerPatternId.ANSWER_TAGS_JP
        def _download(self, split):
            name = "train-v1.1.json" if split == Split.TRAIN else "valid-v1.1.json"
            path = directory / name
            if not path.is_file():
                raise FileNotFoundError(f"Provide the officially preprocessed JGLUE MARC-ja file: {path}")
            return path
        @classmethod
        def _preprocess_dataset(cls, dataset_path, split):
            records = [json.loads(line) for line in dataset_path.read_text().splitlines() if line.strip()]
            samples = []
            for r in records:
                if r.get("label") not in {"positive", "negative"}:
                    raise ValueError("Unexpected MARC-ja label")
                samples.append(Sample(input=r.get("sentence", r.get("review_body", "")), output=r["label"]))
                if not samples[-1].input:
                    raise ValueError("MARC-ja text missing")
            return samples


def main(a):
    from huggingface_hub import HfApi, snapshot_download
    from llm_jp_eval.jaster import DatasetRegistry
    from llm_jp_eval.schemas import EvaluationConfig
    from llm_jp_eval import evaluator
    from llm_jp_eval.utils import JSONEncoder
    import yaml
    output = a.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    requested = a.tasks.split(",")
    if set(requested) - set(TASKS):
        raise ValueError("Unknown task")
    if a.max_samples != -1 and a.max_samples < 2:
        raise ValueError("Use at least 2 samples for correlations, or -1 for all")
    if a.marc_dir:
        register_marc(a.marc_dir)
    available = [t for t in requested if t in DatasetRegistry.list_registered()]
    missing = sorted(set(requested) - set(available))
    info = HfApi().model_info(a.model, revision=a.revision)
    if a.backend == "mlx":
        a.model_path = snapshot_download(a.model, revision=info.sha)
    elif not a.base_url.startswith("http://127.0.0.1:") and not a.base_url.startswith("http://localhost:"):
        raise ValueError("Use a local inference endpoint; no implicit remote paid requests")
    run_settings = {"model": a.model, "revision": info.sha, "backend": a.backend,
                    "chat_template": a.chat_template, "require_final": a.require_final,
                    "reasoning_effort": a.reasoning_effort, "max_tokens": a.max_tokens,
                    "few_shots": a.few_shots, "max_samples": a.max_samples, "tasks": requested,
                    "eval_version": importlib.metadata.version("llm-jp-eval"), "seed": a.seed,
                    "max_input_tokens": a.max_input_tokens, "base_url": a.base_url}
    run_settings["evaluator_source_commit"] = a.eval_commit
    fingerprint = hashlib.sha256(json.dumps(run_settings, sort_keys=True).encode()).hexdigest()
    result_path = output / "benchmark_results.json"
    summary = {**run_settings, "run_fingerprint": fingerprint, "status": "running", "evaluation_origin": "local_unverified",
               "missing_tasks": missing, "jglue_complete": False, "jglue_score": None,
               "aggregate_note": "No canonical JGLUE aggregate is invented. JSTS is correlation, JSQuAD includes EM and character F1.",
               "scores": {}, "datasets": {}}
    write_json(result_path, summary)
    config_path = output / "datasets.yaml"
    primary = {"jsts": "pearson", "mgsm": "mathematical_equivalence"}
    categories = {t: {"description": t + " component", "default_metric": primary.get(t, "exact_match"), "metrics": {}, "datasets": [t]} for t in available}
    config_path.write_text(yaml.safe_dump({"datasets": available, "categories": categories, "dataset_info_overrides": {}}, allow_unicode=True))
    cfg = EvaluationConfig.model_validate({"run_name": a.model + "-local", "output_dir": output / "official",
          "eval_dataset_config_path": config_path, "eval_dataset_config": {"datasets": available, "categories": categories, "dataset_info_overrides": {}},
          "exporters": {"local": {"export_output_table": True, "output_top_n": None}}, "max_num_samples": a.max_samples,
          "target_split": "test", "num_few_shots": a.few_shots,
          "online_inference_config": {"provider": "vllm-openai", "model_name": a.model, "hostname": "127.0.0.1:1",
                                     "max_concurrent": 1, "generation_config": {"temperature": 0.0, "max_tokens": a.max_tokens}}})
    version = cfg.version
    for task in available:
        print("PREPARE", task, flush=True)
        processor = DatasetRegistry.get(task)(cfg.output_dir / "datasets", version)
        if not (cfg.target_dataset_dir / (task + ".json")).exists():
            processor.download()
            processor.preprocess_evaluation_data()
    prompts = evaluator.load_dataset_and_construct_prompt_template(cfg)
    all_records = {}
    for data in prompts:
        task = data.target_dataset
        inp = output / (task + ".inference-input.jsonl")
        checkpoint = output / (task + ".generations.jsonl")
        inp.write_text("".join(json.dumps({"prompt": s.prompt}, ensure_ascii=False) + "\n" for s in data.samples))
        args = [a.inference_python, str(Path(__file__).resolve()), "--worker", "--worker-input", str(inp),
                "--worker-output", str(checkpoint), "--fingerprint", fingerprint, "--backend", a.backend,
                "--model", a.model, "--model-path", a.model_path, "--max-tokens", str(a.max_tokens),
                "--max-input-tokens", str(a.max_input_tokens), "--cache-mb", str(a.cache_mb),
                "--reasoning-effort", a.reasoning_effort, "--base-url", a.base_url, "--timeout", str(a.timeout), "--seed", str(a.seed)]
        if a.chat_template: args.append("--chat-template")
        if a.require_final: args.append("--require-final")
        subprocess.run(args, check=True)
        records = [json.loads(s) for s in checkpoint.read_text().splitlines() if s.strip()]
        wanted = {hashlib.sha256(s.prompt.encode()).hexdigest() for s in data.samples}
        records = [r for r in records if r["prompt_sha256"] in wanted]
        all_records.update({r["prompt_sha256"]: r["answer"] for r in records})
        expected = len(json.loads((cfg.target_dataset_dir / (task + ".json")).read_text())["samples"])
        summary["datasets"][task] = {"evaluated_samples": len(data.samples), "available_samples": expected,
            "all_samples": len(data.samples) == expected, "truncated_samples": sum(r["truncated"] for r in records),
            "empty_answers": sum(r["empty_answer"] for r in records)}
        write_json(result_path, summary)
    class RecordedModel:
        async def ainvoke(self, prompt):
            key = hashlib.sha256(prompt.encode()).hexdigest()
            if key not in all_records: raise RuntimeError("Missing inference checkpoint")
            return all_records[key]
    # Only the inference transport is adapted. Official answer parsing and metrics stay unchanged.
    evaluator.get_online_inference_model = lambda config: RecordedModel()
    scores, _ = evaluator.evaluate(cfg)
    summary["scores"] = {k: float(v) if math.isfinite(float(v)) else None for k, v in scores.items()}
    if "AVG" in summary["scores"]:
        summary["selected_tasks_mean_not_jglue"] = summary["scores"].pop("AVG")
    summary["status"] = "completed" if not missing else "completed_available_tasks"
    summary["full_dataset_run"] = a.max_samples == -1 and all(d["all_samples"] for d in summary["datasets"].values())
    summary["jglue_complete"] = not any(t in missing for t in TASKS[:4]) and set(TASKS[:4]) <= set(available) and summary["full_dataset_run"]
    summary["publication_ready"] = summary["full_dataset_run"] and not any(d["truncated_samples"] or d["empty_answers"] for d in summary["datasets"].values())
    if a.max_samples != -1: summary["publication_ready"] = False
    write_json(result_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--revision", default="main")
    p.add_argument("--backend", choices=["mlx", "openai"], default="mlx")
    p.add_argument("--inference-python", default=sys.executable)
    p.add_argument("--output-dir", type=Path, default=Path("benchmark_run"))
    p.add_argument("--tasks", default=",".join(TASKS))
    p.add_argument("--max-samples", type=int, default=-1, help="-1: full data; positive: smoke test, never publishable")
    p.add_argument("--few-shots", type=int, default=4)
    p.add_argument("--max-tokens", type=int, default=1024)
    p.add_argument("--max-input-tokens", type=int, default=8192)
    p.add_argument("--chat-template", action="store_true")
    p.add_argument("--require-final", action="store_true", help="Require a Harmony final channel for this reasoning model")
    p.add_argument("--reasoning-effort", choices=["low", "medium", "high"], default="medium")
    p.add_argument("--marc-dir", type=Path, help="Officially preprocessed MARC-ja v1.1 train/valid JSONL directory")
    p.add_argument("--eval-commit", default="unknown", help="git commit of the installed llm-jp-eval checkout")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--base-url", default="http://127.0.0.1:8080/v1")
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--cache-mb", type=int, default=256)
    p.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--worker-input", type=Path, help=argparse.SUPPRESS)
    p.add_argument("--worker-output", type=Path, help=argparse.SUPPRESS)
    p.add_argument("--fingerprint", help=argparse.SUPPRESS)
    p.add_argument("--model-path", default="", help=argparse.SUPPRESS)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        worker(args) if args.worker else main(args)
    except Exception as exc:
        if not args.worker:
            destination = args.output_dir / "benchmark_results.json"
            current = json.loads(destination.read_text()) if destination.exists() else {}
            current.update(status="failed", error=f"{type(exc).__name__}: {exc}", publication_ready=False)
            write_json(destination, current)
        raise
