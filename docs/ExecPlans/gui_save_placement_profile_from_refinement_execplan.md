# Save a placement profile from the refinement dialog

This ExecPlan is a living document maintained under `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

Users can save the currently edited visible-signature rectangle as a named reusable Placement Profile without applying it to the PDF or closing the refinement dialog. The saved profile means “use this rectangle on the current page,” not “use page N of this document,” so it remains reusable across PDFs.

## Child ExecPlan Dependencies

- [x] Catalog ownership and persistent placement-profile storage exist.

## Progress

- [x] (2026-07-17 00:00Z) Reviewed the live placement draft and storage seam.
- [x] (2026-07-17 00:00Z) Added `SaveCurrentPlacementProfile`, the session wrapper, and coordinator regression tests for rectangle persistence, fixed `current_page` semantics, and disabled-placement rejection.
- [x] (2026-07-17 00:00Z) Added `Save placement for reuse...` to the refinement dialog plus a Qt regression test that proves the dialog stays open and cancellation leaves the live draft unchanged.
- [x] (2026-07-17 00:00Z) Ran focused coordinator and Qt tests, plus Ruff for touched application and Qt files.
- [x] (2026-07-18) Ran the display-backed representative-PDF startup audit after the Settings library landed; the live workspace mounted with the saved catalog after legacy-profile migration coverage was added.
- [x] (2026-07-19) Completed the semantic real-Qt save walkthrough in `scripts/live_gui_parent_audit.py`: the mounted refinement control visibly saved an appearance and a placement profile, then composed and reselected a preset before signing/reopen evidence was captured. Focused application/storage tests prove the persisted placement's reusable `current_page` semantics.

## Surprises & Discoveries

- Observation: the one-based draft page number is document context, while the storage schema already represents reusable placement as `current_page` plus a PDF-space rectangle.
  Evidence: `VisibleSignaturePlacementDraft.page_number` is converted to a live `SignatureRect`; `SignaturePresetCatalogStore.save_placement_profile` writes `page_selection_mode="current_page"`.

## Decision Log

- Decision: do not persist the draft page number.
  Rationale: `docs/SPEC.md` requires placement profiles not to be document-bound; persisting a page number would silently create that coupling.
  Date/Author: 2026-07-17 / Codex

## Outcomes & Retrospective

The placement-profile save tracer bullet is complete at the application and Qt boundaries. Focused application/storage tests establish that it persists only the edited PDF-space rectangle as a reusable `current_page` template and never the draft's document-specific page number. The final semantic real-Qt walkthrough on 2026-07-19 visibly saved the profile through the mounted dialog, composed it into a preset, reselected that preset, and completed sign/reopen verification.

## Context and Orientation

The refinement dialog in `signing_workspace_properties_panel.py` builds a `VisibleSignatureSetupDraft`. Its placement contains enabled state and PDF-space left, bottom, width, and height values. `profile_storage.py` already persists those values in a named `PlacementProfile` with `page_selection_mode="current_page"`.

## Plan of Work

Add `SaveCurrentPlacementProfile(name, placement, overwrite=False)` to `signature_properties_coordinator.py`, reject blank names and disabled placement, and delegate the rectangle to `SignaturePresetCatalogStore.save_placement_profile`. Expose it through `SigningSetupSession`. Add `Save placement for reuse...` beside the existing appearance action; it prompts for a name, builds the dialog draft, saves only the placement, reports errors, and leaves the dialog and live workflow unchanged. Add coordinator and Qt tests before each implementation step.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/pytest -q tests/unit/test_signature_properties_coordinator.py -k placement_profile
    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py -k placement_profile
    .venv/bin/pytest -q tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_preset_storage.py

## Validation and Acceptance

Open a PDF, refine a placement, save it as `Bottom right`, cancel the dialog, and confirm the live draft was not changed while the JSON catalog contains the named profile with the edited rectangle and `current_page` semantics.

## Idempotence and Recovery

Canceling the name prompt changes nothing. Duplicate names never overwrite without explicit confirmation. This slice does not implement applying, editing, or deleting placement profiles.

## Artifacts and Notes

Only behavior changes, focused tests, and plan status updates are allowed. Do not add preset composition, Settings management, or certificate work.

## Interfaces and Dependencies

Use `SignaturePresetCatalogStore.save_placement_profile` as the only persistence boundary. Keep storage out of Qt. The public session method must accept `VisibleSignaturePlacementDraft` and preserve all current workflow state.

Revision note: 2026-07-17 / Codex
Closed the application/Qt slice after compliance review. The restart walkthrough remains deferred to the Settings-library milestone because the shell cannot yet inspect independent placement profiles.

Revision note: 2026-07-19 / Codex
Closed the stale live-walkthrough checkbox after `scripts/live_gui_parent_audit.py` exercised the visible refinement save and reusable preset path as part of the nine-checkpoint parent acceptance audit. The audit is evidence of visible save/compose/reselect behavior; focused application/storage tests remain the evidence for `current_page` persistence semantics.
