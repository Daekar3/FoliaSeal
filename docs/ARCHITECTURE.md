# Architecture

This document is the project-level architecture map for FoliaSeal. It describes the code as it exists in this repository, with facts marked by evidence level.

Status markers used in this document:

- **Confirmed by code**: Verified from source files.
- **Confirmed by tests**: Verified from test coverage names and assertions.
- **Confirmed by docs**: Verified from checked-in documentation.
- **Inferred**: Reasonable interpretation of current code, but not explicitly stated.
- **Needs review**: Requires maintainer confirmation.
- **Debt**: Current structure is known or suspected to be transitional or problematic.

## 1. Purpose and scope

FoliaSeal is a Linux-targeted desktop PDF signing application foundation. The package provides a `foliaseal` command, a Qt-based PDF viewer/signing shell, a headless PDF signing use case, named visible-signature profiles, preview and signed-output QA harnesses, and PyInstaller packaging support. This is confirmed by `README.md`, `pyproject.toml`, and `src/foliaseal/__main__.py`.

This document governs the repository architecture: Python package layout, application/domain/infra/presentation boundaries, object models, file contracts, CLI contracts, rendering/signing dependencies, persistence, and tests. It does not describe a deployed service or network protocol because the current code is a local desktop application and CLI tool.

## 2. Architectural principles

| Principle | Reason | Status |
|---|---|---|
| Keep domain models independent of Qt and pyHanko. | `src/foliaseal/domain` defines validated dataclasses and enums that are used by application, infra, and presentation. | Confirmed by code |
| Keep orchestration in the application layer and concrete adapters in infra/presentation. | `SignPdfUseCase` depends on protocols while `phase3_signing_backend.py`, `infra/render`, `infra/tsa`, and Qt widgets provide concrete behavior. | Confirmed by code |
| Treat CLI arguments, JSON schemas, profile storage, and failure codes as contracts. | These are surfaced to users, tests, harnesses, or persisted files. | Confirmed by code/tests |
| Use bundled font assets as the visible-signature typography source of truth. | `signature_font_registry.py`, README text, and signing/preview tests enforce bundled font behavior. | Confirmed by code/docs/tests |
| Keep visible-signature layout policy behind the application layout boundary. | `visible_signature_layout.py` exposes `VisibleSignatureLayoutEngine`, `LayoutRequest`, and `SignatureLayoutPlan`; backend, canonical preview, Qt preview, and harness diagnostics consume that plan. Some implementation still delegates to backend compatibility helpers as transitional debt. | Confirmed by code/debt |
| Prefer late imports for optional GUI/runtime dependencies. | Qt widgets and render backend load PySide6 dynamically and report diagnostics when unavailable. | Confirmed by code |
| Generated harness outputs should not be committed unless intentionally curated as fixtures. | `.gitignore` excludes run outputs while durable manifests/fixtures remain trackable. | Confirmed by code |

## 3. Repository map

| Path | Responsibility | Notes |
|---|---|---|
| `src/foliaseal/__main__.py` | CLI parser and command dispatch. | Exposes `foliaseal` console script and `python -m foliaseal`. |
| `src/foliaseal/domain/` | Stable domain models, enums, protocols, and failure codes. | No Qt imports found. |
| `src/foliaseal/application/` | Use cases, workflows, geometry, preview/render evidence logic, layout planning, and protocol boundaries. | Some transitional modules still import concrete infra helpers. |
| `src/foliaseal/infra/` | Concrete adapters for certification, config JSON storage, Qt PDF rendering, timestamp authority integration, and trust policy context creation. | Depends on pyHanko, cryptography, PySide6 at runtime where needed. |
| `src/foliaseal/presentation/qt/` | Qt viewer/signing widgets and manual/automated harnesses. | Uses dynamic PySide6 imports so tests can use fakes. |
| `src/foliaseal/resources/fonts/` | Bundled OpenType font assets used by preview and signing. | Package data in `pyproject.toml`. |
| `src/foliaseal/build/` and `foliaseal.spec` | PyInstaller helper code and one-dir bundle spec. | See known debt about runtime asset helper usage. |
| `tests/unit/` | Unit and focused integration-style tests for each layer. | Heavy coverage around signing, preview, Qt shell, and layout policy. |
| `tests/support/` | Test builders and certification fixtures. | Used by multiple unit suites. |
| `tests/fixtures/` | Durable fixture data. | Includes Phase 3 manual replay JSON. |
| `artifacts/` | Manual QA evidence, manifests, and durable acceptance assets. | Run-output directories/files are mostly ignored by `.gitignore`. |
| `docs/ExecPlans/` | Living implementation plans and notes. | Formerly `.agent/`; now documentation-owned. |
| `docs/PLANS.md` | ExecPlan authoring/execution contract. | Referenced by `Agents.md`. |
| `Agents.md` | Agent operating instructions for this repository. | Requires architecture doc updates for architecture-affecting changes. |
| `scripts/` | Local helper scripts. | Includes PyInstaller build and preview stress manifest generation. |

## 4. Major components

### Domain model

