# Validation Architecture Simplification

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`. It records the decision to keep one authoritative backend validation gate while ruthlessly eliminating unnecessary UI-layer validation complexity.

## Purpose / Big Picture

After this change, the signing shell should still prevent sign attempts that would fail in the backend, but it should stop behaving like a second preview interpreter. The preview remains visual. The backend remains the authority on whether a visible signature can actually be built. The Validation box becomes a thin, factual summary of prerequisites and backend fit results rather than a blended pseudo-model that duplicates preview behavior.

The user-visible outcome is simpler and easier to trust: the preview shows what the signature looks like, the Validation box only tells the user whether signing is blocked for an objective reason, and the submit gate matches the same backend semantics that actual signing uses.

## Progress

- [x] (2026-04-05 21:03Z) Created this ExecPlan after agreeing on the architectural direction: keep backend validation, remove unnecessary preview-validation complexity.
- [x] (2026-04-05 21:05Z) Recorded the architectural decision in repo docs and added an explicit complexity-bias rule to `Agents.md`.
- [x] (2026-04-05 21:14Z) Simplified the signing shell so it no longer rewrites preview state into a merged preview-plus-control-issue object.
- [x] (2026-04-05 21:16Z) Updated shell tests to reflect the thinner validation contract and preserved backend-owned submit safety.
- [x] (2026-04-05 21:18Z) Ran targeted and full verification, then updated this plan with outcomes.
- [x] (2026-04-05 22:10Z) Carried the simplification through the workflow/backend seam so preview text composition and pre-submit fit validation now use the same shared layout-text builder.
- [x] (2026-04-05 22:17Z) Restored the existing wrapped-block grouping contract and show-field-names behavior inside the shared composition path so the simplification would not alter output requirements.
- [x] (2026-04-05 22:19Z) Updated harness fixtures to reflect true no-wrap `single_line` behavior and reran focused plus full verification.

## Surprises & Discoveries

- Observation: the current source tree does not contain stray code changes from the earlier architecture-review sub-agent.
  Evidence: `git status --short` showed only generated harness artifacts under `artifacts/`.

- Observation: the feeling of “three code paths” comes mainly from the shell merging preview issues with control issues in `SignaturePropertiesPanel._current_preview()`, then formatting that blended result as validation text.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py` currently uses `_current_preview()` to append `_control_issue` onto `preview.issues` and to override `can_submit` before rendering validation text.

- Observation: the workflow preview object still contains draft-validation issues and `can_submit`, but the shell no longer mutates that object or treats it as a second validation model.
  Evidence: after the change, `SignaturePropertiesPanel.preview` returns `self._workflow.preview()` directly, while validation text is formatted from a thin combination of workflow issues plus any immediate control-building failure.

- Observation: the deeper duplication was not only in the shell; preview detail-text composition and backend fit validation were also composing visible-signature text separately.
  Evidence: `SigningDraftWorkflow._build_preview_detail_text()` previously composed preview text independently of `_build_stamp_text()` and `_visible_signature_fit_issues()`, which allowed preview and pre-submit fit semantics to drift.

- Observation: the first pass at unification exposed two stable output contracts that had to be preserved explicitly rather than “simplified away”: wrapped-block tail grouping and `show_field_names` label prefixes.
  Evidence: `tests/unit/test_qt_signing_shell.py` failed until the shared composition path reproduced the historical three-line wrapped-block grouping and the `Field label: value` fragment format.

## Decision Log

- Decision: keep the backend fit check and submit gate.
  Rationale: the backend fit check in `src/foliaseal/application/phase3_signing_backend.py` catches real output/signing failures that preview alone cannot guarantee away.
  Date/Author: 2026-04-05 / Codex

- Decision: simplify the shell rather than removing validation entirely.
  Rationale: removing validation would shift genuine failures from pre-submit to submit-time. The simpler and safer design is to keep one backend-owned gate but make the UI around it thinner and more factual.
  Date/Author: 2026-04-05 / Codex

- Decision: bias documentation and agent guidance toward ruthless elimination of complexity in architectural decisions.
  Rationale: the recent regression wave showed that extra layers and threshold-driven side paths make the system harder to reason about and easier to destabilize.
  Date/Author: 2026-04-05 / Codex

