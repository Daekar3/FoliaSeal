# Phase 3 Acceptance Governance Upgrade

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

After this change, a Phase 3 harness run will no longer be treated as meaningful evidence just because it printed success text. The harness will classify every run as an engineering run, gate candidate, or release-gating pass, and it will validate the JSON evidence for internal contradictions before the run is treated as acceptance evidence. Contributors and agents will also have explicit repository-local rules for keeping behavior changes, evidence refreshes, and status/documentation updates separated.

The user-visible proof is straightforward: run `foliaseal phase3-signing-harness` and inspect the generated JSON and Markdown artifacts. They will now include gate status and evidence-validation results. Run the new validation CLI against an existing capture file and it will report whether the artifact is internally consistent enough to count toward a gate.

## Progress

- [x] (2026-04-03 23:02Z) Read `.agent/PLANS.md`, `artifacts/team_assessment_2026-04-03.md`, the current harness code, and the policy/docs files that need to stay aligned.
- [x] (2026-04-03 23:19Z) Implemented the evidence contract validator and gate classification in application/harness code.
- [x] (2026-04-03 23:19Z) Updated the generated Phase 3 results artifact so it records gate verdict, validation summary, and required-artifact status.
- [x] (2026-04-03 23:19Z) Added a CLI command that validates an existing Phase 3 harness JSON capture without rerunning the GUI.
- [x] (2026-04-03 23:19Z) Updated `README.md`, `docs/pdf_signing_app_feasibility.md`, `docs/ExecPlans/phase3_parallel_plan.md`, `artifacts/phase3_fr3b_acceptance_checklist.md`, `artifacts/phase3_fr3b_acceptance_results.md`, `Agents.md`, and `.agent/PLANS.md` so they describe one authoritative gating model.
- [x] (2026-04-03 23:19Z) Added regression tests for evidence validation and results rendering, then ran focused verification.

## Surprises & Discoveries

