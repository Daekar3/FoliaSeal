# UI compatibility and release-gate retirement

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK child of
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md` and closes only
compatibility work that can be proven from the current checkout. It does not
claim human display acceptance, privileged host installation, or Wayland
support.

## Purpose / Big Picture

After this slice, the preview/layout path has one canonical request type and
one public fit-validation entry point. The obsolete `LayoutRequest` alias and
the private `_visible_signature_fit_issues_for_stamp_text` delegating wrapper
are removed after every production and test caller migrates. The release
corpus records which compatibility surfaces are still required, and Wayland is
explicitly deferred until Linux Mint treats it as a first-class supported
session. This turns two stale compatibility checkboxes into evidence-backed
status rather than silently retaining dead names.

## Child Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/SCHEMAS.md` are the governing
  contracts in that order.
- [x] `docs/ExecPlans/ui_preview_fidelity_fit_validation_execplan.md` owns the
  authoritative preview/signing parity behavior; this child only retires its
  proven internal aliases.
- [x] `docs/ExecPlans/ui_product_support_and_release_execplan.md` owns final
  display-backed, packaged, privileged-install, and release-matrix gates.
- [x] The Cinnamon/X11 source-tree audit is complete; Wayland is intentionally
  out of scope for the current Mint 22.3 environment.

## Progress

- [x] (2026-08-16) Audited open release plans and current consumers. The layout
  alias and backend fit wrapper are internal compatibility names with complete
  in-repository callers; AppFrame dialog exposure and Acceptance evidence
  contracts remain live consumers and are not safe to delete.
- [x] (2026-08-16) Migrated all callers from `LayoutRequest` to
  `VisibleSignatureLayoutInput` and remove the alias/export.
- [x] (2026-08-16) Replaced direct tests/callers of the private fit wrapper with
  `validate_visible_signature_fit()` and remove the wrapper.
- [x] (2026-08-16) Focused layout/preview/backend validation passed `259`; the
  full 161-file suite was run in four isolated batches for `1537 passed, 20
  skipped, 1 warning`. Ruff, compileall, diff checks, and consumer scans pass;
  no owned processes or temporary roots remain.
- [x] (2026-08-16) Reconciled child/parent/release documentation and recorded
  Wayland deferral. Independent explorer and architecture/documentation reviews
  returned GO after the sentinel and command-path corrections.
- [x] (2026-08-16) Corrected the intentional source-absence regression sentinel
  so the documented retired-name scan is empty; the boundary suite is `26
  passed` and `git diff --check` remains clean.
- [x] (2026-08-16) Committed as `01a0bf20d` (`refactor: retire proven
  compatibility aliases`); the post-commit checkout is clean.

## Surprises & Discoveries

- `AppFrameDialogCompatibilityState`, `CertificateDialogCompatibilityState`,
  and `SigningWorkspaceShell.testing_adapter` still have active production or
  test consumers. They are compatibility/test seams, not dead code, so this
  slice must leave them intact and document their retirement conditions.
- Acceptance-named CLI/DTO/artifact contracts are intentionally observable
  evidence interfaces. Renaming them here would violate the release evidence
  boundary and is not required for a truthful UI cleanup.
- Wayland cannot be claimed from the current Mint 22.3 session. The acceptance
  record must distinguish the completed X11 evidence from the deferred Wayland
  gate.

## Decision Log

- Decision: remove only aliases whose consumers can be migrated entirely in
  this checkout; preserve externally observable evidence contracts and active
  Qt test seams.
  Rationale: compatibility retirement must reduce surface area without
  breaking the frozen product or test contracts.
  Date/Author: 2026-08-16 / Codex
- Decision: use `VisibleSignatureLayoutInput` as the sole neutral input type
  for `VisibleSignatureLayoutEngine.plan()` and `.validate()`.
  Rationale: it is already the governing architecture name and has identical
  fields to the obsolete subclass alias.
  Date/Author: 2026-08-16 / Codex
- Decision: call `validate_visible_signature_fit()` directly from the backend
  and focused tests.
  Rationale: the wrapper adds no behavior and its public boundary is already
  covered by dedicated validation tests.
  Date/Author: 2026-08-16 / Codex
- Decision: defer Wayland acceptance until Mint provides a first-class,
  supported Wayland session.
  Rationale: the user explicitly removed experimental Mint 22.3 Wayland from
  the current acceptance target; X11 evidence remains the supported display
  result.
  Date/Author: 2026-08-16 / Codex

## Outcomes & Retrospective

To be completed after implementation and review. It must state the exact
aliases removed, focused/full validation results, retained live compatibility
seams, Wayland deferral, commit id, and remaining release gates.

## Context and Orientation

