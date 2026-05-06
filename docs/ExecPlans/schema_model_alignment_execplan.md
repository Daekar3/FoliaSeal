# Schema Model Alignment ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change series, FoliaSeal's persisted objects and in-memory signing workflow will match the canonical product vocabulary in `docs/SCHEMAS.md` closely enough that new feature work can proceed without constantly fighting old names and overloaded data models. A contributor should be able to point at a saved object and answer plainly whether it is an `AppearanceProfile`, a `PlacementProfile`, a `SignaturePreset`, a `ManagedCertificate`, a `CertificateConfiguration`, or `AppSettings`, and the code should agree.

The user-visible outcome is not a new button by itself. The payoff is that the next slices can add real certificate management, signature presets, and settings behavior without continuing to layer them onto the existing "named profile" and direct-file-path workflow. The proof will be observable in tests plus in the Qt shell: saved appearance objects stop implicitly carrying unrelated responsibilities, placement is independently reusable, and signing no longer depends on the UI directly owning raw certificate paths and passphrases as its only identity model.

## Child ExecPlan Dependencies

- [ ] No child ExecPlans yet. If this work is split further, each child must declare which of the slices below it depends on.

## Progress

- [x] (2026-05-06 00:00Z) Audited `docs/SCHEMAS.md`, `src/foliaseal/infra/config/schemas.py`, `src/foliaseal/infra/config/profile_storage.py`, `src/foliaseal/application/signing_draft_workflow.py`, `src/foliaseal/domain/models.py`, and the profile-handling portions of `src/foliaseal/presentation/qt/signing_shell.py`.
- [x] (2026-05-06 00:07Z) Identified the highest-leverage drift: the current `SignaturePreset` persistence model is actually a named appearance-plus-placement profile, certificate usage is still direct path/passphrase state, and global app settings do not exist as a first-class persisted object.
- [x] (2026-05-06 00:55Z) Implemented Slice 1: split the current monolithic reusable-profile persistence into canonical `AppearanceProfile`, `PlacementProfile`, and reference-only `SignaturePreset` catalog/storage behavior. Details live in `docs/ExecPlans/schema_model_alignment_slice1_profiles_execplan.md`.
- [x] (2026-05-06 22:24Z) Created child ExecPlan for Slice 2 at `docs/ExecPlans/schema_model_alignment_slice2_certificates_execplan.md`.
- [x] (2026-05-06 22:31Z) Implemented Slice 2: added `ManagedCertificate` and `CertificateConfiguration` persistence plus a signing-material resolver that converts a selected configuration into runtime signing inputs.
- [ ] Implement Slice 3: refactor `SigningDraftWorkflow` and the Qt shell so ephemeral draft state references reusable objects instead of embedding persistence-shaped data directly.
- [ ] Implement Slice 4: add `AppSettings` persistence and move open/save directory defaults into that store.
- [ ] Reconcile `docs/ARCHITECTURE.md` with the implementation after each slice lands.

## Surprises & Discoveries

- Observation: `docs/SCHEMAS.md` is currently frozen by an explicit governance note, so the implementation must move toward the document instead of treating schema drift as a two-way negotiation.
  Evidence: `docs/SCHEMAS.md` now includes a "Document Governance" section that forbids edits without explicit user approval.

- Observation: the current persisted `SignaturePreset` object is not a preset in the canonical sense; it stores a full `SignatureAppearance` and optional `SignaturePlacementDefaults` directly, with no concept of reference composition.
  Evidence: `src/foliaseal/infra/config/schemas.py` defines `SignaturePreset(schema_version, name, appearance, placement_defaults)` and `SignaturePresetCatalog(profiles=...)`.

