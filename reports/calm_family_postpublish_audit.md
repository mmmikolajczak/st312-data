# CALM Family Post-Publish Audit

Date: 2026-04-17

Scope:
- `calm_lendingclub_public_v0` / `RM_CREDIT_LENDINGCLUB_CALM_v0`
- `calm_ccf_public_v0` / `RM_FRAUD_CCF_CALM_v0`
- `calm_ccfraud_public_v0` / `RM_FRAUD_CCFRAUD_CALM_v0`
- `calm_polish_public_v0` / `RM_DISTRESS_POLISH_CALM_v0`
- `calm_taiwan_public_v0` / `RM_DISTRESS_TAIWAN_CALM_v0`
- `calm_portoseguro_public_v0` / `RM_CLAIM_PORTOSEGURO_CALM_v0`
- `calm_travelinsurance_public_v0` / `RM_CLAIM_TRAVELINSURANCE_CALM_v0`

Checks run:
- `python scripts/utils/check_publish_records.py`
- `python scripts/utils/check_tracked_task_requests.py`
- `python scripts/utils/verify_hf_readme_paths.py` for all seven CALM sections in `manifests/hf_repo/README.md`

Summary:
- All seven CALM modules have dataset specs, task specs, dataset/task registry entries, publish records, top-level `README.md` module entries, `manifests/hf_repo/README.md` published-contents sections, and valid listed HF artifact paths.
- All seven modules correctly record `Salesforce/FinEval` CRA subsets as the canonical accessible benchmark release surface.
- Dataset-spec family metadata was already correct across the batch.
- One concrete drift was found and fixed:
  - all seven CALM task specs were missing the explicit `calm_family_metadata` block required by the family contract
  - local task specs and mirrored manifest task specs were updated to add the exact family metadata fields and values
- Request JSONLs remain HF-only artifacts and are not tracked in GitHub.

## Module Audit

### 1) `calm_lendingclub_public_v0` / `RM_CREDIT_LENDINGCLUB_CALM_v0`

- Mode: `eval_only`
- Instruction style: `description_based`
- Control-plane consistency: yes
- HF paths valid: yes
- Request artifacts Git-clean: yes
- Provenance consistency: yes
  - canonical accessible benchmark release recorded as `Salesforce/FinEval` subset `CRA-LendingClub`
  - raw-source confidence recorded as `medium`
- Drift found and fixed:
  - added missing `calm_family_metadata` block to task spec and mirrored manifest task spec

### 2) `calm_ccf_public_v0` / `RM_FRAUD_CCF_CALM_v0`

- Mode: `train_eval`
- Instruction style: `table_based`
- Control-plane consistency: yes
- HF paths valid: yes
- Request artifacts Git-clean: yes
- Provenance consistency: yes
  - canonical accessible benchmark release recorded as `Salesforce/FinEval` subset `CRA-CCF`
  - raw-source confidence recorded as `low`
- Drift found and fixed:
  - added missing `calm_family_metadata` block to task spec and mirrored manifest task spec

### 3) `calm_ccfraud_public_v0` / `RM_FRAUD_CCFRAUD_CALM_v0`

- Mode: `train_eval`
- Instruction style: `description_based`
- Control-plane consistency: yes
- HF paths valid: yes
- Request artifacts Git-clean: yes
- Provenance consistency: yes
  - canonical accessible benchmark release recorded as `Salesforce/FinEval` subset `CRA-CCFraud`
  - raw-source confidence recorded as `low`
- Drift found and fixed:
  - added missing `calm_family_metadata` block to task spec and mirrored manifest task spec

### 4) `calm_polish_public_v0` / `RM_DISTRESS_POLISH_CALM_v0`

- Mode: `eval_only`
- Instruction style: `description_based`
- Control-plane consistency: yes
- HF paths valid: yes
- Request artifacts Git-clean: yes
- Provenance consistency: yes
  - canonical accessible benchmark release recorded as `Salesforce/FinEval` subset `CRA-Polish`
  - raw-source confidence recorded as `high`
- Drift found and fixed:
  - added missing `calm_family_metadata` block to task spec and mirrored manifest task spec

### 5) `calm_taiwan_public_v0` / `RM_DISTRESS_TAIWAN_CALM_v0`

- Mode: `train_eval`
- Instruction style: `description_based`
- Control-plane consistency: yes
- HF paths valid: yes
- Request artifacts Git-clean: yes
- Provenance consistency: yes
  - canonical accessible benchmark release recorded as `Salesforce/FinEval` subset `CRA-Taiwan`
  - raw-source confidence recorded as `high`
- Drift found and fixed:
  - added missing `calm_family_metadata` block to task spec and mirrored manifest task spec

### 6) `calm_portoseguro_public_v0` / `RM_CLAIM_PORTOSEGURO_CALM_v0`

- Mode: `eval_only`
- Instruction style: `table_based`
- Control-plane consistency: yes
- HF paths valid: yes
- Request artifacts Git-clean: yes
- Provenance consistency: yes
  - canonical accessible benchmark release recorded as `Salesforce/FinEval` subset `CRA-ProtoSeguro`
  - raw-source confidence recorded as `low`
  - wording remains cautious and does not overstate raw-source certainty
- Drift found and fixed:
  - added missing `calm_family_metadata` block to task spec and mirrored manifest task spec

### 7) `calm_travelinsurance_public_v0` / `RM_CLAIM_TRAVELINSURANCE_CALM_v0`

- Mode: `train_eval`
- Instruction style: `description_based`
- Control-plane consistency: yes
- HF paths valid: yes
- Request artifacts Git-clean: yes
- Provenance consistency: yes
  - canonical accessible benchmark release recorded as `Salesforce/FinEval` subset `CRA-TravelInsurance`
  - raw-source confidence recorded as `low`
- Drift found and fixed:
  - added missing `calm_family_metadata` block to task spec and mirrored manifest task spec

## Family-Level Findings

- Family metadata now exists in both dataset specs and task specs for all seven modules:
  - `calm_family = true`
  - `calm_instruction_style`
  - `calm_role`
  - `calm_training_recipe_minority_resampled`
- Role split is aligned with the intended CALM public-family semantics:
  - `eval_only`: lendingclub, polish, portoseguro
  - `train_eval`: ccf, ccfraud, taiwan, travelinsurance
- Instruction-style split is aligned:
  - `table_based`: ccf, portoseguro
  - `description_based`: lendingclub, ccfraud, polish, taiwan, travelinsurance
- Minority-resampling flags are aligned:
  - `true`: ccf, ccfraud, taiwan, travelinsurance
  - `false`: lendingclub, polish, portoseguro
- Eval-only signaling is aligned in dataset specs and task-facing documentation for lendingclub, polish, and portoseguro.

## Residual Notes

- `python scripts/utils/check_publish_records.py` still emits unrelated warnings for older `fiqasa_hf_default_v0` registry drift. Those warnings are outside the CALM-family audit scope and were not changed in this pass.
