# Extract app-frame certificate dialog orchestration behind a narrow presentation boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the FoliaSeal top-level window will still expose the same Settings actions for certificate creation, certificate import, and certificate-configuration management. A user will still see the same dialogs, the same success and error messages, and the same live refresh of the loaded signing shell when certificate catalog changes matter.

The architectural win is that `src/foliaseal/presentation/qt/app_frame.py` will stop owning both the top-level menu host and the full certificate-dialog implementation. A new narrow presentation helper will own dialog construction and lifecycle-service orchestration for the managed certificate workflow, while `FoliaSealAppFrame` remains the `QMainWindow` owner that routes menu actions into that helper.

## Child ExecPlan Dependencies

- [x] (2026-06-07 19:07Z) `docs/ExecPlans/app_frame_workspace_open_boundary_execplan.md` is complete; the app-frame open path is already extracted and does not need to be revisited in this slice.
- [x] (2026-06-07 19:07Z) No child ExecPlan is required for this tracer-bullet extraction.

## Progress

- [x] (2026-06-07 19:07Z) Re-read the live certificate dialog code, the app-frame tests, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, and the prior workspace-open ExecPlan.
- [x] (2026-06-07 19:09Z) Ran the required `explorer-light` dev-loop exploration pass and fixed the slice boundary: extract certificate dialog orchestration next; do not further subdivide `app_frame_workspace_open.py`.
- [x] (2026-06-07 19:14Z) Wrote this ExecPlan and fixed the implementation target at one app-frame-facing certificate dialog boundary module.
- [x] (2026-06-07 19:24Z) Added `src/foliaseal/presentation/qt/app_frame_certificate_management.py`, moved the certificate dialog classes and control dataclasses into it, and replaced the app-frame certificate methods with thin routing through `AppFrameCertificateDialogService`.
- [x] (2026-06-07 19:31Z) Added `tests/unit/test_qt_app_frame_certificate_management.py` for detailed certificate workflow coverage and trimmed `tests/unit/test_qt_app_frame.py` to route/compatibility coverage only.
- [x] (2026-06-07 19:35Z) Ran focused validation with `.venv/bin/python -m pytest -q tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_qt_app_frame.py`, `.venv/bin/python -m ruff check ...`, and `git diff --check`; all passed.
- [x] (2026-06-07 19:43Z) Reconciled `docs/ARCHITECTURE.md` to the implemented ownership split so the repo now names `app_frame_certificate_management.py` as the certificate dialog owner and `app_frame.py` as the Settings-action routing edge.
- [x] (2026-06-07 19:46Z) Ran the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan through a fresh `explorer-light` pass; no findings were reported.
- [x] (2026-08-16) Finished slice was committed after focused validation and architecture/compliance
  review; this historical plan is closed by `app_frame_certificate_dialog_status_reconciliation_execplan.md`.

## Surprises & Discoveries

- Observation: after the workspace-open extraction, the app frame's largest remaining shallow concentration is the managed certificate workflow, not document open.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` still defines `CertificateImportDialog`, `CertificateCreationDialog`, and `CertificateConfigurationManagementDialog`, and the corresponding tests occupy most of `tests/unit/test_qt_app_frame.py` from the certificate section onward.

- Observation: the current app-frame tests prove both menu routing and detailed dialog behavior through the same entrypoint.
  Evidence: `tests/unit/test_qt_app_frame.py` asserts both Settings menu labels and dialog control interactions such as import-file prefill, configuration save/delete/export, and lifecycle error handling in one file.

- Observation: the smallest compatibility surface worth preserving in this slice is the window-level `certificate_*_dialog` exposure, not the app-frame-owned private dialog caches.
  Evidence: the existing tests and fake-window inspection only use `window.certificate_creation_dialog`, `window.certificate_import_dialog`, and `window.certificate_management_dialog`; removing the private frame caches did not change behavior once the new boundary returned an explicit compatibility payload.

## Decision Log

- Decision: keep this slice entirely in the Qt presentation layer and do not change `CertificateLifecycleService`.
  Rationale: `docs/SPEC.md` requires the managed certificate feature set, but the feature contract already lives in `src/foliaseal/application/certificate_lifecycle.py`. The shallow-module problem is presentation orchestration, not business logic.
  Date/Author: 2026-06-07 / Codex

