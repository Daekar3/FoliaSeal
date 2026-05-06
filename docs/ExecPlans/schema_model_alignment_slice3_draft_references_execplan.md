# Refactor Draft Workflow Toward Reusable Object References

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `.agents/skills/write-execplan/PLANS.md` and is a child plan of `docs/ExecPlans/schema_model_alignment_execplan.md`.

## Purpose / Big Picture

This slice moves `SigningDraftWorkflow` away from being the center of reusable-object persistence. After this change, the draft can remember which canonical reusable objects are selected, the Qt shell can apply and capture reusable signing setup through canonical method names, and certificate preview field extraction can be injected through a service instead of being hard-coded inside the draft object.

The user-visible behavior should remain the same: saved signature setup entries can still be saved, selected, deleted, and reloaded in the current Qt shell. The architectural payoff is that later slices can wire certificate configurations and app settings into the GUI without first untangling raw draft-owned persistence methods.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/schema_model_alignment_slice1_profiles_execplan.md` split appearance, placement, and signature preset persistence.
- [x] `docs/ExecPlans/schema_model_alignment_slice2_certificates_execplan.md` added certificate configuration persistence and signing-material resolution.

## Progress

- [x] (2026-05-06 22:34Z) Inspected current `SigningDraftWorkflow`, profile controls in the Qt shell, and workflow/shell tests.
- [x] (2026-05-06 22:35Z) Added focused tests for selected reusable-object ids, canonical preset apply/capture methods, and injected certificate preview reading.
- [x] (2026-05-06 22:36Z) Implemented a certificate preview reader service/protocol and injected it into `SigningDraftWorkflow`.
- [x] (2026-05-06 22:36Z) Added draft fields for selected `CertificateConfiguration`, `AppearanceProfile`, `PlacementProfile`, and `SignaturePreset` ids.
- [x] (2026-05-06 22:36Z) Moved shell calls from old profile-oriented workflow methods to canonical methods while preserving compatibility aliases for harness/test call sites not migrated in this slice.
- [x] (2026-05-06 22:38Z) Updated architecture and parent ExecPlan documentation.
- [x] (2026-05-06 22:40Z) Ran focused validation, lint, and the full test suite successfully.
- [x] (2026-05-06 22:41Z) Committed the completed slice as `87509136b refactor: add draft reusable object references`.

## Surprises & Discoveries

- Observation: The Qt shell already persists canonical `SignaturePreset` objects after Slice 1, but the method names and UI labels still say "profile".
  Evidence: `SignaturePropertiesPanel.save_current_profile()` calls `SigningDraftWorkflow.capture_signature_preset()` and `SignaturePresetCatalog.upsert_profile()`.

- Observation: The draft owns a PKCS#12 parsing method directly.
  Evidence: `SigningDraftWorkflow._certificate_values_for_preview()` reads `Path(self.certificate_path).read_bytes()` and calls `pkcs12.load_key_and_certificates(...)`.

- Observation: Focused workflow and shell tests are green after adding canonical methods and the reader seam.
  Evidence: `.venv/bin/pytest -q tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py` reported `72 passed in 4.05s`.

- Observation: Full-suite validation remains green after the Slice 3A refactor.
  Evidence: `.venv/bin/ruff check .` reported `All checks passed!`, and `.venv/bin/pytest -q` reported `583 passed, 1 warning in 37.31s`.

## Decision Log

- Decision: Treat this as Slice 3A, not the entire Slice 3.
  Rationale: The full Slice 3 includes certificate-configuration UI integration and broader draft ownership cleanup. A smaller first step creates canonical draft reference state and a certificate-preview seam without mixing in a large Qt redesign.
  Date/Author: 2026-05-06 / Codex

- Decision: Keep backward-compatible aliases for old workflow methods during this slice.
  Rationale: The current shell and harness tests are broad. Updating the primary shell call sites and adding canonical methods moves the boundary while avoiding a noisy unrelated rename across every existing test in one commit.
  Date/Author: 2026-05-06 / Codex

- Decision: Put certificate preview extraction behind an application-layer service.
  Rationale: The draft should own selected values and session state. Reading PKCS#12 files is a service concern that can later resolve from `CertificateConfiguration` instead of raw file paths.
  Date/Author: 2026-05-06 / Codex

## Outcomes & Retrospective

Implemented Slice 3A. `SigningDraftWorkflow` now has selected reusable-object id fields, canonical `capture_current_signature_setup()` and `apply_resolved_signature_preset()` methods, and compatibility aliases for old profile-oriented call sites. Certificate preview extraction moved to `src/foliaseal/application/certificate_preview.py`, where `Pkcs12CertificatePreviewReader` owns PKCS#12 parsing and the draft calls an injected `CertificatePreviewReader`.

The Qt shell save/select code now calls the canonical workflow methods, while the UI still says "Named profiles" and the catalog compatibility methods still use profile terminology. That remaining terminology cleanup is intentionally deferred until certificate configuration UI integration is ready.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. `SigningDraftWorkflow` lives in `src/foliaseal/application/signing_draft_workflow.py`. The Qt signing shell profile controls live in `src/foliaseal/presentation/qt/signing_shell.py`. Reusable signing object schemas live in `src/foliaseal/infra/config/schemas.py`.

In this plan, a "draft" means the mutable state for the currently open signing session. It can remember selected reusable object ids and snapshots, but it should not be responsible for saving reusable objects to disk.

## Plan of Work

First, add or update tests in `tests/unit/test_signing_draft_workflow.py` to require the draft to expose canonical selection fields and canonical methods. The tests should prove that applying a resolved preset records selected preset, appearance, and placement ids; capturing the current setup returns a resolved preset without storing it; and certificate preview values can come from an injected reader without the draft reading a PKCS#12 file directly.

Second, add an application-layer certificate preview service, likely in a new `src/foliaseal/application/certificate_preview.py` module. It should define a small result dataclass, a protocol, and the existing PKCS#12 implementation moved out of `SigningDraftWorkflow`. The workflow should call the injected reader and cache its result as it does today.

Third, update `SigningDraftWorkflow` with canonical selection fields: `selected_certificate_configuration_id`, `selected_appearance_profile_id`, `selected_placement_profile_id`, and `selected_signature_preset_id`. Add canonical methods such as `capture_current_signature_setup()` and `apply_resolved_signature_preset()`. Keep `capture_signature_preset()` and `apply_signature_preset()` as compatibility wrappers that delegate to the canonical methods.

Fourth, update `src/foliaseal/presentation/qt/signing_shell.py` so save/select code calls the canonical methods. The UI label can remain "Named profiles" in this slice if changing the user-facing wording would expand test churn; the architecture docs should record that UI terminology remains transitional.

Fifth, update `docs/ARCHITECTURE.md` and the parent schema alignment ExecPlan to record Slice 3A completion and remaining Slice 3 work.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`.

