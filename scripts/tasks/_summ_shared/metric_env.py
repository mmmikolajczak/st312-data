from __future__ import annotations

import subprocess
import sys
import shutil
import fcntl
from pathlib import Path


VENV_DIR = Path("data/ectsum_official/.metric_venv")
LOCK_PATH = VENV_DIR.parent / ".metric_venv.lock"
PACKAGE_SPECS = [
    "pip>=25.0",
    "protobuf==3.20.3",
    "rouge-score==0.1.2",
    "bert-score==0.3.11",
    "summac==0.0.4",
    "transformers==4.24.0",
]


def ensure_metric_env() -> Path:
    venv_python = VENV_DIR / "bin" / "python"
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)

        if venv_python.exists():
            check = subprocess.run(
                [
                    str(venv_python),
                    "-c",
                    (
                        "import rouge_score, bert_score, summac, transformers; "
                        "from google.protobuf import __version__ as protobuf_version; "
                        "major, minor, *_ = [int(part) for part in protobuf_version.split('.')]; "
                        "assert (major, minor) <= (3, 20), protobuf_version"
                    ),
                ],
                capture_output=True,
                text=True,
            )
            if check.returncode == 0:
                return venv_python

        if VENV_DIR.exists():
            shutil.rmtree(VENV_DIR)
        VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", *PACKAGE_SPECS], check=True)
        return venv_python