- Observation: the current harness already captures nearly all of the information needed for a machine-validated evidence contract; the main missing piece is the validator and the gate classification.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` already emits preview state, request snapshots, backend reservation diagnostics, output signature metadata, and visible-appearance extraction data.

- Observation: `README.md` already warns that harness success is not final acceptance, but the warning is only prose and is not backed by an actual contract or verdict in the generated artifacts.
  Evidence: the current Phase 3 harness section says the harness "does not prove final Phase 3 readiness on its own" but no gate tier is emitted into JSON or Markdown.

- Observation: the current capture file in `artifacts/phase3_harness_capture.json` already demonstrates the value of the new validator; the run is coherent, but it is still non-gating because it never submitted a sign request and the acceptance-results file was not written.
  Evidence: `foliaseal phase3-signing-harness-validate --summary-json-path artifacts/phase3_harness_capture.json` reports `engineering_run` / `non_gating` with warnings and no contradictions.

## Decision Log

- Decision: keep the evidence validator in a new application-layer module instead of burying the rules in the Qt harness.
  Rationale: the contract needs to be testable and reusable from both the interactive harness and a non-GUI validation CLI.
  Date/Author: 2026-04-03 / Codex

- Decision: classify runs into `engineering_run`, `gate_candidate`, and `release_gate_passed`, but keep explicit validation errors/warnings separate from the tier.
  Rationale: the team assessment asks for both a tiered acceptance model and machine validation. Separating classification from validation lets the harness stay useful for debugging while still rejecting contradictory artifacts for gating.
  Date/Author: 2026-04-03 / Codex

- Decision: keep the first implementation Linux-only and Phase-3-specific.
  Rationale: `Agents.md` and the current product scope explicitly forbid speculative cross-platform process expansion.
  Date/Author: 2026-04-03 / Codex

## Outcomes & Retrospective

The harness/reporting path now proves when a run is only engineering evidence versus when it is suitable to enter gate review. The new evidence contract lives in application code, the Phase 3 harness emits its verdict into both JSON and Markdown, and the CLI can validate an existing capture file without relaunching the GUI. The repo guidance is also aligned: the long-lived docs define the release-gating model, and the contributor/agent guidance now states the stricter change-slicing rules explicitly.

The remaining boundary is intentional. Automation can promote a run to `gate_candidate`, but `release_gate_passed` still belongs in the FR-3B worksheet after manual review.

## Context and Orientation

The interactive Phase 3 acceptance workflow lives in `src/foliaseal/presentation/qt/phase3_harness.py`. That file defines `Phase3HarnessCapture`, serializes it to JSON, and generates the Markdown worksheet seeded from `artifacts/phase3_fr3b_acceptance_checklist.md`. The command-line entry point lives in `src/foliaseal/__main__.py`, where the current `phase3-signing-harness` command launches the Qt flow.

The policy source of truth for release and acceptance work is `docs/pdf_signing_app_feasibility.md`. The current Phase 3 coordination document is `docs/ExecPlans/phase3_parallel_plan.md`. The short operator-facing entry point is `README.md`. Agent execution guidance lives in `Agents.md`, and ExecPlan maintenance rules live in `.agent/PLANS.md`.

The key missing concept is an evidence contract: a set of machine-checkable rules saying whether a harness capture is internally coherent enough to count as acceptance evidence. A gate tier then classifies the run: an engineering run is useful for debugging, a gate candidate has the required artifacts and consistent evidence, and a release-gating run is a gate candidate whose worksheet records an explicit FR-3B pass.

## Plan of Work

First, add `src/foliaseal/application/qa_evidence_contract.py`. That module will define a small validation snapshot data structure and functions that inspect a Phase 3 harness capture payload for contradictions such as “signing succeeded but the output file is missing” or “preview and request disagree on layout template”. It will also derive the acceptance tier and gate verdict.

Second, extend `src/foliaseal/presentation/qt/phase3_harness.py`. `Phase3HarnessCapture` will gain fields for the evidence-contract version, validation pass/fail summary, acceptance tier, and gate verdict. The harness will build the capture as it does today, run the validator, embed the results into the capture, and include a human-readable validation summary at the top of the generated Markdown. This must not make the harness brittle; even an invalid run should still emit artifacts that explain what is wrong.

Third, add a small CLI command in `src/foliaseal/__main__.py` that loads an existing Phase 3 harness JSON file and runs the validator without launching the GUI. This gives the repo a lightweight CI/review path for already-recorded artifacts.

Fourth, update the long-lived guidance files so the repo has one consistent story: `docs/pdf_signing_app_feasibility.md` defines the release-gating model, `README.md` gives the short operator-facing rule, `docs/ExecPlans/phase3_parallel_plan.md` says no Phase 3 completion claim is valid without a release-gating run, the acceptance checklist/results files explicitly distinguish required-for-gate evidence from manual qualitative notes, and `Agents.md` plus `.agent/PLANS.md` define the stricter slicing policy.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Implement the validator and harness wiring:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py

Validate lint for the touched files:

    .venv/bin/ruff check src/foliaseal/application/qa_evidence_contract.py src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/__main__.py tests/unit/test_phase3_harness.py

Validate an existing capture without relaunching the GUI:

    .venv/bin/python -m foliaseal phase3-signing-harness-validate \
      --summary-json-path artifacts/phase3_harness_capture.json

Expected command behavior after implementation:

    Phase 3 evidence contract
    - acceptance tier: engineering_run
    - gate verdict: non_gating
    - validation passed: yes

## Validation and Acceptance

The new behavior is accepted when all of the following are true:

- Running `foliaseal phase3-signing-harness` writes JSON/Markdown artifacts that include an evidence-validation summary, acceptance tier, and gate verdict.
- Running `foliaseal phase3-signing-harness-validate --summary-json-path <file>` on a contradictory capture fails clearly or reports a failed validation verdict.
- A capture with internally consistent success state is classified at least as a gate candidate.
- The generated Markdown distinguishes non-gating runs from release-gating runs instead of only listing generic observations.
- The updated docs consistently say that terminal success alone is non-gating.
- `Agents.md` and `.agent/PLANS.md` both describe the stricter change-slicing policy in compatible language.

## Idempotence and Recovery

This work is additive. Re-running the validator against the same JSON file is safe. Re-running the harness will overwrite the selected JSON/Markdown outputs with fresh capture data, which is already how the current workflow behaves. If a test fails mid-implementation, fix the code and rerun the same commands; no destructive recovery step is required.

## Artifacts and Notes

The most important artifacts produced by this work are:

- `artifacts/phase3_harness_capture.json`, now enriched with gate/evidence status
- `artifacts/phase3_fr3b_acceptance_results.md`, now enriched with gate/evidence summary
- the new validator CLI output for an existing capture file

## Interfaces and Dependencies

In `src/foliaseal/application/qa_evidence_contract.py`, define a plain dataclass result with this shape:

    @dataclass(frozen=True)
    class EvidenceContractEvaluation:
        contract_version: str
        acceptance_tier: str
        gate_verdict: str
        passed: bool
        errors: tuple[str, ...]
        warnings: tuple[str, ...]

The module must expose a function that accepts a JSON-like capture payload and returns `EvidenceContractEvaluation`.

In `src/foliaseal/presentation/qt/phase3_harness.py`, `Phase3HarnessCapture` must expose fields for the evaluation result, and `build_phase3_checklist_results_markdown()` must render them near the top of the file.

In `src/foliaseal/__main__.py`, add a `phase3-signing-harness-validate` command that loads an existing JSON file, runs the validator, and prints a concise verdict summary.

Revision note: created on 2026-04-03 to implement the team assessment’s acceptance-governance recommendations directly in harness code, docs, and contributor guidance.
