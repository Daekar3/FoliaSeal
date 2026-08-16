# Readiness states, caveats, and next-action guidance

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can see ordered readiness states with one plain-language caveat or next action in the real FoliaSeal GUI. It is mapped to UI_SPEC section 11 and acceptance scenarios 2 and 5. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [ ] docs/ExecPlans/ui_signing_rail_stage_status_execplan.md
- [ ] docs/ExecPlans/ui_certificate_selection_readiness_execplan.md
- [ ] docs/ExecPlans/ui_signature_field_targeting_profiles_execplan.md
- [ ] docs/ExecPlans/ui_preview_fidelity_fit_validation_execplan.md
- [x] docs/ExecPlans/ui_readiness_projection_contract_execplan.md — prerequisite typed readiness
  projection and action vocabulary are implemented; this parent remains open for document-safety
  input and full rail state/action integration.

## Progress

- [x] (2026-08-10) Explorer review confirmed that certificate readiness is already implemented,
  while the action coordinator still derives stage text from untyped readiness callbacks; the
  typed projection is split into `ui_readiness_projection_contract_execplan.md`.
- [x] (2026-08-10) Audit current behavior and add a failing focused test; the pure projection now
  owns the ordered readiness vocabulary.
- [x] (2026-08-10) Implement the smallest complete model/application/Qt path through the setup
  port, panel adapter, action coordinator, and shell fixtures.
- [x] (2026-08-10) Retire the migrated readiness callback pair from production callers; no new
  product-facing acceptance nomenclature or compatibility adapter was introduced.
- [x] (2026-08-10) Run focused, regression, and bounded GUI validation; clean owned processes and
  temporary configuration artifacts.
- [x] (2026-08-10) Update this plan and relevant docs, then commit the child slice.
- [x] (2026-08-10) Add a typed document-source monitor at workspace composition, feed its
  changed/missing/unknown decision into the ordered readiness projection, and cover the rail
  blocker without claiming Reload/Locate behavior that belongs to the safe-links/lifecycle child.
- [x] (2026-08-10) Enforce the same source-safety decision at direct workflow request
  construction, so headless callers cannot sign a changed, missing, or unverifiable source.
- [x] (2026-08-10) Add the missing post-write state projection required by UI_SPEC §11:
  a preserved `POST_VERIFY_FAILED` result renders as `Saved but not verified`, disables a new
  signing attempt until recovery is resolved, and retains Verify again, Return to draft, and Open
  preserved copy as the truthful recovery actions. The typed `SigningActionState.status` keeps
  this distinct from ordinary `signing_failed` results.
- [x] (2026-08-10) Focused action-coordinator/sidebar/rail validation passed (`135 passed` before
  the final full-suite run); the coordinator test proves the preserved-artifact discriminator and
  the real offscreen rail test proves the heading, warning, disabled Sign button, and Verify again
  recommendation. The synthetic rail state is intentionally a rendering-boundary test, not a
  replacement for coordinator transition coverage.
- [x] (2026-08-10) Final validation passed: focused action-coordinator/sidebar/rail coverage is
  `135 passed`, full regression is `1482 passed, 20 skipped, 1 warning`, Ruff, `pip check`, and
  `git diff --check` are clean, and no owned Qt/test process or temporary FoliaSeal root remains.

## Surprises & Discoveries

- Observation: readiness is derived by the action coordinator and sidebar, so caveats must remain
  attached to the same state that gates Sign and save rather than being decorative status text.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible readiness states, caveats, and next-action guidance outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: treat document safety as the first readiness blocker, but keep reload/locate/ignore
  mutations outside this slice. A composition-owned source monitor supplies an immutable decision
  to the panel; the future safe-links/lifecycle child owns the condition-only banner and
  draft-preserving recovery operation.
  Rationale: UI_SPEC WF04 requires document safety to precede setup, while the current viewer has no
  safe reload seam. This adds truthful blocking without silently discarding or replacing a draft.
  Date/Author: 2026-08-10 / Codex
