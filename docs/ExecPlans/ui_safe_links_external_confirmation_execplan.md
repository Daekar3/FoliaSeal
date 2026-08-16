# Add safe external-link confirmation and deferred opening

This ExecPlan is a living document maintained under `.agents/skills/write-execplan/PLANS.md`.
It is a bounded child of `docs/ExecPlans/ui_safe_links_external_changes_execplan.md` and the UI
compliance parent. It covers the missing presentation behavior after Pan-only link activation:
the application must show a destination, ask before opening it, launch only an approved
`http`, `https`, or `mailto` destination, and defer requests while signing is active.

## Purpose / Big Picture

After this slice, a user can click a safe external PDF link in Pan mode and see a consequence-labeled
confirmation containing the bounded destination. Cancel, Escape, and window close leave the system
unchanged; approval invokes one injected desktop-launch boundary. Blocked and malformed destinations
never reach the dialog or launcher. If a signing transaction is active, the request is held in
memory, the newest request replaces the older one with a notice, and the request is offered only
after signing succeeds or the recovery path completes. This makes the existing typed runtime result
visible in the real app without adding URL I/O to application policy code.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/ui_safe_links_source_safety_contracts_execplan.md` supplies the pure
  allow/confirm/block destination policy.
- [x] `docs/ExecPlans/ui_safe_links_contract_hardening_execplan.md` covers malformed, unknown, and
  mode-gated destinations.
- [x] `docs/ExecPlans/ui_pdf_link_inspection_execplan.md` supplies neutral page-local link facts.
- [x] `docs/ExecPlans/ui_safe_links_pan_activation_execplan.md` routes Pan clicks to typed
  internal, external, and blocked outcomes without launching anything.
- [ ] `docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md` remains open; this child must not
  reload, locate, close, or replace a changed source.

## Progress

- [x] (2026-08-10) Explorer audit confirmed external confirmation is the next dependency-ready
  slice and that source recovery lacks a draft-transfer boundary.
- [x] (2026-08-10) Added `ExternalLinkRequestResult`/`ExternalLinkOutcome`, an injected launcher,
  AppFrame confirmation, and Qt `QDesktopServices` realization. The dialog is Cancel-default and
  rejects blocked or malformed decisions before it can launch.
- [x] (2026-08-10) Added status-driven active-signing deferral. The newest request replaces an
  older pending request, and success or recovery-to-draft offers it once.
- [x] (2026-08-10) Added focused policy/frame/boundary coverage plus a real offscreen Qt dialog
  test. Display text remains bounded while the complete sanitized external target is retained for
  the approved launcher.
- [x] (2026-08-10) Reconciled `docs/ARCHITECTURE.md` and prepared the parent handoff; the
  architecture now records bounded display versus complete launch targets and explicit lifecycle
  deferral.
- [x] (2026-08-10) Focused validation is `55 passed`; full regression is `1425 passed, 20 skipped,
  1 warning`; Ruff, pip checks, and diff checks are clean. The bounded GUI audit and commit remain.
- [x] (2026-08-10) Bounded offscreen GUI launch reached the known isolated
  `SingleInstanceUnavailable` endpoint (`gui_rc=1`); process inspection found no FoliaSeal/PySide6/
  pytest process and the owned temporary root was removed.
- [x] (2026-08-10) Committed as `96594a95f` (`feat(ui): confirm safe external PDF links`); the
  worktree was clean after staging exactly the intended 13 files.

## Surprises & Discoveries

- Observation: `SigningWorkspaceRuntime` already accepts an optional external-link callback, but
  the production `AppFrame` does not provide one and no `QDesktopServices` boundary is injected.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_runtime.py` emits
  `link_external_confirmation_required` when the callback is absent; app-frame composition only
  passes the callback through when supplied.
- Observation: the destination is already bounded by `classify_link_destination()` to 512 display
  characters and only `http`, `https`, and `mailto` receive confirmation decisions.
  Evidence: `src/foliaseal/application/document_safety.py` returns a non-executable `LinkDecision`.
- Observation: source reload/locate currently creates a replacement `SigningDraftWorkflow`, so
  combining it with external-link opening would risk discarding authored draft state. This child
  therefore stops at confirmation/launch and leaves source-change recovery to its own plan.
- Observation: bounded display text cannot also be the launch target for long URLs.
  Evidence: the safety decision now carries a complete sanitized `launch_destination` separately
  from the 512-character `destination` shown in the dialog; a focused test proves the full target
  reaches the injected launcher.

## Decision Log

- Decision: keep desktop opening behind an injected presentation port and invoke it only after an
  explicit affirmative dialog result.
  Rationale: application policy must remain Qt-free and tests must prove blocked or canceled links
  cannot perform I/O.
  Date/Author: 2026-08-10 / Codex.