- Location: `src/foliaseal/domain/models.py`, `src/foliaseal/domain/errors.py`
- Responsibility: Define validated values shared across layers.
- Owns: `SigningRequest`, `SigningResult`, visible signature models, timestamp trust policy, document operation enums, stable `FailureCode` values.
- Does not own: File I/O, signing backend behavior, Qt behavior, JSON persistence.
- Key collaborators: application workflows, config schemas, signing backend, Qt shell.
- Main entry points: domain dataclass constructors and enum values.
- Important types/classes/functions: `SignatureRect`, `SignatureAppearance`, `SignatureFieldBinding`, `SignatureTextStyle`, `SignatureBoxStyle`, `TimestampTrustPolicy`, `SigningRequest`, `SigningResult`, `DocumentOperation`.
- Known constraints: Constructors validate aggressively and raise `ValueError` for malformed values. Failure codes are stable UI/logging contracts.
- Status: Confirmed by code and tests.

### Headless signing use case

- Location: `src/foliaseal/application/sign_pdf_use_case.py`
- Responsibility: Coordinate PDF signing without Qt and map backend failures to stable `SigningResult` values.
- Owns: Signing pipeline order, compatibility checks, certification restriction checks, timestamp-required checks, atomic output write, failure-code mapping.
- Does not own: pyHanko implementation details, certificate parsing, PDF rendering, UI state.
- Key collaborators: `PdfInspector`, `CertificateLoader`, `PdfSigner`, `SignatureVerifier`, `CertificationInspector` protocols; `phase3_signing_backend.py`; `infra.certification`.
- Main entry points: `SignPdfUseCase.execute()`, `SigningBackendRequest.from_signing_request()`.
- Important types/classes/functions: `SigningBackendAppearance`, `SigningBackendRequest`, `PdfInspector`, `PdfSigner`, `SignatureVerifier`.
- Known constraints: Visible signature requests must include both `signature_rect` and `signature_appearance`; output path must not resolve to input path; writes use temp file plus atomic replace.
- Status: Confirmed by code and tests.

### pyHanko signing backend

- Location: `src/foliaseal/application/phase3_signing_backend.py`
- Responsibility: Concrete pyHanko signing, verification, certificate loading, visible signature style construction, fit validation, and timestamp integration.
- Owns: `PyHankoPdfSigner`, `PyHankoPdfInspector`, `PyHankoCertificateLoader`, `PyHankoSignatureVerifier`, `Phase3SigningExecutor`, rounded visible signature stamp style, backend-only rendered-fit fallbacks.
- Does not own: Qt widgets, persisted profile schemas, high-level request/failure orchestration, visible-signature text/metadata semantics.
- Key collaborators: `SignPdfUseCase`, `visible_signature_semantics.py`, `visible_signature_layout.py`, bundled fonts, `infra.tsa`, `infra.certification`.
- Main entry points: `build_phase3_signing_executor()`, `Phase3SigningExecutor.execute()`.
- Important types/classes/functions: `RoundedBorderTextStampStyle`, `PyHankoPdfSigner.sign()`, `_visible_signature_fit_issues()`, `_build_stamp_text()`.
- Known constraints: This module is currently large and contains both concrete adapter logic and many private layout helpers. Recent layout work introduced `VisibleSignatureLayoutEngine`, and visible text/metadata now comes from `VisibleSignatureSemanticsService`. Some layout helper policy still lives here as compatibility delegation. New production callers should not import those backend-private layout helpers directly. `_build_stamp_text()` remains as a private compatibility wrapper for backend tests and harness diagnostics.
- Status: Confirmed by code and tests; helper concentration is marked as debt.

### Visible signature semantics boundary

- Location: `src/foliaseal/application/visible_signature_semantics.py`
- Responsibility: Resolve meaning-level visible signature state: field values, certificate fallback behavior, signing-time text, detail text, escaped stamp text, metadata reason/location/contact info, and semantic fit issue aggregation.
- Owns: `VisibleSignatureSemanticsService`, `VisibleSignatureSemanticsRequest`, `VisibleSignatureSemantics`, `VisibleSignatureText`, certificate reader, signing clock, and fit-validator ports.
- Does not own: Qt controls, PDF signing, pyHanko stamp style construction, raster/canonical rendering, or layout geometry policy.
- Key collaborators: `signing_draft_workflow.py`, `signing_preview_renderer.py`, `phase3_signing_backend.py`, `visible_signature_layout.py`.
- Main entry points: `VisibleSignatureSemanticsService.resolve()`.
- Important types/classes/functions: `CertificateFieldValues`, `VisibleSignatureField`, `VisibleSignatureText`, `VisibleSignatureFitRequest`, `VisibleSignatureSemanticsMode`.
- Known constraints: Final signing uses a backend-local pyHanko adapter to translate `SimpleSigner.signing_cert.subject.native` into the semantics field map. The boundary itself intentionally has no pyHanko imports.
- Status: Confirmed by code and tests.

### Visible signature layout boundary