- Decision: project a preserved `FailureCode.POST_VERIFY_FAILED` result as `Saved but not verified`
  before ordinary readiness text; keep the requested output untrusted and disable Sign and save
  until Verify again succeeds or the user returns to the draft.
  Rationale: UI_SPEC §11 and WF05 require a distinct state for bytes written without successful
  local verification. A generic signing failure or ready-to-sign state would either hide recovery
  actions or imply that the unverified artifact is safe to use.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The typed readiness child supplies one ordered state and recommended action to the rail while
preserving signed/recovery/no-document precedence. The coordinator now adds the typed
`saved_but_not_verified`/`signing_failed` distinction for terminal signing results. The composition now captures source identity,
the panel prioritizes changed/missing/unknown safety before setup, and direct workflow request
construction rejects unresolved source safety. Reload/locate/ignore, condition-only banners,
full appearance/fit readiness vocabulary, asynchronous signing progress, and the remaining rail
state-machine work remain assigned to the other children.

## Context and Orientation

The relevant code is signing_action_coordinator.py; signing_workspace_sidebar.py; signing_workspace_diagnostics.py; readiness tests. FoliaSeal is a Python/Qt Linux PDF signing application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “acceptance” names identify legacy
evidence/harness infrastructure and must not be introduced into ordinary product UI or new primary
contracts; production backend/evidence imports may be renamed only after a neutral migration proves
the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named modules, focused tests,
bounded ignored local evidence, and minimum truthful documentation. Do not mix unrelated evidence
rebaselines, V2 features, or packaging work.

## Plan of Work

Implement the exact readiness state vocabulary and ordered evaluation: document safety, preset, certificate, placement, appearance content/glyph/fit, then Ready. Keep promptable password/output path outside readiness blockers and show one plain-language recommended action with secondary technical details. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.

## Milestones

Milestone 1 defines the readiness state model and caveat tests. Milestone 2 wires one state source
to rail labels and action enablement. Milestone 3 proves blocked, warning, and ready states in the
GUI and records the evidence handoff.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'Readiness|Ready|Signing|Verified|failed|caveat' src/foliaseal/presentation/qt/signing_action_coordinator.py src/foliaseal/presentation/qt/signing_workspace_sidebar.py
    .venv/bin/pytest -q tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_signing_workspace_sidebar.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the stated user-visible behavior plus a mandatory Qt-test or display-backed
walkthrough. Record the exact input sequence, widget state, expected observation, evidence path, and
cleanup result; the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance is behavioral: The rail distinguishes no document, preset required, setup required, ready, signing, signed/verified, saved/unverified, and failed; caveats do not displace Ready and self-signed trust language is honest. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement and
`docs/ui/sign-and-save-states-exploratory.svg` state-row ownership, exact focused test command/result, readiness-state input sequence and observed next
action, evidence path and cleanup result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

Historical evidence from the source-safety increment: the focused source/readiness/action set was
`49 passed`; the full suite was `1398 passed, 20 skipped, 1 warning`; Ruff, `pip check`, and
`git diff --check` passed. The offscreen
properties-panel integration test observes a changed source and asserts the `document_safety` /
`review_document_safety` state before setup. The bounded CLI walkthrough exits at the known
isolated `SingleInstanceUnavailable` endpoint before window creation; its exact temporary root is
removed and process inspection finds no FoliaSeal/PySide6 process. A display-backed
banner/reload walkthrough remains deferred to the safe-links/lifecycle children.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The source-safety increment is exercised by
`tests/unit/test_document_source_monitor.py` and
`tests/integration/test_readiness_caveats_status.py`; the final behavior
must be exercised by tests/unit/test_qt_signing_action_coordinator.py,
tests/unit/test_signing_workspace_sidebar.py, and that integration test. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
