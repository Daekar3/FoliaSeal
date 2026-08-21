# Correct certificate creation clarity and password recovery

This ExecPlan is a living document and must remain self-contained under
`/home/daekar/.codex/skills/write-execplan/PLANS.md`. It is Child 1 of
`docs/ExecPlans/gui_hitl_defect_recovery_parent_execplan.md`.

## Purpose / Big Picture

After this slice, a first-use user can create a managed certificate without enlarging the dialog to
read it, understands which identity fields are optional, and can recover from a wrong certificate
password without losing the open PDF, selected preset, placement, or signing draft. The behavior is
visible in the installed GUI and is proven by focused offscreen tests.

The correction covers the observed Create Certificate clipping, misleading Display name label, and
wrong-password dead end. It does not redesign certificate storage, add password-change support, or
change the signed-PDF transaction.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/SCHEMAS.md` are available and authoritative.
- [x] `docs/ExecPlans/gui_hitl_defect_recovery_parent_execplan.md` records the observed evidence and
  owns the family boundary.
- [x] Existing certificate creation/import tests in
  `tests/unit/test_qt_app_frame_certificate_management.py` and application tests are the baseline.
- [x] No additional implementation child is required for the audited certificate surfaces; Child 4
  still depends on this child for installed-package and human acceptance.

## Progress

- [x] (2026-08-20) Confirmed the observed UI and recovery failures against
  `app_frame_certificate_management.py`, `certificate_readiness.py`, and
  `signing_material_resolver.py`.
- [x] (2026-08-20) Explorer review identified the concrete recovery failure: coordinator resolution
  clears `_selected_certificate_configuration_name`, the session retry helper prompts once, and the
  invalid-password message does not satisfy `_should_prompt_for_certificate_password`.
- [x] (2026-08-20) Add geometry/copy tests for the creation dialog and bounded wrong-password retry,
  reselect, and cancel coverage.
- [x] (2026-08-20) Implement the smallest dialog and recovery correction: optional display-name copy,
  readable default geometry, preserved certificate selection, exact invalid-read classification, and
  a three-prompt retry budget.
- [x] (2026-08-20) Run focused validation: 71 unit tests passed, including coordinator and session
  recovery coverage.
- [x] (2026-08-20) Display-backed source-tree audit found the still-unrepaired Import Certificate
  dialog at 267×284 pixels: its lowercase title, wrapped introduction, source-file controls,
  inspection guidance, and Display name/Password rows are visibly cramped or truncated, with no
  explicit minimum/default geometry. This is a separate import-dialog correction inside the same
  certificate-management owner.
- [x] (2026-08-20) Corrected Import Certificate title capitalization, explicit 600×460 minimum /
  680×520 default geometry, grouped inspection/form rows, and stable footer.
- [x] (2026-08-20) Corrected Manage Certificate Configurations with explicit 560×520 minimum /
  680×620 default geometry, grouped configuration/managed-certificate actions, and title case.
- [x] (2026-08-20) Source-tree correction validated in the integrated layout slice: 143 focused tests,
  then 1,605 full-suite tests passed with 20 skips; Ruff, compileall, and diff checks passed. The
  bounded X11 sweep confirmed the corrected Import Certificate and certificate-configuration surfaces
  and cleaned its process and temporary root.
- [x] (2026-08-20) Reconciled this child with the integrated correction plan and architecture map;
  installed-package and human acceptance remain in Child 4.

## Surprises & Discoveries

- Observation: the creation dialog’s `create_certificate()` already uses `common_name` when
  `display_name` is blank.
  Evidence: `app_frame_certificate_management.py` assigns `display_name = common_name` before it
  builds `CreateCertificateRequest`.
- Observation: `UI_SPEC.md` requires Full/common name and password confirmation, but permits email,
  title, organization, and a prefilled display name; it does not require a separate user-entered
  display name.
  Evidence: `UI_SPEC.md` §15 Certificate Workflows.
- Observation: wrong-password reporting originates in certificate readiness/material loading, while
  the prompt is adapted by `_QtCertificatePassphrasePrompter` in the signing properties panel.
  Evidence: `certificate_readiness.py`, `signing_material_resolver.py`, and
  `signing_workspace_properties_panel.py`.
- Observation: the selection dead end is not solely a Qt message-box issue.
  Evidence: `DefaultSignaturePropertiesCoordinator._resolve_signing_material` clears the selected
  configuration before raising, and `SigningSetupSession._run_with_manual_certificate_password_retry`
  executes only one prompted attempt.
- Observation: the Import Certificate dialog is materially smaller than the supported main-frame
  minimum and uses a dense form layout that clips user-facing copy. The window title is `Import
  certificate`, and the file chooser title/command labels use the same sentence-case convention.
  Evidence: live X11 `xwininfo` reports `Width: 267`, `Height: 284`; source construction in
  `CertificateImportDialog._build_controls()` sets no dialog minimum/default size and places the
  Choose/Inspect actions and inspection copy on separate narrow form rows.

## Decision Log

- Decision: keep Display name optional in the create dialog and continue using Full name as its
  fallback, while preserving the existing stored configuration requirement that every saved
  configuration has a non-empty display name.
  Rationale: this matches the observed successful behavior and UI_SPEC without weakening persistence
  invariants.
  Date/Author: 2026-08-20 / Codex.
- Decision: recovery must happen before signing begins and must preserve the current unsigned draft.
  Rationale: UI_SPEC WF05 says wrong passwords retry before the transaction; clearing the draft or
  forcing document reopen would be data loss and contradict Cancel-as-lossless behavior.
  Date/Author: 2026-08-20 / Codex.
- Decision: implement retry/reselect/cancel at the existing Qt/application boundary rather than
  catching exceptions in the signing backend.
  Rationale: the backend must continue to report precise validation errors; only the UI owns prompting
  and selection recovery.
  Date/Author: 2026-08-20 / Codex.
- Decision: no compatibility alias or duplicate certificate dialog path will be added.
  Rationale: callers already route through `AppFrameCertificateDialogService`; deepening that path is
  safer than preserving another legacy surface.
  Date/Author: 2026-08-20 / Codex.

## Outcomes & Retrospective

Initially the create and signing flows are incomplete because the dialog is clipped and an invalid
password strands the user. At completion, focused tests should prove readable default geometry,
optional Display name fallback, and recovery that leaves the draft and rail intact. Record whether any
remaining issue is a real certificate-format limitation or an environment limitation; do not mark the
child complete if the user still has no way to leave a wrong-password state.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame_certificate_management.py` contains
`CertificateCreationDialog`, `CertificateImportDialog`, and the app-frame certificate service. The
creation controls include Full name, Display name, optional identity fields, password confirmation,
secure password saving, and Create/Cancel. `src/foliaseal/application/certificate_manager.py` owns
managed-file and configuration persistence and must continue to reject an empty persisted display name.
`src/foliaseal/application/certificate_readiness.py` reads a selected PKCS#12 file and classifies
missing/invalid/password-protected material. `src/foliaseal/application/signing_material_resolver.py`
resolves a selected configuration and can request a manual password. The Qt adapter for that request is
`_QtCertificatePassphrasePrompter` in `signing_workspace_properties_panel.py`; its caller must retain
the selected certificate and draft when resolution fails.