- Location: `src/foliaseal/application/visible_signature_layout.py`
- Responsibility: Provide a public application-layer boundary for visible signature geometry planning.
- Owns: `LayoutRequest`, `SignatureLayoutPlan`, typed text/image/ink metrics, layout fit issues, and adapter ports for text measurement, image probing, and horizontal rendered-ink measurement.
- Does not own: visible-signature field/text semantics, Qt widget sizing details, persisted profile JSON, pyHanko signing pipeline.
- Key collaborators: `visible_signature_semantics.py`, `phase3_signing_backend.py`, `signing_preview_renderer.py`, `presentation/qt/signing_shell.py`, `presentation/qt/phase3_harness.py`.
- Main entry points: `VisibleSignatureLayoutEngine.plan()`, `VisibleSignatureLayoutEngine.validate()`, `PyHankoSignatureAppearanceAdapter.build_stamp_style()`.
- Important types/classes/functions: `TextMeasurer`, `StampImageProbe`, `HorizontalInkMeasurer`, `PyHankoTextMeasurer`, `PillowStampImageProbe`.
- Known constraints: The current implementation intentionally delegates some layout policy to backend-private compatibility helpers and carries `backend_reservation` as an opaque payload for pyHanko parity. Production callers should use `VisibleSignatureLayoutEngine`, `LayoutRequest`, `SignatureLayoutPlan`, and adapter APIs; direct backend-private helper use is limited to backend compatibility wrappers, backend-specific tests, adapter parity tests, and pyHanko-rendered evidence. Moving the remaining helper implementation out of `phase3_signing_backend.py` is deferred until the architecture-steward follow-up defines a cleaner split between neutral policy, pyHanko adapters, backend rendered-fit fallback, preview diagnostics, and harness evidence.
- Status: Confirmed by code and tests.

### Signing draft workflow and preview rendering

- Location: `src/foliaseal/application/signing_draft_workflow.py`, `src/foliaseal/application/signing_preview_renderer.py`
- Responsibility: Normalize in-session signing draft state, validate it for submit, and render deterministic textual/canonical preview snapshots.
- Owns: `SigningDraftWorkflow`, `SigningDraftPreview`, draft validation issues, preview/request parity checks, canonical preview rendering.
- Does not own: visible-signature text/metadata semantics, Qt controls, pyHanko signing execution, persisted profile store.
- Key collaborators: domain models, coordinate transforms, visible signature semantics service, visible signature layout engine, signing backend for canonical pyHanko style.
- Main entry points: `SigningDraftWorkflow.preview()`, `SigningDraftWorkflow.to_signing_request()`, `render_signing_preview()`, `render_canonical_signature_preview()`, `compare_preview_to_request()`.
- Known constraints: `SigningDraftWorkflow.preview()` populates `SigningDraftPreview.stamp_text` from `VisibleSignatureSemanticsService`; direct preview construction still has renderer/presentation compatibility fallbacks. Certificate preview values are read from PKCS#12 when available; the workflow also imports `SignaturePreset` from infra config, so the application layer currently knows a persistence DTO.
- Status: Confirmed by code; infra DTO dependency is debt/needs review.

### Viewer workflow and coordinate geometry

- Location: `src/foliaseal/application/viewer_session.py`, `src/foliaseal/application/viewer_workflow.py`, `src/foliaseal/application/coordinate_transform.py`
- Responsibility: Manage page/zoom state, render current page through a backend, and convert between view coordinates and PDF coordinates.
- Owns: `ViewerSession`, `ViewerWorkflow`, `ViewerRenderSnapshot`, `PageBox`, `PdfRect`, `ViewRect`, `ViewTransform`.
- Does not own: Qt widget event handling or concrete PDF rendering implementation.
- Key collaborators: `infra.render.PdfRenderBackend`, Qt viewer widget, signing draft workflow.
- Main entry points: `ViewerWorkflow.render_current_page()`, `ViewerWorkflow.selection_to_pdf_rect()`, coordinate transform functions.
- Known constraints: `selection_to_pdf_rect()` requires a current render snapshot and authoritative coordinate mapping.
- Status: Confirmed by code and tests.

### Rendering infrastructure

- Location: `src/foliaseal/infra/render/`
- Responsibility: Define rendering adapter protocol, null fallback, LRU cache policy, and QtPdf-based render backend.
- Owns: `PdfRenderBackend`, `RenderPageRequest`, `RenderPageResult`, `PdfPageGeometry`, `RenderCachePolicy`, `QtPdfRenderBackend`.
- Does not own: Viewer workflow state or Qt widget controls.
- Key collaborators: `ViewerWorkflow`, `presentation/qt/viewer_widget.py`.
- Main entry points: `QtPdfRenderBackend.render_page()`, `QtPdfRenderBackend.get_page_geometry()`, `diagnostics()`.
- Known constraints: `QtPdfRenderBackend` dynamically imports PySide6/QtPdf and returns diagnostics when unavailable. It includes fallback PDF metadata parsing to support page boxes/rotation.
- Status: Confirmed by code and tests.

### Qt presentation layer

