# Close reusable signing-object compliance gaps

This child ExecPlan is a living document maintained under
`.agents/skills/write-execplan/PLANS.md`. It is required by the parent
`docs/ExecPlans/reusable_signing_objects_hybrid_execplan.md` because the first
architecture/spec review found behavior gaps after the initial implementation.

## Purpose / Big Picture

The reusable-object boundary is implemented, but the dedicated Settings
library does not yet offer an explicit create/edit path, inline preset overwrite
can orphan component objects, and malformed catalogs can carry dangling or
appearance-less presets until a later operation. This child closes those gaps
without changing the historical catalog path or stable evidence contracts.

## Child ExecPlan Dependencies

- [x] Parent typed boundary and caller migration are implemented.
- [x] Two independent compliance reviews reported the same Settings-library
  management gap and confirmed the dangling-reference/overwrite risks.
- [x] Parent documentation and final commit closure are complete after this
  child and the final full-suite audit.

## Progress

- [x] (2026-08-02) Recorded primary and secondary review findings.
- [x] (2026-08-03) Added explicit Settings-library create/edit actions that
  delegate rich appearance/placement editing to the contextual signing
  workflow through typed callbacks.
- [x] (2026-08-03) Inline preset overwrite preserves existing component IDs and
  updates the referenced records without orphaning generated components.
- [x] (2026-08-03) Repository load rejects malformed/dangling or
  appearance-less preset references; coordinator application maps malformed
  preset resolution to its existing error boundary.
- [x] (2026-08-03) Added focused regression coverage and reconciled README and
  architecture prose.
- [x] (2026-08-03) Post-fix compliance review passed; commit hash remains for
  the root agent to record after commit.

## Surprises & Discoveries

- Observation: SPEC requires full create/edit/delete management in a dedicated
  library while appearance and placement editing must remain contextual.
  Evidence: `docs/SPEC.md` sections 5 and Reusable Object Semantics.
- Observation: Inline `SavePreset` currently uses `ResolvedSignaturePreset` and
  can generate new component IDs when overwriting a composed preset.
  Evidence: `src/foliaseal/application/reusable_signing_objects.py` and the
  coordinator's `_save_current_preset` path.
- Observation: `SignaturePresetCatalog` accepts dangling IDs at construction.
  Evidence: `resolve_preset()` fails later, while a loaded library view renders
  missing component names as `none`.

## Decision Log

- Decision: The Settings library will expose `Create` and `Edit in signing
  workflow` actions, while the existing contextual refinement dialog remains
  the editor for appearance/placement values.
  Rationale: this satisfies the dedicated management entry point without
  duplicating the rich contextual form in a second Qt module.
  Date/Author: 2026-08-02 / Codex.
- Decision: Inline preset saves will update existing referenced component
  records when overwriting, preserving their IDs; new components receive one
  stable ID and are referenced by the resulting preset.
  Rationale: presets remain reference-only and overwrite cannot orphan the
  user's previously composed components.
  Date/Author: 2026-08-02 / Codex.
- Decision: Validate preset references when loading the canonical catalog and
  report malformed preset application as `SignaturePropertiesCoordinatorError`.
  Rationale: invalid persisted data should fail at the repository boundary,
  not leak a raw schema exception from a later UI action.
  Date/Author: 2026-08-02 / Codex.

## Outcomes & Retrospective

The dedicated `ReusableObjectLibraryDialog` now exposes create, contextual
edit, rename, and reference-guarded delete actions while keeping rich editing
in the signing refinement workflow. Preset overwrite preserves referenced
appearance/placement IDs, and repository decoding validates all references
before a catalog view is exposed. Partial presets without certificate
references remain valid and receive explicit coordinator guidance. The focused
reusable-object/coordinator/session/Qt/storage suite passed **183 tests**;
Ruff, compileall, and `git diff --check` are clean. Current README and
architecture prose document the typed boundary, repository-only persistence,
historical storage path, callbacks, and validation. Stable Phase 3 evidence
contracts were not renamed. The root agent records the final commit hash.

## Context and Orientation

`ReusableSigningObjects` is the typed application boundary. Its repository is
`SignaturePresetCatalogStore`, which owns the historical
`Signature Profiles/profiles.json` path and atomic JSON writes. The Settings
dialog is `ReusableObjectLibraryDialog`; the contextual editor is
`SigningWorkspacePropertiesPanel.open_refinement_dialog()`.

The parent slice already removed the old `SignatureProfileLibrary`, string
prefix parsing, and store CRUD helpers. This child must not restore those
interfaces or rename stable Phase 3 evidence names.

## Plan of Work

Add create and contextual-edit controls to
`src/foliaseal/presentation/qt/app_frame_profile_library.py`. The dialog will
accept callbacks supplied by `app_frame.py`, expose a `Create` action and an
`Edit in signing workflow` action, and retain typed references in item data.
The app frame callback will use the active signing workspace's explicit
contextual-editor port; when no PDF is open it will show a clear actionable
message. Add a narrow shell-port verb for opening that editor rather than
reaching through private widget fields.

Change `ReusableSigningObjects._apply(SavePreset)` so an inline save first
locates an existing preset by name. When overwriting, preserve its existing
appearance and placement IDs, update those component records in the same
catalog transformation, and write one reference-only preset. When creating a
new preset, create only the requested component records and reference them from
the preset. No generated component is silently discarded.

Add `SignaturePresetCatalog.validate_references()` and call it after canonical
JSON decoding and legacy migration. It must reject missing appearance or
placement IDs and presets without an appearance reference, using
`ConfigValidationError`. Wrap `resolve()`/appearance access in the coordinator
apply path so user-facing callers receive `SignaturePropertiesCoordinatorError`.

Add tests for Settings create/edit callback wiring, inline overwrite ID
preservation and single-catalog update, dangling-reference load rejection,
appearance-less preset rejection, and coordinator error mapping. Update the
parent focused counts and current architecture prose.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/python -m pytest -q tests/unit/test_reusable_signing_objects.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_app_frame.py
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    git diff --check

Expected focused output is green tests, clean Ruff/compile/diff checks, and no
old library facade or string-prefix references.

## Validation and Acceptance

The child is complete when Settings visibly offers create/edit/delete paths,
contextual editing remains the only rich appearance/placement editor, preset
overwrite preserves component IDs and references, invalid persisted references
fail during load, malformed preset application is translated to the existing
coordinator error, and the focused plus full test suites pass.

## Idempotence and Recovery

All fixes operate on temporary catalogs in tests. Preserve the historical path
and legacy reader. If a repository validation change breaks a fixture, repair
the fixture or add an explicit migration case; do not relax reference
validation or restore string-based compatibility APIs.

## Artifacts and Notes

Record review reports, focused/full test counts, the architecture diff, and the
implementation and closure commit hashes here and in the parent plan.

## Interfaces and Dependencies

The shell-facing addition is a typed contextual-editor verb on
`SigningWorkspacePort`; the Qt implementation delegates to the existing
properties-panel refinement entry point. The reusable-object application API
remains `view()`, `resolve()`, and `execute(command)`.

## Revision Notes

2026-08-02: Created from two independent compliance reviews after the initial
hybrid implementation. The child is intentionally limited to SPEC management,
reference integrity, and error-boundary closure.
2026-08-03: Closed after the postfix review, documentation reconciliation,
1024-test full-suite run, and final clean-tree/process audit; commit hashes are
recorded by the root agent. Implementation commit:
`d9b29cc178d09d3068fba7691ff9a6f944545c47`.
