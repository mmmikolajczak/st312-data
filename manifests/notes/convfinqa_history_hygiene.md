# ConvFinQA History Hygiene Note

## Purpose

`convfinqa_official_v0` is clean in the live tree and no generated request JSONLs are currently tracked in Git.
However, the initial ConvFinQA publication commit briefly tracked two generated request artifacts before the follow-up cleanup commit removed them from the tree.

This note documents the optional coordinated maintenance procedure for removing those transient blobs from Git history.

## Current verified state

- Current `main` does **not** track request JSONLs:
  - `git ls-files 'tasks/*/requests/*.jsonl'` returns nothing
- The transient ConvFinQA request-file history is limited to:
  - `ac2399a` `Add ConvFinQA canonical program-generation module`
  - `d3159c4` `Ignore ConvFinQA generated request artifacts`

## Transient blobs

The generated artifacts that entered history transiently are:

- `tasks/convfinqa_program_generation_v0/requests/train_requests.jsonl`
  - blob: `b93518b2706cb3d81c76f948268de1e6e006d49a`
  - size: `59,359,831` bytes
- `tasks/convfinqa_program_generation_v0/requests/dev_requests.jsonl`
  - blob: `51af2fbd4eaadd1c33e2dead541dc0d5e0380a21`
  - size: `7,610,762` bytes

## Why cleanup is optional but desirable

The repository is functionally correct now, and the generated files are ignored going forward.
The remaining issue is long-term history hygiene:

- the transient large blob remains in `main` history
- GitHub warns about the large tracked file in the historical commit
- future clones still download the historical objects unless history is rewritten

## Recommended rewrite strategy

Because the bad paths were already pushed to `origin/main`, history rewriting must be coordinated.
Do **not** execute this rewrite unilaterally if other collaborators may have based work on current `main`.

Recommended approach: use `git filter-repo` to remove the two transient paths from all refs that contain them.

### Preconditions

- pause merges/pushes to `main`
- ensure branch protection allows a temporary force-push maintenance window
- notify collaborators that they will need to reset or re-clone after the rewrite

### Rewrite commands

Run from a fresh mirror or disposable clone:

```bash
git clone --mirror https://github.com/mmmikolajczak/st312-data.git st312-data-history-clean.git
cd st312-data-history-clean.git

git filter-repo \
  --path tasks/convfinqa_program_generation_v0/requests/train_requests.jsonl \
  --path tasks/convfinqa_program_generation_v0/requests/dev_requests.jsonl \
  --invert-paths

git push --force --mirror origin
```

### Post-rewrite verification

```bash
git log --oneline -- tasks/convfinqa_program_generation_v0/requests/train_requests.jsonl
git log --oneline -- tasks/convfinqa_program_generation_v0/requests/dev_requests.jsonl
git rev-list --objects --all | rg 'b93518b2706cb3d81c76f948268de1e6e006d49a|51af2fbd4eaadd1c33e2dead541dc0d5e0380a21'
```

Expected result:

- no remaining history for the two request paths
- no remaining references to the transient blob ids

## Alternative if rewrite scope is kept strictly to the tip

Because the transient files were introduced in `ac2399a` and removed in `d3159c4`, an interactive rebase could also clean the tip if and only if:

- no one else has based work on current `main`
- rewriting only the recent tip is operationally simpler than a full mirror-based cleanup

That would still require a force-push and collaborator reset, so the coordination burden is similar.
For repeatability and lower operator error, `git filter-repo` is the preferred maintenance path.

## Collaborator recovery after force-push

After a coordinated rewrite, collaborators should either re-clone or hard-reset local branches to the rewritten `origin/main`.

Minimal reset flow:

```bash
git fetch origin
git checkout main
git reset --hard origin/main
git clean -fd
```

Any local feature branches based on the old history should be rebased or recreated on top of the rewritten `main`.
