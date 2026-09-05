# Make same-name Appearance edits transactional and crash-safe

This ExecPlan is a living document and must be maintained in accordance with
`/home/daekar/.codex/skills/write-execplan/PLANS.md`. It is a focused child of
`docs/ExecPlans/gui_hitl_defect_recovery_parent_execplan.md` and must be completed before the
installed release matrix resumes beyond the Appearance-edit gate.

## Purpose / Big Picture

An Appearance is a reusable visual signature definition. When a user opens an existing Appearance,
changes its fields, and saves without changing its display name, FoliaSeal must update that same
profile rather than report a false duplicate. The stable profile identity must remain intact so
presets that reference it continue to resolve. A user who temporarily renames the profile and then
renames it back must see a normal conflict decision or a successful update, never a native crash or a
document-preview refresh loop.

This slice fixes the transaction boundary in the application and Qt editor, proves same-name and
rename-away/rename-back behavior with focused tests, and adds a live installed-package gate. It does
not redesign the Appearance editor, change profile schemas, or replace the PDF backend.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/SCHEMAS.md` are available and authoritative.
- [x] `docs/ExecPlans/ui_appearance_editor_transaction_execplan.md` defines the existing stable-ID
  and nested-editor behavior that this correction must preserve.
- [x] `docs/ExecPlans/gui_preset_pdf_lifecycle_stability_parent_execplan.md` records the installed
  crash evidence and package identity.
- [ ] `docs/ExecPlans/gui_placement_interaction_stability_execplan.md` must separately address the
  placement-release refresh spike; do not hide that failure inside this profile transaction slice.

## Progress

- [x] (2026-09-04) Human acceptance reproduced false duplicate rejection when editing an Appearance
  under its existing name, then a crash after renaming it away and back.
- [x] (2026-09-04) Source audit located the Qt editor save path in
  `presentation/qt/appearance_profile_editor_widget.py` and duplicate/identity enforcement in
  `application/reusable_signing_objects.py`.
- [x] (2026-09-04) Added application and Qt editor tests for same-name edits, different-profile
  collisions, rename-away/rename-back identity, and dependent preset references.
- [x] (2026-09-04) Implemented identity-aware Appearance duplicate handling and skipped expensive
  preview regeneration for placement-only updates and unchanged profile refreshes.
- [x] (2026-09-04) Focused suites pass (`183 passed`); full suite passes (`1616 passed, 20 skipped,
  1 warning`), and Ruff/compileall/diff checks are clean. Fresh package audits pass.
- [x] (2026-09-04) Fresh package executable SHA-256 is `ae2e2cca...fe797`; the
  package is installed over the prior `0.1.0` and `/usr/bin/foliaseal` launched
  successfully on Cinnamon/X11 for the live retest.
- [ ] Repeat the installed edit/save/rename-back gate on Cinnamon/X11 and record the result in the
  release matrix; clean all owned processes and temporary artifacts.

## Surprises & Discoveries

- Observation: `AppearanceProfileEditorWidget.save()` sets `overwrite=False` for all edits, even when
  `appearance_profile_id` identifies the same profile. `ReusableSigningObjects._apply()` then calls
  duplicate checking and rejects the unchanged name.
  Evidence: `appearance_profile_editor_widget.py::save()` and
  `reusable_signing_objects.py::_apply(SaveAppearance)`.
- Observation: the native coredump reached `QPdfDocument::load()` from a Qt button callback. The
  appearance rename callback has no reason to load a PDF, so any such load indicates an unintended
  workspace/preview refresh coupling rather than a valid profile mutation.
  Evidence: coredump PID `1221992` (`SIGABRT`, Qt6Pdf `QPdfDocument::load`) and the installed HITL
  sequence.
- Observation: profile IDs are references used by presets; replacing an object under the same ID is
  safe, while silently generating a new ID would orphan dependent presets.
  Evidence: `SaveAppearance.appearance_profile_id`, catalog resolution, and `SCHEMAS.md` profile
  identity requirements.

## Decision Log

- Decision: treat an edit with the same name and same profile ID as an in-place update, without a
  duplicate prompt.
  Rationale: the name belongs to the object being edited; rejecting it is a false conflict and makes
  ordinary edits impossible.
  Date/Author: 2026-09-04 / Codex.
- Decision: continue rejecting a same-name collision when the name resolves to a different profile ID.
  Rationale: silently merging two reusable objects would alter unrelated presets and violate explicit
  user control over reusable signing material.
  Date/Author: 2026-09-04 / Codex.
- Decision: keep profile-only save/rename mutations document-independent and do not trigger a PDF
  render or viewer refresh.
  Rationale: UI_SPEC requires reusable-object edits to preserve the active placement and document;
  native QtPdf loading is the separate placement stability concern.
  Date/Author: 2026-09-04 / Codex.

## Outcomes & Retrospective

At completion, same-name Appearance edits will save successfully with the original stable ID,
different-profile collisions will remain recoverable validation errors, dependent presets will still
resolve, and rename-away/rename-back will not crash or reload the active PDF. The installed package
must demonstrate this behavior; passing unit tests alone is insufficient. If the live path still
causes a QtPdf load, record the exact callback and hand the remaining issue to the placement/PDF
lifecycle child rather than declaring this plan complete.

## Context and Orientation

`AppearanceProfileEditorWidget` owns the isolated Qt draft and emits `SaveAppearance`. The application
service `ReusableSigningObjects` applies that command to the typed catalog and persists profiles.
`SignaturePreset` stores an appearance-profile ID, so identity must survive edits. The active PDF
workspace is owned by the signing shell and should not be refreshed for a document-independent
catalog mutation. Existing profile-library callbacks may refresh selectors, but they must not invoke
viewer rendering as a side effect.

## Plan of Work

First add tests that construct an isolated catalog with one Appearance and a preset referencing it.
Open the editor with that profile reference, change a visible field, leave the name unchanged, call
`save()`, and assert success, unchanged profile ID, updated field data, and a still-resolving preset.
Add a second profile and assert that attempting to rename the first to the second’s name returns the
existing validation error without changing either profile. Add a rename-away/rename-back sequence
through the public library/editor seam and assert that each successful save preserves the expected ID
and that the document-refresh/viewer callback count remains zero.

Then correct the smallest boundary. The Qt editor should pass the initial profile ID on edits and
request overwrite only when a conflict is a different object; the application layer should recognize
the same-ID case as an allowed replacement while retaining duplicate rejection for different IDs.
Catalog refresh callbacks should update reusable-object selectors only. Do not catch native aborts,
add broad exception handling, or introduce a second profile store.

After focused tests pass, run the full validation suite and rebuild the package from the corrected
checkout. Install that exact package over the existing `0.1.0` host installation, launch on
Cinnamon/X11 with the disposable PDF, and perform: edit an existing Appearance under its original
name and save; rename it away and save; rename it back and save; verify the dependent preset and the
active placement remain intact. Record any dialog text, process/resource behavior, and whether the
PDF viewer changed. Close only the owned FoliaSeal process and remove owned temporary files.

## Milestones

Milestone 1 is the red test set: same-name edit, different-ID collision, dependent-preset resolution,
and zero document-refresh expectations fail or expose the current defect. Milestone 2 implements the
identity-aware save decision and makes all focused tests green. Milestone 3 validates the complete
suite and installed package, then records the human result and cleanup evidence in the parent and
release plans.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`.

    rg -n "class AppearanceProfileEditorWidget|SaveAppearance|_check_duplicate|rename_appearance_profile|refresh_signature_profiles" src/foliaseal tests/unit
    .venv/bin/pytest -q tests/unit/test_qt_appearance_profile_editor.py tests/unit/test_reusable_signing_objects.py tests/unit/test_qt_app_frame_profile_library.py
    .venv/bin/pytest -q
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src
    git diff --check

