# Add draft-preserving source-change recovery

This ExecPlan is a living document maintained under `.agents/skills/write-execplan/PLANS.md`.
It is a child of `docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md` and the UI compliance
parent. It implements the remaining visible source-safety behavior without adding crash recovery.

## Purpose / Big Picture

After this slice, FoliaSeal notices when the open PDF changes or disappears. A condition-only banner
blocks signing and gives the user explicit `Reload` or `Ignore` choices for a changed source, and
`Locate` or `Close` choices for a missing source. Reload and Locate validate a candidate workspace
first, transfer the authored signing draft and session credentials, mount it atomically, and only
then acknowledge the new source. Ignore acknowledges the observed source without replacing the
workspace. Cancelled or failed actions leave the current document, draft, and secrets intact.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are governing contracts.
- [x] `ui_launch_no_document_execplan.md`, `ui_single_instance_open_routing_execplan.md`, and
  `ui_signing_rail_stage_status_execplan.md` supply the existing frame, open, and readiness seams.
- [x] `ui_safe_links_source_safety_contracts_execplan.md` supplies source decisions.
- [x] `ui_readiness_caveats_status_execplan.md` blocks signing for changed/missing/unknown sources.
- [x] `ui_document_lifecycle_recovery_execplan.md` supplies dirty-draft close/open policy and
  candidate `prepare()`/`replace_prepared()` ordering.

## Progress

- [x] (2026-08-10) Explorer audit confirmed readiness already blocks unsafe source states and that
  the missing user-visible recovery actions are the next dependency-ready safety slice.
- [x] (2026-08-10) Added the Qt-free `SigningDraftSnapshot` transfer boundary covering authored placement, appearance,
  field target, output-path confirmation/authorization, setup references, and session secrets.
- [x] (2026-08-10) Added atomic Reload/Locate candidate replacement and explicit Ignore acknowledgement.
- [x] (2026-08-10) Added a condition-only banner with automatic source polling and action routing through public
  workspace/composition seams.
- [x] (2026-08-10) Added focused unit tests and real offscreen Qt coverage for changed-source Ignore,
  draft preservation, candidate replacement, and failed/cancelled-safe recovery boundaries.
- [x] (2026-08-10) Reconcile architecture, lifecycle/parent plans, and acceptance evidence.
- [x] (2026-08-10) Full validation, bounded GUI audit, and owned process/temp cleanup are complete;
  implementation commit `0d5116084` contains the complete slice.
- [x] (2026-08-10) Closeout re-ran the source-recovery focused suite (`89 passed`), the full suite
  (`1465 passed, 20 skipped, 1 warning`), Ruff, pip checks, and the bounded launch audit. The
  display-backed audit still stops at the isolated `SingleInstanceUnavailable` endpoint before
  window creation; no FoliaSeal/PySide6/pytest process or temporary audit root remained.
- [x] (2026-08-10) Compliance review corrected the notice topology and resize behavior: the
  condition-only notice is a viewer-canvas child outside the rail layout, and an event-filter hook
  repositions it when the canvas resizes; offscreen geometry coverage proves both properties.
- [x] (2026-08-10) The overlay correction, resize-aware acceptance evidence, architecture update,
  and downstream plan reconciliation were committed as the source-recovery closeout.

## Surprises & Discoveries

- Observation: `DocumentSourceMonitor` already has a pure decision and an explicit
  `acknowledge_current_source()` operation, but nothing owns the Reload/Ignore/Locate/Close UI.
  Evidence: `document_source_monitor.py` and readiness tests.
- Observation: naïvely replacing the workspace constructs a fresh `SigningDraftWorkflow` and loses
  authored values. The existing lifecycle composes candidates before mounting, so transfer must
  happen before `replace_prepared()` and after candidate validation.
  Evidence: `signing_workspace_lifecycle.py` and `SigningWorkspaceCompositionService`.
- Observation: crash recovery, autosave, and interrupted-session restoration remain unsafe to claim
  because signing transaction artifacts are not yet owned by a durable journal boundary.
  Evidence: the lifecycle parent plan's explicit deferral.

## Decision Log

- Decision: represent transfer with one application-owned immutable snapshot and one restore method;
  do not copy Qt widgets or reach through private panel fields.
  Rationale: the draft is application state and must survive candidate composition independently of
  the presentation tree.
  Date/Author: 2026-08-10 / Codex.
- Decision: preserve the old clean baseline in the snapshot so a dirty draft remains dirty after
  Reload/Locate; do not silently mark transferred edits clean.
  Rationale: source recovery must protect authored work, not hide it from Close/Exit policy.
  Date/Author: 2026-08-10 / Codex.
- Decision: poll source identity from the Qt workspace at a bounded interval and render a condition-
  only banner; never reload automatically.
  Rationale: UI_SPEC requires monitoring and explicit action while reserving permanent layout space
  for the signing workflow.
  Date/Author: 2026-08-10 / Codex.
