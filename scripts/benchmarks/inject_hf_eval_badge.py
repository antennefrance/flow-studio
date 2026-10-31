#!/usr/bin/env python3
"""Add measured local component scores to a model card. This does not certify results."""
import argparse
import copy
import json
from pathlib import Path
import yaml
from huggingface_hub import HfApi, hf_hub_download

METRICS = {"jsts_pearson": ("JSTS", "yahoojapan/JGLUE", "jsts", "pearson", "Pearson correlation"),
           "jsts_spearman": ("JSTS", "yahoojapan/JGLUE", "jsts", "spearmanr", "Spearman correlation"),
           "jnli_exact_match": ("JNLI", "yahoojapan/JGLUE", "jnli", "accuracy", "Accuracy"),
           "jsquad_exact_match": ("JSQuAD", "yahoojapan/JGLUE", "jsquad", "exact_match", "Exact match (llm-jp-eval)"),
           "jsquad_char_f1": ("JSQuAD", "yahoojapan/JGLUE", "jsquad", "char_f1", "Character F1 (llm-jp-eval)"),
           "mgsm_mathematical_equivalence": ("MGSM Japanese", "juletxara/mgsm", "ja", "mathematical_equivalence", "Mathematical equivalence"),
           "marc_ja_exact_match": ("MARC-ja", "yahoojapan/JGLUE", "marc_ja", "accuracy", "Accuracy (local adapter)")}


def render(card_text, summary):
    if summary.get("evaluation_origin") != "local_unverified" or not summary.get("publication_ready"):
        raise ValueError("Refusing to publish incomplete, truncated, smoke-test or unverified-provenance measurements")
    if card_text.startswith("---\n"):
        chunks = card_text.split("---\n", 2)
        if len(chunks) != 3: raise ValueError("Malformed YAML frontmatter")
        metadata = yaml.safe_load(chunks[1]) or {}
        body = chunks[2]
    else:
        metadata, body = {}, card_text
    old = copy.deepcopy(metadata)
    result_entries = []
    for key, value in summary.get("scores", {}).items():
        if key not in METRICS or value is None: continue
        name, dataset_type, config, metric_type, metric_name = METRICS[key]
        result_entries.append({"task": {"type": "text-generation", "name": "Local llm-jp-eval (not leaderboard verified)"},
            "dataset": {"type": dataset_type, "name": name, "config": config, "split": "validation" if dataset_type == "yahoojapan/JGLUE" else "test"},
            "metrics": [{"type": metric_type, "name": metric_name, "value": float(value), "verified": False}]})
    if not result_entries: raise ValueError("No supported measured component scores")
    label = summary["model"].split("/")[-1] + " — local llm-jp-eval"
    existing = metadata.get("model-index", [])
    # Preserve unrelated model-index records and all other YAML metadata.
    metadata["model-index"] = [entry for entry in existing if entry.get("name") != label] + [{"name": label, "results": result_entries}]
    start, end = "<!-- pyrite-local-evaluation:start -->", "<!-- pyrite-local-evaluation:end -->"
    section = f"{start}\n## Local evaluation\n\nSelf-reported results from llm-jp-eval {summary['eval_version']}; not an official leaderboard certification.\nModel revision: `{summary['revision']}`. Few-shot: {summary['few_shots']}; max generation tokens: {summary['max_tokens']}.\n\n"
    section += "\n".join(f"- {key}: {value}" for key, value in summary["scores"].items() if key in METRICS)
    if not summary.get("jglue_complete"): section += "\n\nMARC-ja/JGLUE coverage is incomplete; no aggregate JGLUE score is reported."
    section += f"\n{end}"
    if start in body:
        if end not in body: raise ValueError("Unclosed evaluation section")
        before, rest = body.split(start, 1)
        _, after = rest.split(end, 1)
        body = before + section + after
    else: body = body.rstrip() + "\n\n" + section + "\n"
    return "---\n" + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False) + "---\n" + body


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results", required=True, type=Path)
    p.add_argument("--repo-id", required=True)
    p.add_argument("--readme", type=Path)
    p.add_argument("--output", type=Path, default=Path("README.evaluated.md"))
    p.add_argument("--publish", action="store_true", help="Upload only the validated README with parent-commit conflict protection")
    a = p.parse_args()
    summary = json.loads(a.results.read_text())
    if summary.get("model") != a.repo_id: raise ValueError("Results belong to another model")
    api = HfApi()
    info = api.model_info(a.repo_id)
    if info.sha != summary.get("revision"): raise ValueError("Model revision changed since evaluation; re-evaluate or inspect the change")
    source = a.readme or Path(hf_hub_download(a.repo_id, "README.md", revision=info.sha))
    content = render(source.read_text(), summary)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(content)
    # Validate structured model-index using HF's own parser before uploading.
    from huggingface_hub import ModelCard
    ModelCard(content).validate()
    if a.publish:
        commit = api.upload_file(path_or_fileobj=content.encode(), path_in_repo="README.md", repo_id=a.repo_id,
                                 parent_commit=info.sha, commit_message="Document measured local llm-jp-eval component results")
        print(commit.commit_url)
    else: print(a.output)


if __name__ == "__main__":
    main()