- Decision: use consequence labels such as `Open link` and `Cancel`, make Cancel the default, and
  render the bounded destination as text rather than an executable hyperlink.
  Rationale: UI_SPEC requires destination visibility, safe defaults, and explicit confirmation.
  Date/Author: 2026-08-10 / Codex.
- Decision: defer external requests in the AppFrame while a signing transaction is active; retain
  only the newest request and announce replacement.
  Rationale: UI_SPEC requires active-signing requests to wait until success or recovery and prevents
  multiple stale browser actions from accumulating.
  Date/Author: 2026-08-10 / Codex.
- Decision: do not implement source-change reload, Locate, Ignore, Close, or a recovery journal in
  this child.
  Rationale: those actions require a draft snapshot/transfer contract that is not yet available.
  Date/Author: 2026-08-10 / Codex.
- Decision: preserve a complete sanitized external target separately from bounded display text.
  Rationale: truncating a URL before launch could change its destination; only the bounded text is
  suitable for the dialog, while launch occurs after policy revalidation against the complete target.
  Date/Author: 2026-08-10 / Codex.

## Outcomes & Retrospective

Implementation, compliance review, architecture reconciliation, focused/full validation, and the
bounded GUI cleanup audit are complete. This slice is ready for its commit. Source
reload/locate/recovery remains intentionally outside this child.

## Context and Orientation

FoliaSeal is a local Qt PDF-signing application. `document_safety.py` is a Qt-free policy module;
its `LinkDecision` identifies an allowed internal page, an external destination requiring
confirmation, or a blocked destination. `DocumentLinkActivationService` and
`SigningWorkspaceRuntime.on_viewer_link_click()` already perform Pan-only hit testing and route
these decisions. `OpenWorkspaceCommand` in `app_frame_workspace_open.py`, the signing-shell
composition, and `SigningWorkspaceRuntime` thread an optional callback, but the concrete frame does
not yet show a dialog or open a URL.

The AppFrame in `src/foliaseal/presentation/qt/app_frame.py` owns real Qt bindings and consequence
dialogs. The runtime owns workspace interaction state, not browser I/O. `QDesktopServices.openUrl`
is the intended Qt desktop-launch API; it must be wrapped behind a small injectable callable so
headless tests never open a browser. “Active signing” means the signing action has entered its
non-cancellable transaction state; inspect the existing signing action/state boundary rather than
inventing a second flag.

The ordinary product vocabulary is used in this slice. Do not add `acceptance` names to product-facing
code, new public contracts, or UI text; existing evidence/harness names are outside this slice.

## Change Slice

Primary change class: behavior change. The commit may include the new typed presentation boundary,
AppFrame/runtime/composition wiring, focused tests, and the minimum architecture/ExecPlan status
updates. Generated PDFs, screenshots, browser output, credentials, and unrelated lifecycle,
packaging, evidence, or nomenclature migrations are forbidden from this slice.

## Plan of Work

First define a small presentation-level request/result boundary, either in
`src/foliaseal/presentation/qt/app_frame_workspace_open.py` or a focused neighboring module. It
must carry the already-bounded destination and an explicit approved/canceled result without a URL
launcher in application data. Add an injected launch callable whose production adapter delegates to
`QDesktopServices.openUrl(QUrl(destination))` and whose tests record calls. If Qt reports failure,
return a status/error without retrying or falling back to a shell command.

Implement an AppFrame method that receives only `LinkDecision` values of kind
`CONFIRM_EXTERNAL`, formats the destination as non-interactive text, and shows a consequence-labeled
dialog with `Open link` and `Cancel`. Cancel is the default and Escape/window close cancel. The
method must reject blocked or malformed decisions before constructing the dialog, and must never
launch unless the explicit affirmative result is returned.

Thread this callback through `build_qt_app_frame_host()`, `OpenWorkspaceCommand`, and the existing
workspace composition seams. When no custom launcher is supplied, the real AppFrame may construct
the Qt desktop-services adapter; tests must inject a recorder. Preserve the existing callback shape
where possible so current runtime tests remain valid.

Add a small AppFrame-owned pending request state. When the signing action is active, store the
latest external `LinkDecision` and show a non-destructive status that opening is deferred. If a new
request arrives, replace the pending value and report that the previous request was replaced. On
successful signing or the existing recovery-completion hook, offer the pending request once and
clear it; on signing failure or cancellation, preserve the pending request until the existing
recovery decision is resolved, without launching automatically. Do not add a second signing state
machine; use the existing action/state callback seam and cover the exact transition used by the
workspace.

