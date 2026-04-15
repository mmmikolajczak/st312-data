from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from metric_env import ensure_metric_env


DEFAULT_SUMMAC_MODEL = "vitc"
SUMMAC_WORKDIR = Path("data/ectsum_official/.summac_cache")


def _parse_json_from_stdout(stdout: str) -> dict:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise ValueError("Metric subprocess produced no stdout")
    return json.loads(lines[-1])


def _metric_script() -> str:
    return r"""
import json
import sys
from summac.model_summac import SummaCConv

payload = json.load(open(sys.argv[1], encoding="utf-8"))
sources = payload["sources"]
summaries = payload["summaries"]
model_name = payload["model_name"]

model = SummaCConv(models=[model_name], bins="percentile", granularity="sentence", nli_labels="e", device="cpu", start_file="default", agg="mean")
scores = model.score(sources, summaries)["scores"]
print(json.dumps({"summacconv": sum(scores) / (len(scores) or 1)}))
"""


def compute_summacconv(sources: list[str], summaries: list[str], *, model_name: str = DEFAULT_SUMMAC_MODEL) -> dict:
    if len(sources) != len(summaries):
        raise ValueError("sources and summaries must be the same length")
    venv_python = ensure_metric_env()
    payload = {"sources": sources, "summaries": summaries, "model_name": model_name}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(payload, tmp, ensure_ascii=False)
        tmp_path = tmp.name
    try:
        env = os.environ.copy()
        env["TOKENIZERS_PARALLELISM"] = "false"
        env.setdefault("HUGGINGFACE_HUB_CACHE", "/tmp/hf_cache")
        env.setdefault("HF_XET_CACHE", "/tmp/hf_xet")
        SUMMAC_WORKDIR.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [str(venv_python), "-c", _metric_script(), tmp_path],
            check=True,
            capture_output=True,
            text=True,
            env=env,
            cwd=SUMMAC_WORKDIR,
        )
        return _parse_json_from_stdout(result.stdout)
    finally:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