Rebuild and audit a fresh package in an owned `/tmp/foliaseal-appearance-stability-*` directory using
the existing Debian builder and `scripts/deb_package_audit.py`. Install only after recording the
package checksum and current host package state. The installed binary under test must be
`/usr/bin/foliaseal`, not a source-tree Python entry point.

## Validation and Acceptance

The plan passes only when focused tests prove same-name in-place save, different-ID conflict rejection,
stable dependent references, and zero document/PDF refresh for profile-only edits; the full suite,
Ruff, compileall, and diff checks pass; the fresh package passes offline, private-install-root, and
display-backed X11 audits; and the human installed session completes edit/save/rename-away/rename-back
without a crash, runaway resource use, placement loss, or unexpected document refresh.

## Idempotence and Recovery

Use an isolated catalog fixture for tests and a disposable Appearance name for live acceptance. If a
save fails, leave the editor open, record the exact validation message, and do not delete user profiles.
If the GUI crashes, preserve the coredump ID and timestamp, close only the recorded FoliaSeal PID, and
stop this gate until a focused test explains the path. Restore the prior package only if the release
procedure requires it; never remove the user’s certificate or profile store.

## Artifacts and Notes

Commit only source, focused tests, this plan, and concise status/documentation updates. Do not commit
packages, private keys, certificates, PDFs, coredumps, screenshots containing document content, or
machine-local temporary paths. Record the package version/hash, exact test command results, human
observations, and cleanup verification in the parent and installed-release plans.

## Interfaces and Dependencies

Use `AppearanceProfileEditorWidget.save()`, `SaveAppearance`, `ReusableSigningObjects.execute()`,
`SignaturePresetCatalog`, and the existing Library/editor callback seams. Preserve stable
`appearance_profile_id` references and the application-owned catalog as the source of truth. Do not
call `viewer.refresh()`, `QtPdfRenderBackend`, or any document-load API from a document-independent
Appearance mutation.

## Revision Note

Created on 2026-09-04 after installed Gate 2 reproduced false same-name Appearance rejection and a
rename-back crash. The plan deliberately separates profile transaction correctness from the placement
rectangle/PDF refresh spike so each failure has an independently testable owner.
