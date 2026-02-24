import json
import re
import sys
from pathlib import Path


ROOT = Path(".")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def is_placeholder(x):
    if x is None:
        return False
    if not isinstance(x, str):
        return False
    return "<" in x and ">" in x


def main():
    errors = []
    warnings = []

    def err(msg):
        errors.append(msg)

    def warn(msg):
        warnings.append(msg)

    datasets_registry_path = ROOT / "datasets" / "dataset_registry.json"
    tasks_registry_path = ROOT / "tasks" / "task_registry.json"
    manifests_publish_dir = ROOT / "manifests" / "publish"

    if not datasets_registry_path.exists():
        err(f"Missing dataset registry: {datasets_registry_path}")
    if not tasks_registry_path.exists():
        err(f"Missing task registry: {tasks_registry_path}")

    if errors:
        print_report(errors, warnings)
        sys.exit(1)

    dreg = load_json(datasets_registry_path)
    treg = load_json(tasks_registry_path)

    dataset_entries = dreg.get("datasets", [])
    task_entries = treg.get("tasks", [])

    dataset_ids = []
    task_ids = []

    dataset_specs = {}
    task_specs = {}

    published_dataset_ids_from_spec = set()
    published_dataset_ids_from_records = set()
    published_task_ids_from_records = set()

    # ----------------------------
    # Check datasets registry/specs
    # ----------------------------
    for d in dataset_entries:
        did = d.get("dataset_id")
        if not did:
            err("Dataset registry entry missing dataset_id")
            continue

        dataset_ids.append(did)

        spec_path_str = d.get("dataset_spec_path")
        if not spec_path_str:
            err(f"[dataset:{did}] Missing dataset_spec_path in registry")
            continue

        spec_path = ROOT / spec_path_str
        if not spec_path.exists():
            err(f"[dataset:{did}] dataset_spec_path does not exist: {spec_path_str}")
            continue

        try:
            spec = load_json(spec_path)
        except Exception as e:
            err(f"[dataset:{did}] Failed to parse dataset spec {spec_path_str}: {e}")
            continue

        dataset_specs[did] = spec

        if spec.get("dataset_id") != did:
            err(
                f"[dataset:{did}] dataset_id mismatch: registry={did}, "
                f"spec={spec.get('dataset_id')}"
            )

        reg_hf = d.get("canonical_hf_repo")
        spec_hf = (spec.get("hf_publish") or {}).get("repo_id")
        if reg_hf and spec_hf and reg_hf != spec_hf:
            err(
                f"[dataset:{did}] HF repo mismatch: registry={reg_hf}, spec={spec_hf}"
            )

        if is_placeholder(d.get("upstream_license")):
            warn(f"[dataset:{did}] registry upstream_license still placeholder: {d.get('upstream_license')}")

        hf_publish = spec.get("hf_publish") or {}
        for k in ["upstream_license", "repo_id"]:
            if is_placeholder(hf_publish.get(k)):
                warn(f"[dataset:{did}] spec hf_publish.{k} still placeholder: {hf_publish.get(k)}")

        status = spec.get("status") or {}
        if ((isinstance(status, dict) and status.get("published_to_hf") is True) or (isinstance(status, str) and status in {"published", "published_hf"})):
            published_dataset_ids_from_spec.add(did)

        manifest_spec = ROOT / "manifests" / "datasets" / did / "dataset_spec.json"
        if not manifest_spec.exists():
            warn(f"[dataset:{did}] Missing manifest snapshot: manifests/datasets/{did}/dataset_spec.json")

        manifest_checksums = ROOT / "manifests" / "datasets" / did / "checksums.sha256"
        if not manifest_checksums.exists():
            warn(f"[dataset:{did}] Missing dataset checksums snapshot: manifests/datasets/{did}/checksums.sha256")

    # Duplicate dataset IDs
    seen = set()
    for did in dataset_ids:
        if did in seen:
            err(f"Duplicate dataset_id in dataset_registry.json: {did}")
        seen.add(did)

    # -------------------------
    # Check tasks registry/specs
    # -------------------------
    for t in task_entries:
        tid = t.get("task_id")
        if not tid:
            err("Task registry entry missing task_id")
            continue

        task_ids.append(tid)

        task_spec_path_str = t.get("task_spec_path")
        if not task_spec_path_str:
            err(f"[task:{tid}] Missing task_spec_path in registry")
            continue

        task_spec_path = ROOT / task_spec_path_str
        if not task_spec_path.exists():
            err(f"[task:{tid}] task_spec_path does not exist: {task_spec_path_str}")
            continue

        try:
            task_spec = load_json(task_spec_path)
        except Exception as e:
            err(f"[task:{tid}] Failed to parse task spec {task_spec_path_str}: {e}")
            continue

        task_specs[tid] = task_spec

        if task_spec.get("task_id") != tid:
            err(
                f"[task:{tid}] task_id mismatch: registry={tid}, spec={task_spec.get('task_id')}"
            )

        reg_dataset_id = t.get("dataset_id")
        spec_dataset_id = (task_spec.get("dataset") or {}).get("dataset_id")

        if reg_dataset_id and spec_dataset_id and reg_dataset_id != spec_dataset_id:
            err(
                f"[task:{tid}] dataset_id mismatch: registry={reg_dataset_id}, spec={spec_dataset_id}"
            )

        if spec_dataset_id and spec_dataset_id not in [d.get("dataset_id") for d in dataset_entries]:
            err(f"[task:{tid}] References unknown dataset_id: {spec_dataset_id}")

        task_readme_path_str = t.get("task_readme_path")
        if task_readme_path_str:
            task_readme_path = ROOT / task_readme_path_str
            if not task_readme_path.exists():
                warn(f"[task:{tid}] task_readme_path missing: {task_readme_path_str}")
        else:
            warn(f"[task:{tid}] Missing task_readme_path in task registry")

        # Derive task folder from task_spec_path = tasks/<folder>/task_spec.json
        parts = Path(task_spec_path_str).parts
        if len(parts) >= 3 and parts[0] == "tasks":
            task_folder = parts[1]
            manifest_task_spec = ROOT / "manifests" / "tasks" / task_folder / "task_spec.json"
            if not manifest_task_spec.exists():
                warn(f"[task:{tid}] Missing task manifest snapshot: manifests/tasks/{task_folder}/task_spec.json")
        else:
            warn(f"[task:{tid}] Could not derive task folder from task_spec_path: {task_spec_path_str}")

    # Duplicate task IDs
    seen = set()
    for tid in task_ids:
        if tid in seen:
            err(f"Duplicate task_id in task_registry.json: {tid}")
        seen.add(tid)

    # -----------------------
    # Check publish records
    # -----------------------
    if manifests_publish_dir.exists():
        for p in sorted(manifests_publish_dir.glob("*_publish_record.json")):
            try:
                rec = load_json(p)
            except Exception as e:
                err(f"[publish-record:{p.name}] Failed to parse JSON: {e}")
                continue

            did = rec.get("dataset_id")
            tid = rec.get("task_id")
            hf_repo = rec.get("hf_repo")
            hf_commits = rec.get("hf_commits")
            artifacts = rec.get("artifacts_published")

            if not did:
                err(f"[publish-record:{p.name}] Missing dataset_id")
                continue
            if not tid:
                err(f"[publish-record:{p.name}] Missing task_id")
                continue

            if did not in dataset_specs:
                err(f"[publish-record:{p.name}] Unknown dataset_id: {did}")
            if tid not in task_specs:
                err(f"[publish-record:{p.name}] Unknown task_id: {tid}")

            if did in dataset_specs:
                spec_hf = (dataset_specs[did].get("hf_publish") or {}).get("repo_id")
                if hf_repo and spec_hf and hf_repo != spec_hf:
                    err(f"[publish-record:{p.name}] hf_repo mismatch vs dataset spec: record={hf_repo}, spec={spec_hf}")

            if not isinstance(hf_commits, dict) or not hf_commits:
                err(f"[publish-record:{p.name}] hf_commits must be a non-empty object")
            else:
                for k, v in hf_commits.items():
                    if not isinstance(v, str) or not HEX40_RE.match(v):
                        warn(f"[publish-record:{p.name}] hf_commits['{k}'] is not a 40-char hex commit: {v}")

            if not isinstance(artifacts, list) or not artifacts:
                err(f"[publish-record:{p.name}] artifacts_published must be a non-empty list")

            published_dataset_ids_from_records.add(did)
            published_task_ids_from_records.add(tid)
    else:
        warn("manifests/publish directory not found")

    # -----------------------------------------
    # Cross-check published state vs registries
    # -----------------------------------------
    for did in sorted(published_dataset_ids_from_spec):
        if did not in published_dataset_ids_from_records:
            warn(
                f"[dataset:{did}] dataset_spec.status.published_to_hf=True but no publish record found "
                f"in manifests/publish/*_publish_record.json"
            )

    # Registry statuses can be intentionally lagging; warn only
    dataset_reg_map = {d.get("dataset_id"): d for d in dataset_entries}
    task_reg_map = {t.get("task_id"): t for t in task_entries}

    for did in sorted(published_dataset_ids_from_records):
        reg_status = (dataset_reg_map.get(did) or {}).get("status")
        if reg_status not in {"published", "published_hf"}:
            warn(
                f"[dataset:{did}] Published record exists but dataset_registry status is '{reg_status}' "
                f"(recommended: 'published')"
            )

    for tid in sorted(published_task_ids_from_records):
        reg_status = (task_reg_map.get(tid) or {}).get("status")
        if reg_status not in {"published", "published_hf"}:
            warn(
                f"[task:{tid}] Published record exists but task_registry status is '{reg_status}' "
                f"(recommended: 'published')"
            )

    print_report(errors, warnings)

    if errors:
        sys.exit(1)
    sys.exit(0)


def print_report(errors, warnings):
    print("=" * 88)
    print("ST312 publish consistency check")
    print("=" * 88)

    if not errors and not warnings:
        print("[OK] No issues found.")
    else:
        if errors:
            print(f"[ERRORS] {len(errors)}")
            for i, e in enumerate(errors, 1):
                print(f"  {i}. {e}")
        else:
            print("[ERRORS] 0")

        if warnings:
            print(f"[WARNINGS] {len(warnings)}")
            for i, w in enumerate(warnings, 1):
                print(f"  {i}. {w}")
        else:
            print("[WARNINGS] 0")

    print("-" * 88)
    if errors:
        print("Result: FAIL (fix errors)")
    elif warnings:
        print("Result: PASS with warnings")
    else:
        print("Result: PASS")
    print("=" * 88)


if __name__ == "__main__":
    main()