- Decision: defer cleanup of `window.current_shell`, `window.current_viewer_workflow`, `window.current_signing_workflow`, and `window._foliaseal_app_frame`.
  Rationale: those compatibility surfaces are broader debt and do not belong in a narrow certificate-dialog extraction.
  Date/Author: 2026-06-07 / Codex

- Decision: remove app-frame-owned certificate dialog implementation from `app_frame.py`, but preserve any compatibility exposure that current tests or callers still rely on if it can be retained through the new boundary without widening scope.
  Rationale: the goal is to cut cruft, not to force a second migration slice for external inspection hooks unless they are clearly dead.
  Date/Author: 2026-06-07 / Codex

- Decision: move the detailed certificate behavior tests into a new boundary-focused module instead of keeping them in `test_qt_app_frame.py`.
  Rationale: this is the simplest way to make the new ownership split visible in the tests. The app-frame suite now proves routing, while the new module proves the managed certificate feature behavior.
  Date/Author: 2026-06-07 / Codex

## Outcomes & Retrospective

Implementation, documentation reconciliation, focused validation, and architectural compliance review are complete. The slice added `src/foliaseal/presentation/qt/app_frame_certificate_management.py`, moved certificate dialog construction and lifecycle-service orchestration out of `app_frame.py`, preserved the narrow window-level dialog exposure used by tests, and reduced `FoliaSealAppFrame` to a thin menu/host adapter for the certificate Settings actions.

The work stayed narrow all the way through review. There was no lifecycle-service contract change, no workspace-open refactor follow-up, and no broader compatibility cleanup beyond deleting now-dead app-frame private dialog caches. Only the final commit remains.

## Context and Orientation

The top-level Qt window lives in `src/foliaseal/presentation/qt/app_frame.py`. `FoliaSealAppFrame` owns the real `QMainWindow`, installs the File and Settings menus, exposes the window-level helper methods used by tests and launch wiring, and now delegates PDF workspace creation to `src/foliaseal/presentation/qt/app_frame_workspace_open.py`.

The managed certificate workflow is a product feature described in `docs/SPEC.md`. In this repository, “managed certificate workflow” means three user-visible Settings actions: creating a self-signed managed certificate, importing an existing PKCS#12 certificate into the app-managed catalog, and managing saved certificate configurations plus managed certificate export/delete operations. Those actions currently live in the same `app_frame.py` module as the top-level window host.

The application-layer contract already exists in `src/foliaseal/application/certificate_lifecycle.py`. `CertificateLifecycleService` is the business-logic service that creates, imports, saves, deletes, and exports certificate records and returns result objects with plain-language user messages plus a `refresh_shell` flag. This slice must not change that service contract. The work belongs in Qt presentation code that gathers user input, calls the service, shows success/error messages, and refreshes the live signing shell when the service reports that the catalog changed.

The relevant tests live today in `tests/unit/test_qt_app_frame.py`. That file currently proves both top-level menu wiring and detailed dialog behavior. This slice should add a dedicated certificate boundary test module so the app-frame tests can shrink to routing and compatibility assertions.

## Plan of Work

First, add a new module under `src/foliaseal/presentation/qt/` for certificate dialog orchestration. Move the three dialog classes out of `app_frame.py` into that module, together with the small control dataclasses they need. Add one narrow app-frame-facing boundary object that owns dialog construction and execution for the three Settings actions. The boundary should accept the current Qt bindings, the parent window, the existing `CertificateLifecycleService`, and one refresh callback that it passes into the dialogs when lifecycle results report `refresh_shell = true`.

Second, edit `src/foliaseal/presentation/qt/app_frame.py` so `FoliaSealAppFrame` constructs and stores the new certificate boundary service during initialization. Replace `show_certificate_import()`, `show_certificate_creation()`, and `show_certificate_management()` with thin routing methods that delegate to the new boundary. If current tests rely on `window.certificate_*_dialog` attributes for inspection, keep those compatibility writes in the frame-facing boundary outcome rather than leaving the implementation in `app_frame.py`. Remove any now-dead app-frame dialog fields that are no longer needed.

Third, add focused tests for the new module in a new unit test file. Those tests must prove import-file chooser prefill behavior, creation/import success and error handling, configuration rename/delete/export behavior, and refresh-callback triggering only when lifecycle results request it. Then trim `tests/unit/test_qt_app_frame.py` so its certificate coverage proves that the Settings actions route into the new boundary and preserve any deliberate compatibility exposure, rather than re-proving all dialog internals there.

