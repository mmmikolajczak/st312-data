from __future__ import annotations

import json
import os
import subprocess
import tempfile

from metric_env import ensure_metric_env


DEFAULT_BARTSCORE_MODEL = "facebook/bart-large-cnn"


def _parse_json_from_stdout(stdout: str) -> dict:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise ValueError("Metric subprocess produced no stdout")
    return json.loads(lines[-1])


def _metric_script() -> str:
    return r"""
import json
import math
import sys

import torch
from transformers import BartForConditionalGeneration, BartTokenizer

payload = json.load(open(sys.argv[1], encoding="utf-8"))
predictions = payload["predictions"]
references = payload["references"]
model_name = payload["model_name"]

tokenizer = BartTokenizer.from_pretrained(model_name)
model = BartForConditionalGeneration.from_pretrained(model_name)
model.eval()

def pair_loss(source, target):
    src = tokenizer(source, return_tensors="pt", truncation=True, max_length=1024)
    tgt = tokenizer(target, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        out = model(input_ids=src["input_ids"], attention_mask=src["attention_mask"], labels=tgt["input_ids"])
    return float(out.loss.item())

scores = []
for pred, ref in zip(predictions, references):
    self_loss = pair_loss(ref, ref)
    pred_loss = pair_loss(ref, pred)
    normalized = math.exp(-(pred_loss - self_loss))
    if normalized > 1.0:
        normalized = 1.0
    scores.append(normalized)

print(json.dumps({"bartscore": sum(scores) / (len(scores) or 1)}))
"""


def compute_bartscore(predictions: list[str], references: list[str], *, model_name: str = DEFAULT_BARTSCORE_MODEL) -> dict:
    if len(predictions) != len(references):
        raise ValueError("predictions and references must be the same length")
    venv_python = ensure_metric_env()
    payload = {"predictions": predictions, "references": references, "model_name": model_name}
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
        return _parse_json_from_stdout(result.stdout)
    finally:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