- Location: `src/foliaseal/presentation/qt/`
- Responsibility: Build interactive PDF viewer/signing widgets and manual/automated QA harnesses.
- Owns: Qt widget composition, control wiring, preview card sizing, user interactions, harness artifact capture.
- Does not own: Domain validation rules, headless signing failure mapping, persisted JSON schema definitions.
- Key collaborators: `ViewerWorkflow`, `SigningDraftWorkflow`, `render_canonical_signature_preview()`, `build_phase3_signing_executor()`, profile store.
- Main entry points: `build_qt_pdf_viewer_widget()`, `build_qt_signing_shell()`, `run_phase2_viewer_harness()`, `run_phase3_signing_harness()`, `run_phase3_preview_matrix()`, `run_phase3_signed_acceptance_matrix()`.
- Known constraints: Widgets use dynamic PySide6 imports and many test doubles. `signing_shell.py` is a large module with control dataclasses, helper functions, properties panel, workspace widget, and shell adapter in one file.
- Status: Confirmed by code and tests; size/concentration is debt/needs review.

### Configuration and profile persistence

- Location: `src/foliaseal/infra/config/schemas.py`, `src/foliaseal/infra/config/profile_storage.py`
- Responsibility: Serialize, deserialize, validate, load, and save trust/timestamp/profile configuration.
- Owns: `TrustProfile`, `TimestampPolicy`, `SignaturePreset`, `SignaturePresetCatalog`, `SignaturePresetCatalogStore`.
- Does not own: UI controls or runtime signing flow.
- Key collaborators: domain models, Qt signing shell.
- Main entry points: `SignaturePresetCatalog.from_dict()`, `SignaturePreset.to_dict()`, `SignaturePresetCatalogStore.load_catalog()`, `save_catalog()`, `save_profile()`, `delete_profile()`.
- Known constraints: Profiles are stored as human-readable JSON at `${XDG_DATA_HOME:-~/.local/share}/FoliaSeal/Signature Profiles/profiles.json`.
- Status: Confirmed by code and tests.

### Timestamping, trust, and certification infrastructure

- Location: `src/foliaseal/infra/tsa/`, `src/foliaseal/infra/certification.py`
- Responsibility: Build pyHanko timestamp clients and validation contexts; inspect PDF certification/DocMDP restrictions.
- Owns: `build_http_timestamper()`, `build_dummy_timestamper()`, `build_timestamp_validation_context()`, `PyHankoCertificationInspector`.
- Does not own: Signing use-case failure-code mapping or UI decisions.
- Key collaborators: `phase3_signing_backend.py`, `SignPdfUseCase`, domain `TimestampTrustPolicy`.
- Known constraints: HTTP TSA URLs must be `http` or `https`. Trust validation disables fetching and can require explicit PEM trust roots when system store use is disabled.
- Status: Confirmed by code and tests.

### QA and evidence machinery

- Location: `src/foliaseal/application/qa_*`, `src/foliaseal/application/phase2_evidence.py`, `src/foliaseal/presentation/qt/phase*_harness.py`, `artifacts/`
- Responsibility: Produce manual QA evidence, preview matrix outputs, signed-output acceptance artifacts, and evidence contract evaluations.
- Owns: Evidence contract evaluation, harness capture JSON shape, preview/signed matrix summary generation, checklist rendering.
- Does not own: Core domain models or signing semantics.
- Key collaborators: CLI entry points, Qt shell, signing backend, artifacts directory.
- Status: Confirmed by code, README, tests, and artifacts.

### Packaging

- Location: `pyproject.toml`, `foliaseal.spec`, `scripts/build_pyinstaller.sh`, `src/foliaseal/build/pyinstaller_support.py`
- Responsibility: Python package metadata, console script registration, package data, and PyInstaller one-dir build.
- Owns: `foliaseal` console script, dependencies, package-data declaration for fonts.
- Known constraints: Runtime dependencies in `pyproject.toml` are `pyHanko[opentype]` and Pillow; dev extras include PyInstaller, PySide6, pytest, and ruff. PySide6 is loaded dynamically and remains outside runtime dependencies, but the default dev/test path installs it for QtPdf-backed preview tests.
- Status: Confirmed by code; PySide6 packaging/dependency contract needs review.

## 5. Object model / domain model