- Decision: keep source-change recovery separate from URL activation, signing transaction artifacts,
  and acceptance evidence nomenclature.
  Rationale: each has a distinct ownership boundary and the product UI must use ordinary vocabulary.
  Date/Author: 2026-08-10 / Codex.

## Outcomes & Retrospective

Implementation is complete. Changed sources render a condition-only Reload/Ignore canvas overlay,
missing sources render Locate/Close, and AppFrame candidate replacement transfers the authored draft
and session secret before atomic mount. Focused source-monitor/workflow/AppFrame/offscreen coverage is
green (`89 passed`); the full suite is `1465 passed, 20 skipped, 1 warning`; Ruff, pip checks, and
diff checks are clean. The bounded GUI launch remains display/single-instance limited
(`SingleInstanceUnavailable` before window creation); crash journal, autosave, and interrupted-
session restoration remain explicit follow-on work. Implementation commit: `0d5116084`.

## Evidence Record

The focused command was `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
tests/unit/test_document_source_monitor.py tests/unit/test_signing_draft_workflow.py
tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py
tests/integration/test_readiness_caveats_status.py` (`89 passed`). It covers source fingerprint
decisions, direct signing refusal, snapshot/restore of authored placement/appearance/field/output
state and session passphrase, candidate validation before replacement, failed/cancelled recovery,
Ignore without remount, and the real offscreen condition-only canvas overlay. The full suite passed with
`1465 passed, 20 skipped, 1 warning`; `.venv/bin/ruff check src tests`, `.venv/bin/python -m pip
check`, and `git diff --check` passed. A bounded `foliaseal gui --pdf-path
artifacts/preview_sweep_assets/sweep_fixture.pdf` launch returned `gui_rc=1` at the isolated
  `SingleInstanceUnavailable` endpoint; the owned configuration root was removed and no matching
process remained. The overlay test also proves its viewer-canvas parent, unchanged canvas/rail/
properties-panel geometry while visible, and updated bounds after resizing the workspace. This text
surface has no SVG requirement.

## Context and Orientation

`SigningDraftWorkflow` in `src/foliaseal/application/signing_draft_workflow.py` owns the authored
placement, appearance/content, field target, output path, setup references, passphrase, and dirty
baseline. `DocumentSourceMonitor` owns metadata-only source identity. `SigningWorkspaceLifecycle`
composes and mounts a `WorkspaceHandle`; `FoliaSealAppFrame` owns File/Open/Close/Exit and is the
correct owner for candidate replacement and native dialogs. `SignaturePropertiesPanel` renders the
setup rail and readiness; `SigningWorkspaceWidget`/composition are the public path for adding a
banner and polling hook.

“Condition-only banner” means a modeless, non-modal notice that appears only while the source is
changed, missing, or unverifiable; it must not auto-reload or prevent ordinary navigation except by
the existing readiness/signing gate. Reload/Locate must validate a candidate before disposing the
current workspace. Ignore acknowledges the currently observed identity and leaves the mounted PDF
as-is. Do not introduce product-facing `acceptance` terminology.

## Change Slice

Primary change class: behavior change. The commit may include the snapshot/restore application
contract, lifecycle/frame/composition/banner wiring, focused tests, one offscreen integration test,
and minimum architecture/plan updates. Do not mix crash journals, autosave, package work, evidence
rebaselines, unrelated readiness redesign, or broad nomenclature migration.

## Plan of Work

Define `SigningDraftSnapshot` in the application layer with every value needed to preserve the
authored draft and session: input-independent signing parameters, certificate/preset references,
signature rectangle/field, appearance, placement defaults/context, output path and its explicit
confirmation/overwrite authorization, passphrase, preview fingerprint/time, and the clean baseline.
Add `snapshot_for_source_transfer()` and `restore_source_transfer(snapshot, input_pdf_path=...)`
to `SigningDraftWorkflow`. Restore must invalidate stale preview materialization, attach the
candidate's `DocumentSourceMonitor`, and leave the snapshot's dirty baseline intact.

Add AppFrame-owned `_replace_source_preserving_draft(path)` that snapshots the active workflow,
prepares the candidate through `SigningWorkspaceHost.prepare()`, restores the snapshot into the
candidate workflow, and calls `replace_prepared()` only after all validation succeeds. The method
must dispose only a failed candidate, keep the current workspace on cancellation/error, and refresh
the action state after replacement. Add `_ignore_source_change()` that acknowledges the active
monitor and refreshes readiness without replacing the mounted widget. Locate opens a standard PDF
chooser and routes its chosen path through the same preserving replacement; Close uses existing
dirty-draft policy.

Add source-action callbacks to `OpenWorkspaceCommand`, `SigningWorkspaceEnvironment`, bootstrap,
composition, and `SigningWorkspaceWidget`. `SignaturePropertiesPanel` receives these callbacks and
renders a hidden-by-default condition banner with one explanatory label and the correct Reload/
Ignore or Locate/Close buttons. Expose `refresh_source_safety()` so the workspace can update the
banner and readiness labels without duplicating policy.

