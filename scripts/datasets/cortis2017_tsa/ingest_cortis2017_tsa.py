import argparse
import json
from pathlib import Path
from typing import Iterable, Any


RAW_CONTRACT = {
    "train": "Headline_Trainingdata.json",
    "trial": "Headline_Trialdata.json",
    "test_inputs": "Headlines_Testdata.json",
    "test_gold": "Headlines_Test_GS.json",
}


def load_any_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        rows = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
        return rows


def iter_records(payload: Any) -> Iterable[dict]:
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item
            else:
                yield {"value": item}
        return

    if isinstance(payload, dict):
        for key in ("data", "records", "items", "examples", "headlines", "messages"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield item
                    else:
                        yield {"value": item}
                return

        if payload and all(isinstance(v, dict) for v in payload.values()):
            for value in payload.values():
                yield value
            return

        yield payload
        return

    raise TypeError(f"Unsupported JSON payload type: {type(payload)}")


def dump_jsonl(rows: Iterable[dict], out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default="data/cortis2017_tsa/raw")
    args = ap.parse_args()

    raw_dir = Path(args.raw_dir)
    out_map = {
        "train": raw_dir / "cortis2017_tsa_train_raw.jsonl",
        "trial": raw_dir / "cortis2017_tsa_trial_raw.jsonl",
        "test_inputs": raw_dir / "cortis2017_tsa_test_inputs_raw.jsonl",
        "test_gold": raw_dir / "cortis2017_tsa_test_gold_raw.jsonl",
    }

    meta = {
        "dataset_id": "cortis2017_tsa_v0",
        "raw_dir": str(raw_dir),
        "files": {},
    }

    required = ("train", "trial", "test_inputs")
    for split in required:
        src = raw_dir / RAW_CONTRACT[split]
        if not src.exists():
            raise SystemExit(f"Missing required raw file: {src}")

    for split, filename in RAW_CONTRACT.items():
        src = raw_dir / filename
        if not src.exists():
            meta["files"][split] = {
                "source_path": str(src),
                "present": False,
                "written_jsonl": None,
            }
            continue

        payload = load_any_json(src)
        rows = (
            {
                "official_split": split,
                "raw_index": i,
                "raw_record": rec,
            }
            for i, rec in enumerate(iter_records(payload))
        )
        n = dump_jsonl(rows, out_map[split])
        meta["files"][split] = {
            "source_path": str(src),
            "present": True,
            "written_jsonl": str(out_map[split]),
            "n_rows": n,
        }

    meta_path = raw_dir / "cortis2017_tsa_ingest_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("[DONE] Ingest complete")
    print(f"[META] {meta_path}")
    for split, info in meta["files"].items():
        print(f"[{split}] {info}")


if __name__ == "__main__":
    main()
