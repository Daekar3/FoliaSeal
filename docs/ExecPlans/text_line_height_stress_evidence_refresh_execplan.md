# Text Line-Height Stress Evidence Refresh ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this evidence refresh, FoliaSeal will know whether the shared structural line-height contract reduced the currently documented realistic-content preview clipping clusters. The user-visible value is confidence in the V1 WYSIWYG promise: the preview matrix should identify whether signable `single_line`, `multi_line`, and `wrapped_block` stress scenarios still show text clipping after the contract change.

This slice is an evidence refresh, not a rendering behavior change. It should rerun the three stress families that README currently records as red: `single_line_full_matrix_stress`, `multi_line_full_matrix_stress`, and `wrapped_block_full_matrix_stress`. It must not mix in backend, preview renderer, manifest, or fixture-generation changes unless a separate follow-up ExecPlan is created.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/text_line_height_contract_execplan.md` is complete and the shared structural line-bound helper has landed in commit `163926f`.
- [x] The repository documents local stress manifests and preview fixture assets under `artifacts/preview_sweep_assets/`.
- [ ] Local fixture assets are present in this workspace: `artifacts/preview_sweep_assets/sweep_fixture.pdf`, `test_identity.p12`, `stamp_wide.png`, `stamp_tall.png`, `stamp_script.png`, `single_line_full_matrix_stress.json`, `multi_line_full_matrix_stress.json`, and `wrapped_block_full_matrix_stress.json`.

## Progress

- [x] (2026-05-13T16:00Z) Started the dev-loop evidence refresh after the shared line-height contract slice.
- [x] (2026-05-13T16:01Z) Spawned an explorer to identify the narrowest repo-native rerun and documentation scope.
- [x] (2026-05-13T16:05Z) Initially identified `single_line_full_matrix_stress` and `wrapped_block_full_matrix_stress` as the narrowest rerun from the prior remediation notes.
- [x] (2026-05-13T16:08Z) Checked this workspace and found `artifacts/preview_sweep_assets/` is absent.
- [x] (2026-05-13T16:09Z) Ran the first targeted matrix command and confirmed it fails before execution because `sweep_fixture.pdf` is missing.
- [x] (2026-05-13T16:11Z) Ran available CLI/harness validation successfully.
- [x] (2026-05-13T16:11Z) Documented this slice as a blocked evidence-refresh handoff.
- [x] (2026-05-14T00:00Z) Compliance review found the handoff under-specified fixture restoration, omitted the README-current `multi_line` stress rerun, missed CLI dispatch coverage, and left the single-line batch fallback too vague.
- [x] (2026-05-14T00:05Z) Updated this plan to restore the full preview fixture family, rerun all three stress manifests that README currently records as red, include exact single-line batch output naming, and validate CLI dispatch.
- [ ] Restore or provide the local preview sweep fixture assets.
- [ ] Rerun the three targeted stress matrices.
- [ ] Update this ExecPlan, `README.md`, and, if counts change materially, `docs/ExecPlans/real_world_stress_coverage_execplan.md` and `docs/ExecPlans/stress_matrix_green_path_remediation_execplan.md`.
- [ ] Commit the completed evidence refresh.

## Surprises & Discoveries

- Observation: The current workspace has an empty `artifacts/` directory and no `preview_sweep_assets` subtree.
  Evidence: `find artifacts -maxdepth 3 -type f` returned no files, and searching for `sweep_fixture.pdf`, `test_identity.p12`, `stamp_wide.png`, `stamp_tall.png`, `stamp_script.png`, and the stress manifests returned no matches.

- Observation: The preview matrix command fails cleanly before running any scenarios when the fixture PDF is missing.
  Evidence: running `phase3-signing-preview-matrix` for `single_line_full_matrix_stress` raised `FileNotFoundError: PDF does not exist: artifacts/preview_sweep_assets/sweep_fixture.pdf`.

## Decision Log

- Decision: Rerun `single_line_full_matrix_stress`, `multi_line_full_matrix_stress`, and `wrapped_block_full_matrix_stress`.
  Rationale: The prior remediation note recorded `multi_line_full_matrix_stress_v3` as clean, but README and `docs/ExecPlans/real_world_stress_coverage_execplan.md` currently record stress `multi_line` as red with `18` signable text clipping risks. The evidence refresh must resolve the current project status, so it should include all three red stress families while still excluding unrelated baseline matrices.
  Date/Author: 2026-05-13 / Codex

- Decision: Do not synthesize replacement fixture assets in this slice.
  Rationale: The README treats `artifacts/preview_sweep_assets/` as conventional local QA fixture input. Recreating ad hoc PDFs, certificates, or manifests would risk comparing against a different corpus and producing misleading counts.
  Date/Author: 2026-05-13 / Codex

## Outcomes & Retrospective

This slice is blocked on missing local fixture assets. The narrow rerun path is identified, the first command was validated up to the expected fixture check, the available CLI/harness tests pass, and the recovery path is documented. No stress counts have been refreshed yet.

## Context and Orientation

The preview matrix command is implemented by `src/foliaseal/__main__.py` and delegates to `run_phase3_preview_matrix()` in `src/foliaseal/presentation/qt/phase3_harness.py`. It opens a source PDF, applies each scenario from a JSON manifest, renders a headless canonical preview, writes per-scenario artifacts under `--artifacts-dir`, and writes a `summary.json` file there.

The stress manifests and fixture PDF/certificate are local QA assets under `artifacts/preview_sweep_assets/`. They are intentionally not guaranteed to be tracked source files because `artifacts/` is ignored for repository hygiene. A valid refresh therefore needs those local assets restored from the user's artifact store or from a prior local workspace before the matrix can run.

The summary fields that matter for this refresh are:

- `signable_text_clipping_risk_scenario_count`
- `rejected_text_clipping_risk_scenario_count`
- `signable_text_stamp_overlap_risk_scenario_count`
- `signable_stamp_warning_scenario_count`
- `stamp_edge_touch_scenario_count`

The previous documented post-remediation stress counts in `docs/ExecPlans/stress_matrix_green_path_remediation_execplan.md` were:

- `single_line_full_matrix_stress_v3`: `108` signable text clipping risks and `672` rejected text clipping risks.
- `multi_line_full_matrix_stress_v3`: `0` signable text clipping risks and `264` rejected text clipping risks.
- `wrapped_block_full_matrix_stress_v3`: `48` signable text clipping risks and `606` rejected text clipping risks.

The README's current latest stress summary is newer/different and must be reconciled by this refresh:

- `single_line`: `150` signable text clipping risks and `680` rejected text clipping risks.
- `multi_line`: `18` signable text clipping risks and `264` rejected text clipping risks.
- `wrapped_block`: `15` signable text clipping risks and `423` rejected text clipping risks.

## Plan of Work

First, restore the local fixture inputs under `artifacts/preview_sweep_assets/`. At minimum this directory must contain `sweep_fixture.pdf`, `test_identity.p12`, `stamp_wide.png`, `stamp_tall.png`, `stamp_script.png`, `single_line_full_matrix_stress.json`, `multi_line_full_matrix_stress.json`, and `wrapped_block_full_matrix_stress.json`. If the full baseline manifests are also restored, keep them untouched; this slice does not regenerate stress manifests.

Second, run the three targeted preview matrices with `QT_QPA_PLATFORM=offscreen` and dedicated output directories under `artifacts/preview_sweep_runs/`. If the `single_line` matrix aborts before writing `summary.json`, split that manifest into smaller local batches without editing the checked-in generator or source manifests, then aggregate counts manually in this plan.

Third, inspect each `summary.json` and record the diagnostic counts in `Artifacts and Notes`. Compare against both the prior remediation counts and README's current latest stress summary. If counts improve, update README's current stress summary. If counts are unchanged or worse, record that too; evidence refresh is still useful when it falsifies a hoped-for improvement.

Fourth, run focused verification for the CLI/harness surfaces:

    .venv/bin/python -m pytest -q tests/unit/test_main_cli.py tests/unit/test_cli_parser.py tests/unit/test_phase3_harness.py

Optionally rerun the preview/backend guardrail if the matrix results look surprising:

    .venv/bin/python -m pytest -q tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Verify fixture assets:

    test -f artifacts/preview_sweep_assets/sweep_fixture.pdf
    test -f artifacts/preview_sweep_assets/test_identity.p12
    test -f artifacts/preview_sweep_assets/stamp_wide.png
    test -f artifacts/preview_sweep_assets/stamp_tall.png
    test -f artifacts/preview_sweep_assets/stamp_script.png
    test -f artifacts/preview_sweep_assets/single_line_full_matrix_stress.json
    test -f artifacts/preview_sweep_assets/multi_line_full_matrix_stress.json
    test -f artifacts/preview_sweep_assets/wrapped_block_full_matrix_stress.json

Run `single_line` stress:

    env QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase preview-passphrase \
      --scenario-manifest-path artifacts/preview_sweep_assets/single_line_full_matrix_stress.json \
      --artifacts-dir artifacts/preview_sweep_runs/single_line_full_matrix_stress

If the monolithic `single_line` run aborts before writing `summary.json`, generate temporary batches from the restored manifest:

    .venv/bin/python -c 'import json, math; from pathlib import Path; src=Path("artifacts/preview_sweep_assets/single_line_full_matrix_stress.json"); out=Path("/tmp/foliaseal_single_line_stress_batches"); out.mkdir(parents=True, exist_ok=True); payload=json.loads(src.read_text(encoding="utf-8")); scenarios=payload["scenarios"]; size=100; [((out / f"single_line_full_matrix_stress_batch_{idx:03d}.json").write_text(json.dumps({**payload, "scenarios": scenarios[start:start+size]}, indent=2), encoding="utf-8")) for idx,start in enumerate(range(0, len(scenarios), size), 1)]'

Run each batch to a stable output directory:

    env QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase preview-passphrase \
      --scenario-manifest-path /tmp/foliaseal_single_line_stress_batches/single_line_full_matrix_stress_batch_001.json \
      --artifacts-dir artifacts/preview_sweep_runs/single_line_full_matrix_stress_batch_001

Repeat for every generated `/tmp/foliaseal_single_line_stress_batches/single_line_full_matrix_stress_batch_*.json` file, incrementing the matching `artifacts/preview_sweep_runs/single_line_full_matrix_stress_batch_###` output directory. Afterward, aggregate the batch summaries with:

    .venv/bin/python -c 'import json; from pathlib import Path; keys=("scenario_count","invalid_scenario_count","error_scenario_count","signable_text_clipping_risk_scenario_count","rejected_text_clipping_risk_scenario_count","signable_text_stamp_overlap_risk_scenario_count","signable_stamp_warning_scenario_count","stamp_edge_touch_scenario_count"); totals={key:0 for key in keys}; [totals.__setitem__(key, totals[key] + json.loads((path/"summary.json").read_text(encoding="utf-8")).get(key, 0)) for path in sorted(Path("artifacts/preview_sweep_runs").glob("single_line_full_matrix_stress_batch_*")) for key in keys]; print(json.dumps(totals, indent=2, sort_keys=True))'