- Decision: unify preview detail-text composition and pre-submit backend fit input around one shared visible-signature text-layout helper.
  Rationale: the user requested that preview layout rules live in exactly one place whose output then feeds the structure determining whether real signing would fail before submit-time. Sharing the text-layout composition path removes a major source of preview-vs-validation drift without weakening backend authority.
  Date/Author: 2026-04-05 / Codex

## Outcomes & Retrospective

This slice succeeded.

What changed:

- `SignaturePropertiesPanel.preview` now returns the workflow preview directly instead of a shell-mutated replacement object.
- The shell no longer merges `_control_issue` into preview state or recomputes preview `can_submit`.
- The Validation box now shows a thin factual status:
  - `Place a signature on the page to continue.`
  - `Ready to sign.`
  - `Will fail to sign: ...` for the backend fit failure
  - explicit `ERROR <code>: <message>` lines for other objective blocking issues
- `SigningDraftWorkflow` now builds preview `detail_text` and the pre-submit fit-check `stamp_text` from the same shared backend-owned text-layout helper.
- The shared helper preserves existing output behavior:
  - `single_line` remains one joined `|` row,
  - `wrapped_block` still groups into first line / second line / joined tail line,
  - `show_field_names` still yields `Field label: value` fragments.
- Workflow validation now degrades invalid stamp paths into ordinary draft issues instead of throwing raw exceptions during preview evaluation.
- Harness fixture widths were widened where needed so tests continue to assert output requirements rather than an old narrow-box implementation detail.

What did not change:

- the backend fit gate still blocks sign attempts that would fail in actual signing
- workflow-level draft validation still exists
- preview rendering behavior remains intact

Verification results:

- `ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py README.md docs/ExecPlans/phase3_parallel_plan.md Agents.md .agent/validation_architecture_simplification_execplan.md`
- `pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py`
- `pytest -q`
- `.venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/signing_draft_workflow.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_draft_workflow.py .agent/validation_architecture_simplification_execplan.md README.md docs/ExecPlans/phase3_parallel_plan.md Agents.md`
- `.venv/bin/pytest -q tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_signing_backend.py tests/unit/test_phase3_harness.py tests/unit/test_signing_preview_renderer.py`
- `.venv/bin/pytest -q`

Observed outcome:

- targeted suite: `125 passed`
- full suite: `314 passed`
- deeper seam-unification focused suite: `136 passed`
- full suite after seam unification: `314 passed`

Retrospective:

- The most valuable simplification in this slice was not deleting validation, but deleting the shell’s extra interpretation layer.
- The most valuable follow-on simplification was deleting the separate preview-text composition logic and making preview/feed-forward fit validation consume the same shared text-layout output.
- Preserving output requirements while simplifying architecture required treating existing formatting behavior as contract, not as optional implementation detail.
- A later slice may still choose to split validation fields out of `SigningDraftPreview` itself, but that is no longer necessary to get the user-visible complexity reduction requested here.

## Context and Orientation

The current signing draft has three relevant layers.

`src/foliaseal/application/signing_draft_workflow.py` builds the draft preview and structural draft-validation issues. Those issues cover things like missing placement or malformed input state. This file should remain responsible for draft prerequisites, not backend fit semantics.

`src/foliaseal/application/phase3_signing_backend.py` owns the real visible-signature feasibility check. `_visible_signature_fit_issues()` loads signing material, builds the backend stamp text/style, and returns `visible_signature_layout_unavailable` if the backend cannot produce a valid visible signature. The concrete signing executor uses the same backend logic again during actual signing. This is the authoritative guardrail.

`src/foliaseal/presentation/qt/signing_shell.py` currently blends UI control issues and workflow preview issues inside `SignaturePropertiesPanel._current_preview()`, then uses that merged object to derive `validation_text()` and submit readiness. That blending is what makes the UI feel like it has an extra validation code path.

The simplification target is not to remove validation. It is to stop treating validation as a third semantic model. The shell should render preview visually, ask the backend whether signing would fail, and then display a minimal status summary.

## Plan of Work

First, simplify `SignaturePropertiesPanel` in `src/foliaseal/presentation/qt/signing_shell.py`. Replace `_current_preview()` as the place where control issues are merged into preview data. Introduce small helper methods that separately answer:

- what the current visual preview is,
- what the current control/prerequisite issue is,
- what the effective backend/draft blocking issues are for submit gating,
- and what short validation text should be shown.

