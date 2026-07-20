# Text Line-Height Stress Evidence Refresh ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this evidence refresh, FoliaSeal has a current characterization of the local compact preview-fixture corpus for the `single_line`, `multi_line`, and `wrapped_block` stress families. The user-visible value is scoped confidence that those currently available signable scenarios render without the reported diagnostic risks; this slice does not claim to reduce or resolve the historical large-corpus clipping clusters.

This slice is an evidence refresh, not a rendering behavior change. It should rerun the three stress families that README currently records as red: `single_line_full_matrix_stress`, `multi_line_full_matrix_stress`, and `wrapped_block_full_matrix_stress`. It must not mix in backend, preview renderer, manifest, or fixture-generation changes unless a separate follow-up ExecPlan is created.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/text_line_height_contract_execplan.md` is complete and the shared structural line-bound helper has landed in commit `163926f`.
- [x] The repository documents local stress manifests and preview fixture assets under `artifacts/preview_sweep_assets/`.
- [x] (2026-07-19) Local fixture assets are present in this workspace: `artifacts/preview_sweep_assets/sweep_fixture.pdf`, `test_identity.p12`, `stamp_wide.png`, `stamp_tall.png`, `stamp_script.png`, `single_line_full_matrix_stress.json`, `multi_line_full_matrix_stress.json`, and `wrapped_block_full_matrix_stress.json`.

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
- [x] (2026-05-14T00:20Z) Tightened the single-line batch fallback to an attempt-scoped output directory and added direct CLI dispatch coverage for `phase3-signing-harness-validate`.
- [x] (2026-05-14T00:35Z) Tightened the single-line temporary manifest directory to the same attempt scope and added negative `phase3-signing-harness-validate` CLI coverage for failed evidence contracts.
- [x] (2026-07-19) Rechecked the restored local fixture workspace and current manifests. Each stress manifest has nine scenarios, so this run is a 27-scenario compact-corpus refresh rather than a rerun of the historical large corpus.
- [x] (2026-07-19) Ran all three current compact stress matrices offscreen. Each wrote a summary with `scenario_count=9`, `error_scenario_count=0`, and zero signable/rejected clipping, overlap, stamp-warning, and edge-touch counts.
- [x] (2026-07-19) Reconciled this ExecPlan and `README.md` to report the compact-corpus result as non-comparable to the preserved historical large-corpus evidence. Historic stress plans remain unchanged.
- [x] (2026-07-19) Ran current focused validation: `114 passed, 1 warning`; Ruff and `git diff --check` passed.
- [ ] Commit the completed evidence refresh.

## Surprises & Discoveries

- Observation: the prior workspace was missing fixtures, but the current workspace contains the full local compact fixture family.
  Evidence: on 2026-07-19, `artifacts/preview_sweep_assets/` contained `sweep_fixture.pdf`, `test_identity.p12`, all three stamp PNGs, and all three target stress manifests.

- Observation: each current target manifest contains nine scenarios, not the large scenario counts recorded in historical stress plans.
  Evidence: the 2026-07-19 explorer inspected the three JSON manifests and found nine scenarios in each. Fresh counts therefore describe the current compact corpus and must not overwrite or be compared as like-for-like replacements for historic large-corpus counts.

- Observation: The preview matrix command fails cleanly before running any scenarios when the fixture PDF is missing.
  Evidence: running `phase3-signing-preview-matrix` for `single_line_full_matrix_stress` raised `FileNotFoundError: PDF does not exist: artifacts/preview_sweep_assets/sweep_fixture.pdf`.

## Decision Log

- Decision: Rerun `single_line_full_matrix_stress`, `multi_line_full_matrix_stress`, and `wrapped_block_full_matrix_stress`.
  Rationale: The prior remediation note recorded `multi_line_full_matrix_stress_v3` as clean, but README and `docs/ExecPlans/real_world_stress_coverage_execplan.md` currently record stress `multi_line` as red with `18` signable text clipping risks. The evidence refresh must resolve the current project status, so it should include all three red stress families while still excluding unrelated baseline matrices.
  Date/Author: 2026-05-13 / Codex

- Decision: Do not synthesize replacement fixture assets in this slice.
  Rationale: The README treats `artifacts/preview_sweep_assets/` as conventional local QA fixture input. Recreating ad hoc PDFs, certificates, or manifests would risk comparing against a different corpus and producing misleading counts.
  Date/Author: 2026-05-13 / Codex

- Decision: run the three current compact manifests monolithically and reserve the old single-line batch procedure only for an unexpected runtime failure.
  Rationale: each manifest now has nine scenarios, so batching would add complexity without reducing risk. A passing process is insufficient by itself: each summary must report nine scenarios and zero `error_scenario_count`.
  Date/Author: 2026-07-19 / Codex

- Decision: record compact-corpus results as new scoped evidence, without replacing historical large-corpus numbers in related plans.
  Rationale: the fixture scope materially differs. README may report the current compact result only when it is labelled as such; historical evidence remains useful and must not be falsely treated as directly comparable.
  Date/Author: 2026-07-19 / Codex

## Outcomes & Retrospective

This slice was historically blocked on missing local fixture assets. Those inputs are now present, and the living plan has been corrected for the current compact 27-scenario corpus. On 2026-07-19 all three nine-scenario matrices completed with zero execution errors and zero reported clipping, overlap, warning, or edge-touch risks. Documentation reconciliation and focused validation are complete. This is fresh compact-corpus evidence only; it does not supersede the older large-corpus red counts. Commit remains pending.

## Context and Orientation

The preview matrix command is implemented by `src/foliaseal/__main__.py` and delegates to `run_phase3_preview_matrix()` in `src/foliaseal/presentation/qt/phase3_harness.py`. It opens a source PDF, applies each scenario from a JSON manifest, renders a headless canonical preview, writes per-scenario artifacts under `--artifacts-dir`, and writes a `summary.json` file there.

The stress manifests and fixture PDF/certificate are local QA assets under `artifacts/preview_sweep_assets/`. They are intentionally not guaranteed to be tracked source files because `artifacts/` is ignored for repository hygiene. They are present in this workspace for this refresh; a future fresh clone still needs them restored from approved local or external artifact storage before the matrix can run.

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

First, verify the current local fixture inputs under `artifacts/preview_sweep_assets/`. This workspace has all required files and each target manifest contains nine scenarios. Keep the baseline manifests untouched; this slice does not generate or edit fixtures or manifests.

Second, run the three targeted preview matrices with `QT_QPA_PLATFORM=offscreen` and dedicated output directories under `artifacts/preview_sweep_runs/`. Validate each summary has exactly nine scenarios and zero scenario errors. If the `single_line` matrix unexpectedly aborts before writing `summary.json`, use the retained batch fallback without editing the checked-in generator or source manifests.

Third, inspect each `summary.json` and record the diagnostic counts in `Artifacts and Notes`. Preserve the prior remediation counts and README's historical large-corpus summary as non-comparable context. Update README only with the explicitly scoped compact-corpus result; do not frame a difference in counts as remediation of the historical clusters.

Fourth, run focused verification for the CLI/harness surfaces. This includes direct `test_main_cli.py` dispatch coverage for both `phase3-signing-preview-matrix` and `phase3-signing-harness-validate`, plus parser and harness behavior coverage:

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

If the monolithic `single_line` run aborts before writing `summary.json`, generate temporary batches from the restored manifest and run them under an attempt-scoped directory:

    export SINGLE_LINE_BATCH_RUN=artifacts/preview_sweep_runs/single_line_full_matrix_stress_batches_$(date -u +%Y%m%dT%H%M%SZ)
    export SINGLE_LINE_BATCH_MANIFESTS=/tmp/foliaseal_single_line_stress_batches_$(date -u +%Y%m%dT%H%M%SZ)
    .venv/bin/python -c 'import json, os; from pathlib import Path; src=Path("artifacts/preview_sweep_assets/single_line_full_matrix_stress.json"); out=Path(os.environ["SINGLE_LINE_BATCH_MANIFESTS"]); out.mkdir(parents=True, exist_ok=True); payload=json.loads(src.read_text(encoding="utf-8")); scenarios=payload["scenarios"]; size=100; [((out / f"single_line_full_matrix_stress_batch_{idx:03d}.json").write_text(json.dumps({**payload, "scenarios": scenarios[start:start+size]}, indent=2), encoding="utf-8")) for idx,start in enumerate(range(0, len(scenarios), size), 1)]'

Run each batch to a stable output directory:

    env QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase preview-passphrase \
      --scenario-manifest-path "$SINGLE_LINE_BATCH_MANIFESTS"/single_line_full_matrix_stress_batch_001.json \
      --artifacts-dir "$SINGLE_LINE_BATCH_RUN"/single_line_full_matrix_stress_batch_001

Repeat for every generated `"$SINGLE_LINE_BATCH_MANIFESTS"/single_line_full_matrix_stress_batch_*.json` file, incrementing the matching `"$SINGLE_LINE_BATCH_RUN"/single_line_full_matrix_stress_batch_###` output directory. Do not rerun manifests from prior attempts and do not aggregate across sibling batch directories from prior attempts. Afterward, aggregate only the current attempt's batch summaries with:

    .venv/bin/python -c 'import json, os; from pathlib import Path; root=Path(os.environ["SINGLE_LINE_BATCH_RUN"]); keys=("scenario_count","invalid_scenario_count","error_scenario_count","signable_text_clipping_risk_scenario_count","rejected_text_clipping_risk_scenario_count","signable_text_stamp_overlap_risk_scenario_count","signable_stamp_warning_scenario_count","stamp_edge_touch_scenario_count"); totals={key:0 for key in keys}; [totals.__setitem__(key, totals[key] + json.loads((path/"summary.json").read_text(encoding="utf-8")).get(key, 0)) for path in sorted(root.glob("single_line_full_matrix_stress_batch_*")) for key in keys]; print(json.dumps(totals, indent=2, sort_keys=True))'

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

