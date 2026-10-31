#!/usr/bin/env python3
"""Inspect live submission API and request a preview; never bypass Space OAuth."""
import argparse
import json
import time
from pathlib import Path
import requests
from huggingface_hub import HfApi, get_token, hf_hub_download


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="masahiroid/llm-jp-4.1-8b-thinking-4bit-mlx")
    p.add_argument("--revision", default="main")
    p.add_argument("--space", default="llm-jp/open-japanese-llm-leaderboard-v2")
    p.add_argument("--output", type=Path, default=Path("submission_status.json"))
    p.add_argument("--preview", action="store_true", help="Call the real preview API. Does not submit a queue entry.")
    p.add_argument("--submit", action="store_true", help="Confirm only if preview succeeded in this authenticated session.")
    p.add_argument("--watch-seconds", type=int, default=0)
    p.add_argument("--poll-seconds", type=int, default=30)
    a = p.parse_args()
    api = HfApi(token=get_token())
    info = api.model_info(a.model, revision=a.revision)
    space = api.space_info(a.space)
    domain = next((d["domain"] for d in space.runtime.raw.get("domains", []) if d.get("stage") == "READY"), None)
    if not domain:
        raise SystemExit("Space has no ready public domain")
    response = requests.get(f"https://{domain}/config", timeout=30)
    response.raise_for_status()
    config = response.json()
    names = [d.get("api_name") for d in config.get("dependencies", [])]
    files = [s.rfilename for s in info.siblings]
    model_config = {}
    if "config.json" in files:
        model_config = json.loads(Path(hf_hub_download(a.model, "config.json", revision=info.sha)).read_text())
    quant = model_config.get("quantization_config", model_config.get("quantization", {}))
    mlx = "bits" in quant and "quant_method" not in quant
    report = {"model": a.model, "revision": info.sha, "space": a.space, "space_revision": space.sha,
              "api_names": names, "format": "mlx_affine" if mlx else "gguf" if any(f.endswith(".gguf") for f in files) else "transformers",
              "status": "preflight_only", "submitted": False,
              "warnings": [], "preview_result": None}
    if mlx:
        report["warnings"].append("MLX affine weights are not a declared quantization format for the leaderboard's vLLM backend. Do not relabel precision or replace them with the upstream model.")
    if a.preview or a.submit:
        if "preview_eval" not in names or "confirm_eval" not in names:
            report["status"] = "api_changed"
        else:
            from gradio_client import Client
            client = Client(a.space, token=get_token(), verbose=False)
            result = client.predict(a.model, info.sha, "auto", "⭕ : instruction-tuned", "False", "True", "True", "llmjp4", api_name="/preview_eval")
            report["preview_result"] = result
            status = str(result)
            if "log in" in status.lower() or "login" in status.lower():
                report["status"] = "blocked_oauth_login_required"
            elif isinstance(result, (list, tuple)) and result[0] == "":
                report["status"] = "preview_ready"
                if a.submit and not mlx:
                    confirmation = client.predict(api_name="/confirm_eval")
                    report["confirmation"] = confirmation
                    report["submitted"] = "submitted to the evaluation queue" in str(confirmation).lower()
                    report["status"] = "submitted" if report["submitted"] else "submission_rejected"
                elif a.submit and mlx:
                    report["status"] = "blocked_backend_compatibility"
            else:
                report["status"] = "preview_rejected"
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    if report["submitted"] and a.watch_seconds:
        deadline = time.monotonic() + a.watch_seconds
        while time.monotonic() < deadline:
            entries = api.list_repo_tree("llm-jp/leaderboard-requests-v2", repo_type="dataset", path_in_repo=a.model.split("/")[0])
            matches = [x.path for x in entries if x.path.split("/")[-1].startswith(a.model.split("/")[1] + "_") and x.path.endswith(".json")]
            report["queue_entries"] = []
            for name in matches:
                local = hf_hub_download("llm-jp/leaderboard-requests-v2", name, repo_type="dataset", force_download=True)
                data = json.loads(Path(local).read_text())
                if data.get("revision") == info.sha:
                    report["queue_entries"].append({"path": name, "status": data.get("status")})
            a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str))
            if any(e["status"] in {"FINISHED", "FAILED", "ERROR"} for e in report["queue_entries"]):
                break
            time.sleep(min(a.poll_seconds, max(0, deadline - time.monotonic())))


if __name__ == "__main__":
    main()
