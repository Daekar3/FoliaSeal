# Stabilize preset selection and PDF rendering during signing setup

This ExecPlan is a living document. It is authored under
`/home/daekar/.codex/skills/write-execplan/PLANS.md`; every section must remain
self-contained as implementation and evidence advance.

## Purpose / Big Picture

Selecting a saved signature preset must be a quick, safe setup action. After
this family is complete, one selection will apply the preset once, refresh the
visible preview once, and leave the PDF viewer responsive while certificate
material is resolved. Creating or selecting a certificate afterward must not
drive the application into runaway work or a native QtPdf abort. A human can
see the result by selecting each disposable preset in the installed application,
watching that the interface remains responsive, and continuing to signing
without a crash.

The family addresses the 2026-09-04 installed HITL failure. Gate 1 and the
early document-review gates passed. Selecting an existing preset caused an
immediate resource spike; after certificate creation the installed process
aborted. The retained coredump shows `SIGABRT` in Qt6Pdf while
`QPdfDocument::load()` ran from a Qt timer callback. The evidence strongly
implicates duplicate preset-selection work, but it does not yet prove the
exact timer callback or every condition that caused the abort.

## Child ExecPlan Dependencies

- [ ] `gui_preset_selection_reentrancy_execplan.md` proves and removes duplicate
  preset-selection delivery, bounds preview work, and adds focused regression tests.
- [ ] `gui_pdf_load_lifecycle_safety_execplan.md` maps every PDF load during the
  affected workflow, reproduces the QtPdf abort where possible, and adds the
  smallest evidence-backed lifecycle safeguard.
- [ ] `gui_hitl_defect_regression_acceptance_execplan.md` is resumed only after
  both children pass focused validation; it rebuilds/reinstalls the package and
  repeats the blocked Gate 2 path before later release gates.

Children 1 and 2 may investigate independently, but the installed acceptance
child must consume both completed implementation commits. Do not mix unrelated
UI polish, Wayland work, or broad rendering-backend replacement into this
family.

## Progress

- [x] (2026-09-04) Recorded the installed HITL result: Gate 1 passed; Gate 2
  passed through certificate management; preset selection caused a resource
  spike and the process later aborted.
- [x] (2026-09-04) Preserved and inspected the coredump for installed PID
  `1084811`; it shows `SIGABRT` in Qt6Pdf at `QPdfDocument::load()` from a
  `QTimer::timeout` callback.
- [x] (2026-09-04) Identified a concrete duplicate-event lead: the preset
  combo connects both `currentTextChanged` and `currentIndexChanged` to the
  same handler, and the repository fake emits both signals for one change.
- [x] (2026-09-04) Completed the preset-selection reentrancy correction in
  `eed5c93da`: one `currentTextChanged` delivery, an explicit reentrancy guard,
  and exact handler/session/coordinator/password/preview/viewer call counts.
- [x] (2026-09-04) Added the narrow PDF lifecycle safeguards in the corrected
  checkout and their evidence:
  `_open_document()` status handling, canonical-preview generated-role raster
  counts, reuse of one computed preview layout per refresh, and cleanup when a
  pixmap load fails. Focused lifecycle tests and the full suite pass.
- [x] (2026-09-04) Rebuilt and installed the exact corrected Debian package
  (`0.1.0`); `/usr/bin/foliaseal` matches the artifact executable SHA-256
  (`645be985...cfb4f`), and the installed GUI launched on Cinnamon/X11.
- [x] (2026-09-04) The corrected installed session passed preset selection,
  certificate management, appearance/certificate/placement profile selection,
  and the explicit no-auto-place check.
- [x] (2026-09-04) Implemented bounded placement/profile safeguards: placement
  commits and unchanged profile refreshes no longer regenerate canonical preview
  PDFs; same-name Appearance edits preserve identity and references. Focused and
  full validation pass; the fresh package is installed for live retest.
- [x] (2026-09-04) Extended placement safeguards to retain cross-page navigation with
  exactly one viewer refresh. Focused and full validation report `1617 passed, 20 skipped,
  1 warning`; a fresh package was rebuilt and passed the offline package audit.
- [ ] Confirm installed placement commit and Appearance edit/rename-back paths
  remain responsive and crash-free, then reconcile release plans.
