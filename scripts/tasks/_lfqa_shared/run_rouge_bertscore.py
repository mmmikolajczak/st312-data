from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


PACKAGE_SPECS = [
    "rouge-score==0.1.2",
    "bert-score==0.3.13",
]
DEFAULT_BERTSCORE_MODEL = "roberta-large"
VENV_DIR = Path("data/regulations_public_test/.metric_venv")


def ensure_metric_env() -> Path:
    venv_python = VENV_DIR / "bin" / "python"
    if venv_python.exists():
        return venv_python

    VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(venv_python), "-m", "pip", "install", *PACKAGE_SPECS], check=True)
    return venv_python


def _metric_script() -> str:
    return r"""
import json
import sys
from collections import defaultdict

from bert_score import score as bert_score
from rouge_score import rouge_scorer

payload_path = sys.argv[1]
payload = json.load(open(payload_path, encoding="utf-8"))

predictions = payload["predictions"]
references = payload["references"]
bertscore_model = payload["bertscore_model"]

scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
rouge_totals = defaultdict(float)
for pred, ref in zip(predictions, references):
    ref_list = ref if isinstance(ref, list) else [ref]
    best = None
    for candidate in ref_list:
        scores = scorer.score(candidate, pred)
        if best is None or scores["rougeL"].fmeasure > best["rougeL"].fmeasure:
            best = scores
    for key in ["rouge1", "rouge2", "rougeL"]:
        rouge_totals[key] += best[key].fmeasure

flat_preds = []
flat_refs = []
ownership = []
for idx, (pred, ref) in enumerate(zip(predictions, references)):
    ref_list = ref if isinstance(ref, list) else [ref]
    for candidate in ref_list:
        flat_preds.append(pred)
        flat_refs.append(candidate)
        ownership.append(idx)

P, R, F = bert_score(
    flat_preds,
    flat_refs,
    model_type=bertscore_model,
    lang="en",
    verbose=False,
    rescale_with_baseline=False,
)

best_by_item = {}
for idx, (p, r, f) in enumerate(zip(P.tolist(), R.tolist(), F.tolist())):
    owner = ownership[idx]
    triple = {"precision": p, "recall": r, "f1": f}
    if owner not in best_by_item or triple["f1"] > best_by_item[owner]["f1"]:
        best_by_item[owner] = triple

denom = len(predictions) or 1
result = {
    "rouge1": rouge_totals["rouge1"] / denom,
    "rouge2": rouge_totals["rouge2"] / denom,
    "rougeL": rouge_totals["rougeL"] / denom,
    "bertscore_precision": sum(v["precision"] for v in best_by_item.values()) / denom,
    "bertscore_recall": sum(v["recall"] for v in best_by_item.values()) / denom,
    "bertscore_f1": sum(v["f1"] for v in best_by_item.values()) / denom,
}
print(json.dumps(result))
"""


def compute_rouge_bertscore(
    predictions: list[str],
    references: list[str] | list[list[str]],
    *,
    bertscore_model: str = DEFAULT_BERTSCORE_MODEL,
) -> dict:
    if len(predictions) != len(references):
        raise ValueError("predictions and references must be the same length")

    venv_python = ensure_metric_env()
    payload = {
        "predictions": predictions,
        "references": references,
        "bertscore_model": bertscore_model,
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(payload, tmp, ensure_ascii=False)
        tmp_path = tmp.name

    try:
        env = os.environ.copy()
        env["TOKENIZERS_PARALLELISM"] = "false"
        env.setdefault("HUGGINGFACE_HUB_CACHE", "/tmp/hf_cache")
        env.setdefault("HF_XET_CACHE", "/tmp/hf_xet")
        result = subprocess.run(
            [str(venv_python), "-c", _metric_script(), tmp_path],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        return json.loads(result.stdout)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
