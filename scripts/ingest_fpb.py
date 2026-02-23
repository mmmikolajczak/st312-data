import argparse
import json
import urllib.request
import zipfile
from pathlib import Path

ZIP_URL_DEFAULT = (
    "https://huggingface.co/datasets/takala/financial_phrasebank/"
    "resolve/main/data/FinancialPhraseBank-v1.0.zip"
)

CONFIG_TO_INNER_PATH = {
    "allagree": "FinancialPhraseBank-v1.0/Sentences_AllAgree.txt",
    "75agree":  "FinancialPhraseBank-v1.0/Sentences_75Agree.txt",
    "66agree":  "FinancialPhraseBank-v1.0/Sentences_66Agree.txt",
    "50agree":  "FinancialPhraseBank-v1.0/Sentences_50Agree.txt",
}

ALLOWED_LABELS = {"positive", "neutral", "negative"}


def download_zip(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Cache it locally so reruns are fast and reproducible
    if dst.exists() and dst.stat().st_size > 0:
        print(f"[OK] ZIP already exists: {dst}")
        return

    print(f"[DL] Downloading ZIP from: {url}")
    urllib.request.urlretrieve(url, dst)

    if not dst.exists() or dst.stat().st_size == 0:
        raise RuntimeError(f"Download failed or file is empty: {dst}")

    print(f"[OK] Downloaded ZIP to: {dst} ({dst.stat().st_size} bytes)")


def decode_bytes(b: bytes) -> str:
    # Try utf-8, fallback to latin-1 (common for this dataset)
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("latin-1")


def parse_zip(config: str, zip_path: Path, out_path: Path) -> None:
    if config not in CONFIG_TO_INNER_PATH:
        raise ValueError(f"Unknown config '{config}'. Options: {list(CONFIG_TO_INNER_PATH.keys())}")

    inner_path = CONFIG_TO_INNER_PATH[config]
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_lines = 0
    n_written = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        if inner_path not in zf.namelist():
            candidates = [n for n in zf.namelist() if "Sentences_" in n]
            raise FileNotFoundError(
                f"Expected file not found in ZIP: {inner_path}\n"
                f"Found sentence files: {candidates}"
            )

        raw_text = decode_bytes(zf.read(inner_path))
        lines = raw_text.splitlines()

        with out_path.open("w", encoding="utf-8") as f_out:
            for line in lines:
                n_lines += 1
                line = line.strip()
                if not line:
                    continue

                # Format is: "<sentence>@<label>"
                if "@" not in line:
                    raise ValueError(f"Malformed line (missing '@'): {line[:200]}")

                sentence, label = line.rsplit("@", 1)
                sentence = sentence.strip()
                label = label.strip().lower()

                if label not in ALLOWED_LABELS:
                    raise ValueError(f"Unexpected label '{label}' in: {line[:200]}")

                record = {
                    "sentence": sentence,
                    "label": label,
                    "config": config,
                    "source": "takala/financial_phrasebank",
                }
                f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                n_written += 1

    print(f"[DONE] Read {n_lines} lines, wrote {n_written} JSONL records")
    print(f"[OUT]  {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="allagree", choices=list(CONFIG_TO_INNER_PATH.keys()))
    parser.add_argument("--zip-url", default=ZIP_URL_DEFAULT)
    parser.add_argument("--zip-path", default="data/fpb/raw/FinancialPhraseBank-v1.0.zip")
    parser.add_argument("--out", default="data/fpb/raw/fpb_allagree_raw.jsonl")
    args = parser.parse_args()

    zip_path = Path(args.zip_path)
    out_path = Path(args.out)

    download_zip(args.zip_url, zip_path)
    parse_zip(args.config, zip_path, out_path)


if __name__ == "__main__":
    main()
