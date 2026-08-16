# First-use nested Certificate creation and import

## Purpose / Big Picture

Complete the remaining first-use Preset workflow required by `docs/SPEC.md` and
`docs/UI_SPEC.md`: from the modeless Signature Library's suspended Preset editor, a user can
explicitly create or import a certificate, return to the Preset draft, select the resulting
certificate configuration, and save the Preset. The operation must attach only the stable
`certificate_configuration_id`; it must never copy a certificate path, password, or secret into a
Preset and must never apply the new certificate to the active document.

The existing `CertificateManager`, creation/import dialogs, catalog repository, and shell refresh
seams are reused. This slice owns only the nested Library/Preset return path and its evidence.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/in_app_certificate_creation_execplan.md` — self-signed creation service and
  dialog are complete.
- [x] `docs/ExecPlans/schema_model_alignment_slice5a_certificate_import_execplan.md` — PKCS#12
  import service and dialog are complete.
- [x] `docs/ExecPlans/ui_first_use_nested_placement_creation_execplan.md` — establishes the
  suspended Preset callback/selector pattern.
- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` — governing reference-only Preset and first-use
  Certificate requirements.
- [x] Scope boundary confirmed: Certificate creation/import from a nested Preset is separate from
  current-document Placement capture, which remains a separate slice.

## Progress

- [x] (2026-08-16) Explorer audit identified nested Certificate creation/import as the next
  dependency-ready gap; existing lifecycle/storage code needs no model changes.
- [x] (2026-08-16) Added typed create/import callbacks and explicit actions to the nested Preset
  editor.
- [x] (2026-08-16) Returned saved `CertificateConfiguration` identity from AppFrame dialog
  wrappers and refreshed
  the Library catalog before selecting it.
- [x] (2026-08-16) Added focused unit and real offscreen Library/Preset integration coverage,
  including cancel and active-workflow invariance.
- [x] (2026-08-16) Reconciled parent/release/architecture documentation and completed an
  independent compliance review. The review found stale-catalog construction, missing invalid-
  result evidence, and stale documentation; all were corrected.
- [x] (2026-08-16) Ran focused validation (`35 passed` for the added slice set; independent review
  observed `102 passed`) and full validation (`1559 passed, 20 skipped, 1 warning`), with Ruff,
  compileall, and diff checks clean.
- [x] (2026-08-16) Committed the bounded slice as `b701a095f` (`Add nested certificate create and
  import flow`), verified the commit diff, and removed all 208 FoliaSeal-owned temporary roots;
  no FoliaSeal, Qt, pytest, or audit processes remain.

## Surprises & Discoveries

- The certificate selector already persists `certificate_configuration_id`; only the nested
  creation/import actions and return path are absent.
- Existing certificate dialogs return `CertificateOperationResult`, whose
  `certificate_configuration` is the correct stable object to return. Cancellation and dialog
  failure are represented by `None` at the AppFrame callback boundary.
- A certificate operation commits independently before the parent Preset is saved. If a user
  cancels the parent afterward, the reusable certificate remains in its catalog; this is existing
  reusable-object behavior and does not justify inventing cross-store rollback in this slice.
- Wayland acceptance is deliberately deferred because Mint 22.3 treats Wayland as experimental.

## Decision Log

- Reuse `CertificateManager` and the existing modal dialogs instead of duplicating certificate
  validation or secret handling in the Preset editor.
- Expose separate `Create certificate…` and `Import certificate…` actions so the user can choose
  the intended operation explicitly.
- Return a `CertificateConfiguration` value (or `None`) across the callback seam; reject any
  unexpected result rather than attaching a truthy non-domain object.
- Refresh the catalog through the existing provider, then select the returned stable ID and mark
  only the suspended Preset draft dirty.
- Keep Wayland, certificate password-change workflows, current-document Placement capture,
  packaged release acceptance, and HITL accessibility/display acceptance out of scope.

## Outcomes & Retrospective

The nested Preset editor now exposes explicit Create/Import certificate actions. AppFrame reuses
the existing modal dialogs and returns only a `CertificateConfiguration`; the Library refreshes its
provider-backed catalog before opening a Preset and after a successful operation, then attaches
only the stable ID on explicit Preset Save. Focused validation is `35 passed`; full validation is
`1559 passed, 20 skipped, 1 warning`. The independent review initially found stale-catalog
construction, missing invalid-result evidence, and stale docs; those corrections are complete.
Current-document Placement capture, display/package/final-release acceptance, human accessibility
and DPI checks, and Wayland remain outside this slice.

## Context and Orientation

The nested editor lives in
`src/foliaseal/presentation/qt/signature_preset_editor_widget.py`. The modeless Library composes it
from `src/foliaseal/presentation/qt/app_frame_profile_library.py`; `AppFrame` owns the existing
certificate dialog port and catalog provider in `src/foliaseal/presentation/qt/app_frame.py`.
`CertificateManager` already atomically creates/imports managed files plus matching
`CertificateConfiguration` records. `SavePreset` stores only component IDs.