The acceptance minimum is the 1100×700 logical-pixel main frame from UI_SPEC. Dialogs may be larger than
that frame, but their default layout must show every instruction and action without manual resizing.

## Plan of Work

First inspect the live dialog size hints, font metrics, form-layout margins, and the fake Qt bindings
used by `tests/unit/test_qt_app_frame_certificate_management.py`. Add a focused test that mounts the
creation dialog with real PySide6 offscreen bindings, resizes it to its default size, and asserts that the
introductory text has a non-zero visible height, the Create/Cancel buttons are visible, and the dialog’s
minimum size is sufficient for all rows. Keep the test resilient to platform font differences by testing
visibility and minimum dimensions, not pixel-perfect coordinates.

Correct the title to `Create Certificate`, label the row `Display name (optional)`, preserve automatic
prefill from Full name, and set a clear minimum/default size or a scrollable content region if the full
form cannot fit on the smallest supported desktop. The normal path must not hide password confirmation
or actions behind an unannounced resize. Add an accessible description for the optional field and ensure
the initial focus lands on Full name.

Next trace the wrong-password path from selection through readiness and signing invocation. Preserve the
prior selected configuration while the failure is being resolved; do not clear it merely because a
candidate password was invalid. Extend the bounded manual-password flow so an invalid attempt can return
to a prompt a finite number of times, then offers reselect or cancel without looping forever. The
invalid-password result must be classified as promptable even though it currently says `The selected
certificate could not be read. Check the file and password.`. A successful retry must continue the
existing signing flow exactly once; Cancel must leave the draft and selected document unchanged;
selecting another certificate must refresh readiness without silently changing appearance or placement.
Do not store the wrong password, log it, or show it in diagnostics.