Fourth, run focused validation. After the code is stable, update `docs/ARCHITECTURE.md` and this ExecPlan so the repo describes certificate dialog ownership accurately. Then run the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this plan. If the review finds a mismatch, fix only the mismatch inside this slice, rerun validation, and then create one narrow commit.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the certificate boundary module and migrate `app_frame.py` to use it.

       apply_patch ... on src/foliaseal/presentation/qt/app_frame_certificate_management.py
       apply_patch ... on src/foliaseal/presentation/qt/app_frame.py

2. Add focused boundary tests and trim the app-frame certificate tests.

       apply_patch ... on tests/unit/test_qt_app_frame_certificate_management.py
       apply_patch ... on tests/unit/test_qt_app_frame.py

3. Run focused validation for the new module and app-frame routing.

       .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_qt_app_frame.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame_certificate_management.py src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_qt_app_frame.py
       git diff --check

4. Reconcile `docs/ARCHITECTURE.md` and this ExecPlan to the implemented boundary, then rerun focused validation if any code or tests changed during reconciliation.

5. Run the architectural compliance review, address any findings inside this slice only, and create the git commit.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- Settings actions for certificate creation, import, and management still open the same user-facing dialogs and still call `CertificateLifecycleService` for the same operations;
- certificate creation, import, rename, delete, and export success/error behavior is proven by focused tests on the new boundary module instead of through `FoliaSealAppFrame`;
- the live signing shell still refreshes only when lifecycle results report `refresh_shell = true`;
- `FoliaSealAppFrame` becomes a thin menu/host adapter for certificate dialog actions;
- `docs/ARCHITECTURE.md` describes the new ownership split accurately;
- no lifecycle-service contract, workspace-open boundary, or broad compatibility-surface cleanup is mixed into this slice.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_qt_app_frame.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame_certificate_management.py src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. The visible managed certificate workflow must not change in this slice.

## Idempotence and Recovery

This is a behavior-preserving Qt presentation extraction. It is safe to retry. If the new boundary causes failures, keep the new module in place and move only the missing callback or compatibility write across the seam; do not collapse the dialog implementations back into `app_frame.py`.

If a test fails because callers still inspect a dialog instance through `window.certificate_*_dialog`, preserve that compatibility through an explicit boundary outcome or app-frame-assigned attribute. If a compliance review suggests broader cleanup of compatibility attributes or lifecycle service contracts, record it as follow-up and do not widen this slice.

## Artifacts and Notes

The most important final evidence for this slice will be:

- a new `src/foliaseal/presentation/qt/app_frame_certificate_management.py` module that owns certificate dialog construction and lifecycle-service orchestration;
- a visibly smaller `FoliaSealAppFrame` certificate surface in `src/foliaseal/presentation/qt/app_frame.py`;
- a new focused certificate boundary test module;
- focused validation output showing the boundary tests and app-frame tests still pass.

Current validation transcript:

    $ .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_qt_app_frame.py
    ...........................
    27 passed in 0.53s

    $ .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame_certificate_management.py src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_qt_app_frame.py
    All checks passed!

    $ git diff --check
    <no output>

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the app frame depends on one narrow certificate boundary with an explicit compatibility payload:

    @dataclass(frozen=True)
    class CertificateDialogCompatibilityState:
        import_dialog: Any | None = None
        creation_dialog: Any | None = None
        management_dialog: Any | None = None

    @dataclass(frozen=True)
    class CertificateDialogOutcome:
        result: Any | None
        compatibility: CertificateDialogCompatibilityState

    class CertificateDialogPort(Protocol):
        def show_import_dialog(self) -> CertificateDialogOutcome: ...
        def show_creation_dialog(self) -> CertificateDialogOutcome: ...
        def show_management_dialog(self) -> CertificateDialogOutcome: ...

`FoliaSealAppFrame` must depend on that port and on the existing `CertificateLifecycleService`. The new boundary may own the dialog classes directly. It must not depend on `SigningWorkspacePort`; instead it should receive a plain refresh callback from the frame.

Revision note: Created on 2026-06-07 by Codex for the next `dev-loop` slice after the completed app-frame workspace-open boundary extraction.

Revision note: Updated on 2026-06-07 after implementation and focused validation to record the extracted certificate dialog boundary, the slimmer app-frame test surface, and the preserved compatibility exposure.

Revision note: Updated on 2026-06-07 after architecture reconciliation and compliance review to record the completed documentation work, the clean review outcome, and the concrete `CertificateDialogOutcome` interface that the implementation settled on.