The preview object should remain what `SigningDraftWorkflow.preview()` produced, except for the shell’s widget rendering needs. It should not be rewritten into a blended validation model.

Second, keep the backend fit issue authoritative. The shell should continue to respect `preview.can_submit`, because that already reflects draft validation and backend fit checks through the workflow path. The shell should also continue to respect any immediate control-building failure such as `signature_appearance_invalid`. The resulting submit gate should be the conjunction of those two sources rather than a rewritten preview object.

Third, simplify validation text. `SignaturePropertiesPanel._format_validation_text()` should emit only short, factual strings:

- `Place a signature on the page to continue.` for the missing-rectangle case,
- `Ready to sign.` when there are no blocking issues,
- and concise objective error lines for blocking issues, especially backend fit failures.

Avoid duplicating preview semantics in the text. The Validation box should not attempt to describe aesthetic or layout judgments that are already visible in the preview widget.

Fourth, update tests in `tests/unit/test_qt_signing_shell.py` and any touched harness tests so they assert the thinner contract: preview content remains preview content, validation text remains concise and factual, and submit gating remains blocked only by objective errors.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Document the architectural decision:

    sed -n '1,220p' README.md
    sed -n '1,220p' docs/ExecPlans/phase3_parallel_plan.md
    sed -n '1,220p' Agents.md

Inspect the current shell/backend boundary:

    sed -n '330,430p' src/foliaseal/application/signing_draft_workflow.py
    sed -n '654,710p' src/foliaseal/application/phase3_signing_backend.py
    sed -n '980,1105p' src/foliaseal/presentation/qt/signing_shell.py
    sed -n '2050,2105p' src/foliaseal/presentation/qt/signing_shell.py

After edits, run:

    .venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/application/signing_draft_workflow.py tests/unit/test_qt_signing_shell.py
    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py
    .venv/bin/pytest -q

Expected success:

    All checks passed!
    ...
    <all targeted tests passed>
    ...
    <full suite passed>

## Validation and Acceptance

This change is acceptable only if all of the following are true:

- The shell still blocks sign attempts when the backend fit gate would fail.
- The preview data is no longer rewritten into a mixed preview-plus-validation object.
- The Validation box is concise and factual.
- Existing preview rendering continues to work.
- The full test suite passes.

The manual spot-check after code completion is:

    .venv/bin/python -m foliaseal phase3-signing-harness \
      --pdf-path "/path/to/representative.pdf" \
      --certificate-path "/path/to/identity.p12" \
      --passphrase "secret" \
      --summary-json-path artifacts/phase3_harness_capture.json \
      --checklist-results-path artifacts/phase3_fr3b_acceptance_results.md

Then confirm:

- the preview still renders normally,
- the Validation box says `Ready to sign.` when appropriate,
- and blocked states are phrased as objective failures rather than quasi-preview commentary.

## Idempotence and Recovery

This change is safe to rerun because it is confined to shell composition, documentation, and tests. If a simplification removes too much information from the Validation box, restore only the last factual message layer; do not reintroduce a merged preview-validation model.

## Artifacts and Notes

Baseline architectural facts before the change:

- `SigningDraftWorkflow.preview()` returns a `SigningDraftPreview` with `issues` and `can_submit`.
- `SignaturePropertiesPanel._current_preview()` currently mutates that conceptual boundary by adding `_control_issue` and recomputing `can_submit`.
- `_visible_signature_fit_issues()` in the backend is the true authority on visible-signature feasibility.

The intended result after the change:

- preview remains preview,
- validation remains factual and backend-owned,
- submit gating remains safe,
- and complexity is reduced.

That intended result is now implemented for the shell/UI layer in this repository.

## Interfaces and Dependencies

No new dependencies are allowed.

Keep using:

- `foliaseal.application.signing_draft_workflow.SigningDraftWorkflow`
- `foliaseal.application.phase3_signing_backend._visible_signature_fit_issues`
- `foliaseal.presentation.qt.signing_shell.SignaturePropertiesPanel`

Do not add a new validation abstraction layer. Simplify the existing shell logic instead.

Revision note: created on 2026-04-05 to implement the architectural decision that validation must stay backend-owned while the UI is simplified toward ruthless elimination of unnecessary complexity.

Revision note: updated on 2026-04-05 after implementation to record that the shell-level merged preview-validation path was removed, the docs were updated, and the targeted plus full test suites passed.
