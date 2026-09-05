# Diagnose and stabilize the QtPdf load lifecycle after preset changes

This ExecPlan is a living document and must be maintained under
`/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The installed process aborted while Qt was loading a PDF during a timer event.
This slice identifies which FoliaSeal operation caused that load, separates
ordinary Qt warnings from a user-visible failure, and adds the smallest safe
guard if repeated or re-entrant loads are confirmed. Afterward, selecting a
preset and creating a disposable certificate will either complete normally or
show a recoverable application error; it will not drive the application into a
native QtPdf abort.

## Child ExecPlan Dependencies

- [x] The parent plan records the coredump and the duplicate-signal resource
  hypothesis.
- [x] `gui_preset_selection_reentrancy_execplan.md` completed first so
  load-count evidence is not dominated by known duplicate selection work.
- [ ] The installed regression acceptance child consumes this plan’s result and
  must retest the package on Cinnamon/X11.

## Progress

- [x] (2026-09-04) Confirmed the coredump’s main-thread path:
  `QPdfDocumentPrivate::tryLoadDocument` → `QPdfDocument::load(QString)` →
  PySide signal dispatch → `QTimer::timeout`.
- [x] (2026-09-04) Located Qt PDF load boundaries in
  `app_frame_workspace_open.py` and `infra/render/qt_backend.py`, plus shell
  timers in `signing_shell.py`.
- [x] (2026-09-04) Completed the load-boundary inventory: workspace page-count
  loading, QtPdf render/geometry/link loads, generated canonical-preview
  `full`/`text`/`stamp` requests, and the separate text-search/selection and
  harness paths. Test-only counters cover backend load status and generated
  preview roles without shipping runtime logging.
- [ ] Reproduce preset-only, certificate-only, combined, and stale-image-preset
  cases with RSS/stderr/coredump evidence.
- [x] (2026-09-04) Implemented the smallest evidence-backed safeguards: reuse
  one computed canonical layout per refresh and discard a snapshot when its
  pixmap cannot be loaded; `_open_document()` reports failed QtPdf status
  instead of returning an invalid document.
- [x] (2026-09-04) No diagnostics were added to release code. Focused tests,
  full validation, and package audits pass; placement tests prove same-page
  placement skips the PDF refresh and cross-page placement performs one. The
  full suite reports `1617 passed, 20 skipped, 1 warning`; the installed
  placement/Appearance retest remains pending because the package predates this
  correction.
- [x] (2026-09-04) Follow-up HITL reported sustained 1.8–1.9 MiB/s writes and
  elevated CPU after placement/profile selection. No FoliaSeal process remained
  when inspected, but the timing and preview temp-file pattern implicated
  resize-triggered canonical preview regeneration. Added a size/reentrancy guard;
  focused tests and static checks pass. Rebuilt-package HITL remains pending.
- [x] (2026-09-04) Direct observation of PID `1281291` confirmed the loop: 66–69%
  CPU, approximately 5.9 MiB written in 3 seconds and 53 MiB in 5 seconds, with
  new canonical-preview directories. The resize path now reapplies layout using
  the existing render state, eliminating canonical PDF generation from resize
  callbacks. Full validation is `1618 passed, 20 skipped, 1 warning`.
- [x] (2026-09-05) The installed resize guard did not stop repeated identical
  canonical renders. Added a preview/layout-key cache at the canonical update
  boundary so duplicate requests reuse the live snapshot and cannot create fresh
  temporary PDFs. Full validation remains `1618 passed, 20 skipped, 1 warning`;
  installed confirmation is pending.
- [x] (2026-09-05) Installed package verification matched the latest bundle
  (`/usr/lib/foliaseal/foliaseal` SHA-256 `c00681bd...`, package SHA-256
  `a7599f81...`, commit `1276d5961`), but the live workflow still sustained
  84–86% CPU, wrote about 6.5 MiB every 3 seconds, and created a new
  `foliaseal-canonical-preview-*` directory at the same cadence.
- [x] (2026-09-05) The process self-terminated; no user close action occurred.
  Coredump PID `1826521` is `SIGABRT` in `libQt6Pdf.so.6` while constructing
  `QPdfDocument` from a PySide callback entered by `QTimer::timeout`.
- [x] (2026-09-05) Source tracing identifies the timer-specific trigger:
  the optional 100-ms transaction timer calls `poll_signing_transaction()`;
  while no transaction is active, it unconditionally calls `reload_state()`.
  `SigningActionCoordinator.load()` then calls `SigningDraftWorkflow.preview()`;
  after a rectangle and a horizontal image-stamp appearance are selected, the
  fit validator's default raster path creates a fresh QtPdf document on every
  tick. This directly explains the sustained preview-directory churn and the
  native abort. A narrow timer-idle guard is required before another installed
  acceptance run.
- [x] (2026-09-05) Implemented the typed idle-poll guard in the working tree:
  `transaction_active` is exposed read-only by the coordinator and boundary,
  and the bridge now skips idle readiness reloads while still polling for an
  active worker result. Focused idle/active bridge coverage and boundary
  exposure coverage were added; execution and installed retest remain pending.
- [x] (2026-09-05) Added idle-pending, active-pending, queued-completion, and
  boundary-activity regression coverage. Focused transaction/signing tests pass
  (`150 passed`), Ruff and compileall pass, and the full suite passes
  (`1622 passed, 20 skipped, 1 warning`).
- [x] (2026-09-05) Rebuilt the package from this guard. Bundle executable SHA-256
  is `1a153dd7...`; package SHA-256 is `57587617...`. The installed package is
  intentionally not overwritten by the agent because `dpkg` requires the user's
  visible sudo session.
- [ ] Install the rebuilt package on Cinnamon/X11 and repeat the rectangle +
  Single Left acceptance gate while observing CPU, disk writes,
  preview-directory churn, and coredump state.

## Surprises & Discoveries

- Observation: `QtPdfRenderBackend._open_document()` creates a fresh
  `QPdfDocument` for each render or geometry request, so one preview can load a
  generated PDF more than once even without duplicate UI events. These are
  synchronous sequential loads in the current implementation; no concurrency
  is established.
- Observation: the canonical preview may render three temporary PDFs and the
  horizontal image-stamp reservation path may request recursive measurement.
  This can multiply short-lived QtPdf objects and explains the resource spike
  without proving a backend defect.
- Observation: the first coredump did not name the Python timer callback. The
  second coredump plus source tracing now identify the optional 100-ms
  transaction timer: its idle polling path reloads signing readiness and
  re-enters the workflow preview/fit validator.
- Observation: a persisted image-stamp preset references a missing external
  path. Preview fallback should be tested, but a handled missing image is not
  evidence of a native abort.
- Observation: after layout reuse, the representative canonical preview emits
  exactly three generated raster requests (`full`, `text`, `stamp`) and no
  duplicate layout calculation. No evidence establishes concurrent QtPdf
  loads; the remaining risk is installed runtime behavior.
- Observation: the panel resize callback was an unbounded render trigger: each
  resize invoked canonical preview generation even when the panel dimensions had
  not changed. Preview pixmap replacement can itself emit resize events, matching
  sustained writes without a user continuing to interact.

## Decision Log

- Decision: instrument before changing the render backend.
  Rationale: the stack identifies the failure boundary but not its trigger;
  changing caching or backend technology without a measured reproduction risks
  obscuring the real defect.
  Date/Author: 2026-09-04 / Codex.
- Decision: prefer coalescing or reuse at the narrowest caller that causes
  repeated sequential loads; consider serialization only if instrumentation
  proves a thread-affinity or overlap problem. Preserve the existing QtPdf API
  and PDF fidelity.
  Rationale: the user-visible requirement is stability during setup, not a new
  rendering architecture, and serialization cannot fix purely sequential
  over-rendering.
  Date/Author: 2026-09-04 / Codex.
- Decision: do not catch or ignore `SIGABRT` as an application error.
  Rationale: a native abort must be prevented by lifecycle correctness or a
  backend-safe fallback, not hidden from acceptance evidence.
  Date/Author: 2026-09-04 / Codex.
- Decision: make the transaction poller idle when no transaction is active;
  retain periodic reloads only while an owned signing worker is running.
  Rationale: readiness polling is the timer-driven caller shown to re-enter
  `SigningDraftWorkflow.preview()` every 100 ms, and the coredump proves that
  this path reaches QtPdf. Recomputing readiness while idle has no user-visible
  value and creates unbounded native PDF work.
  Date/Author: 2026-09-05 / Codex.
- Decision: expose transaction activity as a typed boundary property rather than
  inspecting the worker thread.
  Rationale: a worker may finish and queue its result while the coordinator is
  still active; polling must continue until that completion is delivered. The
  coordinator's `_transaction_active` flag is authoritative and does not perform
  readiness or preview work.
  Date/Author: 2026-09-05 / Codex.

## Outcomes & Retrospective

At completion, the plan must identify the triggering operation (or state that
controlled reproduction did not reproduce it), show load/refresh counts before
and after, and explain why the chosen safeguard prevents repeated, re-entrant,
or otherwise runaway work. Installed Gate 2 preset/certificate acceptance is the
final proof.

Current evidence (2026-09-05): the installed render-key correction still
reproduced the native abort. The pre-fix resize/cache hypotheses were
insufficient because an idle 100-ms transaction timer independently reran
workflow fit validation and its default QtPdf raster path. The source correction
now suppresses that idle work and is fully test-validated; installed package
retest remains the only acceptance gap.
Host installation and the human placement/Appearance sequence are the remaining
proof; the source correction is intentionally not treated as installed evidence.

## Context and Orientation

Opening a PDF for the workspace uses `QtPdfPageCountLoader` in
`src/foliaseal/presentation/qt/app_frame_workspace_open.py`. Rendering and page
geometry use `QtPdfRenderBackend` in `src/foliaseal/infra/render/qt_backend.py`.
`ViewerWorkflow.render_current_page()` calls both render and geometry operations;
the Qt viewer adapter calls it when the viewer first shows or refreshes.

The signing shell in `src/foliaseal/presentation/qt/signing_shell.py` owns
periodic timers. Setup changes normally update the signing preview and notify
the shell, while document viewer refreshes occur through the workspace runtime
and interaction bridge. The optional transaction timer currently polls every
100 ms; its idle branch reloads signing action state, which invokes readiness
and preview validation even when no signing transaction exists. The 2026-09-05
coredump and source trace establish this as the live QtPdf load path.

## Plan of Work

Add a diagnostic seam that counts `_open_document`, `render_page`, and geometry
loads with a short reason label. Inventory all repository QtPdf load sites,
including `interactive_harness.py`, `phase2_harness.py`, `document_text_search.py`,
and `document_text_selection.py`, while documenting which are outside the
installed workflow. In tests, use a fake `QPdfDocument` that records loads and
can raise a controlled load error. In an isolated X11 run, capture timestamps,
process RSS, stderr, callback/request IDs, and whether loads are merely repeated
sequentially or actually overlap. Correlate those records with preset-selection
and certificate-creation events.

Run four independent cases: selecting a preset without a certificate,
selecting one with a certificate, creating a certificate without selecting a
preset, and performing both actions in the user-reported order. Exercise the
stale image-stamp preset separately. The measured call graph now requires one
narrow guard rather than another render cache: add a read-only
`transaction_active` property to `SigningActionCoordinator`, delegate it through
`SigningActionBoundary`, and change
`SigningWorkspaceActionBridge.poll_signing_transaction()` so a pending poll
reloads state only when that property is true. Do not inspect worker-thread
liveness, stop the timer, or change QtPdf behavior. Add focused tests for an
idle pending poll (no reload), an active pending poll (one reload), and a queued
completion (terminal state still applied after the worker has finished).

Add a dedicated fake-binding test for `_open_document()` status handling and
cleanup, plus preview-lifecycle tests for generated `full`, `text`, and `stamp`
loads, successful rendering, controlled load failure, rapid repeated refresh
requests, and cleanup after a failed or replaced snapshot. Ensure the viewer
remains responsive and the signing preview still reflects the selected
appearance.

## Concrete Steps

From `/home/daekar/FoliaSeal`, locate all load boundaries and run the existing
render/viewer tests before editing:

    rg -n "QPdfDocument|\.load\(|render_current_page|refresh_viewer|QTimer|singleShot" src/foliaseal tests
    .venv/bin/python -m pytest tests/unit tests/integration -q

Run the focused lifecycle tests after each change, then the full suite:

    .venv/bin/python -m pytest tests/unit/test_qt_signing_workspace_runtime.py tests/integration/test_gui_launch_no_document.py -q
    .venv/bin/python -m pytest -q

For the installed proof, use a freshly built package and `/usr/bin/foliaseal
gui` on Cinnamon/X11. Preserve a coredump if one recurs and report its
timestamp, signal, and top stack frames; do not delete it as “cleanup.”

## Validation and Acceptance

The slice passes when all load boundaries are accounted for, the focused tests
cover repeated refresh, load failure, generated-preview cleanup, and stale-image
fallback, the full suite is green, and the installed preset/certificate
sequence remains responsive without a QtPdf abort. Missing external image data
must produce a clear recoverable preview state, leave no unbounded temporary
roots, and must not crash or loop. Qt AT-SPI warning text remains contextual
unless Orca behavior fails.

## Idempotence and Recovery

Diagnostics must be isolated to tests or temporary launch instrumentation and
removed before packaging. Use disposable PDFs/profiles and fresh temporary
roots for each run. If the application crashes, verify no owned process remains,
retain safe coredump metadata, and restart from a clean process. Never remove
the user’s profile catalog or shared desktop accessibility state.

## Artifacts and Notes

Allowed artifacts are load-count summaries, bounded stderr, focused test logs,
package audit JSON, and safe screenshots. Do not commit coredump binaries,
temporary PDFs, certificates, passwords, package files, or profiling traces.

## Interfaces and Dependencies

Preserve `PdfRenderBackend`, `QtPdfRenderBackend.render_page()`,
`QtPdfRenderBackend.get_page_geometry()`, `ViewerWorkflow.render_current_page()`,
and the typed signing-shell timer boundaries unless the measured defect requires
a narrow extension. Any new seam must keep the PDF-first viewer topology and
remain testable without a display.

Revision note: 2026-09-04 / Codex — explorer review corrected “overlapping
loads” to distinguish repeated synchronous work from concurrency, expanded the
load-boundary inventory, added callback correlation, and made generated-preview
cleanup/stale-image behavior explicit.

Revision note: 2026-09-04 / Codex — implementation reused the canonical layout
computed for the full render, added generated-role/load-status regression
coverage, and cleans failed pixmap snapshots without retaining temp roots.

Revision note: 2026-09-05 / Codex — after the installed render-key correction
still reproduced the CPU/disk loop and a new QtPdf `SIGABRT`, source tracing
identified the idle 100-ms transaction poll as the remaining trigger. The plan
now specifies a typed transaction-activity guard and idle/active/completion
regression coverage.