Add tests for wrong-password-then-correct, wrong-password-then-cancel, and wrong-password-then-reselect.
Use a generated disposable PKCS#12 certificate and a fake passphrase prompt; assert that the signing
backend is not called until a valid password is resolved and that the error text contains no secret.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`.

    rg -n "CertificateCreationDialog|_QtCertificatePassphrasePrompter|SigningMaterialResolutionError|CertificateReadiness" src tests
    .venv/bin/pytest -q tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_certificate_manager.py tests/unit/test_certificate_readiness.py tests/unit/test_signing_material_resolver.py
    .venv/bin/ruff check src/foliaseal/presentation/qt/app_frame_certificate_management.py src/foliaseal/presentation/qt/signing_workspace_properties_panel.py src/foliaseal/application/certificate_manager.py src/foliaseal/application/certificate_readiness.py src/foliaseal/application/signing_material_resolver.py tests/unit

After implementation, add or update focused tests in the same modules and run:

    .venv/bin/pytest -q tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_qt_app_frame_recovery.py tests/unit/test_certificate_manager.py tests/unit/test_certificate_readiness.py tests/unit/test_signing_material_resolver.py tests/unit/test_signing_setup_session.py tests/unit/test_signature_properties_coordinator.py
    .venv/bin/pytest -q
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src
    git diff --check

For the display-backed check, use an isolated config/cache root and the existing fixture; do not use a
real certificate or personal PDF. Open Create Certificate, inspect it without resizing, intentionally
enter a wrong password during signing, and verify the recovery controls remain in the same workspace.

## Validation and Acceptance

The child passes when:

- `Create Certificate` is title-cased exactly, the introduction is fully readable at the default size,
  Full name and password confirmation are visible, and Create/Cancel are reachable.
- Display name is visibly optional, is prefilled from Full name, and an empty value persists using the
  existing Full name fallback without violating catalog validation.
- A wrong password offers retry, reselect, and cancel (or an equivalent explicit set of actions); no
  action closes the document or loses the unsigned draft.
- A correct retry performs one signing attempt, a cancel performs none, and a reselect updates only
  certificate-dependent readiness.
- Focused tests, the full suite, Ruff, compileall, and diff checks pass.
- No password/private key appears in logs, errors, screenshots, or test artifacts.

## Idempotence and Recovery

Use `tmp_path` and generated test certificates. If a test leaves a managed file, remove only the exact
test root after the test process exits. If a GUI run fails, capture the terminal traceback and close only
the FoliaSeal process started by this child. Do not alter the user’s real certificate catalog. If the
recovery design requires a new callback, keep the old public test controls intact until all callers are
migrated, then remove any compatibility piece proven unused in the same focused commit.

## Artifacts and Notes

The commit may contain only certificate-dialog/recovery source, focused tests, this plan, and narrowly
reconciled architecture/status text. Do not commit generated certificates, passwords, PDFs, screenshots,
or temporary package outputs. Preserve a short safe transcript such as:

    wrong password -> recovery actions visible; draft preserved
    retry with correct password -> signing request invoked once
    cancel -> no signing request; document remains open

## Interfaces and Dependencies

Keep `CreateCertificateRequest`, `CertificateManager`, `CertificateReadiness`, and
`SigningMaterialResolver` as the domain/application contracts. The Qt layer may add a narrow recovery
result or callback, but it must not move PKCS#12 parsing into widgets or mutate the certificate catalog
while merely prompting for a password. Use the existing `CertificateDialogPort`, signing properties
panel, and AppFrame command/session seams. UI copy must remain plain language and secret-free.

## Revision Note

Revised on 2026-08-20 after the required explorer review to make bounded retry explicit and name the
coordinator/session causes of the observed dead end. The plan now requires preserving the selected
draft, classifying the invalid-password message as promptable, and testing the actual session and
coordinator modules.