Run `multi_line` stress:

    env QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase preview-passphrase \
      --scenario-manifest-path artifacts/preview_sweep_assets/multi_line_full_matrix_stress.json \
      --artifacts-dir artifacts/preview_sweep_runs/multi_line_full_matrix_stress

Run `wrapped_block` stress:

    env QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase preview-passphrase \
      --scenario-manifest-path artifacts/preview_sweep_assets/wrapped_block_full_matrix_stress.json \
      --artifacts-dir artifacts/preview_sweep_runs/wrapped_block_full_matrix_stress

Inspect summary counts:

    .venv/bin/python -m json.tool artifacts/preview_sweep_runs/single_line_full_matrix_stress/summary.json > /tmp/single_line_summary.pretty.json
    .venv/bin/python -m json.tool artifacts/preview_sweep_runs/multi_line_full_matrix_stress/summary.json > /tmp/multi_line_summary.pretty.json
    .venv/bin/python -m json.tool artifacts/preview_sweep_runs/wrapped_block_full_matrix_stress/summary.json > /tmp/wrapped_block_summary.pretty.json

## Validation and Acceptance

This evidence refresh is accepted when all three targeted stress matrices produce `summary.json` or complete batch summaries, the key diagnostic counts are recorded in this plan, relevant status docs are updated to match the fresh counts, and focused CLI/harness tests pass.