Use an optional Qt `QTimer` owned by the mounted signing widget (one-second interval is sufficient)
to call `refresh_source_safety()`. Stop it during widget disposal. Tests may call the refresh method
directly to avoid timing flakiness, but the real offscreen integration test must mutate a temporary
source fingerprint, process events, observe the changed banner, choose Ignore or Reload, and assert
the banner disappears only after the explicit action.

## Milestones

### Milestone 1: prove snapshot/restore without Qt

Add red workflow tests for dirty and clean snapshots, passphrase preservation, output-path
authorization, appearance/placement transfer, and stale-preview invalidation. Implement the
application boundary until those tests pass.

### Milestone 2: wire atomic recovery and condition actions

Add frame/lifecycle tests proving candidate validation precedes replacement, Reload/Locate preserve
the current draft, Ignore acknowledges without remounting, and failed/cancelled actions leave the
old handle untouched. Add the banner callbacks through typed composition seams.

### Milestone 3: prove live offscreen monitoring and finish the slice

Run the real Qt polling/banner test, full suite, Ruff, pip checks, bounded GUI audit, compliance
review, architecture reconciliation, process/temp cleanup, and commit. Record crash recovery as the
explicit next plan rather than implying it exists.

## Concrete Steps

Run from `/home/daekar/FoliaSeal` with `.venv`.

    rg -n 'SigningDraftSnapshot|acknowledge_current_source|source_safety|QTimer|prepare\(|replace_prepared' src/foliaseal/application src/foliaseal/presentation/qt
    .venv/bin/pytest -q tests/unit/test_document_source_monitor.py tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_app_frame_workspace_open.py
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/integration/test_readiness_caveats_status.py
    .venv/bin/ruff check src tests
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
    .venv/bin/python -m pip check
    git diff --check

For the bounded GUI audit use an owned temporary root and always remove it:

    audit_root=$(mktemp -d /tmp/foliaseal-source-recovery-XXXXXX)
    set +e
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf
    rc=$?
    set -e
    printf 'gui_rc=%s\n' "$rc"
    ps -eo pid=,cmd= | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

## Validation and Acceptance

Acceptance is behavioral: changing an open source shows a non-modal notice, blocks signing through
the existing readiness state, and does nothing until the user chooses an action. Reload and Locate
mount a validated candidate with identical authored draft values and passphrase, then clear the
notice; Ignore clears the notice without changing the mounted widget; missing-source Locate/Close
behaves explicitly; Cancel and failed candidate loading preserve the old workspace. The real
offscreen Qt overlay test proves the canvas parent, unchanged rail geometry, condition-only notice,
and explicit Ignore action; fake-Qt
AppFrame tests prove candidate Reload/Locate transfer and failure preservation. No action may
auto-reload or silently discard a draft. Focused and full tests, Ruff, pip check, diff check, and
cleanup must pass. Crash journals/autosave are not acceptance claims.

## Idempotence and Recovery

Snapshots are in-memory and candidates are disposable. Re-running tests uses temporary PDFs and
isolated configuration. If a candidate or timer fails, dispose only the candidate, stop the timer,
remove only owned temp roots, and rerun from the existing mounted handle. Never delete user PDFs or
credentials. If QTimer is unavailable in a fake binding, direct refresh tests remain valid and the
real binding path must still be covered by the offscreen integration test.

## Artifacts and Notes

Keep generated PDFs, screenshots, and logs under ignored `artifacts/` or `/tmp`. Record exact source
mutation, action choice, draft equality/secret preservation, test counts, GUI return code, process
cleanup, and compatibility grep proof. Do not commit private material or machine-local paths.

## Interfaces and Dependencies

The application boundary must remain Qt-free:

    @dataclass(frozen=True)
    class SigningDraftSnapshot: ...

    SigningDraftWorkflow.snapshot_for_source_transfer() -> SigningDraftSnapshot
    SigningDraftWorkflow.restore_source_transfer(
        snapshot: SigningDraftSnapshot,
        *,
        input_pdf_path: str,
    ) -> None

The presentation boundary carries callbacks equivalent to:

    on_source_reload: Callable[[], Any]
    on_source_ignore: Callable[[], Any]
    on_source_locate: Callable[[], Any]
    on_source_close: Callable[[], Any]

`DocumentSourceMonitor` remains the only source identity policy owner. AppFrame owns candidate
replacement and dialogs; the panel owns banner rendering; the widget owns polling cleanup. No
interface may launch URLs, auto-reload a source, persist secrets, or create a crash journal.

Revision note: 2026-08-10 / Codex. Created after the external-link confirmation slice and explorer
audit; selected draft-preserving source recovery as the next dependency-ready safety vertical slice.