| Object | Defined in | Responsibility | Important fields | Notes |
|---|---|---|---|---|
| `SigningRequest` | `domain/models.py` | Public signing command payload. | input/output PDF paths, certificate path/passphrase, TSA URL, timestamp flag, trust policy, optional visible signature rect/appearance. | Visible signature settings must be complete pair. |
| `SigningResult` | `domain/models.py` | Stable result for UI/logging. | success, failure_code, message, PDF/signature/timestamp/certification metadata. | Failure codes are stable contract. |
| `SignatureRect` | `domain/models.py` | PDF-space visible signature rectangle. | page index, left/bottom/width/height in points. | Bottom-left PDF coordinate system. |
| `SignatureAppearance` | `domain/models.py` | Normalized visible signature style/content settings. | field bindings, layout template, stamp position, font/box style, image path. | Validates field order and binding rules. |
| `SignatureFieldBinding` | `domain/models.py` | One visible field source/display rule. | source, show flag, override text, display label. | Hidden fields cannot be visible. |
| `SignatureTextStyle` / `SignatureBoxStyle` | `domain/models.py` | Typography, border, and background settings. | font family/size/style/color; border/background settings. | Font family support enforced elsewhere by registry. |
| `TimestampTrustPolicy` | `domain/models.py` | Runtime timestamp trust validation inputs. | system store flag, CA bundle path, revocation mode. | Converted from config `TrustProfile`. |
| `SigningBackendRequest` | `application/sign_pdf_use_case.py` | Backend-facing normalized signing payload. | public signing fields plus `SigningBackendAppearance`. | Created by `from_signing_request()`. |
| `SigningDraftWorkflow` | `application/signing_draft_workflow.py` | Mutable application state for an in-progress signing draft. | signing paths, credentials, rect, appearance, placement context. | Produces preview and final `SigningRequest`. |
| `SigningDraftPreview` | `application/signing_draft_workflow.py` | UI-ready normalized preview payload. | rect, appearance settings, fields, detail text, stamp text, issues, can_submit. | Used by Qt and preview renderer. |
| `VisibleSignatureSemantics` | `application/visible_signature_semantics.py` | Resolved visible-signature meaning-level payload. | resolved fields, title/detail/stamp text, metadata reason/location/contact info, fit issues, readiness. | Shared source for workflow preview, canonical preview text, backend signing text, and metadata. |
| `SignatureLayoutPlan` | `application/visible_signature_layout.py` | Canonical visible-signature geometry result. | text/stamp area dimensions, layout rules, fit issues, optional ink reservation. | Boundary for backend/canonical/Qt preview geometry. |
| `ViewerSession` | `application/viewer_session.py` | Viewer page/zoom state. | page count, current page, zoom. | Clamps zoom via `ViewerZoomLimits`. |
| `ViewerRenderSnapshot` | `application/viewer_workflow.py` | Current rendered page state for interactions. | page index, zoom, pan, page box, rotation, image size, mapping readiness. | Required for selection mapping. |
| `SignaturePreset` / `SignaturePresetCatalog` | `infra/config/schemas.py` | Persisted named visible-signature profiles. | schema version, name, appearance, placement defaults. | Serialized to JSON. |
| `RenderPageRequest` / `RenderPageResult` | `infra/render/base.py` | Render backend request/result. | document path, page index, zoom; width/height/RGBA bytes. | Backend protocol contract. |
| `Phase3HarnessCapture` | `presentation/qt/phase3_harness.py` | Structured acceptance harness result. | preview/request/signing/evidence fields. | JSON output is validated by evidence contract. |

## 6. Contracts and boundaries

### CLI contract

- Producer: `src/foliaseal/__main__.py`
- Consumer: Developers, manual QA, local automation.
- Stability: Needs review. Commands are documented in README and covered by CLI tests, so treat them as user-facing.
- Commands: default `foliaseal`, `phase2-evidence`, `phase2-viewer-harness`, `phase3-signing-harness`, `phase3-signing-preview-matrix`, `phase3-signing-acceptance-matrix`, `phase3-signing-harness-validate`.
- Validation: `argparse` enforces required arguments; command handlers raise on invalid evidence captures.
- Error behavior: Python exceptions surface for invalid harness/evidence flows unless command handlers map them.
- Source files: `src/foliaseal/__main__.py`, tests in `tests/unit/test_cli_parser.py` and `tests/unit/test_main_cli.py`.

### Signing use-case contract

- Producer: `SignPdfUseCase.execute()`
- Consumer: `Phase3SigningExecutor`, Qt signing shell, tests, future non-Qt callers.
- Stability: Confirmed public application contract.
- Backward compatibility requirements: Preserve `FailureCode` meanings, `SigningResult` fields, timestamp-required behavior, atomic write behavior, and visible-signature rect/appearance pairing rule.
- Validation: domain constructors, compatibility profile, certification inspector, certificate loader, backend request normalization.
- Error behavior: Known exceptions are mapped to stable `FailureCode` values; unknown exceptions map to `UNEXPECTED_INTERNAL_ERROR`.
- Source files: `src/foliaseal/application/sign_pdf_use_case.py`, `src/foliaseal/domain/errors.py`.

### Render backend contract

- Producer: `PdfRenderBackend` implementations.
- Consumer: `ViewerWorkflow`.
- Stability: Confirmed application/infra boundary.
- Backward compatibility requirements: `render_page()` returns RGBA bytes matching width*height*4; `get_page_geometry()` returns boxes and rotation for coordinate mapping.
- Validation: backend checks path existence, page index, zoom; viewer checks mapping readiness.
- Error behavior: concrete backend raises for missing files, invalid pages, unavailable Qt runtime; diagnostics reports backend availability.
- Source files: `src/foliaseal/infra/render/base.py`, `src/foliaseal/infra/render/qt_backend.py`.

### Visible-signature layout contract

- Producer: `VisibleSignatureLayoutEngine.plan()`
- Consumer: backend signing, canonical preview rendering, Qt preview sizing.
- Stability: Active application boundary; some internals remain transitional.
- Backward compatibility requirements: Preserve preview/output parity and fit validation behavior across backend, canonical preview, and Qt preview.
- Validation: layout engine returns `VisibleSignatureFitIssue` values instead of throwing for fit failures; adapters may raise when fit issues are not explicitly allowed.
- Error behavior: invalid image paths/read failures from default `PillowStampImageProbe` raise `ValueError`; fit checker failures become typed issues.
- Source files: `src/foliaseal/application/visible_signature_layout.py`.