This evidence refresh is accepted when all three targeted stress matrices produce `summary.json` with exactly nine scenarios and `error_scenario_count == 0`, the key diagnostic counts are recorded in this plan as compact-corpus evidence, relevant status docs preserve the historical large-corpus numbers as non-comparable evidence, and focused CLI/harness tests pass. It does not accept or reject the historical large-corpus findings.

If fixtures are unavailable in a future workspace, this plan is accepted only as a blocked handoff document, not as a completed evidence refresh. In that state, the final report must clearly say no counts were refreshed.

## Idempotence and Recovery

The matrix commands are safe to rerun. They write under `artifacts/preview_sweep_runs/`, which is ignored by git. If a run partially writes artifacts and then fails, rerun into a new timestamped or suffixed directory, or remove the failed output directory outside source control.

Do not commit generated PNGs, PDFs, or full summary JSON files from `artifacts/`. Commit only concise documentation updates that record the counts and artifact paths.

## Artifacts and Notes

Attempted command before fixture restoration:

    env QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf --certificate-path artifacts/preview_sweep_assets/test_identity.p12 --passphrase preview-passphrase --scenario-manifest-path artifacts/preview_sweep_assets/single_line_full_matrix_stress.json --artifacts-dir artifacts/preview_sweep_runs/single_line_full_matrix_stress
    FileNotFoundError: PDF does not exist: artifacts/preview_sweep_assets/sweep_fixture.pdf