- [ ] Reconcile parent/release plans and commit the complete plan/evidence set.

## Surprises & Discoveries

- Observation: a single preset application refreshes a canonical preview that
  can render full, text-only, and stamp-only temporary PDFs; each Qt backend
  render creates and loads a new `QPdfDocument`.
  Evidence: `signing_preview_renderer.py`, `signature_preview_lifecycle.py`,
  and `infra/render/qt_backend.py`.
- Observation: horizontal image-stamp layout measurement can recursively ask
  for another preview measurement, multiplying work for one refresh.
  Evidence: `application/horizontal_signature_reservation.py`.
- Observation: the persisted profile catalog contains an old image-stamp path
  under `/mnt/Fast Storage/...` that is absent on this host. This should remain
  a handled data-quality case, not an assumed native-crash cause.
  Evidence: the local profile catalog and preview fallback handling.
- Observation: one representative canonical preview refresh emits three
  generated raster requests (`full`, `text`, `stamp`), while the corrected
  renderer computes its layout once. The previous code computed the same
  layout twice before those requests, and horizontal image-stamp measurement
  could add a nested reference render.
  Evidence: `tests/unit/test_signing_preview_renderer.py::test_canonical_preview_reuses_layout_and_bounds_generated_raster_requests`.
- Observation: the corrected full suite and fresh package audits do not
  reproduce the native abort; installed preset/certificate behavior remains
  unverified until the package is installed and exercised by HITL.
- Observation: the coredump identifies QtPdf and a timer/event-loop boundary but
  not the originating Python callback. Instrumentation must distinguish
  source-safety, transaction polling, layout restoration, queued callbacks, and
  viewer refresh activity.

## Decision Log

- Decision: make preset selection single-delivery before attempting deeper
  rendering changes.
  Rationale: duplicate signal delivery is directly visible in the source and
  explains the user-observed immediate spike with the smallest behavior change.
  Date/Author: 2026-09-04 / Codex.
- Decision: retain the QtPdf backend unless a controlled reproduction proves a
  lifecycle defect that cannot be solved by bounded, serialized rendering.
  Rationale: replacing the renderer would expand the slice and could change PDF
  fidelity without evidence that the backend itself is the primary fault.
  Date/Author: 2026-09-04 / Codex.
- Decision: treat the coredump as release-blocking evidence, but do not claim
  duplicate signals are the sole crash cause until load counts and timer origin
  are measured.
  Rationale: the stack proves a native abort during PDF loading, not the exact
  initiating action.
  Date/Author: 2026-09-04 / Codex.

## Outcomes & Retrospective

At completion, this family must state whether one preset selection produces one
selection callback, one session/coordinator application, one password-prompt
path, one canonical preview refresh, no unintended viewer refresh, and a
bounded number of PDF loads; whether the crash reproduces; and which installed
package was tested. Any remaining QtPdf warning or data-quality case must be
separated from user-visible release failures.

## Context and Orientation

The Qt signing properties panel is in
`src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`. Its
preset combo invokes `_on_signature_preset_selected()`, which delegates to
`src/foliaseal/application/signing_setup_session.py` and
`src/foliaseal/application/signature_properties_coordinator.py`. Applying a
preset updates appearance, placement, and possibly certificate material, then
refreshes the canonical preview.

Preview rendering is implemented in
`src/foliaseal/application/signing_preview_renderer.py` and
`src/foliaseal/presentation/qt/signature_preview_lifecycle.py`. The Qt PDF
backend in `src/foliaseal/infra/render/qt_backend.py` opens a fresh
`QPdfDocument` for render and geometry requests. The live shell owns periodic
Qt timers in `src/foliaseal/presentation/qt/signing_shell.py` for source-safety
polling and, when enabled, signing-transaction polling. Viewer refreshes are
implemented by `src/foliaseal/presentation/qt/viewer_widget.py` and
`src/foliaseal/application/viewer_workflow.py`.

The installed acceptance target is `/usr/bin/foliaseal gui` from the Debian
package, not the checkout's Python entry point. Temporary PDFs and profiles
must be disposable; never use private credentials or private documents.

## Plan of Work