### Profile catalog JSON contract

- Producer: `SignaturePresetCatalogStore.save_catalog()`.
- Consumer: Qt signing shell/profile controls and future launches.
- Stability: Persisted file contract.
- Storage path: `${XDG_DATA_HOME:-~/.local/share}/FoliaSeal/Signature Profiles/profiles.json`.
- Format: JSON object with `schema_version` and `profiles`; profiles include `schema_version`, `name`, `appearance`, and optional `placement_defaults`.
- Validation: `SignaturePresetCatalog.from_dict()` and nested schema constructors reject malformed shape/types/duplicates.
- Error behavior: missing or blank file loads as empty catalog; invalid JSON raises `ConfigValidationError`.
- Source files: `src/foliaseal/infra/config/schemas.py`, `src/foliaseal/infra/config/profile_storage.py`.

### Timestamp and trust contract

- Producer: `TimestampTrustPolicy`, `build_http_timestamper()`, `build_timestamp_validation_context()`.
- Consumer: signing backend and verifier.
- Stability: Needs review, but surfaced by signing request/config schemas.
- Backward compatibility requirements: TSA URL validation, no network fetching in validation context, explicit trust material behavior when system store is disabled.
- Validation: URL scheme/netloc check; PEM CA bundle parsing.
- Error behavior: invalid TSA URL raises `TsaUnavailableError`; invalid/missing trust material raises `TimestampTrustMaterialError`; trust failure maps through `SignPdfUseCase`.
- Source files: `src/foliaseal/infra/tsa/`, `src/foliaseal/domain/models.py`.

### Harness artifact contracts

- Producer: Phase 2/Phase 3 harness commands.
- Consumer: manual QA and evidence contract validation.
- Stability: Engineering validation contract.
- Format: JSON summaries, markdown checklists, preview PNGs, signed-output crops/comparisons.
- Validation: `evaluate_phase3_evidence_contract()` checks capture consistency and gate verdict.
- Error behavior: `phase3-signing-harness-validate` raises when evidence contract fails.
- Source files: `src/foliaseal/presentation/qt/phase3_harness.py`, `src/foliaseal/application/qa_evidence_contract.py`, `artifacts/`.

## 7. Control flow

### CLI startup

1. Console script `foliaseal` calls `foliaseal.__main__:main`.
2. `_build_parser()` builds subcommands and argument contracts.
3. `main()` dispatches to evidence generation, Qt harnesses, preview/signed matrices, validation, or prints the skeleton-ready message when no command is provided.

### Headless signing

1. Caller builds a domain `SigningRequest`.
2. `SignPdfUseCase.execute()` rejects input/output path conflicts.
3. Public request is normalized to `SigningBackendRequest`.
4. PDF compatibility and certification policy are inspected.
5. Certificate material is validated.
6. Concrete signer produces `SigningOutput`.
7. Timestamp-required and PDF-version policies are checked.
8. Output bytes are written via temp file and atomic replace.
9. Verifier checks signed output and timestamp trust.
10. `SigningResult` reports success or a stable failure code.

### Qt signing workflow

1. `build_qt_signing_shell()` constructs a `SigningShellAdapter`.
2. The shell creates a viewer workflow and signing draft workflow.
3. User interactions update `SigningDraftWorkflow` state through placement and appearance controls.
4. Preview controls render a UI preview from `SigningDraftPreview`; sizing uses `SignatureLayoutPlan`.
5. On sign, the workflow converts the draft into `SigningRequest`.
6. The injected signing executor runs and returns a `SigningResult`.
7. The shell displays success/failure state and harnesses can capture structured evidence.

### Viewer selection to PDF rectangle

1. `ViewerWorkflow.render_current_page()` renders with the backend and stores page geometry.
2. Qt widget receives mouse selection in view pixels.
3. `ViewerWorkflow.selection_to_pdf_rect()` converts `ViewRect` through `view_rect_to_pdf_rect()`.
4. The PDF rectangle is rejected if no snapshot exists, coordinate mapping is unavailable, or the result is outside the page box.
5. Signing workflow stores the rectangle as `SignatureRect`.

### Profile save/load

1. Qt shell loads `SignaturePresetCatalogStore.default()`.
2. `load_catalog()` returns empty catalog if no file exists.
3. Saving creates or replaces a `SignaturePreset` in `SignaturePresetCatalog`.
4. Store writes indented sorted JSON to a `.tmp` file and replaces `profiles.json`.
5. Delete rewrites the catalog without the named profile.

### Phase 3 evidence validation

1. Harness or matrix command writes structured JSON and optional images.
2. `phase3-signing-harness-validate` reads a summary JSON.
3. `evaluate_phase3_evidence_contract()` classifies errors, warnings, acceptance tier, and gate verdict.
4. CLI prints the evaluation and raises if validation failed.

## 8. Data flow and persistence