Add the required focused tests in `tests/unit/test_qt_safe_links_external_changes.py`, extending
`tests/unit/test_qt_signing_workspace_runtime.py` only where the existing callback contract needs
coverage. Add a real offscreen Qt integration test for the dialog and launcher adapter, using a
recording callable and deterministic dialog response. Prove `https` and `mailto` approval, Cancel,
Escape/default behavior, 512-character bounded display, blocked/file/JavaScript rejection, pending
request replacement, and no browser launch while signing is active. Keep all test artifacts in
temporary roots.

After implementation, update `docs/ARCHITECTURE.md` to describe the AppFrame confirmation boundary,
the injected desktop launcher, and active-signing deferral while keeping URL policy in the
application module. Update the safe-links parent and this child with exact evidence, leave document
source recovery explicitly open, run the compliance review, and commit only this coherent slice.

## Milestones

### Milestone 1: establish a non-executable confirmation boundary

Add red tests for blocked/canceled/approved decisions and an injected launch recorder. Implement
the typed presentation helper until the tests prove that only an affirmative allowed decision can
reach the launcher.

### Milestone 2: wire the production dialog and signing deferral

Thread the callback through AppFrame composition, show the consequence-labeled dialog, and connect
pending-request handling to the existing signing action transition. Focused tests must prove the
newest request replaces an older one and no request launches during active signing.

### Milestone 3: exercise real Qt and finish the slice

Run the offscreen dialog/launcher integration test, the complete suite, Ruff, pip checks, and the
bounded GUI audit. Clean all owned processes and temporary roots, reconcile architecture and parent
plans, then commit the implementation and evidence together.

## Concrete Steps

Run from `/home/daekar/FoliaSeal` with `.venv`.

    rg -n 'on_external_link_confirmation|LinkDecisionKind|QDesktopServices|signing.*active|signing.*state' src/foliaseal/presentation/qt src/foliaseal/application
    .venv/bin/pytest -q tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_app_frame.py
    .venv/bin/ruff check src tests
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/unit/test_qt_safe_links_external_changes.py tests/integration/test_qt_safe_links_external_confirmation.py
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
    .venv/bin/python -m pip check
    git diff --check

For the bounded GUI audit, create and remove an owned root even if the isolated single-instance
endpoint prevents window creation:

    audit_root=$(mktemp -d /tmp/foliaseal-safe-links-confirm-XXXXXX)
    set +e
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf
    rc=$?
    set -e
    printf 'gui_rc=%s\n' "$rc"
    ps -eo pid=,cmd= | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

## Validation and Acceptance

The slice is accepted only when a real or deterministic offscreen Qt dialog displays the bounded
destination and an approval calls exactly one injected launcher with the same destination. Cancel,
Escape, and window close call no launcher. `file:`, `javascript:`, executable, embedded-launch,
arbitrary-scheme, malformed, and non-Pan decisions call neither dialog nor launcher. During active
signing, an external request is deferred; a newer request replaces it with a status notice; no
launch occurs until the existing success/recovery transition offers it. The pending value is cleared
after it is offered once.

The focused tests must pass, the complete suite must remain green, Ruff and `pip check` must pass,
and `git diff --check` must be clean. Record exact counts in this plan. The bounded GUI audit must
remove its temporary root and leave no FoliaSeal, PySide6, or pytest process. The parent remains open
for source-change monitoring UI and draft-preserving recovery.

## Idempotence and Recovery

All launch tests use an in-memory recorder; no browser or shell command is permitted during tests.
The dialog can be rerun with an offscreen Qt platform and isolated configuration. If a dialog or
process survives, close only the process created by this slice, remove only its owned temp root,
and rerun the focused test. Never delete repository fixtures or broad system directories. If the
desktop-services adapter fails, preserve the confirmation result and report a concise status rather
than retrying through an unbounded fallback.

## Artifacts and Notes

Keep generated PDFs, screenshots, and logs under ignored `artifacts/` or `/tmp`; commit only source,
tests, and concise plan/architecture updates. Record the exact test counts, dialog outcome matrix,
pending-request transition, bounded GUI return code, process cleanup, and final commit hash.

## Interfaces and Dependencies

`LinkDecision` remains the application policy output. The presentation boundary should expose a
callable equivalent to:

    confirm_external_link(decision: LinkDecision) -> ExternalLinkRequestResult

and an injected launcher equivalent to:

    launch_external_url(destination: str) -> bool

The AppFrame owns the dialog, pending request, and status messages. `SigningWorkspaceRuntime` only
emits the existing typed callback. `OpenWorkspaceCommand`, the signing-shell bootstrap, and the
composition request carry the callback without importing Qt into application modules. No interface
may carry a shell command, browser process, source reload operation, or signing-draft mutation.

Revision note: 2026-08-10 / Codex. Created after the Pan-only activation commit and post-pass audit;
selected external confirmation as the next dependency-ready vertical slice while explicitly keeping
draft-preserving source recovery separate.