First complete the preset child. Count real signal delivery, coordinator
application, preview refreshes, and backend loads with focused test doubles or
temporary diagnostic hooks. Keep exactly one user-facing preset-selection
signal and guard programmatic selector updates with the existing suspension
mechanism. Add a regression test that fails when one real combo change invokes
the handler twice. Bound or coalesce preview work only where the counts prove it
is part of the same duplicate event.

Then complete the PDF lifecycle child. Inventory every repository
`QPdfDocument` import/load boundary and, for the affected session, distinguish
source-PDF loads from generated canonical-preview `full`, `text`, and `stamp`
loads, geometry-only loads, and text-search/selection loads. Identify the active
callback through timestamped correlation rather than inferring it from the
coredump. Run preset-only, certificate-only, and combined reproductions,
including the stale image-stamp profile. If repeated sequential loads or
re-entrant refreshes remain after the preset fix, implement the narrowest safe
coalescing, reuse, or thread-affinity guard justified by the measurements. Do
not assume concurrent loads, and do not hide a native abort by swallowing
ordinary application exceptions.

Finally rebuild the package from the corrected checkout, run the existing
offline/private/display-backed audits, install it through the authorized host
path, and repeat the blocked human Gate 2 sequence. Only after the preset and
certificate path remains responsive and crash-free may the remaining release
matrix gates resume.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`. Each child records its exact
test commands and expected focused results. The integrated package pass must
include:

    git rev-parse HEAD
    git diff --check
    .venv/bin/python -m pytest tests/unit/test_qt_signing_shell.py tests/unit/test_signing_setup_session.py
    .venv/bin/python -m pytest
    .venv/bin/python scripts/deb_package_audit.py <fresh-deb> --artifacts-dir <owned-root>/offline
    .venv/bin/python scripts/deb_package_audit.py <fresh-deb> --artifacts-dir <owned-root>/install-root --package-manager-root <owned-root>/dpkg-root
    DISPLAY=:0 QT_QPA_PLATFORM=xcb .venv/bin/python scripts/deb_package_audit.py <fresh-deb> --artifacts-dir <owned-root>/x11 --display-backed

Evidence captured on 2026-09-04: full suite `1616 passed, 20 skipped, 1
warning`; offline, disposable-root, and display-backed package audits passed
with `gui_startup.status=started`. The corrected package is installed and the
placement/Appearance human retest remains pending.

The human rerun uses `/usr/bin/foliaseal gui`, a disposable PDF, and disposable
profile/certificate data. Record responsiveness, preset selection, certificate
creation, preview stability, and whether any crash occurs. Preserve the
system-owned coredump if a crash recurs; clean only session-owned processes and
temporary roots.

## Validation and Acceptance

The family passes when focused tests prove one selection delivery and bounded
preview work, the full suite remains green, package audits pass, and the
installed application completes preset selection plus certificate creation
without runaway resource use or a crash. The coredump path must either be
absent on the corrected reproduction or be explained as an unrelated controlled
fixture failure. Gate 2 may then continue to placement, signing, reopen/verify,
and accessibility checks.

## Idempotence and Recovery

Use a new owned temporary directory for every package and diagnostic run. Do
not delete the retained coredump or unrelated user data. If a run crashes,
record its timestamp and process identity, verify no FoliaSeal process remains,
and retry from a fresh process. Never kill Orca or unrelated windows. If the
host package is replaced, record its prior state and restore it after acceptance
according to the installed-package release plan.

## Artifacts and Notes

Allowed artifacts are focused test output, concise load/event counters, safe
stack summaries, package audit JSON, and screenshots without private content.
Do not commit `.deb` files, build directories, coredump binaries, PDFs,
certificates, passwords, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing Qt/PySide6 signal and timer APIs, `SigningSetupSession`,
`DefaultSignaturePropertiesCoordinator`, `QtCanonicalPreviewLifecycle`, and
`QtPdfRenderBackend`. Preserve the typed signing-shell boundaries and the
PDF-first UI topology. Any new diagnostic seam must be test-only or a narrow
typed hook removed before release; no acceptance-only behavior may ship.

Revision note: 2026-09-04 / Codex — explorer review qualified the timer-origin
claim, distinguished repeated synchronous PDF loads from unproven concurrency,
expanded diagnostics to generated preview PDFs and all repository load sites,
and made session/password counts, viewer-refresh invariants, and cleanup
criteria explicit.