| Data | Source | Transformations | Storage | Format/schema | Notes |
|---|---|---|---|---|---|
| Input PDF | User CLI/GUI path | rendered for viewer; signed by pyHanko; inspected for certification/version | Original file remains at user path | PDF | Signing output must not target same resolved path. |
| Signed PDF output | pyHanko backend bytes | atomic temp-file replace | User-provided output path | PDF | `SigningResult` reports PDF version, signature subfilter, timestamp metadata. |
| PKCS#12 certificate | User path/passphrase | validated/loaded by pyHanko/cryptography | Not persisted by app | PKCS#12 | Passphrase can appear in CLI history for harness commands; README warns about this. |
| Signature profiles | Qt shell/user input | domain appearance -> config schema -> JSON | XDG data dir under `FoliaSeal/Signature Profiles/profiles.json` | `SignaturePresetCatalog` JSON | Missing/blank catalog becomes empty. |
| Trust profile/timestamp policy | Config schema callers | JSON dicts <-> dataclasses -> runtime trust policy | Needs review | JSON schema in `infra/config/schemas.py` | Storage location outside profile catalog is not yet clearly documented in code. |
| Viewer render buffers | Render backend | PDF page -> RGBA bytes | Memory; optional render cache | `RenderPageResult` | Cache is in-memory LRU keyed by path/page/zoom. |
| Preview artifacts | Qt harness/matrix | widget/canonical preview capture, overlays, diagnostics | `artifacts/` run directories | PNG/JSON/markdown | Generated run outputs are mostly ignored. |
| Bundled fonts | Package resources | resolved by font registry and backend/preview | `src/foliaseal/resources/fonts/` in package data | TTF files | User-facing families map to bundled font faces. |

## 9. Dependency rules

| From | May depend on | Must not depend on | Notes |
|---|---|---|---|
| `domain` | Python stdlib and typing/dataclasses/enums. | `application`, `infra`, `presentation`, Qt, pyHanko. | Confirmed by current imports. |
| `application` | `domain`, small infra protocols/adapters where currently wired, Pillow for layout image probing. | Qt presentation widgets. | Some application modules import infra DTOs or backend concrete helpers; see debt. |
| `infra` | `domain`, application protocol DTOs where implementing adapters, external libraries such as pyHanko/PySide6/cryptography/Pillow. | Qt presentation widgets. | Rendering backend uses dynamic Qt imports. |
| `presentation/qt` | `domain`, `application`, `infra` concrete adapters, dynamic PySide6 bindings. | Domain mutation rules duplicated outside workflows. | Qt shell should orchestrate, not reinterpret signing semantics. |
| `tests` | All layers plus fakes/fixtures. | Production code depending on tests. | Tests intentionally inspect private helpers in some transitional layout areas. |
| `docs` / `artifacts` | N/A. | Runtime imports from production code. | Artifacts are evidence, not app dependencies. |

## 10. Extension points

| Extension point | Location | Intended use | Constraints |
|---|---|---|---|
| Signing backend ports | `application/sign_pdf_use_case.py` | Swap PDF inspector, certificate loader, signer, verifier, certification inspector in tests or future adapters. | Must return domain `SigningOutput` / `VerificationSummary` and preserve failure-code mapping. |
| Render backend protocol | `infra/render/base.py` | Replace QtPdf renderer with another renderer. | Must provide page geometry and RGBA render bytes. |
| Visible-signature semantics ports | `application/visible_signature_semantics.py` | Inject certificate field reading, signing clock, and fit validation. | Must keep preview and final-signing text/metadata behavior aligned. |
| Visible-signature layout ports | `application/visible_signature_layout.py` | Inject text measurement, image probing, and horizontal ink measurement. | Must preserve `SignatureLayoutPlan` semantics and fit-issue reporting. |
| Timestamp factory | `phase3_signing_backend.py`, `infra/tsa/pyhanko_adapter.py` | Use dummy TSA in tests/matrices or HTTP TSA in real signing. | Production URLs must validate as HTTP(S). |
| Profile storage root | `SignaturePresetCatalogStore.default(app_name=...)` | Test/custom app-name storage location. | Default follows XDG data home. |
| Qt binding loaders | `presentation/qt/*` | Test with fake widgets or run with real PySide6. | Dynamic imports should fail with explicit unavailable errors/diagnostics. |
| PyInstaller support | `src/foliaseal/build/pyinstaller_support.py` | Collect hidden imports/runtime assets for bundles. | Current spec may not yet use the helper; needs review. |

## 11. Testing architecture

Tests live under `tests/unit/` with support builders in `tests/support/`. The suite is broad and includes unit tests plus focused integration-style tests that exercise pyHanko signing, Qt-shell behavior through fakes, and harness artifact generation.