No generated artifacts were produced by this failed attempt.

Current compact-corpus evidence (2026-07-19):

    single_line_full_matrix_stress: scenario_count=9, error_scenario_count=0,
      signable_text_clipping_risk_scenario_count=0,
      rejected_text_clipping_risk_scenario_count=0,
      signable_text_stamp_overlap_risk_scenario_count=0,
      signable_stamp_warning_scenario_count=0, stamp_edge_touch_scenario_count=0
    multi_line_full_matrix_stress: scenario_count=9, error_scenario_count=0,
      signable_text_clipping_risk_scenario_count=0,
      rejected_text_clipping_risk_scenario_count=0,
      signable_text_stamp_overlap_risk_scenario_count=0,
      signable_stamp_warning_scenario_count=0, stamp_edge_touch_scenario_count=0
    wrapped_block_full_matrix_stress: scenario_count=9, error_scenario_count=0,
      signable_text_clipping_risk_scenario_count=0,
      rejected_text_clipping_risk_scenario_count=0,
      signable_text_stamp_overlap_risk_scenario_count=0,
      signable_stamp_warning_scenario_count=0, stamp_edge_touch_scenario_count=0

The summaries are ignored local artifacts under `artifacts/preview_sweep_runs/`. The
current nine-scenario manifests are not comparable to the historical large corpus,
so the result must be described as a scoped compact-fixture refresh.

Available local validation:

    .venv/bin/python -m pytest -q tests/unit/test_cli_parser.py tests/unit/test_phase3_harness.py
    85 passed, 13 skipped, 1 warning in 7.72s

Compliance follow-up validation:

    .venv/bin/python -m pytest -q tests/unit/test_main_cli.py tests/unit/test_cli_parser.py tests/unit/test_phase3_harness.py
    100 passed, 13 skipped, 1 warning in 7.35s

Second compliance follow-up validation:

    .venv/bin/python -m pytest -q tests/unit/test_main_cli.py tests/unit/test_cli_parser.py tests/unit/test_phase3_harness.py
    101 passed, 13 skipped, 1 warning in 7.45s

    .venv/bin/python -m ruff check tests/unit/test_main_cli.py
    All checks passed!

Third compliance follow-up validation:

    .venv/bin/python -m pytest -q tests/unit/test_main_cli.py tests/unit/test_cli_parser.py tests/unit/test_phase3_harness.py
    102 passed, 13 skipped, 1 warning in 7.64s

    .venv/bin/python -m ruff check tests/unit/test_main_cli.py
    All checks passed!

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

Revision note: Updated 2026-05-14 by Codex after the second compliance review to scope single-line batch aggregation to one attempt and add `phase3-signing-harness-validate` CLI dispatch coverage.

Revision note: Updated 2026-05-14 by Codex after the final compliance review to also scope temporary single-line batch manifests to one attempt and test the validate subcommand's failure path.

Revision note: Updated 2026-07-19 by Codex after a fresh explorer review found the formerly missing fixtures restored but the current manifests reduced to nine scenarios per family. The plan now treats this as a compact-corpus refresh, requires zero scenario errors, and preserves historic large-corpus evidence as non-comparable context.

Revision note: Updated 2026-07-19 by Codex after the compact refresh completed. README and this plan now distinguish the nine-scenario-per-family result from historical large-corpus evidence; focused validation and documentation reconciliation are complete, with commit still pending.