If fixture assets remain unavailable, this plan is accepted only as a blocked handoff document, not as a completed evidence refresh. In that state, the final report must clearly say no counts were refreshed.

## Idempotence and Recovery

The matrix commands are safe to rerun. They write under `artifacts/preview_sweep_runs/`, which is ignored by git. If a run partially writes artifacts and then fails, rerun into a new timestamped or suffixed directory, or remove the failed output directory outside source control.

Do not commit generated PNGs, PDFs, or full summary JSON files from `artifacts/`. Commit only concise documentation updates that record the counts and artifact paths.

## Artifacts and Notes

Attempted command before fixture restoration:

    env QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf --certificate-path artifacts/preview_sweep_assets/test_identity.p12 --passphrase preview-passphrase --scenario-manifest-path artifacts/preview_sweep_assets/single_line_full_matrix_stress.json --artifacts-dir artifacts/preview_sweep_runs/single_line_full_matrix_stress
    FileNotFoundError: PDF does not exist: artifacts/preview_sweep_assets/sweep_fixture.pdf

No generated artifacts were produced by this failed attempt.

Available local validation:

    .venv/bin/python -m pytest -q tests/unit/test_cli_parser.py tests/unit/test_phase3_harness.py
    85 passed, 13 skipped, 1 warning in 7.72s

Compliance follow-up validation:

    .venv/bin/python -m pytest -q tests/unit/test_main_cli.py tests/unit/test_cli_parser.py tests/unit/test_phase3_harness.py
    100 passed, 13 skipped, 1 warning in 7.35s

Whitespace validation:

    git diff --check
    <no output>

## Interfaces and Dependencies

Use the existing CLI only:

    python -m foliaseal phase3-signing-preview-matrix

Do not add new Python APIs for this evidence refresh. The relevant existing implementation entry points are `src/foliaseal/__main__.py` for CLI parsing and `src/foliaseal/presentation/qt/phase3_harness.py::run_phase3_preview_matrix()` for matrix execution.

Revision note: Created 2026-05-13 by Codex to resume the recommended post-line-height-contract stress evidence refresh and record the current missing-fixture blocker.

Revision note: Updated 2026-05-13 by Codex after confirming the matrix command fails on missing local fixture assets and after running the available CLI/harness validation.

Revision note: Updated 2026-05-14 by Codex after compliance review to include the full fixture restore set, the README-current `multi_line` stress rerun, exact single-line batch fallback paths, and CLI dispatch validation.