- Observation: the current Qt "Named profiles" UI is wired straight to that non-canonical preset model, so the wrong vocabulary is not isolated to storage code.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py` builds a "Named profiles" group, saves via `SigningDraftWorkflow.capture_signature_preset()`, and applies via `SigningDraftWorkflow.apply_signature_preset()`.

- Observation: certificate handling is still raw runtime state, not reusable product objects.
  Evidence: `src/foliaseal/application/signing_draft_workflow.py` stores `certificate_path`, `passphrase`, `tsa_url`, and `timestamp_required` directly on the workflow, while `src/foliaseal/domain/models.py` requires `SigningRequest(certificate_path, passphrase, tsa_url, ...)`.

- Observation: the workflow currently reads PKCS#12 data directly for preview semantics, which makes certificate preview behavior depend on local file access from the draft object itself.
  Evidence: `SigningDraftWorkflow._certificate_values_for_preview()` in `src/foliaseal/application/signing_draft_workflow.py` calls `pkcs12.load_key_and_certificates(Path(self.certificate_path).read_bytes(), self.passphrase.encode(...))`.

- Observation: there is no first-class persisted `AppSettings` object at all.
  Evidence: `src/foliaseal/infra/config/profile_storage.py` only defines profile-catalog storage rooted at `Signature Profiles`, and repository search finds no `AppSettings` or default output-directory persistence type.

- Observation: Slice 1 validation is locally clean for focused tests and lint, while the full suite has unrelated artifact-manifest failures.
  Evidence: focused schema/storage/workflow/shell tests reported `92 passed`, `ruff check .` passed, and full `pytest -q` reported four failures in `tests/unit/test_phase3_harness.py` manifest expectation tests.

- Observation: Slice 2 can be additive because Slice 1 already added `certificate_configuration_id` to the reference-only `SignaturePreset` shape.
  Evidence: `SignaturePreset` in `src/foliaseal/infra/config/schemas.py` now stores optional `certificate_configuration_id`, `appearance_profile_id`, and `placement_profile_id` references.

## Decision Log

- Decision: treat the current schema drift as an architecture problem, not just a naming cleanup.
  Rationale: the wrong names correspond to the wrong responsibilities. Renaming `SignaturePreset` without splitting persistence and draft ownership would leave the same coupling in place.
  Date/Author: 2026-05-06 / Codex

- Decision: sequence the work so reusable signing-object persistence is split before certificate management and draft-state refactoring.
  Rationale: the current Qt shell and workflow are built around one overloaded "profile" concept. Untangling that concept first creates a clean surface for certificate and preset composition work instead of mixing all migrations together.
  Date/Author: 2026-05-06 / Codex

- Decision: keep timestamp/trust-policy objects out of the first schema-alignment slice unless they are required to keep existing signing tests passing.
  Rationale: `docs/SPEC.md` explicitly places timestamping and broad trust policy outside the primary V1 GUI path. The immediate goal is to align the reusable signing-object model and certificate workflow, not to redesign backend timestamp plumbing.
  Date/Author: 2026-05-06 / Codex

- Decision: preserve behavior where practical by adding new stores and adapters first, then migrating call sites, rather than rewriting the entire Qt shell in one step.
  Rationale: the repo already has substantial tests and harness flows around the current shell. An additive migration path keeps the reviewable slice narrow and observable.
  Date/Author: 2026-05-06 / Codex

- Decision: implement certificate persistence and resolution as a separate catalog/store rather than adding certificate arrays to the profile catalog.
  Rationale: managed certificate files and certificate configurations have distinct lifecycle rules from appearance, placement, and preset objects. Keeping them separate makes deletion/export/backup work easier to reason about in later slices.
  Date/Author: 2026-05-06 / Codex

- Decision: use a resolver-side secret-provider protocol for saved certificate passwords.
  Rationale: `docs/SCHEMAS.md` forbids plain-text password storage in ordinary config JSON. The protocol lets tests use an in-memory provider while a later GUI slice can add a real OS credential-store adapter.
  Date/Author: 2026-05-06 / Codex

## Outcomes & Retrospective

At plan creation time, the main outcome was clarity rather than code. Slice 1 then split profile persistence into `AppearanceProfile`, `PlacementProfile`, and reference-only `SignaturePreset`. Slice 2 added the certificate side of the canonical object model with `ManagedCertificate`, `CertificateConfiguration`, `CertificateCatalog`, `CertificateCatalogStore`, and `CertificateSigningMaterialResolver`.

The remaining work is still implementation-heavy: draft workflow and Qt shell state need to consume these canonical objects, and app settings still need a first-class store. The biggest lesson from the audit remains that the drift is not localized: persistence, workflow state, and UI labels all currently reinforce old object ownership, so the refactor must stay staged but deliberate.

## Context and Orientation

The current persistence layer for reusable signing objects lives in `src/foliaseal/infra/config/schemas.py` and `src/foliaseal/infra/config/profile_storage.py`. Those files presently define three concepts: `TrustProfile`, `TimestampPolicy`, and `SignaturePresetCatalog`. The important fact is that `SignaturePreset` in the current code does not mean what `SignaturePreset` means in `docs/SCHEMAS.md`. Today it means "a saved visible-signature appearance plus optional placement defaults." In the canonical model it means "a lightweight composition object that references a `CertificateConfiguration`, an `AppearanceProfile`, and a `PlacementProfile`."

The application draft model lives in `src/foliaseal/application/signing_draft_workflow.py`. A "draft" here means the mutable in-memory state for one currently open signing session. That file currently owns both ephemeral choices, such as the active rectangle and current preview state, and long-lived object concerns, such as the capture and application of reusable named profiles. It also stores raw signing inputs such as `certificate_path`, `passphrase`, `tsa_url`, and `timestamp_required`.

The Qt shell lives in `src/foliaseal/presentation/qt/signing_shell.py`. The relevant area is the `SignaturePropertiesPanel`, which exposes "Named profiles" and talks directly to the draft workflow and `SignaturePresetCatalogStore`. This means the UI label, storage type, and workflow method names all currently encode the old schema model.

The domain signing request lives in `src/foliaseal/domain/models.py` as `SigningRequest`. It still requires certificate path, passphrase, and TSA settings directly. That is acceptable as an internal runtime payload, but it is not acceptable as the product-level persistence model because `docs/SCHEMAS.md` requires reusable certificate objects and app-managed certificate files.

The canonical target vocabulary is defined in `docs/SCHEMAS.md`. That document is frozen unless the user explicitly approves changes, so implementation work must converge toward it.

## Plan of Work

Slice 1 is the highest-leverage persistence split. In `src/foliaseal/infra/config/schemas.py`, replace the current monolithic `SignaturePreset` and `SignaturePresetCatalog` model with separate dataclasses and serializers for `AppearanceProfile`, `PlacementProfile`, and `SignaturePreset`. `AppearanceProfile` should own only the visible-signature appearance payload. `PlacementProfile` should own only the reusable placement payload. `SignaturePreset` should own only stable identifiers and optional references to the other reusable objects. The code should stop using user-facing names as the only persistent key. Every persisted object in this slice needs a stable internal identifier and a display name. In `src/foliaseal/infra/config/profile_storage.py`, either evolve the existing file format or replace it outright with a catalog/store shape that can persist these split objects cleanly. Because `docs/SCHEMAS.md` explicitly deprioritizes backward compatibility, it is acceptable to replace the old shape instead of maintaining migration shims, as long as the change is explicit and tested.

Slice 2 adds certificate persistence and resolution. Introduce canonical persistence types and stores for `ManagedCertificate` and `CertificateConfiguration`. `ManagedCertificate` represents an app-owned PKCS#12 file in managed storage. `CertificateConfiguration` is the reusable user-facing object that points at one managed certificate and describes whether password persistence is enabled. The exact implementation can live in new files under `src/foliaseal/infra/config/` and a new certificate-management module under `src/foliaseal/application/` or `src/foliaseal/infra/`, but the end state must provide one resolver seam: given a selected `CertificateConfiguration`, produce the runtime signing inputs required by the current backend (`certificate_path`, `passphrase`, optional alias). This keeps `SigningRequest` usable as an internal runtime payload while removing the need for the UI and draft workflow to persist raw file paths and passphrases as their primary identity model.

Slice 3 refactors draft state ownership. In `src/foliaseal/application/signing_draft_workflow.py`, split long-lived reusable-object concerns from ephemeral session state. The draft should own the currently open document, the active rectangle, the active per-signing values such as `reason` and `location`, and references or snapshots of the selected reusable objects. It should not be the persistence owner for reusable profiles. Methods like `capture_signature_preset()` and `apply_signature_preset()` should either disappear or be replaced by operations that accept canonical objects from the persistence layer. The workflow should stop reading certificate files directly for preview semantics. Instead, give it a certificate-preview reader service that resolves certificate-derived identity data from the active certificate selection. That service can still use PKCS#12 under the hood, but the file-system dependency should no longer live inside the draft object itself.

Slice 4 introduces `AppSettings`. Add a first-class persisted settings object and store, probably in new files under `src/foliaseal/infra/config/`, to own defaults such as open/save directories. The Qt shell should stop hard-coding or implicitly inheriting those decisions from transient state. This slice is intentionally later than the object split and certificate split because it is lower leverage, but it is still necessary to satisfy the canonical model and the product requirement around default output directories.

Throughout all slices, keep `docs/ARCHITECTURE.md` synchronized with the actual implementation, because this refactor changes persistent object ownership, workflow boundaries, and UI/storage collaboration.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Before changing code for Slice 1, re-read the canonical docs and the current storage/workflow implementation:

    sed -n '1,260p' docs/SCHEMAS.md
    sed -n '260,520p' src/foliaseal/infra/config/schemas.py
    sed -n '1,220p' src/foliaseal/infra/config/profile_storage.py
    sed -n '1,360p' src/foliaseal/application/signing_draft_workflow.py
    sed -n '1130,1565p' src/foliaseal/presentation/qt/signing_shell.py

For Slice 1, add or update focused tests first so the split object model is enforced in code. The likely test files are `tests/unit/test_config_schemas.py`, `tests/unit/test_profile_storage.py`, and any Qt-shell tests that currently assume a monolithic profile store. The exact commands should be kept narrow while iterating:

    pytest -q tests/unit/test_config_schemas.py tests/unit/test_profile_storage.py

After Slice 1 compiles and the focused tests pass, run the shell-level tests that touch saved profiles:

    pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_signing_draft_workflow.py

For Slice 2, add focused tests for certificate stores and the signing-material resolver. The commands should stay similarly narrow until the new seam is stable:

    pytest -q tests/unit/test_certificate_config_storage.py tests/unit/test_signing_material_resolver.py

When a slice changes public object ownership or module responsibilities, update `docs/ARCHITECTURE.md` in the same commit and run the broad regression commands before merging:

    ruff check .
    pytest -q

Expected evidence for progress is straightforward. After Slice 1, schema/storage tests should refer to `AppearanceProfile`, `PlacementProfile`, and reference-only `SignaturePreset` objects rather than to monolithic appearance profiles masquerading as presets. After Slice 2, no user-facing persistence path should require the UI to save a raw certificate path as the reusable identity object. After Slice 3, the draft workflow should no longer expose "save named profile" as its core persistence API. After Slice 4, the default output/open directory behavior should be driven by a persisted settings object.

## Validation and Acceptance

This refactor is accepted only when both code structure and observable behavior align with the canonical schema model.

For Slice 1, a human reviewer should be able to inspect the persisted config schema code and see distinct types for `AppearanceProfile`, `PlacementProfile`, and `SignaturePreset`. The relevant tests should pass, and the Qt shell tests should confirm that selecting and applying reusable objects still updates the draft correctly.

For Slice 2, the acceptance test is that a reusable certificate object exists in code and storage, and the signing path can resolve it into runtime signing inputs without the UI or draft workflow treating raw path/passphrase pairs as the only persistent identity model. Focused certificate-store and resolver tests must pass, followed by the signing workflow tests that consume the resolved runtime request.

For Slice 3, the acceptance test is that `SigningDraftWorkflow` is visibly reduced to session-state ownership. A reviewer should be able to read `src/foliaseal/application/signing_draft_workflow.py` and see that reusable-object persistence is no longer centered there. Qt shell tests must still pass.

For Slice 4, the acceptance test is that settings-backed open/save directory defaults exist and are persisted independently of reusable signing objects.

At the end of the full plan, run:

    cd /home/daekar/FoliaSeal
    ruff check .
    pytest -q

The result should be a green test suite plus a codebase whose persisted-object vocabulary matches `docs/SCHEMAS.md` closely enough that new product work can use those names without translation layers.

## Idempotence and Recovery

This plan is safe to execute incrementally because `docs/SCHEMAS.md` explicitly allows replacing old local object shapes instead of preserving backward compatibility. That means a failed or partial attempt should be recovered by fixing the code and rerunning the focused tests, not by trying to maintain dual long-term schemas.

The main risk is mixing too many change classes in one slice. Keep each commit centered on one primary behavior change: object-model split, certificate persistence, draft-state refactor, or settings persistence. Documentation updates to `docs/ARCHITECTURE.md` are allowed in those commits because they describe the same architecture-affecting change. Evidence refreshes and unrelated UI redesign work are forbidden from being mixed into these slices.

## Artifacts and Notes

The core audit evidence for this plan is already present in the current code:

    src/foliaseal/infra/config/schemas.py
        SignaturePreset(schema_version, name, appearance, placement_defaults)

    src/foliaseal/infra/config/profile_storage.py
        SignaturePresetCatalogStore with storage rooted at "Signature Profiles"

    src/foliaseal/application/signing_draft_workflow.py
        certificate_path
        passphrase
        tsa_url
        capture_signature_preset(...)
        apply_signature_preset(...)
        _certificate_values_for_preview(...)

    src/foliaseal/presentation/qt/signing_shell.py
        "Named profiles"
        save_current_profile()
        delete_current_profile()
        _on_profile_selected()

These examples are the concrete proof that the current implementation still centers the old object model.

## Interfaces and Dependencies

The canonical persistence work should stay inside the existing Python stack. No new runtime dependency is justified for this plan by itself.

The important module boundaries at the end of the work should be:

- `src/foliaseal/infra/config/schemas.py` or successor modules define canonical persisted object dataclasses and serialization rules.
- `src/foliaseal/infra/config/profile_storage.py` or successor modules persist those objects in human-readable local files.
- `src/foliaseal/application/signing_draft_workflow.py` owns only ephemeral signing-session state and request building.
- `src/foliaseal/presentation/qt/signing_shell.py` orchestrates user interaction, but it does not define the meaning of persisted reusable objects.
- `src/foliaseal/domain/models.py` may continue to define runtime signing payloads such as `SigningRequest`, but those payloads should be fed by resolver seams from canonical persisted objects rather than by UI-owned raw file-path state.

If new modules are added, prefer names that match the canonical vocabulary exactly. For example, `appearance_profile_store.py`, `placement_profile_store.py`, `signature_preset_store.py`, `certificate_configuration_store.py`, `managed_certificate_store.py`, or a small `signing_material_resolver.py` are preferable to more generic names that hide responsibility.

Revision note: created on 2026-05-06 after the first schema-model audit so the implementation can proceed in narrow, high-leverage slices rather than shell-level opportunistic changes.