The governing flow is: create Preset → create/import Certificate → return to suspended Preset →
select Certificate → explicitly Save Preset → explicitly select Preset in the signing rail.

## Scope

### In scope

- Typed nested create/import callbacks from Library through AppFrame.
- Two explicit certificate actions in the nested Preset editor.
- Catalog refresh and stable-ID selector attachment after successful creation/import.
- Truthful cancel/failure handling and rejection of invalid callback values.
- Focused unit, offscreen integration, and active-workflow invariance tests.
- Architecture, parent/release, and this plan updates.

### Out of scope

- Changes to certificate cryptography, storage, secret handling, export, deletion, or password
  change workflows.
- Current-document Placement capture.
- Automatic preset selection, automatic signing, or active-document mutation.
- Wayland execution or acceptance on Mint 22.3.
- Human screen-reader, high-contrast, physical-DPI, multi-monitor, packaged-install, or final
  release acceptance.

## Plan of Work

1. Extend the nested Preset widget controls and constructor with typed create/import callbacks.
2. Implement explicit actions that suspend the parent controls, invoke the callback, refresh the
   certificate catalog, select the returned configuration ID, mark the draft dirty, and notify the
   Library/shell without changing the active signing draft.
3. Thread callbacks through `ReusableObjectLibraryDialog` and `AppFrame`; wrap existing dialog
   results into `CertificateConfiguration | None`.
4. Add focused fake-Qt tests for create, import, cancel, invalid callback results, catalog refresh,
   and parent save; add a real offscreen Library/Preset wiring test and active-workflow invariance.
5. Run the independent compliance review, correct findings, update all owning plans and
   architecture documentation, run full validation, commit, and clean up.

## Milestones

- **M1 — Typed UI seam:** actions and callbacks are present, disabled when unavailable, and do not
  mutate the active document.
- **M2 — Returned identity:** successful create/import refreshes and selects the stable configuration
  ID; cancel leaves selector/catalog/draft unchanged.
- **M3 — Evidence:** focused and offscreen integration tests cover the full nested return path and
  active-workflow invariance.
- **M4 — Closeout:** review, docs, full suite, commit, and cleanup are complete.

## Concrete Steps

- Update `signature_preset_editor_widget.py` with `CertificateConfiguration` typing, public create
  and import controls, a shared attachment helper, and defensive `isinstance` checks.
- Update `app_frame_profile_library.py` with typed callbacks and provider-backed catalog refresh
  before constructing or refreshing the nested editor.
- Update `app_frame.py` with narrow wrappers that call existing creation/import dialog ports and
  return only `result.certificate_configuration` on success.
- Add tests in `tests/unit/test_qt_app_frame_profile_library.py`,
  `tests/integration/test_signature_library_topology.py`, and
  `tests/unit/test_qt_app_frame.py`.
- Update `docs/ARCHITECTURE.md`,
  `docs/ExecPlans/ui_first_use_preset_setup_execplan.md`,
  `docs/ExecPlans/ui_product_support_and_release_execplan.md`, and
  `docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md` with current status and remaining
  gaps.

## Validation and Acceptance

- Focused Qt/unit/integration tests pass for create, import, cancel, invalid return, selector
  refresh, parent save, and active workflow invariance.
- Existing certificate-manager and certificate-dialog tests remain green.
- `.venv/bin/python -m ruff check src tests`, `.venv/bin/python -m compileall -q src tests`, and
  `git diff --check` pass.
- `.venv/bin/python -m pytest -q` passes with the observed count recorded here.
- Independent explorer compliance review reports no unresolved in-scope issue after corrections.
- `git status --short` is clean; no FoliaSeal/Qt/pytest/audit process or `foliaseal-*` temporary
  root remains.

## Idempotence and Recovery

Repeated callback invocation creates distinct reusable certificate entries subject to existing
catalog duplicate-name validation. A canceled or failed dialog returns `None` and leaves the
suspended Preset unchanged. If parent Preset saving is canceled after a successful certificate
operation, the certificate remains reusable in its catalog. Tests use isolated stores and temporary
roots; cleanup targets only exact FoliaSeal-owned prefixes.

## Artifacts and Notes

- New/modified source and test files listed in Concrete Steps.
- This plan is the restart point for any follow-up certificate or first-use work.
- Final commit subject should describe nested certificate creation/import attachment.

## Interfaces and Dependencies

- `CertificateOperationResult.certificate_configuration` is the only certificate value crossing
  into the Preset editor.
- `CertificateConfiguration.certificate_configuration_id` is the persisted reference.
- `certificate_catalog_provider` is the authoritative refresh source.
- The existing `on_reusable_objects_changed` callback remains notification-only; it must not be
  treated as permission to apply a certificate to the active document.

## Revision Notes

- 2026-08-16: Created after explorer review of the completed Placement slice and the governing
  first-use workflow. Explicitly deferred Wayland and current-document Placement capture.