The neutral visible-signature layout boundary is implemented in
`src/foliaseal/application/visible_signature_layout.py`. Preview and evidence
adapters construct layout requests in
`src/foliaseal/presentation/qt/signature_preview_layout.py` and
`src/foliaseal/presentation/qt/interactive_harness.py`; application exports
are assembled in `src/foliaseal/application/__init__.py`. Backend fit
validation lives in `src/foliaseal/application/signing_backend.py`.

The current product flow remains open, review, reusable setup, placement,
preview, sign/save, verify, and reopen. No V2 feature, schema migration,
packaging mutation, or display-only workaround belongs in this slice.

## Change Slice

Primary change class: compatibility-retirement refactor with documentation
status reconciliation. Allowed files are the named layout/backend modules,
their focused tests, `docs/ARCHITECTURE.md`, the affected child/release plans,
and this plan. Generated artifacts, certificates, private keys, and package
outputs are disposable only and must not be committed.

## Plan of Work

1. Inventory exact imports and references with `rg`; confirm the two aliases
   have no external checkout consumer beyond the files named below.
2. Replace `LayoutRequest` with `VisibleSignatureLayoutInput` in the engine,
   preview/evidence adapters, application lazy exports, and tests. Remove the
   subclass and its `__all__`/lazy-export entry.
3. Replace backend/test calls to
   `_visible_signature_fit_issues_for_stamp_text()` with
   `validate_visible_signature_fit()` and remove the private wrapper. Keep
   backend-specific `_build_stamp_style` and other behavior-bearing adapters
   unchanged.
4. Run focused tests, full pytest, Ruff, compile/import checks, diff checks,
   and a final consumer scan proving the retired names are absent from active
   code. Run the existing X11 source-tree audit only if the changed import
   surface warrants it; do not launch Wayland.
5. Update the release/preview/single-instance/no-document child plans and the
   parent/architecture record: close only the retired aliases, explicitly
   retain active compatibility seams with consumers, and mark Wayland deferred
   pending a supported OS/session. Do not mark screen-reader, physical DPI,
   multi-monitor, packaged GUI, privileged install, or final human release
   gates complete.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    rg -n '\\bLayoutRequest\\b|_visible_signature_fit_issues_for_stamp_text' src tests docs/ARCHITECTURE.md
    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_visible_signature_layout_boundary.py tests/unit/test_signing_backend.py tests/unit/test_signing_preview_renderer.py tests/unit/test_signature_preview_layout.py
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    .venv/bin/pytest -q
    git diff --check
    rg -n '\\bLayoutRequest\\b|_visible_signature_fit_issues_for_stamp_text' src tests || true
    rg -n 'Wayland|Mint 22\\.3|compatibility|legacy acceptance' docs/ExecPlans docs/ARCHITECTURE.md

All tests must run with the repository `.venv`; do not silently substitute a
system Python or Qt installation. Any display-backed command must be bounded,
owned, and cleaned up. This slice does not run Wayland.

## Validation and Acceptance

Acceptance requires:

- no active source or test reference to `LayoutRequest` or
  `_visible_signature_fit_issues_for_stamp_text`;
- layout, preview, backend, and evidence behavior remains green through the
  focused suite and full suite;
- `ruff`, compileall, import checks, and `git diff --check` pass;
- architecture and ExecPlans identify the remaining live compatibility seams
  and their retirement conditions rather than claiming all compatibility is
  gone;
- Wayland is recorded as deferred, while X11 evidence remains the supported
  display-backed result;
- no FoliaSeal, PySide6, pytest, or helper processes/dialogs and no temporary
  roots owned by this slice remain after validation.

## Idempotence and Recovery

Edits are source/docs-only and safe to repeat. If a migration fails, restore
the canonical names in the affected file only, record the failing consumer in
`Surprises & Discoveries`, and do not resurrect the alias globally without a
named consumer and retirement condition. Remove only temporary roots created
by this slice. Never use destructive Git commands.

## Artifacts and Notes

Record focused/full command results and the final consumer-scan result in this
plan. Keep any local reports under ignored `artifacts/` or `/tmp`; do not
commit generated PDFs, certificates, screenshots, package files, or absolute
machine-local paths.

## Interfaces and Dependencies

`VisibleSignatureLayoutEngine.plan()` and `.validate()` accept
`VisibleSignatureLayoutInput`. Backend callers use the public
`validate_visible_signature_fit()` function. Qt and evidence adapters remain
application-boundary consumers and must not import backend-private layout
helpers. Existing active dialog/test seams remain until their owning release
plans prove migration.

Revision note: 2026-08-16 / Codex: created after a fresh release-plan audit;
scope narrowed to proven internal alias retirement and explicit Wayland
deferral.