| Test area | Location | What it protects | Expected when changing |
|---|---|---|---|
| Domain/config validation | `test_signature_appearance_models.py`, `test_config_schemas.py`, `test_signature_preset_storage.py` | Dataclass invariants and persisted JSON shape. | Add/update schema tests for persisted fields. |
| Signing use case | `test_sign_pdf_use_case.py` | Failure-code mapping, timestamp policy, certification restriction, atomic writes. | Preserve stable failure codes and output metadata. |
| pyHanko signing backend | `test_phase3_signing_backend.py` | Real signing, timestamping, visible signature layout, semantics adapter behavior, private layout helper behavior. | Run focused backend tests for signing/layout changes. |
| Visible semantics boundary | `test_visible_signature_semantics.py` | Visible field resolution, certificate fallback, signing-time text, escaped stamp text, metadata, and fit-validator propagation. | Add boundary tests for text/metadata behavior before changing workflow, preview, or backend signing. |
| Visible layout boundary | `test_visible_signature_layout.py` | `SignatureLayoutPlan` and adapter parity. | Add boundary tests before relying on private helper changes. |
| Preview rendering | `test_signing_preview_renderer.py` | Textual/canonical preview snapshots and preview/request parity. | Run with backend/layout tests for visible-signature changes. |
| Qt shell/viewer | `test_qt_signing_shell.py`, `test_qt_viewer_widget.py`, `test_qt_render_backend.py` | Widget behavior through fakes, selection geometry, render diagnostics. | Use fakes; avoid requiring a live GUI unless intentionally running harnesses. |
| Viewer geometry/workflow | `test_coordinate_transform.py`, `test_viewer_session.py`, `test_viewer_workflow.py` | Coordinate math and page/zoom workflow. | Add cases for rotations/page boxes when geometry changes. |
| Evidence/harnesses | `test_phase2_harness.py`, `test_phase3_harness.py`, `test_phase2_evidence.py`, `test_preview_stress_fixtures.py` | Capture JSON, checklist/evidence contract behavior, matrix diagnostics. | Keep generated outputs controlled and `.gitignore` aligned. |
| Packaging/build helpers | `test_pyinstaller_support.py`, CLI tests | Hidden imports and command dispatch. | Update when CLI commands or packaging runtime imports change. |

Default local validation from README:

    ruff check .
    python -m pytest -q

## 12. Known architectural debt

| Issue | Impact | Current workaround | Preferred direction |
|---|---|---|---|
| `phase3_signing_backend.py` mixes concrete pyHanko adapter code with many private visible-signature layout helpers. | Harder to navigate and test at a single public boundary. | `VisibleSignatureLayoutEngine` wraps/migrates parts of layout behavior while preserving parity. | Move policy behind the layout boundary and reduce private-helper test reliance after coverage is equivalent. |
| `signing_shell.py` is a large module containing widget composition, profile handling, preview sizing, and workflow orchestration. | Changes risk broad review scope and can hide UI/domain coupling. | Tests use fakes and helper-level coverage. | Split only when clear ownership boundaries emerge, likely panel/profile/preview adapter components. |
| Application layer imports some infra DTOs and concrete backend helpers. | Layer boundary is not perfectly clean. | Semantics decisions now live behind `VisibleSignatureSemanticsService`; remaining imports are primarily layout/backend compatibility and profile DTOs. | Move shared DTOs/interfaces upward or add adapter methods when it reduces coupling. |
| `SignatureLayoutPlan.backend_reservation` carries an opaque backend object. | Public layout boundary is not fully neutral. | Preserve pyHanko parity during migration. | Replace with neutral data once backend/private helpers are no longer required. |
| PySide6 is dynamically imported but not listed in `pyproject.toml` runtime dependencies. | A fresh install may run CLI helpers but fail GUI/harness commands without extra packages. | Runtime diagnostics report unavailable Qt bindings. | Decide whether PySide6 belongs in optional extras or documented system setup only. |
| `foliaseal.spec` does not visibly use `collect_runtime_assets()`. | PyInstaller hidden-import behavior may diverge between helper tests and real spec. | `foliaseal.spec` independently collects FoliaSeal submodules. | Wire the helper into the spec or delete the unused helper path after review. |
| Checked-in artifact docs include historical status and roadmap notes. | README warns some narrative notes may be stale. | Current gate status should come from latest checked-in summaries/artifacts. | Keep live status in generated summaries or curated release notes, not scattered narratives. |

## 13. Open questions

| Question | Why it matters | Options | Recommendation |
|---|---|---|---|
| Should `application` be strictly independent from `infra`? | Current imports include infra config DTOs and backend helper dependencies. | A: enforce strict dependency direction; B: allow pragmatic exceptions. | Prefer A for new work, retire existing exceptions gradually. |
| What is the public stability level of CLI harness commands? | They are documented and tested, but some are engineering acceptance tools. | A: stable developer contract; B: internal tool contract. | Treat command names/required args as stable unless a migration note is added. |
| Should PySide6 be an optional package extra? | GUI and render backend require it dynamically, but package metadata omits it. | A: add `gui` extra; B: document external install only. | Add a `gui` extra if packaging work resumes. |
| Where should trust/timestamp policy config be persisted outside tests? | Schemas exist, but only signature profile storage has an obvious store. | A: add a store; B: keep CLI/request-only for now. | Needs maintainer decision before documenting as settled. |
| How much of `phase3_harness.py` should become reusable analysis library code? | The file owns many PDF/render/diagnostic helpers. | A: keep as harness-local; B: extract evidence analyzers. | Keep local until reuse pressure is concrete. |

## 14. Change log

| Date | Change | Reason |
|---|---|---|
| 2026-04-30 | Replaced skeleton with first-pass architecture map. | Documented current repository structure, contracts, flows, persistence, tests, debts, and open questions from code inspection. |
| 2026-04-30 | Created architecture document skeleton. | Establish canonical architecture documentation path referenced by agent instructions. |