Focused iteration:

    .venv/bin/pytest -q tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py

    Output observed on 2026-05-06:

        72 passed in 4.05s

Broader regression:

    .venv/bin/ruff check .
    .venv/bin/pytest -q

    Output observed on 2026-05-06:

        All checks passed!
        583 passed, 1 warning in 37.31s

## Validation and Acceptance

This slice is accepted when the draft workflow exposes selected reusable object references, shell save/select paths use canonical workflow methods, certificate preview parsing is no longer implemented directly inside the draft class, focused tests pass, lint passes, and the full test suite passes.

Compatibility aliases may remain, but docs must clearly identify them as transitional.

## Idempotence and Recovery

The changes are source and test changes only. No generated artifacts should be committed. If the refactor causes broad shell failures, keep the canonical methods and reader seam but restore compatibility wrappers rather than rewriting unrelated UI behavior.

## Artifacts and Notes

No generated artifact files are part of this slice.

## Interfaces and Dependencies

Expected new or changed interfaces:

- `CertificatePreviewReader`, `CertificatePreviewValues`, and `Pkcs12CertificatePreviewReader` in an application-layer module.
- `SigningDraftWorkflow.selected_certificate_configuration_id`
- `SigningDraftWorkflow.selected_appearance_profile_id`
- `SigningDraftWorkflow.selected_placement_profile_id`
- `SigningDraftWorkflow.selected_signature_preset_id`
- `SigningDraftWorkflow.capture_current_signature_setup(...)`
- `SigningDraftWorkflow.apply_resolved_signature_preset(...)`

No new third-party dependency is needed.

Revision note: updated on 2026-05-06 after implementation to record the draft reference fields, canonical workflow methods, certificate preview reader seam, and focused validation evidence.

Revision note: updated on 2026-05-06 after commit to record commit `87509136b` in the progress checklist.
