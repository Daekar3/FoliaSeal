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

FoliaSeal is a Linux-targeted desktop PDF signing application foundation. The package provides a `foliaseal` command, a Qt-based PDF viewer/signing shell, an application-layer signature-properties coordinator, a headless PDF signing use case, named visible-signature profiles, preview and signed-output QA harnesses, and a Debian-family desktop distribution built around a PyInstaller bundle. This is confirmed by `README.md`, `pyproject.toml`, `scripts/build_deb.sh`, and `src/foliaseal/__main__.py`.

This document governs the repository architecture: Python package layout, application/domain/infra/presentation boundaries, object models, file contracts, CLI contracts, rendering/signing dependencies, persistence, and tests. It does not describe a deployed service or network protocol because the current code is a local desktop application and CLI tool.

The canonical repository document split is:

- `docs/SPEC.md`: intended product requirements, goals, and anti-goals
- `docs/SCHEMAS.md`: intended persistent object model and naming
- `docs/ARCHITECTURE.md`: current code structure and implementation reality

## 2. Architectural principles

| Principle | Reason | Status |
|---|---|---|
| Keep domain models independent of Qt and pyHanko. | `src/foliaseal/domain` defines validated dataclasses and enums that are used by application, infra, and presentation. | Confirmed by code |
| Keep orchestration in the application layer and concrete adapters in infra/presentation. | `SignPdfUseCase` depends on protocols while `phase3_signing_backend.py`, `infra/render`, `infra/tsa`, and Qt widgets provide concrete behavior. | Confirmed by code |
| Treat CLI arguments, JSON schemas, profile storage, and failure codes as contracts. | These are surfaced to users, tests, harnesses, or persisted files. | Confirmed by code/tests |
| Use bundled font assets as the visible-signature typography source of truth. | `signature_font_registry.py`, README text, and signing/preview tests enforce bundled font behavior. | Confirmed by code/docs/tests |
| Keep visible-signature layout policy behind one prepare-once boundary. | `visible_signature_layout.py` exposes `VisibleSignatureLayoutPort` and the concrete `VisibleSignatureLayoutService`; `VisibleSignaturePreparation` freezes the neutral plan, fit decision, and reservation evidence before signing or canonical-preview materialization. Qt preview remains a presentation adapter over neutral layout data. Preview-only stamp suppression is an explicit derived result, not an implicit re-plan. | Confirmed by code |
| Keep signature-properties reconciliation in the application layer. | `signature_properties_coordinator.py` owns catalog reconciliation, selection state, validation/readiness text, and workflow-backed preview state; `signing_shell.py` renders that state and keeps preview/presentation concerns local. | Confirmed by code and tests |
| Prefer late imports for optional GUI/runtime dependencies. | Qt widgets and render backend load PySide6 dynamically and report diagnostics when unavailable. | Confirmed by code |
| Generated harness outputs and local artifact workspaces should not be committed unless intentionally curated as clone-stable fixtures. | `.gitignore` ignores `artifacts/`; durable small fixtures belong in `tests/fixtures/` or another explicitly tracked fixture location. | Confirmed by code |

## 3. Repository map

| Path | Responsibility | Notes |
|---|---|---|
| `src/foliaseal/__main__.py` | CLI parser and command dispatch. | Exposes `foliaseal` console script and `python -m foliaseal`. |
| `src/foliaseal/domain/` | Stable domain models, enums, protocols, and failure codes. | No Qt imports found. |
| `src/foliaseal/application/` | Use cases, workflows, geometry, preview/render evidence logic, layout planning, protocol boundaries, and the Phase 3 evidence service. | Some transitional modules still import concrete infra helpers. |
| `src/foliaseal/application/visible_signature_color.py` | Shared visible-signature color conversion helper. | Owns the RGBA conversion used by horizontal reservation and preview diagnostics. |
| `src/foliaseal/application/phase3_evidence_service.py` | Explicit injected service boundary for Phase 3 evidence capture, matrix execution, validation, and signed-acceptance evidence generation. | Owns request/result dataclasses and typed service verbs consumed by the canonical orchestrator and concrete adapters. |
| `src/foliaseal/application/phase3_evidence_core.py` | Qt-free Phase 3 result models and evidence decisions. | Owns typed matrix/evidence results, normalization, summary validation, capture loading, and markdown rendering. |
| `src/foliaseal/application/phase3_evidence_ports.py` | Narrow effect protocols for Phase 3 evidence execution. | Keeps runners, asset generation, capture loading, writers, and runtime contexts behind injectable ports. |
| `src/foliaseal/application/phase3_evidence_orchestrator.py` | Canonical application-owned dispatcher for tagged Phase 3 evidence operations and capture validation. | Performs payload validation and delegates to the injected service port; intentionally has no Qt, PyHanko, Pillow, TSA, filesystem-artifact, or presentation imports. |
| `src/foliaseal/presentation/qt/phase3_signed_acceptance_lifecycle.py` | Lifecycle port and Qt/fake adapters for one signed matrix shell session. | Keeps application/window creation, shell attachment, event processing, and cleanup outside scenario logic. |
| `src/foliaseal/presentation/qt/phase3_matrix_artifacts.py` | Matrix artifact directory and summary publication port. | Filesystem and memory adapters return the authoritative `summary_json_path`. |
| `src/foliaseal/application/phase3_fidelity_contract.py` | Versioned release-fidelity manifest contract for the tracked Phase 3 corpus. | Validates `manifest_version`, `phase3_fidelity_v1` tolerances/critical counters, and per-scenario expected outcomes/diagnostics before matrix execution. |
| `src/foliaseal/infra/` | Concrete adapters for certification, config JSON storage, QtPdf geometry plus Poppler interactive-viewer rasterisation, timestamp authority integration, and trust policy context creation. | Depends on pyHanko, cryptography, PySide6 at runtime where needed; the interactive viewer also late-resolves the Linux `pdftoppm` executable. |
| `src/foliaseal/application/signature_properties_coordinator.py` | Application-layer reconciliation boundary for signing-shell certificate and preset state. | Owns display-name selection state, validation/readiness text, preset certificate display-name lookup, and catalog refresh/save/delete commands. |
| `src/foliaseal/application/document_review_workspace.py` | Qt-free review/text workspace session plus the nested review-card and document-text state types consumed by the shell. | Returns `DocumentReviewCardState` and `DocumentTextWorkspaceState` inside `DocumentReviewWorkspaceState`, and continues to own viewer-effect intents. |
| `src/foliaseal/presentation/qt/` | Qt viewer/signing widgets and manual/automated harnesses. | Uses dynamic PySide6 imports so tests can use fakes; app-frame, signing-shell, workspace, lifecycle, reporting, matrix, snapshotter, and render responsibilities are documented in their focused modules below. `phase3_harness.py` remains the Qt composition root for concrete factories and interactive capture wiring, but no longer exposes the removed three-verb `Phase3Composition`/`Phase3Harness` compatibility facade. `phase3_matrix_operations.py` owns the dependency-light lazy matrix boundary, and `phase3_signed_acceptance_evidence.py` supplies default service wiring and runtime-noise suppression; the application service/orchestrator remains the caller boundary. |
| `src/foliaseal/presentation/qt/app_frame_workspace_open.py` | App-frame-facing workspace-open boundary for one PDF. | Owns page-count loading, `ViewerWorkflow` / `SigningDraftWorkflow` creation, output-path defaulting, shell bootstrap assembly, and shell creation while leaving widget installation and frame-owned snapshot storage in `app_frame.py`. |
| `src/foliaseal/presentation/qt/signing_workspace_lifecycle.py` | App-frame-facing lifecycle coordinator for the active signing workspace. | `SigningWorkspaceLifecycle` composes a candidate through `WorkspaceOpenPort`, mounts it through `WorkspaceMountPort`/`QtWorkspaceMount`, and disposes the prior widget only after the candidate is mounted; `close()` disposes the active widget idempotently. |
| `src/foliaseal/presentation/qt/app_frame_certificate_management.py` | App-frame-facing certificate-management boundary for Settings certificate actions. | Owns certificate dialog construction/execution and delegates create, import, rename, delete, and export work to `CertificateLifecycleService` while leaving menu routing and window-level compatibility exposure in `app_frame.py`. |
| `src/foliaseal/presentation/qt/signing_shell_port.py` | Shell-owned workspace bootstrap/port/factory contract for the signing workspace. | Defines `SigningWorkspaceBootstrap`, the narrow production `SigningWorkspacePort`, and the `SigningWorkspaceBundle` returned by `QtSigningWorkspaceFactory`, which pairs that port with the explicit testing adapter while keeping the live shell widget concrete. |
| `src/foliaseal/presentation/qt/signing_workspace_diagnostics.py` | Qt-free immutable diagnostic read model for one live signing workspace state. | Defines `SigningWorkspaceSnapshot`, the consistent read bundle shared by runtime diagnostics and Phase 3 capture. |
| `src/foliaseal/presentation/qt/signing_workspace_testing_port.py` | Neutral diagnostics/testing-port contracts for live signing workspace harness callers. | Defines `SigningWorkspaceDiagnosticsPort` and `SigningWorkspaceTestingPort` plus its narrower `panel` port; the testing port adds snapshot reads without widening the production shell port. |
| `src/foliaseal/presentation/qt/phase3_harness_reporting.py` | Pure Phase 3 harness reporting boundary. | Finalizes raw capture payloads into JSON/checklist evidence without owning the interactive Qt session. |
| `src/foliaseal/presentation/qt/phase3_harness_workspace.py` | Narrow Phase 3 harness workspace boundary. | Owns preview-matrix and signed-acceptance scenario application plus viewer priming refresh and snapshot-returning capture assembly for live-shell and headless workflow paths. The Qt adapter consumes one `SigningWorkspaceSnapshot` from the explicit `SigningWorkspaceTestingPort` for current request, appearance, and last-result reads; compatibility serializers remain only at the evidence edge, and interactive session lifecycle/callback wiring stays in `phase3_harness_session_runner.py`. |
| `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` | Interactive Qt session-runner boundary for the Phase 3 harness. | Owns the Qt window lifecycle, toolbar wiring, shell callback cluster, typed session-runner dependency bundle, and `Phase3HarnessSessionResult` while leaving payload shaping and report writing to the extracted helpers. |
| `src/foliaseal/presentation/qt/phase3_matrix_operations.py` | Dependency-light lazy matrix-operation boundary for Phase 3 evidence. | Owns explicit `preview` and `signed_acceptance` callables over `Phase3MatrixRequest`; constructs each concrete runner only when selected and does not import Qt, PIL, pyHanko, rendering, or the harness composition root. |
| `src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py` | Headless preview-matrix runner boundary for Phase 3 QA. | Owns preview-matrix manifest loading, scenario iteration, exception mapping, summary shaping, `summary.json` writing, and the typed dependency bundle that injects manifest/scenario/json collaborators while leaving scenario-specific preview capture logic in `phase3_harness.py` and `phase3_harness_workspace.py`. |
| `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` | Qt-backed signed-acceptance matrix runner boundary for Phase 3 QA. | Owns signed-acceptance manifest loading, `timestamping_mode` validation, one shell/lifecycle setup for scenario iteration, exception mapping, acceptance-expectation evaluation, summary shaping, `summary.json` writing, and the typed dependency bundle that injects shell/workspace/scenario collaborators while leaving scenario-specific preview capture and signed-output shaping in `phase3_harness_workspace.py` and `phase3_signed_acceptance_scenario_executor.py`. `Phase3MatrixOperations.signed_acceptance` is the typed operation entrypoint. |
| `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py` | Per-scenario signed-acceptance execution boundary for Phase 3 QA. | Owns one signed-acceptance row from scenario application through preview capture, optional signing submission, successful-output snapshotting, and final result shaping while leaving matrix-level looping and expectation evaluation in `phase3_signed_acceptance_matrix_runner.py`. |
| `src/foliaseal/presentation/qt/phase3_pdf_signature_snapshotter.py` | Pure signed-PDF evidence boundary for Phase 3 QA. | Owns signature counting, signature metadata, cryptographic/certification/timestamp verification projections, visible-appearance stream parsing, and JSON-safe PDF/pyHanko serialization; the harness composition root injects its bound methods into signed-output and capture assemblers. |
| `src/foliaseal/presentation/qt/phase3_appearance_snapshotter.py` | Shared appearance parity-model boundary for Phase 3 QA. | Owns preview-side and signed-output-side `SignatureAppearanceSnapshot` reconstruction for render-parity comparison. |
| `src/foliaseal/presentation/qt/phase3_image_comparison_helper.py` | Shared image-comparison boundary for Phase 3 QA. | Owns crop hashing, preview flattening, change-ratio calculations, aspect-ratio delta, and side-by-side comparison artifact writing. |
| `src/foliaseal/presentation/qt/phase3_text_geometry_helper.py` | Shared preview text-geometry boundary for Phase 3 QA. | Owns source-to-preview bounds projection, rendered-text geometry detection, candidate filtering, and reference-label fallback capture. |
| `src/foliaseal/presentation/qt/phase3_signed_output_snapshotter.py` | Shared successful-output evidence boundary for Phase 3 QA. | Owns successful-output evidence aggregation and compact preview-vs-output comparison projection for both signed-acceptance scenario rows and interactive harness capture payloads. |
| `src/foliaseal/presentation/qt/phase3_signed_output_render_snapshotter.py` | Signed-output render-analysis boundary for Phase 3 QA. | Owns page rendering, crop normalization, text-detection, appearance snapshotting, parity comparison, and output render artifact writing for one successful signed output. |
| `src/foliaseal/presentation/qt/signing_workspace_action_bridge.py` | Shell-facing bridge for signing-action dialog and state glue. | Owns output-path dialog handling, overwrite confirmation, sign-submit state application, signed-output reopen forwarding, and certificate-refresh signing-state reload while delegating policy decisions to `signing_action_boundary.py`. |
| `src/foliaseal/presentation/qt/signing_workspace_shell_surface.py` | Narrow caller-facing shell-surface helper for the signing workspace. | Owns the explicit production shell verbs consumed by `app_frame.py` and `signing_shell_port.py`, while `signing_shell.py` remains the composition root and orchestration edge. |
| `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` | Transitional widget-export and testing seam for the signing workspace shell. | Owns the named `widget.compat_surface`, the explicit `SigningWorkspaceTestingPort` implementation exported as `testing_adapter`, the typed testing-panel adapter exposed as `testing_adapter.panel` including preview-render capture bridging, and the concrete widget exports needed because `build_qt_signing_shell()` returns the widget itself rather than the wrapper object; new live diagnostic reads go through `testing_adapter.snapshot()`, while legacy widget exports remain for compatibility. |
| `src/foliaseal/presentation/qt/signing_workspace_orchestrator.py` | Shell-local startup and interaction-plan orchestrator for the signing workspace. | Owns the bootstrap ordering for widget export installation, initial viewer refresh, review-state load, and signing-action state load, and owns delegation of ordered `WorkspaceInteractionPlan` execution to the interaction bridge. |
| `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` | Extracted Qt properties-panel module for the signing workspace. | Owns `SignaturePropertiesPanel`, its preview/validation widget helpers, setup-session prompt adapter, and panel disposal behavior while `signing_shell.py` remains the composition root. |
| `src/foliaseal/presentation/qt/signing_workspace_composition.py` | Extracted workspace-composition helper for the signing workspace. | Owns constructor-time session/bridge/widget assembly, the persistent viewer-toolbar interaction-mode cue, and construction of the shell-local runtime, surfaces, and orchestrator while `signing_shell.py` remains the outer shell adapter and public workspace class. |
| `src/foliaseal/presentation/qt/signing_workspace_runtime.py` | Shell-local runtime/controller for the signing workspace. | Owns the live workspace verbs for viewer/panel/page routing, review/text refresh and navigation, logical-page and signature-rectangle operations, current-request/testing reads, placement-context application, overlay sync, and shell-edge error/status handling, while delegating startup ordering and ordered interaction-plan execution to `signing_workspace_orchestrator.py`. |
| `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py` | Pure capture-assembly helper for the interactive Phase 3 harness. | Owns signed-run bundle assembly and final capture-payload shaping from raw `Phase3HarnessSessionResult` state while leaving Qt session control in `phase3_harness_session_runner.py` and report writing in `phase3_harness_reporting.py`. |
| `src/foliaseal/presentation/qt/signing_action_boundary.py` | Shell-facing boundary for the signing-action flow. | Bridges the shell to `SigningActionCoordinator` while keeping dialog/callback orchestration separate from the state machine. |
| `src/foliaseal/presentation/qt/signature_preview_layout.py` | Widget-facing preview geometry planning and application. | Owns preview card sizing, orientation, ordering, and widget visibility decisions. |
| `src/foliaseal/presentation/qt/signature_preview_lifecycle.py` | Canonical preview snapshot lifecycle for the Qt shell. | Owns canonical render invocation, backend reuse, pixmap loading, and snapshot cleanup. |
| `src/foliaseal/resources/fonts/` | Bundled OpenType font assets used by preview and signing. | Package data in `pyproject.toml`. |
| `src/foliaseal/build/` and `foliaseal.spec` | PyInstaller helper code and one-dir bundle spec. | `collect_runtime_assets()` is wired into the spec for bundled runtime assets. |
| `tests/unit/` | Unit and focused integration-style tests for each layer. | Heavy coverage around signing, preview, Qt shell, and layout policy. |
| `tests/support/` | Test builders and certification fixtures. | Used by multiple unit suites. |
| `tests/fixtures/` | Durable fixture data. | Includes Phase 3 manual replay JSON. |
| `artifacts/` | Local manual QA evidence, manifests, generated runs, and acceptance fixture workspace. | The whole tree is ignored by `.gitignore`; artifact-backed tests skip when local fixtures are absent. Promote small durable fixtures to `tests/fixtures/` only when they must be clone-stable. |
| `docs/SPEC.md` | Canonical product requirements and anti-goals. | Product intent; may lead current implementation. |
| `docs/SCHEMAS.md` | Canonical persistent object model and vocabulary. | Product-facing schema target; may lead current implementation. |
| `docs/ExecPlans/` | Living implementation plans and notes. | Formerly `docs/ExecPlans/`; now documentation-owned. |
| `.agents/skills/write-execplan/PLANS.md` | ExecPlan authoring/execution contract. | Referenced by `Agents.md` and the `$write-execplan` skill. |
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
- Owns: `PyHankoPdfSigner`, `PyHankoPdfInspector`, `PyHankoCertificateLoader`, `PyHankoSignatureVerifier`, `Phase3SigningExecutor`, `PreparedSigningPlan`, `prepare_phase3_signing_plan()`, `BackendReservationEvidence`, `build_backend_reservation_evidence()`, `PyHankoSignatureTextBoxEngine`, rounded visible signature stamp style, backend-owned fit-issue orchestration, backend-only rendered-fit fallbacks, and the explicit invisible signature-field path.
- Does not own: Qt widgets, persisted profile schemas, high-level request/failure orchestration, visible-signature text/metadata semantics.
- Key collaborators: `SignPdfUseCase`, `visible_signature_semantics.py`, `visible_signature_layout.py`, bundled fonts, `infra.tsa`, `infra.certification`.
- Main entry points: `build_phase3_signing_executor()`, `Phase3SigningExecutor.execute()`, `prepare_phase3_signing_plan()`, `PyHankoPdfSigner.sign()`, and `build_backend_reservation_evidence()`.
- Important types/classes/functions: `RoundedBorderTextStampStyle`, `PyHankoPdfSigner.sign()`, `_visible_signature_fit_issues()`, `_build_stamp_text()`.
- Known constraints: This module is currently large and contains both concrete adapter logic and backend fit-policy implementation. Recent layout work introduced `VisibleSignatureLayoutEngine`, and visible text/metadata now comes from `VisibleSignatureSemanticsService`. `prepare_phase3_signing_plan()` obtains one `VisibleSignaturePreparation`, converts its fit issues to `SigningDraftValidationIssue`, and keeps third-party objects out of the DTO. The signer materializes PyHanko/Pillow objects, constructs hidden fields for invisible headless requests, performs signing/TSA work, and verifies output. `PyHankoSignatureTextBoxEngine` is the concrete owner of PyHanko text-box style and metric preparation; backend compact-reservation checks consume one `PreparedTextBox` from this engine. Background-layout construction and structural reservation sizing route through `visible_signature_layout.py`; the backend retains behavior-bearing rendered-ink fallback and fit-gate orchestration because those implement the authoritative acceptance policy, not as compatibility facades. `build_backend_reservation_evidence()` remains the JSON-ready reservation snapshot/error boundary; temporary UI layers such as the Phase 3 harness should consume it rather than reconstructing evidence. For incremental approval signing, `PyHankoPdfSigner` allocates the first unused `SignatureN` field in the input PDF so subsequent signatures append without modifying the prior signed revision.
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
- Responsibility: Provide the application-owned prepare-once port and the concrete composition that turns one neutral layout decision into signing and canonical-preview artifacts.
- Owns: `VisibleSignatureLayoutPort`, `VisibleSignatureLayoutRequest`, immutable `VisibleSignaturePreparation`, `VisibleSignatureLayoutService`, `VisibleSignatureLayoutInput`, `VisibleSignatureLayoutOptions`, `LayoutRequest`, `SignatureLayoutPlan`, typed text/image/ink metrics, layout fit issues, `TextMeasurer`/`PyHankoTextMeasurer` ports, target result types, and adapter ports for text measurement, image probing, and horizontal rendered-ink measurement.
- Does not own: visible-signature field/text semantics, Qt widget sizing details, persisted profile JSON, pyHanko signing pipeline.
- Key collaborators: `visible_signature_semantics.py`, `phase3_signing_backend.py`, `signing_preview_renderer.py`, `presentation/qt/signing_shell.py`, `presentation/qt/phase3_harness.py`, `visible_signature_color.py`.
- Main entry points: `VisibleSignatureLayoutPort.prepare()`, `VisibleSignatureLayoutService.prepare()`, `VisibleSignatureLayoutService.plan()` (low-level geometry operation), `VisibleSignaturePreparation.signing()`, `VisibleSignaturePreparation.preview()`, `VisibleSignatureLayoutEngine.plan()`, `PyHankoSignatureAppearanceAdapter.build_stamp_style()`, and the public inset operations `single_line_stamp_content_inset()`, `single_line_vertical_stamp_border_gap()`, and `single_line_horizontal_stamp_vertical_inset()`.
- Important types/classes/functions: `PyHankoVisibleSignatureStyle`, `CanonicalPreviewLayout`, `TextMeasurer`, `StampImageProbe`, `HorizontalInkMeasurer`, `PyHankoTextMeasurer`, `PillowStampImageProbe`, `PreparedTextBox`, `SignatureTextBoxEngine`.
- Known constraints: `VisibleSignaturePreparation` freezes the application decision plus lazy target materializers; its `fit_gate_passed`/`fit_gate_error` values are captured once and reused by signing, validation, and evidence. `preview()` may carry an explicitly derived text-only plan when compact horizontal stamp policy suppresses the preview stamp; this is observable as `CanonicalPreviewLayout.stamp_suppressed`. The current module still co-locates PyHanko/Pillow-backed adapters with the application contracts, so import-purity extraction remains tracked debt; target construction nevertheless stays behind `PyHankoSignatureAppearanceAdapter` and injected measurement adapters. The backend retains behavior-bearing rendered-ink and fit-policy helpers where they implement the authoritative backend gate; these are implementation policy, not compatibility facades. The removed planner/boundary facades and optional-plan materialization paths must not be reintroduced. Boundary coverage lives in `tests/unit/test_visible_signature_layout_boundary.py` alongside the layout tests.
- Status: Confirmed by code and tests.

### Signing draft workflow and preview rendering

- Location: `src/foliaseal/application/signing_draft_workflow.py`, `src/foliaseal/application/certificate_preview.py`, `src/foliaseal/application/signing_preview_renderer.py`
- Responsibility: Normalize in-session signing draft state, validate it for submit, and render deterministic textual/canonical preview snapshots.
- Owns: `SigningDraftWorkflow`, selected reusable-object ids for the current draft, `CertificatePreviewReader`, `Pkcs12CertificatePreviewReader`, `SigningDraftPreview`, draft validation issues, preview/request parity checks, canonical preview rendering.
- Does not own: visible-signature text/metadata semantics, Qt controls, pyHanko signing execution, persisted profile or certificate stores.
- Key collaborators: domain models, coordinate transforms, visible signature semantics service, visible signature layout engine, signing backend for canonical pyHanko style.
- Main entry points: `SigningDraftWorkflow.preview()`, `SigningDraftWorkflow.build_signing_request()`, `suggest_signed_output_path()`, `render_signing_preview()`, `render_canonical_signature_preview()`, `compare_preview_to_request()`.
- Known constraints: `SigningDraftWorkflow.preview()` populates `SigningDraftPreview.stamp_text` from `VisibleSignatureSemanticsService`; direct preview construction still has renderer/presentation compatibility fallbacks. Certificate preview values are read through an injected application-layer reader, with `Pkcs12CertificatePreviewReader` as the default implementation. Signed-output path suggestions are computed by application-layer path policy so the app frame and signing shell share the same default filename behavior. The workflow can apply resolved `CertificateConfiguration` material but still imports reusable-object DTOs from infra config, so the application layer still knows transitional persistence DTOs while schema-alignment work continues.
- Status: Confirmed by code; infra DTO dependency is debt/needs review.

### Signature properties coordinator

- Location: `src/foliaseal/application/signature_properties_coordinator.py`
- Responsibility: Reconcile signing-shell certificate and preset selection, visible-signature setup state, catalog refresh, dirty-selection clearing, validation text, readiness-to-sign, workflow-backed preview state, and preset certificate display-name lookup without involving Qt widgets.
- Owns: `DefaultSignaturePropertiesCoordinator`, `SignaturePropertiesViewState`, `VisibleSignatureSetupDraft`, `VisibleSignaturePlacementDraft`, command dataclasses for applying certificates/presets, applying visible-signature setup, applying appearance-only updates, saving/deleting presets, refreshing catalogs, clearing the selected preset, the `certificate_configuration_name_for_preset()` helper, and the certificate-material resolver wiring used for selected certificate configurations.
- Does not own: Qt control construction, preview-card rendering, canonical preview snapshot lifecycle, signature geometry rendering, or signing execution.
- Key collaborators: `SigningDraftWorkflow`, `CertificateCatalogStore`, `SignaturePresetCatalogStore`, `CertificateSecretProvider`, `signing_shell.py`.
- Main entry points: `DefaultSignaturePropertiesCoordinator.load()`, `DefaultSignaturePropertiesCoordinator.apply_visible_setup()`, `DefaultSignaturePropertiesCoordinator.set_signature_appearance()`, `DefaultSignaturePropertiesCoordinator.apply_signature_preset()`, `DefaultSignaturePropertiesCoordinator.apply_certificate_configuration()`, `DefaultSignaturePropertiesCoordinator.certificate_configuration_name_for_preset()`, `DefaultSignaturePropertiesCoordinator.reconcile()`.
- Important types/classes/functions: `SignaturePropertiesViewState`, `VisibleSignatureSetupDraft`, `VisibleSignaturePlacementDraft`, `ApplyVisibleSignatureSetup`, `SetSignatureAppearance`, `ApplyCertificateConfiguration`, `ApplySignaturePreset`, `SaveCurrentPreset`, `DeletePreset`, `RefreshCatalogs`, `ClearSelectedSignaturePreset`, `SignaturePropertiesCoordinatorError`.
- Known constraints: The coordinator exposes display-name based state and a Qt-independent visible-signature setup draft to the panel but resolves and mutates workflow ids internally. `load()` and `reconcile()` can fold an optional control issue into validation/readiness state so the panel does not duplicate formatting rules. `certificate_configuration_name_for_preset()` is read-only and returns the display name for the preset's certificate configuration, or `None` when the preset, configuration reference, or certificate record cannot be resolved. Refreshes reconcile stale selections against current catalogs, preset application without a certificate reference preserves the active certificate selection through `SigningDraftWorkflow`, the live apply path now calls `SigningDraftWorkflow.apply_signature_preset_values(...)` while `apply_resolved_signature_preset(...)` remains a compatibility wrapper, certificate application is available through the public `apply_certificate_configuration()` entrypoint, appearance-only application is available through the public `set_signature_appearance()` entrypoint, and visible-signature setup application clears selected preset state when the current draft diverges. `SigningSetupSession.select_signature_preset()` now asks the coordinator for the preset certificate display name instead of walking `preset_catalog` and `certificate_catalog` directly, and `SigningSetupSession.set_signature_appearance()` now delegates appearance-only mutation through the coordinator instead of mutating `workflow` directly. The shell no longer renders a permanent certificate-password row; instead, the setup session prompts on demand through a Qt `QInputDialog` adapter, retains a session-local passphrase cache for repeated manual entries, and still bypasses prompting when a saved secret can be resolved through `CertificateSecretProvider`.
- Status: Confirmed by code and tests.

### Document review summary

- Location: `src/foliaseal/application/document_review.py`
- Responsibility: Inspect the currently opened PDF in a read-only way and return a plain-language signature/certification review summary for the shell.
- Owns: `DocumentSignatureReviewItem`, `DocumentReviewSummary`, `DocumentReviewInspector`, `PyHankoDocumentReviewInspector`, and summary formatting for unavailable, unsigned, signed, and certification-restricted PDFs plus per-signature drill-in guidance.
- Does not own: viewer rendering, signing execution, or any mutable document actions.
- Key collaborators: `infra.certification.inspect_pdf_certification_reader()`, `pyHanko.pdf_utils.reader.PdfFileReader`, `pyHanko.sign.validation.validate_pdf_signature`, and `presentation/qt/signing_shell.py`.
- Main entry points: `summarize_document_review()`, `PyHankoDocumentReviewInspector.inspect()`.
- Known constraints: The helper must stay failure-tolerant for missing or unreadable PDFs and should only claim that signatures were verified locally, not that they are trusted by any external policy source. Top-level summary text remains latest-signature oriented for compact shell display, while `signature_items` carries both the compact row text and a selector-driven drill-in detail payload for each embedded signature. `DocumentSignatureReviewItem.drill_in_detail` includes signer information, local verification state, certification guidance, and a conservative `Recommended next step:` line for signatures that are not locally verified. Certification guidance is surfaced as plain-language status, not as a write action.
- Status: Implemented and confirmed by code and tests.

### Document text search

- Location: `src/foliaseal/application/document_text_search.py`, `src/foliaseal/infra/document_text_search.py`
- Responsibility: Search the currently opened PDF in a read-only way, track the active query/current hit, and expose plain-language shell state plus copyable current-hit text.
- Owns: `DocumentTextMatch`, `DocumentTextSearchState`, `DocumentTextSearchSession`, `DocumentTextSearchEngine`, and `QtPdfDocumentTextSearchEngine`.
- Does not own: arbitrary viewer drag-mode routing, manual text highlight overlay state, clipboard UI, or document mutation.
- Key collaborators: `PySide6.QtPdf.QPdfDocument`, `presentation/qt/signing_shell.py`, and `ViewerWorkflow.document_path`.
- Main entry points: `DocumentTextSearchSession.search()`, `DocumentTextSearchSession.next_match()`, `DocumentTextSearchSession.previous_match()`, `DocumentTextSearchSession.current_copy_text()`, `QtPdfDocumentTextSearchEngine.search()`.
- Known constraints: The search boundary is independent from arbitrary text selection. It supports search, page navigation to the current hit, and copy-current-hit text only; manual selection/highlight is handled by a separate selection boundary so search state can survive selection-mode toggles. It must fail soft for missing or unreadable PDFs.
- Status: Confirmed by code and tests.

### Document text selection

- Location: `src/foliaseal/application/document_text_selection.py`, `src/foliaseal/infra/document_text_selection.py`
- Responsibility: Turn a manual viewer drag on one PDF page into selected text plus highlight rectangles, and expose plain-language shell state for copy/clear actions.
- Owns: `DocumentTextSelection`, `DocumentTextSelectionState`, `DocumentTextSelectionSession`, `DocumentTextSelectionEngine`, and `QtPdfDocumentTextSelectionEngine`.
- Does not own: viewer drag gesture routing, signature placement semantics, or clipboard UI.
- Key collaborators: `PySide6.QtPdf.QPdfDocument`, `presentation/qt/viewer_widget.py`, `presentation/qt/signing_shell.py`, and `ViewerWorkflow.selection_to_pdf_rect()`.
- Main entry points: `DocumentTextSelectionSession.select()`, `DocumentTextSelectionSession.clear()`, `DocumentTextSelectionSession.current_copy_text()`, `QtPdfDocumentTextSelectionEngine.select()`.
- Known constraints: This first pass uses rectangle highlights derived from `QPdfSelection.bounds()` polygon extents rather than polygon-accurate painting. It must not break signature placement mode, and it must fail soft for missing or unreadable PDFs.
- Status: Confirmed by code and tests.

### Document review workspace session

- Location: `src/foliaseal/application/document_review_workspace.py`
- Responsibility: Own the cross-session workflow for document review, document text search, and document text selection so the shell no longer owns the state restoration rules between those helpers.
- Owns: `DocumentReviewWorkspaceSession`, `DocumentReviewCardState`, `DocumentTextWorkspaceState`, `DocumentReviewWorkspaceState`, `DocumentReviewWorkspaceTransition`, `DocumentReviewWorkspaceViewerEffects`, selected-signature preservation across review refreshes, search current-hit page-jump intents, text-selection mode transitions, selected-text highlight intents, and restoring the active search summary when text-selection mode is turned off.
- Does not own: Qt widgets, clipboard UI, signature placement behavior, signing action state, or actual PDF rendering.
- Key collaborators: `DocumentReviewInspector`, `DocumentTextSearchSession`, `DocumentTextSelectionSession`, `ViewerWorkflow`, and `presentation/qt/signing_shell.py`.
- Main entry points: `DocumentReviewWorkspaceSession.load()`, `refresh_review()`, `select_review_signature()`, `search_text()`, `next_text_match()`, `previous_text_match()`, `set_text_selection_mode()`, `handle_viewer_selection()`, `clear_selected_text()`.
- Known constraints: The session is intentionally Qt-free. It returns immutable nested state plus viewer-effect intents using repository types such as `PdfRect`, and the shell remains responsible for applying those effects to the concrete viewer widget and for copying text through the clipboard callback seam. A viewer drag outside text-selection mode is intentionally not consumed so signature placement can remain in the signing workflow.
- Status: Implemented and confirmed by code and tests.

### Viewer workflow and coordinate geometry

- Location: `src/foliaseal/application/viewer_session.py`, `src/foliaseal/application/viewer_workflow.py`, `src/foliaseal/application/coordinate_transform.py`
- Responsibility: Manage page/zoom state, render current page through a backend, and convert between view coordinates and PDF coordinates.
- Owns: `ViewerSession`, `ViewerWorkflow`, `ViewerRenderSnapshot`, `PageBox`, `PdfRect`, `ViewRect`, `ViewTransform`.
- Does not own: Qt widget event handling or concrete PDF rendering implementation.
- Key collaborators: `infra.render.PdfRenderBackend`, Qt viewer widget, signing draft workflow.
- Main entry points: `ViewerWorkflow.render_current_page()`, `ViewerWorkflow.selection_to_pdf_rect()`, coordinate transform functions.
- Known constraints: `selection_to_pdf_rect()` requires a current render snapshot and authoritative coordinate mapping. The workflow also exposes the current `document_path` so the signing shell can inspect the PDF that is open in the viewer without reaching into the widget layer.
- Status: Confirmed by code and tests.

### Viewer interaction session

- Location: `src/foliaseal/application/viewer_interaction_session.py`
- Responsibility: Own the application-layer translation from viewer state and viewer drags into signing-placement updates so the shell does not reconstruct placement logic from raw viewer outputs.
- Owns: `ViewerInteractionSession`, `ViewerPlacementContextResult`, `ViewerSelectionPlacementResult`, placement-context derivation from the active viewer snapshot, `PdfRect` to `SignatureRect` translation for signing placement, and logical page-index updates for shell-driven navigation.
- Does not own: Qt mouse handling, text-selection routing, sidebar widget mutation, canonical preview refresh, or signature overlay painting.
- Key collaborators: `ViewerWorkflow`, `SignaturePlacementContext`, `SignatureRect`, `presentation/qt/signing_shell.py`.
- Main entry points: `ViewerInteractionSession.current_placement_context()`, `select_signature_rect()`, `set_logical_page_index()`, `set_page_number()`.
- Known constraints: The boundary is intentionally Qt-free and leaves widget refresh/application of overlays to the shell. It composes with `document_review_workspace.py`: the review/text workspace gets first chance to consume a viewer drag, and only then does the viewer-interaction session translate that drag into a signing placement.
- Status: Implemented and confirmed by code and tests.

### Workspace interaction session

- Location: `src/foliaseal/application/workspace_interaction_session.py`
- Responsibility: Own the shell-level sequencing for viewer selection, page changes, document-text jump navigation, panel-change follow-up, and viewer-refresh follow-up while staying Qt-free.
- Owns: `WorkspaceInteractionSession`, `WorkspaceInteractionPlan`, the routing between `DocumentReviewWorkspaceSession` and `ViewerInteractionSession`, and the ordered effect vocabulary for review-transition application, viewer refresh, placement-context application, signature-rectangle application, overlay sync, preview refresh, signing-action reload, signing-action invalidation, and error emission.
- Does not own: widget refresh calls themselves, signature overlay painting, preview rendering, or direct `SignatureRect` mutation in the panel.
- Key collaborators: `DocumentReviewWorkspaceSession`, `ViewerInteractionSession`, `ViewerWorkflow`, `presentation/qt/signing_shell.py`.
- Main entry points: `select_in_viewer()`, `change_page()`, `refresh_navigation_to_page_index()`, `refresh_after_panel_change()`, `refresh_after_viewer_refresh()`.
- Known constraints: The boundary is intentionally Qt-free and returns an explicit `WorkspaceInteractionPlan`. `signing_workspace_interaction_bridge.py` iterates that ordered plan, applies `SignatureRect` values through a non-notifying panel path, and explicitly chooses when `refresh_after_panel_change()` should run instead of relying on the panel's generic `on_change` callback for internal rect application.
- Status: Implemented and confirmed by code and tests.

### Rendering infrastructure

- Location: `src/foliaseal/infra/render/`
- Responsibility: Define the rendering adapter protocol, null fallback, LRU cache policy, QtPdf geometry adapter, and Poppler-backed interactive-viewer raster adapter.
- Owns: `PdfRenderBackend`, `RenderPageRequest`, `RenderPageResult`, `PdfPageGeometry`, `RenderCachePolicy`, `QtPdfRenderBackend`, `PopplerPdfRenderBackend`.
- Does not own: Viewer workflow state or Qt widget controls.
- Key collaborators: `ViewerWorkflow`, `presentation/qt/viewer_widget.py`.
- Main entry points: `PopplerPdfRenderBackend.render_page()`, `PopplerPdfRenderBackend.get_page_geometry()`, `QtPdfRenderBackend.render_page()`, `QtPdfRenderBackend.get_page_geometry()`, and `diagnostics()`.
- Known constraints: The live `FoliaSealAppFrame` defaults to `PopplerPdfRenderBackend`. That adapter delegates page boxes, rotation, and placement-coordinate geometry to `QtPdfRenderBackend`, but delegates interactive page pixels to `pdftoppm` and returns opaque RGBA bytes. `pdftoppm` is a late-resolved Linux runtime requirement: a missing executable or unavailable Qt geometry is reported through diagnostics instead of failing on import. QtPdf remains the intentional default for canonical-preview generation and Phase 2/Phase 3 evidence, whose generated-preview scope was not implicated by the reopened signed-PDF rasterisation defect. `QtPdfRenderBackend` dynamically imports PySide6/QtPdf and includes fallback PDF metadata parsing to support page boxes/rotation.
- Status: Confirmed by code and tests.

### Qt presentation layer

- Location: `src/foliaseal/presentation/qt/`
- Responsibility: Build the top-level Qt app frame, interactive PDF viewer/signing widgets, and manual/automated QA harnesses.
- Owns: Qt application-frame menus, widget composition, control wiring, preview card sizing, user interactions, harness artifact capture.
- Does not own: Domain validation rules, headless signing failure mapping, persisted JSON schema definitions.
- Key collaborators: `ViewerWorkflow`, `SigningDraftWorkflow`, `render_canonical_signature_preview()`, `build_phase3_signing_executor()`, profile store, certificate catalog store, signing-material resolver.
- Main entry points: `build_qt_app_frame_host()`, `launch_qt_app_frame()`, `build_qt_pdf_viewer_widget()`, `build_qt_signing_shell()`, `run_phase2_viewer_harness()`.
- Known constraints: Widgets use dynamic PySide6 imports and many test doubles. `app_frame.py` owns the top-level `QMainWindow` wrapper plus the explicit Qt bootstrap helper `launch_qt_app_frame()`, which creates or reuses `QApplication`, shows the window, and can open an initial PDF path before entering the event loop. The frame exposes `File > Open file`, `File > Save As...`, `Edit > Text selection mode`, and Settings actions for application settings, signing-profile management, certificate creation, certificate import, and certificate-configuration management. `Open file` uses `Ctrl+O`; `Save As...` uses `Ctrl+Shift+S`, stays disabled until a shell is loaded, and the `Edit > Text selection mode` action also stays disabled until a shell is loaded. `app_frame_workspace_open.py` owns page-count loading, `ViewerWorkflow` creation, `SigningDraftWorkflow` creation, output-path defaulting, shell bootstrap assembly, and shell creation for one opened PDF. `app_frame_certificate_management.py` owns certificate dialog construction/execution for its Settings actions and delegates create, import, rename, delete, and export work to `CertificateLifecycleService`; `app_frame_profile_library.py` is the Qt adapter for `Settings > Manage signing profiles...`; and `app_frame.py` remains the menu-routing `QMainWindow` host and owns the frame snapshot that exposes `current_workspace`, `current_shell`, `current_viewer_workflow`, and `current_signing_workflow`. Closing the profile-library dialog refreshes the mounted shell's reusable profile and preset selectors through the production port. `signing_shell_port.py` carries the live workspace bootstrap, port, factory, and testing-bundle seam: `SigningWorkspaceBootstrap` carries the workflows, settings, stores, and callbacks needed to build one workspace; `QtSigningWorkspaceFactory` turns that bootstrap into a `SigningWorkspaceBundle` containing a narrow `SigningWorkspacePort` plus the explicit `SigningWorkspaceTestingPort`; the production port depends only on the neutral contract module `signing_workspace_testing_port.py` rather than the compatibility-surface implementation module; and the frame uses only the production port for `choose_output_pdf_path()`, live `apply_app_settings(...)`, `refresh_certificate_configurations()`, `refresh_signature_profiles()`, and `set_document_text_selection_mode(...)` while the compatibility snapshot on the frame supplies the shell widget for inspection and central-widget installation. The frame still owns `window.setCentralWidget(...)`, save-as enablement, and top-level text-selection-mode action enablement/checked-state reset after a successful open, while the frame properties derive the live workspace state from `_current_workspace`. The frame also owns a typed dialog-inspection snapshot for fake-Qt tests and compatibility callers, exposed through frame properties such as `settings_dialog` and `certificate_creation_dialog`, instead of mirroring those dialogs onto the window object. `build_qt_app_frame_host()` and `QtAppFrameAdapter.create_frame()` expose the real `FoliaSealAppFrame` behavior host directly, and `launch_qt_app_frame()` remains the supported runtime entrypoint. `FoliaSealAppFrame.app_settings` is the frame-owned settings source of truth, and saved settings still propagate into the live shell only through the explicit shell port. The settings action opens an app-wide settings dialog for default directories. `signing_shell.py` remains the outer composition root for the production workspace, but constructor-time workspace assembly now lives in `signing_workspace_composition.py`, and the production workspace is no longer composed as a staged top rail above the viewer. `SigningWorkspaceWidget` now uses a document-left / sidebar-right composition: the viewer occupies the left side, while `signing_workspace_sidebar.py` owns the right-side production chrome for the scrolled signature-properties editor, a cohesive `Sign PDF` action panel, document review, and document text. `signing_workspace_composition.py` now owns the constructor-time session graph, bridge graph, viewer/sidebar assembly, and construction of the shell-local runtime, surfaces, and orchestrator for one workspace instance. `signing_workspace_orchestrator.py` owns startup ordering for one live shell by installing widget exports, installing production port exports, refreshing the viewer, loading the initial review state, and reloading the signing-action state, and it also owns delegation of ordered `WorkspaceInteractionPlan` execution to `signing_workspace_interaction_bridge.py`. `signing_workspace_runtime.py` owns the live shell-local workspace verbs that the returned widget exports: viewer/panel/page routing, review refresh, document-text search/navigation/copy/selection-mode operations, logical-page and signature-rectangle operations, current-request/testing reads, placement-context application, overlay sync, and shell-edge error/status handling, while delegating ordered interaction-plan execution to the orchestrator. `signing_workspace_properties_panel.py` now owns `SignaturePropertiesPanel` and its private helper surface: panel widget construction, preview/validation wiring, setup-session orchestration, preset/certificate control wiring, the compact manual-refinement entrypoint, and panel disposal behavior. The signing action panel now renders `SigningActionState` inside the sidebar module, including the staged guidance text, output-path chooser, primary sign action, reopen action, result messaging, and the primary readiness display. `signing_workspace_action_bridge.py` owns the shell-facing dialog and state glue for those actions, while `signing_action_boundary.py` remains the narrower policy layer beneath it. `signing_action_coordinator.py` still owns the signing action state machine for output-path acceptance, signing submission transitions, reopen enablement, last-result tracking, and flow-summary stage/detail derivation; the sidebar applies the returned state to Qt widgets, while the action bridge handles dialog behavior, callback emission, and the public shell surface. `signing_workspace_review_bridge.py` owns the review/text bridge between `DocumentReviewWorkspaceSession` and the live widgets: it renders `DocumentReviewWorkspaceState` into the sidebar, applies `DocumentReviewWorkspaceTransition`, handles text-highlight clearing and setting, changes viewer interaction mode for text selection, and triggers page-jump follow-up callbacks. `document_review_workspace.py` now owns the cross-session review/text workflow: review refresh, selected-signature preservation, text-search navigation, text-selection mode transitions, search-state restoration, and viewer-effect intents for page jumps and highlight overlays. `viewer_interaction_session.py` now owns the adjacent viewer-to-signing workflow: placement-context derivation from the active viewer snapshot, translation from a `PdfRect` drag into a `SignatureRect`, and logical page-index updates for shell-driven navigation. `signing_workspace_shell_surface.py` now owns only the narrow caller-facing production verbs that remain part of the live shell port, including live `app_settings` mirroring and delegation for `apply_app_settings(...)`, `choose_output_pdf_path()`, `refresh_certificate_configurations()`, `refresh_signature_profiles()`, `set_document_text_selection_mode(...)`, `submit_sign_request()`, and `open_signed_output()`. `signing_workspace_compatibility_surface.py` now owns thin widget export installation for the returned shell widget, the named `widget.compat_surface`, `last_signing_result` surface setup, and the `testing_adapter` harness seam instead of housing the live review/text/rect/page/current-request behavior itself, while `signing_workspace_testing_port.py` owns the shared testing contracts consumed by the factory bundle and harness boundary. That harness seam now exposes a typed `panel` port rather than the concrete `SignaturePropertiesPanel`, so Phase 3 callers can mutate appearance, refresh previews, and inspect preview controls without depending on the full panel object. `phase3_harness_workspace.py` continues to consume the explicit `testing_adapter` installed by that surface for live-shell preview scenario mutation and capture instead of adapting `compat_surface` inside the harness boundary. `phase3_harness.py` delegates duplicated scenario mutation there instead of keeping separate inline helpers. `phase3_harness_session_runner.py` still intentionally owns the interactive Qt session lifecycle, toolbar wiring, and callback cluster; this slice did not absorb that runtime control path. `signing_shell.py` now acts as the outer widget/lifecycle adapter around those helpers: it delegates workspace assembly to `signing_workspace_composition.py`, keeps copy-to-clipboard behavior at the edge, and leaves the returned widget methods bound through the compatibility export layer and the narrow production port surface. The signature-properties panel delegates certificate configuration application, preset apply/save/delete, visible-signature setup load/apply orchestration, catalog refresh, dirty-selection clearing, validation text, and readiness state to `signature_properties_coordinator.py`; visible-signature edits now clear selected preset state only through `ApplyVisibleSignatureSetup`, and the panel re-renders certificate/preset selector widgets from returned `SignaturePropertiesViewState` when coordinator-owned selection state changes. The setup presentation is now preset-first: `Signature preset` renders before `Certificate configuration`, while deeper appearance and placement editing no longer occupies the default sidebar and instead lives behind the compact manual-refinement dialog entrypoint. `visible_signature_setup_form.py` now owns visible-signature widget construction, `VisibleSignatureSetupDraft` load/build mapping, field enablement rules, and font-style availability rules. Its `Signature style` group keeps only bounded MVP controls such as signer label prefix, layout, stamp position, timezone mode, font family, font size, emphasis, and `Show field names`; direct datetime-format, image-stamp-path, text-color, border, background, and other low-level appearance editors are no longer exposed in Qt. Hidden appearance values loaded from presets or workflow state are preserved through the form's internal template cache so preview/signing parity is maintained while the UI stays narrow. Its `Visible text` section keeps per-field visibility checkboxes, preserves loaded `field_order` during rebuilds, and normalizes custom override text away so hidden fields stay hidden after the form is reapplied. The shell no longer exposes `field_controls`; callers only interact with the slimmer form boundary. Document text query state and current-hit navigation live behind `application/document_text_search.py` with a concrete `QPdfDocument` adapter in `infra/document_text_search.py`; arbitrary manual text selection state lives behind `application/document_text_selection.py` with a concrete QtPdf selection adapter in `infra/document_text_selection.py`; the viewer exposes explicit `"signature"` and `"text"` interaction modes plus a separate text-highlight overlay path, and now changes the cursor to match those modes while the sidebar keeps only copy/clear controls visible for document-text selection. Canonical preview render invocation, render-backend reuse, pixmap loading, snapshot replacement/cleanup, and teardown disposal now live behind `signature_preview_lifecycle.py`; preview geometry planning, stamp/text band fitting, widget ordering, and canonical-render handoff now live behind `signature_preview_layout.py`; `signing_shell.py` keeps close-aware lifecycle cleanup and top-level widget installation while delegating workspace assembly, sidebar widget construction, properties-panel implementation, signing-action dialog/state glue, review/text bridge behavior, interaction-plan execution, and widget-export/testing-seam ownership to the extracted presentation helpers. The app frame now applies live shell settings, certificate-selector refreshes, and profile/preset-selector refreshes through the explicit shell port instead of private workspace hooks or direct widget duck typing. The shell can select and apply existing certificate configurations, including configurations that resolve saved passwords through the app-frame-provided secret provider, can refresh its selector after lifecycle results report certificate catalog changes, can refresh reusable profile/preset choices after the profile library closes, and can refresh the document review card from the current viewer path without mutating the PDF. The signing shell consumes `AppSettings` for output-path defaults but no longer edits app-wide directory settings directly.
- Lifecycle clarification: `SigningWorkspaceLifecycle` owns workspace replacement mounting through `QtWorkspaceMount`; `FoliaSealAppFrame` no longer directly calls `window.setCentralWidget(...)` for workspace replacement. The frame still owns action state and compatibility properties, while the lifecycle owns compose/mount/dispose ordering and idempotent active-widget cleanup.
- Status: Confirmed by code and tests; size/concentration is debt/needs review.

### Qt signing action boundary

- Location: `src/foliaseal/presentation/qt/signing_workspace_action_bridge.py`
- Responsibility: Own the shell-facing dialog and state glue for the signing-action flow while delegating policy decisions to `SigningActionBoundary`.
- Owns: output-path dialog handling, overwrite confirmation, sign-submit state application, signed-output reopen forwarding, certificate-refresh signing-state reload, and the small apply/reset helpers needed to keep the live shell widgets in sync.
- Does not own: signing-action policy, result/state-machine rules, Qt widget construction, or signing backend execution.
- Key collaborators: `SigningActionBoundary`, `SigningWorkspaceWidget`, `SigningWorkspaceSidebar`, shell-provided dialog/callback/open-output helpers.
- Main entry points: `SigningWorkspaceActionBridge.choose_output_pdf_path()`, `SigningWorkspaceActionBridge.submit_sign_request()`, `SigningWorkspaceActionBridge.open_signed_output()`, `SigningWorkspaceActionBridge.refresh_certificate_configurations()`.
- Known constraints: The bridge must keep overwrite confirmation and state application explicit so the shell can remain thin while `SigningActionBoundary` stays the narrower policy layer beneath it.
- Status: Confirmed by code and tests.

### Qt signing action boundary

- Location: `src/foliaseal/presentation/qt/signing_action_boundary.py`
- Responsibility: Own the narrower signing-action policy boundary under the action bridge while delegating state transitions to `SigningActionCoordinator`.
- Owns: `SigningActionBoundary`, `SigningActionBoundaryResult`, shell callback routing for status/error/open-output events, and the small adapter methods that load, accept output paths, submit, reopen, and invalidate.
- Does not own: Qt widget mutation, signing state-machine policy, preview layout, or signing backend execution.
- Key collaborators: `SigningActionCoordinator`, `SigningWorkspaceActionBridge`, `SigningWorkspaceWidget`, `SigningWorkspaceSidebar`, shell-provided error/status/open-output callbacks.
- Main entry points: `SigningActionBoundary.load()`, `SigningActionBoundary.accept_output_path()`, `SigningActionBoundary.submit()`, `SigningActionBoundary.open_signed_output()`, `SigningActionBoundary.invalidate()`.
- Known constraints: `open_signed_output()` must only forward the callback when the coordinator reports a successful output path, and the boundary must continue to return immutable result snapshots so shell tests can focus on delegation behavior.
- Status: Confirmed by code and tests.

### Qt signing action coordinator

- Location: `src/foliaseal/presentation/qt/signing_action_coordinator.py`
- Responsibility: Own the state machine for the signing action panel while keeping Qt widget mutation and shell callback routing out of the coordinator.
- Owns: `SigningActionState`, `SigningActionTransition`, result tracking, the active flow-stage and plain-language next-action text, sign-enabled state, reopen enablement, output-path acceptance, readiness gating, and sign-result reset behavior when the draft or selected path changes. The sidebar renders the persistent six-step journey while the coordinator derives the current setup, placement, readiness, confirmation, or verification state from the active draft.
- Does not own: Qt dialog handling, shell callback emission, document rendering, preview layout, signing-action boundary orchestration, or signing backend implementation.
- Key collaborators: `SigningDraftWorkflow`, shell-provided `apply_changes()`, shell readiness/validation callables, signing executor protocol, shell reopen callback.
- Main entry points: `SigningActionCoordinator.load()`, `SigningActionCoordinator.accept_output_path()`, `SigningActionCoordinator.invalidate()`, `SigningActionCoordinator.submit()`, `SigningActionCoordinator.open_signed_output()`.
- Known constraints: The shell still owns overwrite confirmation and the boundary still owns error emission routing. The sidebar owns widget mutation for returned state, and the coordinator intentionally returns immutable snapshots so shell and sidebar tests can focus on adapter behavior instead of duplicated state policy.
- Status: Confirmed by code and tests.

### Qt signing workspace sidebar

- Location: `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`
- Responsibility: Build the right-hand sidebar for the production signing workspace and render `SigningActionState` into the `Sign PDF` panel without involving the shell in widget mutation.
- Owns: `SigningWorkspaceSidebar`, `SigningActionControls`, `DocumentReviewControls`, `DocumentTextControls`, the `Sign PDF` panel widget tree, and the panel-width fallback used when the container width is not yet established.
- Does not own: dialog handling, callback emission, viewer refresh policy, application settings forwarding, or the public shell surface.
- Key collaborators: `SigningActionCoordinator`, `SigningWorkspaceWidget`, `presentation/qt/signing_shell.py`.
- Main entry points: `SigningWorkspaceSidebar.apply_signing_action_state()`, the sidebar constructor, and the panel helper functions that compose the action, review, and text sections.
- Known constraints: `apply_signing_action_state()` must remain safe when the container reports zero width during early layout or tests; it falls back to a sensible width limit so the flow-detail label does not collapse. The sidebar must remain a widget-level renderer only, while the shell keeps the higher-level orchestration boundary.
- Status: Implemented and confirmed by code and tests.

### Qt signing workspace lifecycle

- Location: `src/foliaseal/presentation/qt/signing_workspace_lifecycle.py`
- Responsibility: Coordinate replacement and shutdown of the one active signing workspace at the app-frame boundary.
- Owns: `WorkspaceMountPort`, the `QtWorkspaceMount` adapter over `QMainWindow.setCentralWidget()`, `SigningWorkspaceLifecyclePort`, and `SigningWorkspaceLifecycle`.
- Does not own: workspace composition, shell behavior, frame menu state, or the production/testing shell-port split.
- Key collaborators: `WorkspaceOpenPort`, `OpenWorkspaceCommand`, `OpenWorkspaceOutcome`, `FoliaSealAppFrame`.
- Main entry points: `SigningWorkspaceLifecycle.replace()` and `SigningWorkspaceLifecycle.close()`.
- Known constraints: Replacement is ordered compose → mount → dispose-old → publish-active. If mounting fails, the candidate is disposed and the previous active workspace remains recorded. Widget cleanup is best effort (`close()` then `deleteLater()`), and repeated close calls are no-ops. The frame delegates central-widget installation to `QtWorkspaceMount`; it does not reach into the concrete shell widget for lifecycle replacement. `SigningWorkspacePort` remains the narrow production caller contract; `SigningWorkspaceTestingPort` remains the separate diagnostics/harness contract and is not widened by lifecycle management.
- Status: Confirmed by code and tests.

### Qt signing workspace diagnostics and testing boundary

- Location: `src/foliaseal/presentation/qt/signing_workspace_diagnostics.py`, `signing_workspace_testing_port.py`
- Responsibility: Provide a Qt-free, immutable read model for one live workspace state and the explicit non-production diagnostics/testing contract consumed by Phase 3.
- Owns: `SigningWorkspaceSnapshot`, `SigningWorkspaceDiagnosticsPort`, `SigningWorkspaceTestingPort`, and the narrower typed panel port.
- Does not own: widget construction, signing policy, persistence, or the caller-facing production `SigningWorkspacePort`.
- Key collaborators: `signing_workspace_runtime.py`, `signing_workspace_compatibility_surface.py`, `phase3_harness_workspace.py`, and `signing_shell_port.py`.
- Main entry points: `SigningWorkspaceRuntime.snapshot()`, `SigningWorkspaceCompatibilitySurface.snapshot()`, and `SigningWorkspaceTestingAdapter.snapshot()`.
- Known constraints: A snapshot is assembled from one runtime read and includes current request, placement, appearance, certificate selection, timestamp requirement, sign readiness, and last signing result. The production shell port remains narrow; `testing_adapter` is the explicit harness seam and `compat_surface` is transitional.
- Status: Confirmed by code and tests.

### Qt signing workspace runtime

- Location: `src/foliaseal/presentation/qt/signing_workspace_runtime.py`
- Responsibility: Own live shell-local workspace verbs and produce the consistent diagnostic snapshot used by testing and Phase 3.
- Owns: Viewer/panel/page routing, review/text refresh and navigation, placement and overlay operations, shell-edge status/error handling, and `SigningWorkspaceSnapshot` production from bound workflow state.
- Does not own: app-frame production-port policy, widget-export compatibility, signing-action state-machine ownership, or Phase 3 evidence serialization.
- Key collaborators: `SigningDraftWorkflow`, `ViewerWorkflow`, `DocumentReviewWorkspaceSession`, `SignaturePropertiesPanel`, `signing_workspace_diagnostics.py`, and `signing_workspace_orchestrator.py`.
- Main entry points: `SigningWorkspaceRuntime.snapshot()` and its existing workspace mutation/read verbs.
- Known constraints: Snapshot production must preserve the same binding errors and live values as the existing individual accessors; action-coordinator result state is supplied by the compatibility/testing adapter rather than duplicated in runtime.
- Status: Confirmed by code and tests.

### Qt canonical preview lifecycle

- Location: `src/foliaseal/presentation/qt/signature_preview_lifecycle.py`
- Responsibility: Render canonical preview snapshots and manage their lifetime for the Qt shell.
- Owns: `CanonicalPreviewRenderState`, `QtCanonicalPreviewLifecycle`, backend reuse, pixmap loading, replacement cleanup, and explicit disposal.
- Does not own: Widget-tree composition, preview geometry planning, or coordinator reconciliation.
- Key collaborators: `render_canonical_signature_preview()`, `QtPdfRenderBackend`, `SignaturePropertiesPanel`, `signature_preview_layout.py`.
- Main entry points: `QtCanonicalPreviewLifecycle.refresh()`, `QtCanonicalPreviewLifecycle.current_snapshot()`, `QtCanonicalPreviewLifecycle.dispose()`.
- Important types/classes/functions: `CanonicalPreviewRenderState`.
- Known constraints: Cleanup is best-effort and only removes temporary canonical-preview directories; normal widget close must reach `dispose()` so temp snapshots are not left behind. The helper returns widget-facing render state rather than mutating widgets directly.
- Status: Confirmed by code and tests.

### Qt signature preview layout

- Location: `src/foliaseal/presentation/qt/signature_preview_layout.py`
- Responsibility: Plan and apply preview card geometry, widget ordering, and visibility for the Qt signing shell.
- Owns: `PreviewLayoutState`, `QtSignaturePreviewLayout`, available-width calculation, body/card sizing, reserved stamp/text dimensions, stamp loading, preview scaling, card styling, and widget visibility handoff.
- Does not own: Canonical preview rendering, widget-tree creation, or signing semantics.
- Key collaborators: `SigningDraftPreview`, `CanonicalPreviewRenderState`, `SignatureLayoutPlan`, `VisibleSignatureLayoutEngine`, `SignaturePropertiesPanel`.
- Main entry points: `QtSignaturePreviewLayout.plan()`, `QtSignaturePreviewLayout.apply()`.
- Important types/classes/functions: `PreviewLayoutState`, `_preview_available_width()`, `_preview_body_size()`, `_preview_layout_geometry()`, `_preview_card_padding_pt()`.
- Known constraints: The helper is widget-facing and must stay compatible with the fake Qt widget surfaces used by tests. It should consume the application-layer layout plan and the canonical preview lifecycle state instead of reimplementing either boundary.
- Status: Confirmed by code and tests.

### Configuration and reusable signing-object persistence

- Location: `src/foliaseal/infra/config/schemas.py`, `src/foliaseal/infra/config/app_settings_storage.py`, `src/foliaseal/infra/config/profile_storage.py`, `src/foliaseal/infra/config/certificate_storage.py`, `src/foliaseal/infra/secret_storage.py`, `src/foliaseal/application/certificate_creation.py`, `src/foliaseal/application/certificate_import.py`, `src/foliaseal/application/certificate_lifecycle.py`, `src/foliaseal/application/signing_material_resolver.py`
- Responsibility: Serialize, deserialize, validate, load, and save trust/timestamp configuration plus reusable signing-object catalogs; coordinate certificate lifecycle policy for creating, importing, editing, deleting, and exporting app-managed certificates and configurations; store saved certificate passwords through secure external secret storage.
- Owns: `AppSettings`, `AppSettingsStore`, `TrustProfile`, `TimestampPolicy`, `ManagedCertificate`, `CertificateConfiguration`, `CertificateCatalog`, `CertificateCatalogStore`, `CertificateCreationService`, `CertificateImportService`, `CertificateLifecycleService`, `SecretToolCertificateSecretStore`, `SigningMaterial`, `CertificateSigningMaterialResolver`, `AppearanceProfile`, `PlacementProfile`, reference-only `SignaturePreset`, `ResolvedSignaturePreset`, `SignaturePresetCatalog`, `SignaturePresetCatalogStore`.
- Does not own: UI controls or runtime signing flow.
- Key collaborators: domain models, Qt signing shell, Linux Secret Service through `secret-tool`.
- Main entry points: `AppSettings.default()`, `AppSettings.from_dict()`, `AppSettingsStore.load_settings()`, `AppSettingsStore.save_settings()`, `ManagedCertificate.from_dict()`, `CertificateConfiguration.from_dict()`, `CertificateCatalog.from_dict()`, `CertificateCatalog.remove_configuration_by_id()`, `CertificateCatalog.remove_managed_certificate_by_id()`, `CertificateCatalogStore.load_catalog()`, `CertificateCatalogStore.delete_configuration_by_id()`, `CertificateCatalogStore.delete_managed_certificate_by_id()`, `CertificateCatalogStore.export_managed_certificate_by_id()`, `CertificateCreationService.create_self_signed_certificate()`, `CertificateImportService.import_pkcs12()`, `CertificateLifecycleService.create_self_signed_certificate()`, `CertificateLifecycleService.import_pkcs12()`, `CertificateLifecycleService.save_configuration()`, `CertificateLifecycleService.delete_configuration()`, `CertificateLifecycleService.delete_managed_certificate()`, `CertificateLifecycleService.export_managed_certificate()`, `SecretToolCertificateSecretStore.set_secret()`, `SecretToolCertificateSecretStore.get_secret()`, `SecretToolCertificateSecretStore.delete_secret()`, `CertificateSigningMaterialResolver.resolve_by_configuration_id()`, `AppearanceProfile.from_dict()`, `PlacementProfile.from_dict()`, `SignaturePreset.from_dict()`, `SignaturePresetCatalog.from_dict()`, `SignaturePresetCatalog.resolve_preset()`, `SignaturePresetCatalog.preset_names()`, `SignaturePresetCatalog.preset_named()`, `SignaturePresetCatalog.upsert_preset()`, `SignaturePresetCatalog.remove_preset()`, `SignaturePresetCatalogStore.load_catalog()`, `save_catalog()`, `save_preset()`, `delete_preset()`.
- Known constraints: App settings storage uses `${XDG_CONFIG_HOME:-~/.config}/FoliaSeal/settings.json` and returns home-directory defaults when missing or blank. The Qt app frame uses the default open directory for File/Open, owns the app-wide settings dialog for editing default directories, and passes settings into the signing shell; the save-output dialog uses the default output directory. The profile store still uses the historical user-visible `Signature Profiles/profiles.json` path, but the JSON shape now separates `appearance_profiles`, `placement_profiles`, and `signature_presets`. Certificate configuration storage uses `${XDG_DATA_HOME:-~/.local/share}/FoliaSeal/Certificates/certificates.json` plus a `Managed/` directory for app-owned PKCS#12 files. Self-signed PKCS#12 files can be created through `CertificateLifecycleService`, which delegates PKCS#12 generation to `CertificateCreationService`; creation writes into managed storage, creates one `ManagedCertificate(source_kind="created")`, creates one `CertificateConfiguration`, and can optionally save the password through `SecretToolCertificateSecretStore`. Existing PKCS#12 files can be imported through `CertificateLifecycleService`, which delegates PKCS#12 validation and copying to `CertificateImportService`; import creates one `ManagedCertificate(source_kind="imported")`, creates one `CertificateConfiguration`, and can optionally save the password through `SecretToolCertificateSecretStore`. `CertificateLifecycleService` can rename, edit notes for, and delete `CertificateConfiguration` records by stable id; deleting a configuration with a saved `password_secret_ref` deletes the referenced secret first and leaves the catalog entry in place if secret deletion is unavailable or fails. If catalog deletion fails after secret deletion, the lifecycle service attempts to restore the saved secret and reports restore failure explicitly. The lifecycle service can export selected managed PKCS#12 files to a user-selected destination without mutating the catalog and can delete unreferenced `ManagedCertificate` records by stable id, which removes the app-managed PKCS#12 file; deletion is blocked while any `CertificateConfiguration` references the managed certificate. Passwords are not stored in ordinary JSON; `certificates.json` stores only the saved-password flag and opaque secret reference. Obsolete signature-preset compatibility wrappers such as `profile_names()`, `profile_named()`, `save_profile()`, and `delete_profile()` have been removed; `appearance_profile_named()` and `placement_profile_named()` remain because they address canonical profile objects.
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

- Location: `src/foliaseal/application/qa_*`, `src/foliaseal/application/phase2_evidence.py`, `src/foliaseal/application/phase3_evidence_service.py`, `src/foliaseal/presentation/qt/phase*_harness.py`, `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py`, `artifacts/`
- Responsibility: Produce manual QA evidence, preview matrix outputs, signed-output acceptance artifacts, signed acceptance evidence summaries, and evidence contract evaluations through an explicit application-layer service boundary.
- Owns: Evidence contract evaluation, harness capture JSON shape, preview/signed matrix summary generation, Phase 3 evidence orchestration, scoped filtering of known benign evidence-command runtime chatter, checklist rendering. `phase3_evidence_core.py` owns the Qt-free result models and evidence decisions, `phase3_evidence_ports.py` owns effect protocols, and `Phase3EvidenceOrchestrator` is the canonical typed dispatch/validation boundary. `phase3_harness.py` remains the Qt execution adapter and `phase3_signed_acceptance_evidence.py` only supplies default service wiring and runtime-noise suppression.
- Does not own: Core domain models, signing semantics, or backend reservation evidence assembly.
- Key collaborators: CLI entry points, `phase3_evidence_core.py`, `phase3_evidence_ports.py`, `phase3_evidence_orchestrator.py`, `phase3_evidence_service.py`, Qt shell, signing backend, artifacts directory.
- Known constraints: The Phase 3 harness now splits the Qt-backed adapter/composition root, scenario application, interactive session collection, preview-matrix runtime looping, signed-acceptance matrix execution, interactive signing-harness orchestration, signed-acceptance per-scenario execution, shared appearance snapshot shaping, sign-time diagnostics shaping, shared image comparison, shared preview text geometry, shared signed-output evidence shaping, signed-output render analysis, capture assembly, and report finalization across `src/foliaseal/presentation/qt/phase3_harness.py`, `src/foliaseal/presentation/qt/phase3_harness_workspace.py`, `src/foliaseal/presentation/qt/phase3_harness_session_runner.py`, `src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py`, `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py`, `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py`, `src/foliaseal/presentation/qt/phase3_appearance_snapshotter.py`, `src/foliaseal/presentation/qt/phase3_sign_time_diagnostics_snapshotter.py`, `src/foliaseal/presentation/qt/phase3_image_comparison_helper.py`, `src/foliaseal/presentation/qt/phase3_text_geometry_helper.py`, `src/foliaseal/presentation/qt/phase3_signed_output_snapshotter.py`, `src/foliaseal/presentation/qt/phase3_signed_output_render_snapshotter.py`, `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py`, and `src/foliaseal/presentation/qt/phase3_harness_reporting.py`; `phase3_harness_workspace.py` now owns preview-matrix and signed-acceptance scenario application plus viewer priming refresh and snapshot-returning capture reads for both live-shell and headless workflow paths, while `phase3_harness_session_runner.py` still owns the interactive Qt session lifecycle, toolbar wiring, and callback cluster. The reporting module still owns JSON serialization and checklist markdown rendering, while `phase3_harness.py` consumes the application-layer request dataclasses instead of defining its own public request type. `build_backend_reservation_evidence()` now carries the neutral planner snapshot alongside the adapter-derived reservation evidence, and the backend/preview callers now consume the neutral boundary first. `src/foliaseal/application/phase3_evidence_service.py` is the explicit boundary for the CLI-facing evidence flows, while `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` only provides default service helpers and runtime-noise suppression. Any remaining legacy free-function wrappers are internal implementation helpers, not stable public seams; the removed `Phase3Composition`/`Phase3Harness` facade is historical only.
- Status: Confirmed by code, README, tests, and artifacts.

### Phase 3 evidence core and effect ports

- Location: `src/foliaseal/application/phase3_evidence_core.py`, `src/foliaseal/application/phase3_evidence_ports.py`
- Responsibility: Keep Phase 3 result truth and evidence decisions Qt-free while expressing runner, asset, loader, writer, and runtime-context effects as narrow protocols.
- Owns: `Phase3MatrixKind`, typed matrix/evidence result DTOs, matrix normalization and validation, capture loading, evidence markdown rendering, and effect-port protocols.
- Does not own: Qt lifecycle, signing, rendering, filesystem implementation, or CLI parsing.
- Key collaborators: `phase3_evidence_service.py`, `phase3_evidence_orchestrator.py`, and the presentation-layer runners/adapters.
- Main entry points: `normalize_matrix_result()`, `validate_signed_acceptance_matrix_summary()`, `matrix_summary_row()`, `render_evidence_markdown()`, and the protocols in `phase3_evidence_ports.py`.
- Status: Confirmed by code and tests.

### Phase 3 evidence service

- Location: `src/foliaseal/application/phase3_evidence_service.py`
- Responsibility: Own the injected execution boundary used by the Phase 3 orchestrator for harness capture, preview matrices, signed-acceptance matrices, capture validation, and signed-acceptance evidence generation.
- Owns: `Phase3HarnessCaptureRequest`, `Phase3MatrixRequest`, `Phase3SignedAcceptanceEvidenceRequest`, `Phase3HarnessValidationRequest`, `Phase3EvidenceService`, `capture_harness()`, `preview_matrix_result()`, `signed_acceptance_matrix_result()`, `validate_harness_capture()`, and `run_signed_acceptance_evidence()`.
- Does not own: Qt widget behavior, direct harness UI orchestration, or the concrete artifact writer implementation.
- Key collaborators: `presentation/qt/phase3_harness.py`, `presentation/qt/phase3_signed_acceptance_evidence.py`, `__main__.py`, `qa_evidence_contract.py`, `qa_signed_acceptance_generation.py`.
- Main entry points: `build_default_phase3_evidence_service()`, `Phase3EvidenceService.for_pdf()`, `Phase3EvidenceService.capture_harness()`, `Phase3EvidenceService.preview_matrix_result()`, `Phase3EvidenceService.signed_acceptance_matrix_result()`, `Phase3EvidenceService.validate_harness_capture()`, `Phase3EvidenceService.run_signed_acceptance_evidence()`.
- Known constraints: The service is intentionally thin over injected runners and writers. Typed result normalization and evidence decisions live in `phase3_evidence_core.py`; effect dependencies are expressed by `phase3_evidence_ports.py`. The service does not publish raw `run_*` methods. Signed normalization treats nonzero `error_scenario_count` as a failure, and aggregate rows preserve a runner-provided `summary_json_path` with the artifacts-directory fallback. The Qt helper module only suppresses known benign Qt/pyHanko chatter and preserves documented output paths for default service construction.
- Status: Confirmed by code and tests; the orchestrator boundary and CLI routing are covered by focused tests. Exact focused/full-suite totals for this slice are recorded in the ExecPlan after final validation.

### Phase 3 evidence orchestrator

- Location: `src/foliaseal/application/phase3_evidence_orchestrator.py`
- Responsibility: Provide the single application-owned boundary for tagged Phase 3 evidence dispatch and read-only capture validation.
- Owns: `Phase3OperationKind`, `Phase3OperationRequest`, `Phase3ValidationRequest`, `Phase3EvidenceServicePort`, operation payload type checks, dispatch to capture/preview/signed/aggregate service methods, and conversion of validation requests into the service validation DTO.
- Does not own: runner execution, Qt application or window lifecycle, scenario mutation, artifact writing, summary schema shaping, signing, preview rendering, or runtime-noise suppression.
- Key collaborators: `Phase3EvidenceService`, `Phase3EvidenceSession`, CLI composition in `__main__.py`, and the existing preview/headless, signed/Qt, and interactive adapters.
- Main entry points: `Phase3EvidenceOrchestrator.run()`, `Phase3EvidenceOrchestrator.validate()`, and `orchestrator_for_service()`.
- Known constraints: The module must remain free of Qt, PyHanko, Pillow, TSA, filesystem-artifact implementations, and presentation imports. It deliberately preserves separate execution contexts behind the service port rather than merging incompatible lifecycles.
- Status: Confirmed by code and focused boundary tests.

### Phase 3 release-fidelity contract

- Location: `src/foliaseal/application/phase3_fidelity_contract.py`, `tests/fixtures/phase3/release_fidelity_manifest.json`
- Responsibility: Validate the versioned, tracked manifest contract used for the bounded release-fidelity corpus before matrix execution.
- Owns: `manifest_version: 1`, `phase3_fidelity_v1` comparison tolerances and critical-zero counters, per-scenario `expected_outcome` and expected diagnostics, and the six-supported/two-intentional-fit-rejection corpus declaration.
- Does not own: preview rendering, signing, PDF verification, or historical stress-corpus remediation.
- Key collaborators: Phase 3 preview and signed-acceptance matrix runners, `phase3_evidence_service.py`, and the tracked release manifest.
- Known constraints: This is a bounded release claim, not a universal layout guarantee. The eight scenarios and zero-tolerance comparison fields are the only supported scope; compact or historical stress manifests remain separate, non-comparable evidence.
- Status: Confirmed by code, tests, and matrix evidence (`/tmp/foliaseal-release-preview-final/summary.json`, `/tmp/foliaseal-release-signed-final/summary.json`; manifest SHA-256 `4dd4545c94398411268589666caf06ee7cdceb3a79f03aeac6591008b5e1085e`).

### Phase 3 harness session runner

- Location: `src/foliaseal/presentation/qt/phase3_harness_session_runner.py`
- Responsibility: Run the interactive Qt session for Phase 3 and collect raw state before capture assembly.
- Owns: `Phase3HarnessSessionResult`, `_QtHarnessBindings`, `Phase3HarnessSessionRunnerDeps`, `Phase3HarnessSessionRunner`, session-level sign request/error/state tracking, toolbar wiring, workspace-snapshot capture orchestration, and final-state capture inputs.
- Does not own: report finalization, JSON serialization, checklist rendering, matrix execution, or evidence-contract evaluation.
- Key collaborators: `phase3_harness.py`, `phase3_harness_capture_assembler.py`, `phase3_harness_reporting.py`, `build_qt_signing_shell()`, `SigningDraftWorkflow`, `ViewerWorkflow`.
- Main entry points: `Phase3HarnessSessionRunner.run()` and the explicit capture factory in `phase3_harness.py`.
- Known constraints: The helper keeps the interactive shell flow Qt-bound, but the collected session result must stay stable enough for later payload assembly and report finalization. The runner now consumes `Phase3HarnessWorkspaceSnapshot` and adapts it back to the legacy dict payload expected by `phase3_harness_capture_assembler.py`; `phase3_harness_workspace.py` still intentionally does not absorb the session lifecycle itself. Matrix callers use `Phase3MatrixOperations`, while interactive capture is installed separately and remains lazy until requested. Operation-local dependency bundles inject profile stores, lifecycles, renderers, artifact ports, and signing executors.
- Status: Confirmed by code and tests.

### Phase 3 harness workspace boundary

- Location: `src/foliaseal/presentation/qt/phase3_harness_workspace.py`
- Responsibility: Own the narrow workspace boundary used by the Phase 3 harness for preview-matrix and signed-acceptance style mutations plus snapshot-returning capture reads.
- Owns: `Phase3HarnessScenarioCommand`, `Phase3HarnessCaptureCommand`, `Phase3HarnessWorkspaceSnapshot`, `Phase3HarnessWorkspacePort`, `QtPhase3HarnessWorkspaceDeps`, `QtPhase3HarnessWorkspaceAdapter`, `HeadlessPhase3HarnessWorkspaceDeps`, `HeadlessPhase3HarnessWorkspaceAdapter`, `snapshot_current_draft_request(...)`, `capture_qt_preview_render(...)`, and the shared appearance/rect normalization applied to both live-shell and headless workflow paths.
- Does not own: interactive Qt session lifecycle, toolbar wiring, signed-run capture assembly, or report finalization.
- Key collaborators: `phase3_harness.py`, `phase3_signed_acceptance_scenario_executor.py`, `signing_workspace_testing_port.py`, `signing_workspace_compatibility_surface.py`, `SigningDraftWorkflow`, `SignaturePresetCatalogStore`.
- Main entry points: `Phase3HarnessScenarioCommand.from_mapping()`, `QtPhase3HarnessWorkspaceAdapter.apply_scenario()`, `QtPhase3HarnessWorkspaceAdapter.capture_snapshot()`, `HeadlessPhase3HarnessWorkspaceAdapter.apply_scenario()`, `HeadlessPhase3HarnessWorkspaceAdapter.capture_snapshot()`, and `phase3_harness.py::_apply_preview_matrix_scenario()`.
- Known constraints: This is still a narrow tracer-bullet seam, not the full harness resolution. The live adapter now translates directly through the explicit `SigningWorkspaceTestingPort` installed as `testing_adapter`, consuming its typed `panel` port rather than the concrete properties panel, and it keeps preview-render capture behind that port even though the lower-level preview-analysis payload builder still lives in `phase3_harness.py`. The helper now receives those collaborators through typed live/headless dependency bundles so the remaining shell-anatomy knowledge stays concentrated in one module instead of being duplicated across preview-matrix, signed-acceptance, and session-runner call sites.
- Status: Confirmed by code and tests.

### Phase 3 preview matrix runner

- Location: `src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py`
- Responsibility: Run the headless preview-only matrix sweep and emit the stable summary artifact for one manifest.
- Owns: `Phase3PreviewMatrixRunnerDeps`, `Phase3PreviewMatrixRunner`, preview-matrix manifest loading, scenario iteration, scenario-level exception mapping, aggregate counter shaping, and `summary.json` writing.
- Does not own: interactive Qt session control, signed-acceptance matrix execution, scenario-specific preview capture logic, or evidence-contract evaluation.
- Key collaborators: `phase3_matrix_operations.py`, `phase3_harness.py`, `_load_preview_matrix_manifest()`, `_execute_headless_preview_matrix_scenario()`, `_preview_matrix_error_result()`, and `_preview_matrix_diagnostic_summary()`.
- Main entry points: `Phase3PreviewMatrixRunner.run()` and `Phase3MatrixOperations.preview`.
- Known constraints: The runner is intentionally headless and still depends on repository-default preset resolution, but that dependency is now injected through `Phase3PreviewMatrixRunnerDeps.profile_store_factory` instead of being looked up inline. `phase3_harness.py` remains the composition root that wires the real manifest loader, scenario executor, error mapper, profile-store factory, and JSON normalization helper into the runner.
- Status: Confirmed by code and tests.

### Phase 3 signed-acceptance matrix runner

- Location: `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py`
- Responsibility: Run the Qt-backed signed-acceptance matrix sweep and emit the stable summary artifact for one manifest.
- Owns: `Phase3SignedAcceptanceMatrixRunnerDeps`, `Phase3SignedAcceptanceMatrixRunner`, signed-acceptance manifest loading, `timestamping_mode` validation, one-shell scenario iteration, scenario-level exception mapping, aggregate counter shaping, acceptance-expectation evaluation, and `summary.json` writing through `Phase3MatrixArtifactPort`.
- Does not own: the public harness entrypoint signature, interactive harness capture assembly, preview-only matrix execution, or evidence-contract evaluation.
- Key collaborators: `phase3_matrix_operations.py`, `phase3_harness.py`, `_load_signed_acceptance_manifest()`, `phase3_harness_workspace.py`, `phase3_signed_acceptance_scenario_executor.py`, `_preview_matrix_error_result()`, `_signed_matrix_diagnostic_summary()`, and `_evaluate_signed_matrix_acceptance_expectations()`.
- Main entry points: `Phase3SignedAcceptanceMatrixRunner.run()` and `Phase3MatrixOperations.signed_acceptance`.
- Known constraints: The runner intentionally keeps the matrix-level workflow together, including `timestamping_mode` validation and dummy timestamper wiring, while delegating Qt window/event-loop work to `Phase3SignedAcceptanceLifecyclePort`. It starts and attaches the shell, processes events after priming and each scenario, and closes in `finally`, including failure paths. `Phase3SignedAcceptanceScenarioResult` rows are converted with `as_mapping()` before existing counters are calculated. The artifact adapter's returned path is authoritative for `summary_json_path`; `phase3_harness.py` remains the composition root that wires the real manifest loader, lifecycle, artifact, scenario, workspace, error mapper, render-backend factory, acceptance evaluator, and JSON normalization collaborators.
- Status: Confirmed by code and tests.

### Phase 3 signed-acceptance lifecycle and artifact ports

- Location: `src/foliaseal/presentation/qt/phase3_signed_acceptance_lifecycle.py`, `src/foliaseal/presentation/qt/phase3_matrix_artifacts.py`
- Responsibility: Isolate replaceable side effects from signed matrix orchestration.
- Owns: `Phase3SignedAcceptanceLifecyclePort`, `QtPhase3SignedAcceptanceLifecycle`, `FakePhase3SignedAcceptanceLifecycle`, `Phase3MatrixArtifactPort`, `FilesystemPhase3MatrixArtifactPort`, and `MemoryPhase3MatrixArtifactPort`.
- Does not own: scenario application, signing, acceptance counters, or report schema decisions.
- Known constraints: Lifecycle call order is start -> attach shell -> process events -> scenario/event processing -> close. Artifact adapters only prepare the matrix directory and write `summary.json`; generated PDFs and image evidence remain owned by scenario/output snapshot helpers.
- Status: Confirmed by code and tests.

### Phase 3 signed-acceptance scenario executor

- Location: `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py`
- Responsibility: Execute one signed-acceptance scenario row from live shell state through optional signed-output capture.
- Owns: `Phase3SignedAcceptanceScenarioExecutor`, `Phase3SignedAcceptanceScenarioResult`, scenario application, workspace snapshot capture consumption, signing submission, successful-output snapshotting, and final result-row shaping.
- Does not own: matrix-level iteration, exception mapping, acceptance-expectation evaluation, or summary writing.
- Key collaborators: `phase3_harness.py`, `phase3_harness_workspace.py`, `_apply_preview_matrix_scenario()`, `_capture_preview_render()`, `phase3_signed_output_snapshotter.py`, `Phase3SignedAcceptanceMatrixRunner`.
- Main entry points: `Phase3SignedAcceptanceScenarioExecutor.run()`, `phase3_harness.py::_execute_signed_acceptance_scenario()`.
- Known constraints: The executor intentionally keeps the per-scenario preview and signing flow together because the result-row contract spans both preview evidence and optional signed-output evidence. Its typed result's `as_mapping()` is the compatibility serializer for existing row keys, including intentional fit rejections. `phase3_harness_workspace.py` owns workspace reads, while successful-output evidence shaping lives in the shared snapshotter boundary.
- Status: Confirmed by code and tests.

### Phase 3 signed-output snapshotter

- Location: `src/foliaseal/presentation/qt/phase3_signed_output_snapshotter.py`
- Responsibility: Shape the stable successful-output evidence bundle and the compact preview-vs-output comparison view used by Phase 3 QA.
- Owns: `Phase3SignedOutputSnapshotter`, `snapshot_successful_signed_output()`, and `signed_output_preview_comparison_snapshot()`.
- Does not own: lower-level PDF verification, signed-output render analysis orchestration, matrix iteration, or evidence-contract evaluation.
- Key collaborators: `phase3_harness.py`, `phase3_harness_capture_assembler.py`, `phase3_pdf_signature_snapshotter.py` (bound `snapshot_output_signature()`, `snapshot_output_verification()`, and `snapshot_visible_signature_appearance()` methods), `phase3_signed_output_render_snapshotter.py`.
- Main entry points: `Phase3SignedOutputSnapshotter.snapshot_successful_signed_output()`, `signed_output_preview_comparison_snapshot()`.
- Known constraints: The snapshotter intentionally stays in the Qt harness package because it composes the focused PDF evidence adapter and render snapshotter, but it centralizes the signed-output payload contract so both scenario execution and interactive capture assembly reuse the same shaping logic while delegating render-analysis orchestration to the dedicated render snapshotter.
- Status: Confirmed by code and tests.

### Phase 3 PDF signature snapshotter

- Location: `src/foliaseal/presentation/qt/phase3_pdf_signature_snapshotter.py`
- Responsibility: Extract JSON-ready signed-PDF evidence without owning Qt lifecycle, scenario mutation, or matrix/report orchestration.
- Owns: `Phase3PdfSignatureSnapshotter`, embedded-signature counting, signature metadata, cryptographic/certification/timestamp verification projections, visible signature appearance parsing, appearance XObject/text/image summaries, PDF rectangle/name/numeric serializers, and pyHanko metadata normalization.
- Does not own: signed-output render comparison, preview geometry, Qt widgets, signing semantics, matrix iteration, or evidence-contract evaluation.
- Key collaborators: `phase3_harness.py` composition wiring, `phase3_signed_output_snapshotter.py`, `phase3_harness_capture_assembler.py`, pyHanko/PDF readers, and timestamp trust adapters.
- Main entry points: `count_embedded_signatures()`, `snapshot_output_signature()`, `snapshot_output_verification()`, and `snapshot_visible_signature_appearance()`.
- Known constraints: The adapter preserves the existing mapping keys, error strings, `None` versus `False` distinctions, malformed-input fallbacks, and timestamp projections. Recursive appearance-state/hex-text parsing and any timestamp-presence semantic redesign remain deferred behavior-focused debt rather than part of this extraction.
- Status: Confirmed by code and direct boundary tests.

### Phase 3 signed-output render snapshotter

- Location: `src/foliaseal/presentation/qt/phase3_signed_output_render_snapshotter.py`
- Responsibility: Run the signed-output render-analysis workflow for one successful output.
- Owns: `Phase3SignedOutputRenderSnapshotter`, page rendering, direct-appearance rendering, annotation-rect projection, crop extraction, normalization to preview analysis size, text-detection output, appearance snapshotting, parity comparison, and side-by-side artifact writing.
- Does not own: matrix iteration, successful-output bundle shaping, or evidence-contract evaluation.
- Key collaborators: `phase3_harness.py`, `phase3_appearance_snapshotter.py`, `phase3_signed_output_snapshotter.py`, `_render_signed_annotation_appearance_direct()`, `compare_signature_appearance_snapshots()`.
- Main entry points: `Phase3SignedOutputRenderSnapshotter.run()`, `phase3_harness.py::_snapshot_signed_output_render()`.
- Known constraints: The render snapshotter intentionally remains in the Qt harness package because it composes many harness-private render and comparison helpers. `phase3_harness.py` remains the composition root that wires those real callables into the helper while the payload contract stays unchanged, and the preview-side / signed-output-side `SignatureAppearanceSnapshot` shaping now comes from the extracted appearance snapshotter boundary.
- Status: Confirmed by code and tests.

### Phase 3 appearance snapshotter

- Location: `src/foliaseal/presentation/qt/phase3_appearance_snapshotter.py`
- Responsibility: Shape both sides of the `SignatureAppearanceSnapshot` parity model used by Phase 3 render comparison.
- Owns: `Phase3AppearanceSnapshotter`, `preview_appearance_snapshot_from_capture()`, and `signed_output_appearance_snapshot()`.
- Does not own: render-analysis orchestration, successful-output bundle shaping, or evidence-contract evaluation.
- Key collaborators: `phase3_harness.py`, `phase3_signed_output_render_snapshotter.py`, `_signature_text_style_from_snapshot()`, `_structural_line_bounds_px()`, `_snapshot_visible_appearance_text_fragments()`, `_reconstruct_text_box_bounds_px()`.
- Main entry points: `Phase3AppearanceSnapshotter.preview_appearance_snapshot_from_capture()`, `Phase3AppearanceSnapshotter.signed_output_appearance_snapshot()`.
- Known constraints: The appearance snapshotter intentionally stays in the Qt harness package because it depends on harness-local reconstruction helpers, but it centralizes both sides of the parity model so render comparison no longer has to reach back into two separate harness-local builders.
- Status: Confirmed by code and tests.

### Phase 3 sign-time diagnostics snapshotter

- Location: `src/foliaseal/presentation/qt/phase3_sign_time_diagnostics_snapshotter.py`
- Responsibility: Shape the merged sign-time diagnostics payload stored inside Phase 3 preview snapshots.
- Owns: `Phase3SignTimeDiagnosticsSnapshotter` and `snapshot()`.
- Does not own: preview render capture, backend reservation evidence generation, matrix iteration, or evidence-contract evaluation.
- Key collaborators: `phase3_harness.py`, `_mapping()`, `build_backend_reservation_evidence()`.
- Main entry points: `Phase3SignTimeDiagnosticsSnapshotter.snapshot()`, `phase3_harness.py::_snapshot_sign_time_fit_diagnostics()`.
- Known constraints: The diagnostics snapshotter intentionally stays in the Qt harness package because it still consumes harness-local preview render captures, but it centralizes the backend-fit plus canonical-preview-geometry merge so this capture payload no longer lives inline in `phase3_harness.py`.
- Status: Confirmed by code and tests.

### Phase 3 image comparison helper

- Location: `src/foliaseal/presentation/qt/phase3_image_comparison_helper.py`
- Responsibility: Own the shared preview/output image-comparison primitives used by transition diagnostics and signed-output parity.
- Owns: `Phase3ImageComparisonHelper`, crop hashing, white-background flattening, raw crop change ratio, normalized crop change ratio, aspect-ratio delta, and side-by-side comparison artifact writing.
- Does not own: transition-diagnostics policy, signed-output render orchestration, or evidence-contract evaluation.
- Key collaborators: `phase3_harness.py`, `phase3_signed_output_render_snapshotter.py`, `_analyze_capture_state_transitions()`.
- Main entry points: `Phase3ImageComparisonHelper.image_crop_sha256()`, `flatten_preview_image_to_white()`, `image_crop_change_ratio()`, `normalized_image_crop_change_ratio()`, `aspect_ratio_delta()`, `write_side_by_side_comparison()`.
- Known constraints: The image-comparison helper intentionally stays in the Qt harness package because it still serves harness-local transition analysis and signed-output parity, but it centralizes the shared crop/comparison primitives so those behaviors no longer reach back into a large inline helper block in `phase3_harness.py`.
- Status: Confirmed by code and tests.

### Phase 3 text geometry helper

- Location: `src/foliaseal/presentation/qt/phase3_text_geometry_helper.py`
- Responsibility: Own the shared preview text-geometry primitives used by preview diagnostics and signed-output parity.
- Owns: `Phase3TextGeometryHelper`, source-to-preview bounds projection, preview text content/line detection wrappers, candidate-pixel analysis, border-stroke filtering, reference-envelope restriction, and reference-label fallback capture.
- Does not own: preview-capture orchestration, text-edge policy, or evidence-contract evaluation.
- Key collaborators: `phase3_harness.py`, `phase3_signed_output_render_snapshotter.py`, `_capture_preview_render()`, `detect_text_content_bounds_in_image()`, `detect_text_line_bounds_in_image()`.
- Main entry points: `Phase3TextGeometryHelper.project_content_bounds_to_preview()`, `detect_text_content_bounds_in_preview()`, `detect_text_line_bounds_in_preview()`, `detect_text_geometry_in_preview()`, `reference_text_content_bounds()`.
- Known constraints: The text-geometry helper intentionally stays in the Qt harness package because it still serves harness-local preview diagnostics and signed-output parity, but it centralizes the multi-step preview text-geometry reconstruction so those behaviors no longer reach back into a large inline helper block in `phase3_harness.py`.
- Status: Confirmed by code and tests.

### Phase 3 harness capture assembler

- Location: `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py`
- Responsibility: Turn raw interactive harness session state into stable JSON-ready signed-run bundles and final capture payload dictionaries.
- Owns: `Phase3HarnessCaptureAssembler`, `build_signed_run_bundle()`, and `build_capture_payload()`.
- Does not own: Qt session control, widget capture, checklist rendering, JSON writing, or evidence-contract evaluation.
- Key collaborators: `phase3_harness.py`, `phase3_signed_output_snapshotter.py`, `phase3_pdf_signature_snapshotter.py` (bound `count_embedded_signatures()`, `snapshot_output_signature()`, `snapshot_output_verification()`, and `snapshot_visible_signature_appearance()` methods), `_snapshot_signed_output_render()`, `_analyze_capture_state_transitions()`.
- Main entry points: `Phase3HarnessCaptureAssembler.build_signed_run_bundle()`, `Phase3HarnessCaptureAssembler.build_capture_payload()`.
- Known constraints: The assembler is still a presentation-layer helper because it depends on preview/output snapshot functions in the Qt harness package. It delegates low-level signed-PDF evidence to bound `Phase3PdfSignatureSnapshotter` methods and shared successful-output shaping to `phase3_signed_output_snapshotter.py`, while preserving the current capture JSON keys and artifact semantics exactly. In particular, `backend_reservation_snapshot`, `signed_runs`, `captured_states`, and the final evidence fields are treated as a stable payload contract for downstream report finalization and validation.
- Status: Confirmed by code and tests.

### Phase 3 harness reporting boundary

- Location: `src/foliaseal/presentation/qt/phase3_harness_reporting.py`
- Responsibility: Finalize the post-Qt reporting boundary for a single Phase 3 harness run.
- Owns: `Phase3HarnessReportRequest`, `Phase3HarnessReportResult`, `finalize_phase3_harness_report()`, summary JSON writing, checklist markdown rendering, checklist file writing.
- Does not own: interactive Qt session control, raw capture-state collection, or backend reservation evidence generation.
- Key collaborators: `phase3_harness.py`, `phase3_harness_capture_assembler.py`, `qa_evidence_contract.py`, `build_phase3_checklist_results_markdown()`, `Phase3HarnessCapture`.
- Known constraints: direct unit tests can exercise this module without the interactive harness path; it should stay a narrow pure boundary with injected evaluator/renderer/writer callables that consume the raw capture payload produced by the session runner. The refactor did not change the summary/checklist output contract: this module still finalizes the same stable capture payload into `summary.json` and the checklist artifact.
- Status: Confirmed by code and tests.

### Packaging

- Location: `pyproject.toml`, `foliaseal.spec`, `scripts/build_pyinstaller.sh`, `scripts/build_deb.sh`, `scripts/deb_package_audit.py`, `src/foliaseal/build/pyinstaller_support.py`, `src/foliaseal/build/debian_packaging.py`, and `packaging/foliaseal.svg`
- Responsibility: Python package metadata, console script registration, package data, PyInstaller one-dir bundle support, and Debian-family desktop distribution.
- Owns: the `foliaseal` console script; bundled font assets, Python runtime, and Qt runtime; deterministic `.deb` naming and staging; `/usr/bin/foliaseal` relocation-aware launcher; desktop entry and icon; `Depends: poppler-utils`; and package-owned extraction/startup/signed-acceptance auditing.
- Does not own: system-wide package installation, distribution repositories, or copying arbitrary host libraries into the bundle.
- Known constraints: Runtime dependencies in `pyproject.toml` are `pyHanko[opentype]` and Pillow; the optional `gui` extra installs `PySide6`, while the Debian package bundles PySide6 and the Python runtime. Interactive pixels still late-resolve the host `pdftoppm` supplied by `poppler-utils`; canonical preview and evidence rendering remain QtPdf-scoped. The first supported distribution mode is Debian-family `amd64` (architecture is read from `dpkg --print-architecture`).
- Status: Confirmed by code and tests. The built `dist/foliaseal_0.1.0_amd64.deb` passed package inspection, extracted wrapper/help and offscreen Qt startup, and the package-owned signing audit (10 scenarios/7 successful signings, 18/18 parity, 3/3 fit rejection). SHA-256: `14403f944861636ca8729893eb4be721668f197e07ae733154e493b70b6a8d95`.

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
| `PreparedSigningPlan` | `application/phase3_signing_backend.py` | Immutable application-owned preparation shared by visible signing and layout adapters. | normalized backend request, optional visible semantics/layout plan, typed fit issues, stamp text, visible flag. | `prepare_phase3_signing_plan()` creates it; no PyHanko/Pillow objects cross this boundary. |
| `SigningDraftWorkflow` | `application/signing_draft_workflow.py` | Mutable application state for an in-progress signing draft. | signing paths, credentials, selected reusable-object ids, rect, appearance, placement context. | Produces preview and final `SigningRequest`; can apply resolved `CertificateConfiguration` material. |
| `CertificatePreviewReader` / `Pkcs12CertificatePreviewReader` | `application/certificate_preview.py` | Extract certificate-derived visible-signature preview values. | certificate path, passphrase -> field-value map and availability flag. | Injected into draft workflow so PKCS#12 parsing is not implemented inside the draft object. |
| `SigningDraftPreview` | `application/signing_draft_workflow.py` | UI-ready normalized preview payload. | rect, appearance settings, fields, detail text, stamp text, issues, can_submit. | Used by Qt and preview renderer. |
| `BackendReservationEvidence` | `application/phase3_signing_backend.py` | JSON-ready backend reservation evidence for non-Qt callers and temporary harnesses. | snapshot dict, top-level error string. | Lets the harness consume backend reservation facts without reconstructing them from private helpers. |
| `SignaturePropertiesViewState` | `application/signature_properties_coordinator.py` | Immutable signing-properties panel state. | selected certificate/preset display names, catalog names, visible-signature setup draft, validation text, readiness, preview. | Display-name boundary plus Qt-independent visible-signature setup state between the panel and application-layer reconciliation. |
| `SigningSetupSelectionOutcome` | `application/signing_setup_session.py` | Explicit result for certificate/preset selection attempts. | `SignaturePropertiesViewState` state, `applied` flag. | Lets Qt distinguish applied updates from canceled/no-op selection attempts while still carrying the current rendered state. |
| `VisibleSignatureSetupDraft` / `VisibleSignaturePlacementDraft` | `application/signature_properties_coordinator.py` | Qt-independent visible-signature setup form state. | `SignatureAppearance`, placement values, placement-enabled flag. | Lets the panel load and submit visible-signature setup without mutating `SigningDraftWorkflow` directly on the main form path. |
| `ApplyVisibleSignatureSetup` / `ApplyCertificateConfiguration` / `ApplySignaturePreset` / `SaveCurrentPreset` / `DeletePreset` / `RefreshCatalogs` / `ClearSelectedSignaturePreset` | `application/signature_properties_coordinator.py` | Command payloads for signing-properties reconciliation. | setup draft, selected name, optional passphrase, overwrite flag. | Used by the panel to express user intent without mutating widget internals directly. |
| `DocumentSignatureReviewItem` | `application/document_review.py` | UI-ready read-only summary for one embedded signature. | display label, signer subject, local validation result, compact list text, selector-driven drill-in detail text with status-sensitive next-action guidance for non-verified states. | Rendered as the compact per-signature list and the selector-backed detail view in the Qt signing shell `Document review` card. |
| `DocumentReviewSummary` | `application/document_review.py` | UI-ready read-only signature review payload. | headline, detail, signature count, per-signature items, signer subject, certification state, local validation result, inspection error. | Used by the Qt signing shell `Document review` card; its top-level text stays compact and latest-signature oriented while per-signature items own the drill-in guidance. |
| `VisibleSignatureSemantics` | `application/visible_signature_semantics.py` | Resolved visible-signature meaning-level payload. | resolved fields, title/detail/stamp text, metadata reason/location/contact info, fit issues, readiness. | Shared source for workflow preview, canonical preview text, backend signing text, and metadata. |
| `SignatureLayoutPlan` | `application/visible_signature_layout.py` | Canonical visible-signature geometry result. | text/stamp area dimensions, layout rules, fit issues, optional ink reservation. | Boundary for backend/canonical/Qt preview geometry. |
| `VisibleSignatureLayoutRequest` / `VisibleSignaturePreparation` | `application/visible_signature_layout.py` | Prepare-once visible-signature decision and memoized target materializers. | appearance, rectangle, stamp inputs/options; neutral `SignatureLayoutPlan`, reservation snapshot, typed fit diagnostics, captured fit-gate decision, signing/preview results. | Preview may carry an explicitly derived stamp-suppressed plan; PyHanko/Pillow objects are created only by target materialization. |
| `CanonicalPreviewRenderState` | `presentation/qt/signature_preview_lifecycle.py` | Widget-facing canonical preview render output. | snapshot, pixmap, card style, render-label visibility, body size. | Returned by the canonical lifecycle helper and consumed by the layout helper and shell. |
| `PreviewLayoutState` | `presentation/qt/signature_preview_layout.py` | Widget-facing preview layout result. | stamp text, stamp position, available width, card size, detail width, preview scale, padding, body size, reserved band sizes, stamp aspect ratio, raw stamp pixmap, fallback card style, text CSS. | Returned by `QtSignaturePreviewLayout.plan()` and consumed by `apply()`. |
| `ViewerSession` | `application/viewer_session.py` | Viewer page/zoom state. | page count, current page, zoom. | Clamps zoom via `ViewerZoomLimits`. |
| `ViewerRenderSnapshot` | `application/viewer_workflow.py` | Current rendered page state for interactions. | page index, zoom, pan, page box, rotation, image size, mapping readiness. | Required for selection mapping. |
| `AppearanceProfile` | `infra/config/schemas.py` | Persisted signing-specific visible appearance. | stable id, display name, `SignatureAppearance`. | Canonical reusable appearance object. |
| `PlacementProfile` | `infra/config/schemas.py` | Persisted reusable placement defaults. | stable id, display name, current-page rect, numeric fine-tuning flag. | Converted to current shell width/height defaults when resolved. |
| `SignaturePreset` / `ResolvedSignaturePreset` / `SignaturePresetCatalog` | `infra/config/schemas.py` | Persisted reference-only preset plus resolved view for current UI/harness consumers. | preset id, display name, optional referenced object ids. | `SignaturePreset` stores references only; resolved objects expose appearance/placement for transitional call sites. |
| `ManagedCertificate` / `CertificateConfiguration` / `CertificateCatalog` | `infra/config/schemas.py` | Persist managed certificate file records and user-facing certificate selections. | managed certificate id, display name, storage filename, subject summary; configuration id, managed certificate id, save-password flag, password secret reference. | Passwords are referenced by secret id only, never stored in config JSON. |
| `SigningMaterial` / `CertificateSigningMaterialResolver` | `application/signing_material_resolver.py` | Convert a selected certificate configuration into runtime signing inputs. | certificate path, passphrase, optional alias. | Uses explicit passphrase or a `CertificateSecretProvider`; reports helpful missing-file/secret errors. |
| `RenderPageRequest` / `RenderPageResult` | `infra/render/base.py` | Render backend request/result. | document path, page index, zoom; width/height/RGBA bytes. | Backend protocol contract. |
| `Phase3HarnessReportRequest` / `Phase3HarnessReportResult` | `presentation/qt/phase3_harness_reporting.py` | Post-Qt reporting request/result for one Phase 3 harness run. | raw capture payload, summary/checklist paths, finalized capture, contract evaluation, rendered checklist text. | Gives the harness a smaller direct reporting boundary for tests and orchestration. |
| `Phase3HarnessCaptureRequest` / `Phase3MatrixRequest` / `Phase3HarnessValidationRequest` | `application/phase3_evidence_service.py` | Caller-facing Phase 3 request dataclasses. | capture inputs, matrix inputs, capture-validation path. | Shared by the CLI and the Qt-backed harness adapter so the application service owns the public request contract. |
| `Phase3MatrixKind` / `Phase3MatrixResult` | `application/phase3_evidence_core.py` | Typed preview or signed-acceptance matrix result over the existing summary mapping. | kind, raw summary, passed, artifacts directory, authoritative summary path, counts, errors, warnings. | Core-owned typed result; service adapters provide execution summaries. |
| `Phase3OperationKind` / `Phase3OperationRequest` / `Phase3ValidationRequest` | `application/phase3_evidence_orchestrator.py` | Tagged application inputs for effectful operations and read-only validation. | operation kind/payload or summary JSON path. | The orchestrator validates payload types and keeps dispatch explicit. |
| `Phase3EvidenceOrchestrator` | `application/phase3_evidence_orchestrator.py` | Canonical application dispatcher over the injected service port. | service port, tagged operation request, validation request. | Returns service result objects unchanged; does not know runner or Qt details. |
| `Phase3EvidenceSession` | `application/phase3_evidence_orchestrator.py` | Canonical PDF-bound convenience facade. | orchestrator; PDF/certificate/passphrase; default artifact directory. | Session methods build typed requests and preserve matrix/capture/validation outputs. |
| `Phase3SignedAcceptanceScenarioResult` | `presentation/qt/phase3_signed_acceptance_scenario_executor.py` | Typed result for one signed-acceptance scenario row. | existing row fields plus optional signed-output evidence. | `as_mapping()` preserves the established JSON row contract, including intentional rejection rows. |
| `Phase3MatrixOperations` | `presentation/qt/phase3_matrix_operations.py` | Lazy typed preview and signed-acceptance matrix operations injected into the application evidence service. | `preview` and `signed_acceptance` callables consuming `Phase3MatrixRequest` and returning existing raw summaries. | The module is dependency-light and does not import Qt, PIL, pyHanko, rendering, or `phase3_harness.py`; each concrete runner is constructed only when selected. |
| `Phase3HarnessSessionResult` | `presentation/qt/phase3_harness_session_runner.py` | Raw interactive Qt session state before capture assembly. | first render timing, sign requests, signed runs, errors, interaction counts, captured states, final session state, capture request, last signing result. | Feeds `Phase3HarnessCaptureAssembler.build_capture_payload()` so capture assembly stays separate from the Qt loop. |
| `Phase3HarnessCaptureAssembler` | `presentation/qt/phase3_harness_capture_assembler.py` | Pure helper that turns raw session state into signed-run bundles and the final capture payload dictionary. | output snapshot collaborators plus `build_signed_run_bundle()` and `build_capture_payload()`. | Lets harness tests target capture assembly directly without patching as much of the interactive Qt runner. |
| `Phase3HarnessCapture` | `presentation/qt/phase3_harness.py` | Structured acceptance harness result. | preview/request/signing/evidence fields. | JSON output is validated by evidence contract. |
| `DocumentReviewCardState` | `application/document_review_workspace.py` | Immutable review-card state rendered by the Qt shell. | review summary, signature labels, selected signature index/label/detail, selector enablement. | Gives the shell a narrow review-only view model instead of a mixed review/text bag. |
| `DocumentTextWorkspaceState` | `application/document_review_workspace.py` | Immutable document-text card state rendered by the Qt shell. | search state, selection state, selection mode flag, display source, status text, detail text. | The shell reads `state.document_text` directly and uses its nested search/selection state for button enablement. |
| `DocumentReviewWorkspaceState` | `application/document_review_workspace.py` | Composition root for the review and text card states. | `review`, `document_text`. | The shell now consumes `state.review` and `state.document_text` directly rather than unpacking a flat mixed object. |

## 6. Contracts and boundaries

### CLI contract

- Producer: `src/foliaseal/__main__.py`
- Consumer: Developers, manual QA, local automation.
- Stability: Needs review. Commands are documented in README and covered by CLI tests, so treat them as user-facing.
- Commands: default `foliaseal`, `phase2-evidence`, `phase2-viewer-harness`, `phase3-signing-harness`, `phase3-signing-preview-matrix`, `phase3-signing-acceptance-matrix`, `phase3-signing-acceptance-evidence`, `phase3-signing-harness-validate`.
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

### Signature-properties coordinator contract

- Producer: `DefaultSignaturePropertiesCoordinator.load()`, `DefaultSignaturePropertiesCoordinator.apply_visible_setup()`, `DefaultSignaturePropertiesCoordinator.apply_signature_preset()`, `DefaultSignaturePropertiesCoordinator.reconcile()`
- Consumer: `SigningSetupSession`, coordinator tests, future non-Qt orchestration callers.
- Stability: Active application boundary.
- Backward compatibility requirements: Preserve display-name based UI state, workflow-backed selection ids, catalog refresh reconciliation, password resolution for saved certificate configurations, preset save/delete behavior, and preview/readiness values returned to the panel.
- Validation: catalog lookups, `SigningDraftWorkflow` methods, `CertificateSigningMaterialResolver`, and `control_issue` folding into validation text.
- Error behavior: Invalid selections or resolution failures raise `SignaturePropertiesCoordinatorError`; the panel maps those to user-visible error messages.
- Source files: `src/foliaseal/application/signature_properties_coordinator.py`, `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`.

### Signing setup session contract

- Producer: `SigningSetupSession`
- Consumer: `SignaturePropertiesPanel`, direct setup-session tests, future non-Qt setup orchestration callers.
- Stability: Active application boundary.
- Backward compatibility requirements: Preserve preset-first setup behavior, partial preset preservation of the active certificate when a preset omits a certificate reference, on-demand manual certificate-password prompting, session-local passphrase cache reuse, explicit applied/canceled selection outcomes, preset save/delete state refresh, coordinator-owned programmatic appearance-update dirty clearing, and coordinator-backed `SignaturePropertiesViewState` rendering inputs.
- Validation: delegates signing-draft rule enforcement to `DefaultSignaturePropertiesCoordinator`; retries only when coordinator errors indicate manual password entry is required.
- Error behavior: non-promptable coordinator failures still raise `SignaturePropertiesCoordinatorError`; canceled manual-password prompts return `SigningSetupSelectionOutcome(state=..., applied=False)` so the Qt adapter can restore the current setup state without mutating the workflow.
- Source files: `src/foliaseal/application/signing_setup_session.py`, `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, `tests/unit/test_signing_setup_session.py`.

### Qt visible-signature setup form contract

- Producer: `QtVisibleSignatureSetupForm`
- Consumer: `SignaturePropertiesPanel`, direct Qt form tests.
- Stability: Active presentation-layer boundary.
- Backward compatibility requirements: Preserve the visible-signature and placement control structure, `VisibleSignatureSetupDraft` load/build parity, the preset-first visible-signature framing, the `Show field names` toggle, per-field visibility checkbox behavior, loaded `field_order` preservation, hidden loaded-appearance value preservation for UI-removed fields, font-style availability rules, and generic/page-change callback behavior. The advanced per-field override editor, direct datetime/image/color/box appearance editors, and shell-exposed `field_controls` are no longer part of this contract.
- Validation: direct fake-Qt boundary tests plus thin shell integration coverage.
- Error behavior: invalid enum text or appearance values raise while building a draft; unsupported font-style combinations disable the bold/italic controls instead of crashing.
- Source files: `src/foliaseal/presentation/qt/visible_signature_setup_form.py`, `src/foliaseal/presentation/qt/signing_shell.py`, `tests/unit/test_qt_visible_signature_setup_form.py`.

### Render backend contract

- Producer: `PdfRenderBackend` implementations.
- Consumer: `ViewerWorkflow`.
- Stability: Confirmed application/infra boundary.
- Backward compatibility requirements: `render_page()` returns RGBA bytes matching width*height*4; `get_page_geometry()` returns boxes and rotation for coordinate mapping. The live adapter must preserve QtPdf geometry even though it rasterises pixels with Poppler.
- Validation: backend checks path existence, page index, zoom; `PopplerPdfRenderBackend` has focused coverage for missing `pdftoppm`, unavailable geometry, command failure, missing output, page-number conversion, zoom-to-DPI conversion, and opaque RGBA conversion; viewer checks mapping readiness.
- Error behavior: concrete backend raises for missing files, invalid pages, and rendering-command failures. `PopplerPdfRenderBackend.diagnostics()` identifies missing `pdftoppm` or unavailable Qt geometry; `QtPdfRenderBackend.diagnostics()` reports unavailable Qt bindings.
- Source files: `src/foliaseal/infra/render/base.py`, `src/foliaseal/infra/render/qt_backend.py`, `src/foliaseal/infra/render/poppler_backend.py`, `tests/unit/test_poppler_render_backend.py`.

### Visible-signature layout contract

- Producer: `VisibleSignatureLayoutEngine.plan()`
- Consumer: backend signing, canonical preview rendering, Qt preview sizing.
- Stability: Active application boundary; some internals remain transitional.
- Backward compatibility requirements: Preserve preview/output parity and fit validation behavior across backend, canonical preview, and Qt preview.
- Validation: layout engine returns `VisibleSignatureFitIssue` values instead of throwing for fit failures; adapters may raise when fit issues are not explicitly allowed.
- Error behavior: invalid image paths/read failures from default `PillowStampImageProbe` raise `ValueError`; fit checker failures become typed issues.
- Source files: `src/foliaseal/application/visible_signature_layout.py`.

### Visible-signature layout preparation contract

- Producer: `VisibleSignatureLayoutPort.prepare()`; production implementation is `VisibleSignatureLayoutService.prepare()`.
- Consumer: `phase3_signing_backend.py`, canonical preview rendering, Qt preview geometry, and tests.
- Stability: Active application boundary.
- Backward compatibility requirements: One preparation must feed signing and preview without optional-plan re-planning; preview/signing must retain matching geometry evidence, fit issue codes/messages, and image behavior. Compact horizontal preview suppression is explicit in `CanonicalPreviewLayout.stamp_suppressed`.
- Validation: `tests/unit/test_visible_signature_layout_boundary.py` proves one-preparation reuse and explicit suppression; focused layout, preview, workflow, Qt, and backend suites preserve numerical and message parity.
- Error behavior: public image loading preserves `ValueError` messages; public fit validation preserves `SigningDraftValidationIssue` severity/code/message mapping.
- Source files: `src/foliaseal/application/visible_signature_layout.py`, `src/foliaseal/application/phase3_signing_backend.py`, `src/foliaseal/application/signing_preview_renderer.py`, `src/foliaseal/application/signing_draft_workflow.py`, `src/foliaseal/presentation/qt/signature_preview_layout.py`.

### Qt preview layout contract

- Producer: `QtSignaturePreviewLayout.plan()`, `QtSignaturePreviewLayout.apply()`
- Consumer: `SignaturePropertiesPanel`, shell tests, future Qt preview callers.
- Stability: Active presentation-layer boundary.
- Backward compatibility requirements: Preserve preview card sizing, orientation, stamp/text band sizing, widget ordering, and visibility behavior for canonical and non-canonical preview states.
- Validation: `PreviewLayoutState` planning, fake-widget tests, and parity with application-layer layout planning where the preview card depends on layout geometry.
- Error behavior: missing or invalid stamp pixmaps fall back to safe sizing and default visibility instead of crashing; test doubles without full Qt APIs are tolerated where the helper probes for methods dynamically.
- Source files: `src/foliaseal/presentation/qt/signature_preview_layout.py`, `src/foliaseal/presentation/qt/signing_shell.py`, `tests/unit/test_signature_preview_layout.py`.

### Signing workspace lifecycle contract

- Producer: `SigningWorkspaceLifecycle.replace()` / `SigningWorkspaceLifecycle.close()`.
- Consumer: `FoliaSealAppFrame` and future app-frame hosts.
- Stability: Active presentation-layer lifecycle boundary.
- Backward compatibility requirements: Preserve compose-before-mount ordering, candidate cleanup on mount failure, old-widget disposal only after successful mount, idempotent close, and the separate production `SigningWorkspacePort` / non-production `SigningWorkspaceTestingPort` contracts.
- Validation: lifecycle boundary tests with fake workspace-open and mount ports, plus app-frame open/close integration coverage.
- Error behavior: workspace composition errors are propagated to the frame's open-error path; mount errors dispose the candidate and re-raise while retaining the previous active record; widget close/delete failures are swallowed as best-effort cleanup.
- Source files: `src/foliaseal/presentation/qt/signing_workspace_lifecycle.py`, `src/foliaseal/presentation/qt/app_frame.py`, `src/foliaseal/presentation/qt/signing_shell_port.py`, `src/foliaseal/presentation/qt/signing_workspace_testing_port.py`.

### Canonical preview lifecycle contract

- Producer: `QtCanonicalPreviewLifecycle.refresh()`, `QtCanonicalPreviewLifecycle.dispose()`
- Consumer: `SignaturePropertiesPanel`, shell tests, future canonical-preview callers.
- Stability: Active presentation-layer boundary.
- Backward compatibility requirements: Preserve canonical render parameters, backend reuse, snapshot replacement cleanup, widget-facing render state, and explicit disposal on close or destroy.
- Validation: lifecycle boundary tests plus thin shell-level cleanup checks.
- Error behavior: unavailable Qt rendering or invalid preview data falls back to hidden-preview state and best-effort cleanup.
- Source files: `src/foliaseal/presentation/qt/signature_preview_lifecycle.py`, `src/foliaseal/presentation/qt/signing_shell.py`, `tests/unit/test_signature_preview_lifecycle.py`.

### Profile catalog JSON contract

- Producer: `SignaturePresetCatalogStore.save_catalog()`.
- Consumer: Qt signing shell/profile controls and future launches.
- Stability: Persisted file contract.
- Storage path: `${XDG_DATA_HOME:-~/.local/share}/FoliaSeal/Signature Profiles/profiles.json`.
- Format: JSON object with `schema_version`, `appearance_profiles`, `placement_profiles`, and `signature_presets`. `SignaturePreset` entries are reference-only and can point to optional certificate configuration, appearance profile, and placement profile ids.
- Validation: `SignaturePresetCatalog.from_dict()` and nested schema constructors reject malformed shape/types/duplicates.
- Error behavior: missing or blank file loads as empty catalog; invalid JSON raises `ConfigValidationError`.
- Source files: `src/foliaseal/infra/config/schemas.py`, `src/foliaseal/infra/config/profile_storage.py`.

### Certificate catalog JSON contract

- Producer: `CertificateLifecycleService` through the app-frame certificate dialogs, delegating persistence to `CertificateCatalogStore`, `CertificateCreationService`, and `CertificateImportService`. Saved certificate password values are produced only to the external secret provider, not to the JSON catalog.
- Consumer: Qt app-frame certificate dialogs, signing-material resolver, Qt signing shell certificate selector, and future launches.
- Stability: Persisted file contract.
- Storage path: `${XDG_DATA_HOME:-~/.local/share}/FoliaSeal/Certificates/certificates.json`.
- Managed files path: `${XDG_DATA_HOME:-~/.local/share}/FoliaSeal/Certificates/Managed/`.
- Format: JSON object with `schema_version`, `managed_certificates`, and `certificate_configurations`. `CertificateConfiguration` entries reference managed certificates by id and may reference saved passwords by secret id only.
- Validation: `CertificateCatalog.from_dict()` and nested schema constructors reject malformed shape/types, duplicate ids, duplicate configuration names, path-like storage filenames, and saved-password configurations without a secret reference.
- Error behavior: missing or blank file loads as an empty catalog; invalid JSON raises `ConfigValidationError`; deleting an unknown configuration or managed certificate id raises `KeyError`; deleting a managed certificate referenced by a certificate configuration raises `ConfigValidationError`; exporting a missing managed PKCS#12 file raises `FileNotFoundError`; import failures raise `CertificateImportError`; resolver failures raise `SigningMaterialResolutionError` with user-actionable messages; saved-password writes/deletes raise `SecretStorageError` when `secret-tool` or the desktop Secret Service cannot complete the operation.
- Source files: `src/foliaseal/infra/config/schemas.py`, `src/foliaseal/infra/config/certificate_storage.py`, `src/foliaseal/infra/secret_storage.py`, `src/foliaseal/application/certificate_creation.py`, `src/foliaseal/application/certificate_import.py`, `src/foliaseal/application/certificate_lifecycle.py`, `src/foliaseal/application/signing_material_resolver.py`, `src/foliaseal/presentation/qt/app_frame.py`, `src/foliaseal/presentation/qt/app_frame_certificate_management.py`.

### App settings JSON contract

- Producer: `AppSettingsStore.save_settings()`.
- Consumer: Qt app-frame Settings menu and Open-file behavior; Qt signing shell save-output file-dialog default directory behavior.
- Stability: Persisted file contract.
- Storage path: `${XDG_CONFIG_HOME:-~/.config}/FoliaSeal/settings.json`.
- Format: JSON object with `schema_version`, `default_output_directory`, `default_open_directory`, `linux_packaging_channel`, and `ui`.
- Validation: `AppSettings.from_dict()` rejects malformed shape/types and blank directory strings.
- Error behavior: missing or blank file loads home-directory defaults; invalid JSON raises `ConfigValidationError`; save failures preserve the original filesystem exception and remove `settings.json.tmp` when cleanup is possible.
- Source files: `src/foliaseal/infra/config/schemas.py`, `src/foliaseal/infra/config/app_settings_storage.py`.

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
- Known constraints: `backend_reservation_snapshot` and `backend_reservation_error` remain part of the capture payload, but Phase 3 harness code now consumes those values from `build_backend_reservation_evidence()` instead of reconstructing them from backend-private helpers. The session runner returns `Phase3HarnessSessionResult`, and `Phase3HarnessCaptureAssembler.build_capture_payload()` derives the stable capture payload before `phase3_harness_reporting.py` finalizes the files.
- Source files: `src/foliaseal/presentation/qt/phase3_harness.py`, `src/foliaseal/application/qa_evidence_contract.py`, `artifacts/`.

### Phase 3 evidence command/session contract

- Producer: `Phase3EvidenceOrchestrator` and `Phase3EvidenceService.for_pdf()`.
- Consumer: Reusable Python callers that need repeated preview, signed-acceptance, capture, or validation operations for one PDF.
- Stability: Active application boundary; additive to the existing service, harness, and CLI contracts.
- Format: `Phase3OperationRequest` tags effectful operations; `Phase3ValidationRequest` remains read-only. `Phase3EvidenceSession` binds `pdf_path`, `certificate_path`, `passphrase`, and default `artifacts/phase3` paths, with per-call artifact overrides.
- Validation: The orchestrator checks command/payload pairing and delegates capture validation through the service and evidence core.
- Error behavior: Type mismatches raise `TypeError`; unsupported operation kinds raise `ValueError`; underlying service/runner errors retain their existing behavior.
- Compatibility rule: Preserve CLI command names, printed labels, exit behavior, raw summary mappings, and serialized artifact fields. The application service/orchestrator remains the execution boundary; removed presentation composition/facade classes and forwarding aliases were not compatibility contracts.
- Source files: `src/foliaseal/application/phase3_evidence_core.py`, `src/foliaseal/application/phase3_evidence_ports.py`, `src/foliaseal/application/phase3_evidence_orchestrator.py`, `src/foliaseal/application/phase3_evidence_service.py`, `src/foliaseal/presentation/qt/phase3_harness.py`, `src/foliaseal/__main__.py`.

### Phase 3 evidence orchestrator contract

- Producer: `src/foliaseal/application/phase3_evidence_orchestrator.py`
- Consumer: CLI composition, reusable session callers, and focused boundary tests.
- Stability: Active application boundary; canonical typed command contract.
- Validation: `run()` checks the payload type required by each `Phase3OperationKind`; `validate()` delegates to `Phase3EvidenceServicePort.validate_harness_capture()`.
- Compatibility rule: Service result objects, raw summary mappings, artifact paths, and error behavior pass through unchanged. Preview/headless, signed/Qt, and interactive adapters remain separate behind the service port.
- Source files: `src/foliaseal/application/phase3_evidence_orchestrator.py`, `src/foliaseal/application/phase3_evidence_service.py`.

### Phase 3 matrix result contract

- Producer: `Phase3EvidenceService` and the preview/signed matrix runners.
- Consumer: CLI dispatch, focused tests, and evidence tooling.
- Stability: Active typed application contract; serialized summary mappings remain compatible.
- Format: `Phase3MatrixResult` exposes `kind`, raw `summary`, `passed`, artifact and summary paths,
  counts, errors, and warnings. Runner summary mappings and serialized summary fields remain
  unchanged.
- Validation: Normalization reads existing summary keys; signed rows are serialized through
  `Phase3SignedAcceptanceScenarioResult.as_mapping()`.
- Error behavior: Runner exceptions remain scenario error rows where previously mapped; lifecycle
  cleanup runs in `finally`; artifact writers return the authoritative summary path.
- Source files: `src/foliaseal/application/phase3_evidence_service.py`,
  `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py`,
  `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py`,
  `src/foliaseal/presentation/qt/phase3_signed_acceptance_lifecycle.py`,
  `src/foliaseal/presentation/qt/phase3_matrix_artifacts.py`.

## 7. Control flow

### CLI startup

1. Console script `foliaseal` calls `foliaseal.__main__:main`.
2. `_build_parser()` builds subcommands and argument contracts.
3. `main()` dispatches to evidence generation, Qt harnesses, preview/signed matrices, validation, or prints the skeleton-ready message when no command is provided.

### Reusable Phase 3 evidence session

1. A caller constructs or receives `Phase3EvidenceService`, then obtains `Phase3EvidenceOrchestrator` (or uses the CLI composition helper) as the application boundary.
2. The orchestrator/session builds tagged `Phase3OperationRequest` values; `Phase3EvidenceOrchestrator.run()` validates each payload and delegates to the injected service port.
3. Preview/headless, signed/Qt, and interactive adapters execute behind the service with their existing lifecycle, artifact, and summary contracts.
4. `Phase3EvidenceSession.validate()` delegates a read-only `Phase3ValidationRequest`; the orchestrator converts it to the service validation DTO and the evidence-contract evaluator runs unchanged.
5. Matrix operations and interactive capture remain separate Qt-side adapters, while serialized outputs and CLI behavior remain stable; the canonical orchestrator owns the application-facing command contract.

### Headless signing

1. Caller builds a domain `SigningRequest`.
2. `SignPdfUseCase.execute()` rejects input/output path conflicts.
3. Public request is normalized to `SigningBackendRequest`.
4. PDF compatibility and certification policy are inspected.
5. Certificate material is validated.
6. `PyHankoPdfSigner.sign()` calls `prepare_phase3_signing_plan()` when a prepared plan was not supplied; the preparation step resolves visible semantics/layout once (or marks an invisible plan), and exposes fit issues as `SigningDraftValidationIssue` values.
7. `PyHankoPdfSigner.sign()` materializes the prepared plan. Visible requests build a stamp; invisible requests create a hidden `SigFieldSpec` with no stamp style. TSA setup, incremental writing, and adapter-owned verification remain unchanged.
8. Timestamp-required and PDF-version policies are checked.
9. Output bytes are written via temp file and atomic replace.
10. Verifier checks signed output and timestamp trust.
11. `SigningResult` reports success or a stable failure code. `Phase3SigningExecutor.execute(request)` remains the compatibility facade throughout.

### Qt application frame and file opening

1. `build_qt_app_frame_host()` constructs a `QtAppFrameAdapter` and returns the real `FoliaSealAppFrame` host.
2. `FoliaSealAppFrame` creates a `QMainWindow` and installs File/Open, Settings/Application settings, Settings/Create certificate, Settings/Import certificate, and Settings/Manage certificate configurations menu actions.
3. File/Open calls `QFileDialog.getOpenFileName()` with `AppSettings.default_open_directory`.
4. The selected PDF is handed to `app_frame_workspace_open.py`, which loads it through `QPdfDocument` to determine page count.
5. The same workspace-open boundary creates `ViewerWorkflow`, `ViewerSession`, and `SigningDraftWorkflow`; the draft output path defaults to `AppSettings.default_output_directory / "<input-stem>-signed.pdf"`.
6. The workspace-open boundary builds the existing Qt signing shell through the shell-owned workspace port/factory boundary and returns the live shell port plus compatibility state. `SigningWorkspaceLifecycle.replace()` is the frame's transition boundary: it composes the candidate, mounts it through `QtWorkspaceMount`, then disposes the old widget and publishes the new active record. A mount failure disposes only the candidate and leaves the prior workspace active.
   Calling `FoliaSealAppFrame.close_workspace()` delegates idempotent active-widget cleanup to the same lifecycle boundary, clears the frame's current workspace/production port, and mounts the placeholder view.
7. Settings/Application settings opens an editable dialog for default open and output directories, saves through `AppSettingsStore`, and refreshes the frame/current shell settings through the live workspace port.
8. Settings certificate actions route through `app_frame_certificate_management.py`, which constructs and executes the dialogs, delegates create, import, rename, delete, and export operations to `CertificateLifecycleService`, and then refreshes the loaded signing shell certificate selector through the live workspace port when the lifecycle result reports a catalog change.
9. Open and certificate operation failures are reported through the frame warning/error callback path.

### Qt signing workflow

1. `build_qt_signing_shell()` constructs a `SigningShellAdapter`.
2. The shell creates a viewer workflow and signing draft workflow.
3. The workspace resolves the current document review summary from `ViewerWorkflow.document_path` through the injected application review helper; optional `AppSettings` or `AppSettingsStore` input is loaded by the workspace, otherwise home-directory defaults are used.
4. The workspace shows the document viewer on the left with a compact page-navigation toolbar above it, plus read-only signing-flow and document-review cards in the right sidebar derived from current draft/readiness/result state and the currently open PDF. `signing_workspace_composition.py` owns the toolbar widgets and its persistent interaction-mode label; it changes that label from placement dragging to text-selection instructions as the review bridge publishes `DocumentTextWorkspaceState`. The toolbar also owns visible previous/next page controls, editable current-page entry, and total-pages readout, while the review card owns only the summary, compact per-signature list, and selector-driven per-signature detail. Reopening the last successful signed output now lives exclusively in the primary sign panel.
5. `signing_workspace_properties_panel.py` now owns `SignaturePropertiesPanel` as a dedicated shell-local module. The panel delegates the common setup workflow to `SigningSetupSession`, which composes `DefaultSignaturePropertiesCoordinator` plus a tiny Qt passphrase-prompt adapter. The panel still maps Qt controls to and from the visible-signature draft, still owns overwrite/delete confirmation dialogs, still owns preview rendering, and now owns the compact `Manual refinement` entrypoint that opens a separate current-PDF refinement dialog for appearance and placement edits, but it no longer lives inside `signing_shell.py` and no longer owns the main setup orchestration for load, visible-signature apply, nonblank preset selection, preset save/delete mutation, programmatic appearance dirty clearing, certificate selection, or catalog refresh. Selection calls now return `SigningSetupSelectionOutcome`; the panel applies `outcome.state` in both success and cancel paths and uses `outcome.applied` to decide whether to notify change. The session now owns manual certificate-password retry, explicit applied/canceled selection outcomes, session-local passphrase caching, and preset mutation delegation instead of the panel, while the coordinator owns the underlying appearance-only mutation and preset-clearing rules.
6. `build_signing_workspace_composition()` constructs the workspace session graph and bridge graph for one shell instance, installs the viewer/sidebar row layout, builds the runtime, surfaces, and orchestrator, and then `SigningWorkspaceOrchestrator.bootstrap()` runs the initial bootstrap ordering for widget exports, viewer refresh, review-state load, and signing-action state load.
7. `SigningWorkspaceWidget` delegates recurring viewer/panel interaction sequencing to `WorkspaceInteractionSession`, which composes `DocumentReviewWorkspaceSession` plus `ViewerInteractionSession`. That session returns a `WorkspaceInteractionPlan` whose ordered effects cover review-transition application, viewer refresh, placement-context application, signature-rectangle application, overlay sync, preview refresh, signing-action reload, signing-action invalidation, and error emission, and `SigningWorkspaceRuntime` now delegates that ordered plan through `SigningWorkspaceOrchestrator.apply(...)`, which in turn uses `signing_workspace_interaction_bridge.py` to execute the concrete Qt effects without re-deriving the choreography from flag fields.
8. The panel derives `SigningDraftPreview`, asks `QtCanonicalPreviewLifecycle` for canonical render state when a snapshot is available, and hands that state plus the preview draft to `QtSignaturePreviewLayout` to plan and apply card sizing, widget ordering, and visibility.
9. When the user chooses an output path, `SigningWorkspaceWidget.choose_output_pdf_path()` delegates to `SigningWorkspaceActionBridge.choose_output_pdf_path()`, which opens the file dialog, confirms overwrite if needed, and forwards the resulting path through `SigningActionBoundary.accept_output_path()` into `SigningActionCoordinator.accept_output_path()` before applying the returned signing-state snapshot to the live widgets.
10. When the user signs, `SigningWorkspaceWidget.submit_sign_request()` delegates to `SigningWorkspaceActionBridge.submit_sign_request()`, which applies pending property changes, checks readiness, builds the `SigningRequest`, and routes success or failure callbacks through `SigningActionBoundary.submit()` before applying the updated state.
11. When certificates are refreshed, `SigningWorkspaceWidget.refresh_certificate_configurations()` delegates to `SigningWorkspaceActionBridge.refresh_certificate_configurations()`, which reloads the signing state, reapplies the current snapshot to the sidebar, and preserves the bridge-owned state-apply/reset behavior around the refresh.
12. If no executor is injected, the boundary returns the request and a neutral state snapshot; the bridge applies that returned state and stops.
13. If an executor is injected, it runs the request and returns a `SigningResult`; the coordinator stores the result, the boundary returns the updated state snapshot, the bridge applies that state to the sidebar renderer, and the shell emits either `sign_success` or a plain error depending on the transition metadata.
14. When the user opens the signed output, `SigningWorkspaceWidget.open_signed_output()` delegates to `SigningWorkspaceActionBridge.open_signed_output()`, which asks the boundary for the saved output path, forwards it to the shell callback when present, and leaves the guarded-disabled path as a no-op.
15. On success, the coordinator records the signed output path so the shell can enable `Open signed PDF`; on failure, it clears the reopen target, keeps the error text visible, and harnesses can capture structured evidence.

### Qt output path selection

1. The signing shell receives settings from an explicit `AppSettings`, an `AppSettingsStore`, or `AppSettings.default()`.
2. App-wide editing is handled by the app-frame `Settings > Application settings` dialog, which persists changes through `AppSettingsStore.save_settings()` and refreshes any loaded shell.
3. `choose_output_pdf_path()` opens `QFileDialog.getSaveFileName()` with the initial path from `suggest_signed_output_path()`, rooted at `AppSettings.default_output_directory`.
4. If the selected path already exists, the shell asks for explicit overwrite confirmation before mutating the draft path, so platforms without native save-dialog warnings still require user consent.
5. When the user selects a non-existing file or confirms overwriting an existing file, `SigningWorkspaceActionBridge.accept_output_path()` forwards the chosen path through `SigningActionBoundary.accept_output_path()`, which forwards it to `SigningActionCoordinator.accept_output_path()`, writes `SigningDraftWorkflow.output_pdf_path`, clears any previous signing result, and updates the flow-summary/result state.
6. Empty dialog results or declined overwrite confirmation leave the current output path unchanged.

### Viewer selection to PDF rectangle

1. `ViewerWorkflow.render_current_page()` renders with the backend and stores page geometry.
2. Qt widget receives mouse selection in view pixels.
3. `ViewerWorkflow.selection_to_pdf_rect()` converts `ViewRect` through `view_rect_to_pdf_rect()`.
4. The PDF rectangle is rejected if no snapshot exists, coordinate mapping is unavailable, or the result is outside the page box.
5. Signing workflow stores the rectangle as `SignatureRect`.

### Signature preset save/load

1. Qt shell loads `SignaturePresetCatalogStore.default()`.
2. `load_catalog()` returns empty catalog if no file exists.
3. Saving creates or replaces a resolved preset, which stores separate `AppearanceProfile`, optional `PlacementProfile`, and reference-only `SignaturePreset` entries in `SignaturePresetCatalog`.
4. Store writes indented sorted JSON to a `.tmp` file and replaces `profiles.json`.
5. Delete rewrites the catalog without the named preset.
6. The coordinator calls canonical draft methods `capture_current_signature_setup()` and `apply_signature_preset_values()` on the live apply path, with `apply_resolved_signature_preset()` retained as a compatibility wrapper, and on the live save path now persists the already-updated catalog through `save_catalog(self.preset_catalog)` while `save_preset()` remains a compatibility helper alongside preset-oriented catalog/store methods such as `preset_named()`, `upsert_preset()`, and `delete_preset()`.

### Certificate configuration selection

1. `build_qt_signing_shell()` may receive a `CertificateCatalogStore`, `CertificateCatalog`, and `CertificateSecretProvider`.
2. The coordinator loads certificate configuration display names into a compact selector state.
3. The user selects a saved certificate configuration and the panel delegates that action to `SigningSetupSession.select_certificate_configuration(...)`.
4. `CertificateSigningMaterialResolver` verifies the referenced managed certificate record and app-managed PKCS#12 file, then returns runtime `SigningMaterial` either from a saved secret or a provided passphrase.
5. If the resolver reports that a manual password must be entered, the setup session prompts through its injected `CertificatePassphrasePrompter`, retries once with the entered passphrase, and keeps that passphrase in a session-local cache keyed by certificate configuration so the same UI session does not re-prompt unnecessarily.
6. `SigningSetupSession.select_certificate_configuration()` returns `SigningSetupSelectionOutcome`, so the panel can tell whether the selection applied or only refreshed the current setup state after a cancel/no-op.
7. `SigningDraftWorkflow.apply_certificate_configuration()` records the selected configuration id, updates runtime certificate path/passphrase/alias, clears certificate-preview cache state, and future preview/request calls use the resolved material.
8. Resolver failures, such as a missing managed certificate file, blank password retry, or unavailable saved password, are reported through the Qt shell error path instead of escaping as uncaught exceptions; canceled prompts return an outcome with `applied = false` and the current rendered state.

### Signature-properties reconciliation

1. `signing_workspace_properties_panel.py` creates `SignaturePropertiesPanel` as a dedicated module and that panel creates `DefaultSignaturePropertiesCoordinator` with the current `SigningDraftWorkflow` plus optional catalog/store and secret-provider dependencies.
2. `SignaturePropertiesPanel` also creates `SigningSetupSession`, injecting the coordinator and a Qt `QInputDialog` adapter for manual certificate-password prompts.
3. `load()` seeds the combo-box selections, validation text, and ready-to-sign state from workflow/catalog state through the setup session.
4. User actions on the certificate and preset controls become explicit setup-session verb calls, while the compact manual-refinement affordance opens a separate dialog that reuses `QtVisibleSignatureSetupForm` for current-PDF appearance and placement edits; the panel passes any current control issue so UI validation text can include placement/appearance errors.
5. The session delegates signing-draft rule enforcement to the coordinator, asks `certificate_configuration_name_for_preset()` for preset password prompt labels, routes programmatic appearance-only updates through `set_signature_appearance()`, owns manual password retry/cancel/cache policy plus preset save/delete orchestration, and returns `SigningSetupSelectionOutcome` for certificate/preset selection while returning plain `SignaturePropertiesViewState` for the other setup verbs.
6. The panel renders the returned state into controls and labels, then refreshes the existing preview card and canonical preview snapshot machinery.
7. `ClearSelectedSignaturePreset` is used when appearance or placement edits dirty a saved preset selection without mutating the underlying workflow state.

### Workspace interaction sequencing

1. `build_signing_workspace_composition()` creates `DocumentReviewWorkspaceSession`, `ViewerInteractionSession`, and `WorkspaceInteractionSession`, then installs those collaborators onto `SigningWorkspaceWidget`.
2. Viewer drags go first to `WorkspaceInteractionSession.select_in_viewer(...)`, which lets the review/text workspace consume selection-mode drags before trying signing placement.
3. If a drag becomes a signing placement, the workspace interaction session returns a `WorkspaceInteractionPlan` carrying ordered effects for the `SignatureRect`, optional placement context, overlay sync, preview refresh, and signing-action invalidation/reload.
4. `signing_workspace_interaction_bridge.py` executes that ordered plan against concrete widgets and the signing draft through a non-notifying `SignaturePropertiesPanel.set_signature_rect(...)` path, while the shell delegates to the bridge so viewer-selection placement does not loop back through the generic panel-change callback.
5. Page changes, document-text jump navigation, panel-change follow-up, and viewer-refresh follow-up all go through explicit workspace-interaction session verbs that return the same ordered-effect shape. The visible viewer-toolbar page controls are a thin shell affordance over the existing viewer navigation path, while composition-local callbacks keep the toolbar page-number entry and total-pages readout synchronized with both button-driven and hidden keyboard-driven navigation, and render the persistent placement-versus-text-selection cue from review-state changes.

### Phase 3 evidence validation

1. CLI dispatch calls the application evidence service; legacy matrix verbs return raw dictionaries,
   while typed callers use `preview_matrix_result()` or `signed_acceptance_matrix_result()`.
2. The signed runner loads the manifest, starts the lifecycle adapter, attaches the shell, primes the
   workspace, and processes events before iterating scenarios.
3. Each scenario returns a typed result (or a mapped error row), is converted to the existing JSON
   mapping, and is followed by lifecycle event processing.
4. Acceptance expectations and counters are computed without renaming summary fields. The artifact
   port writes `summary.json`; its returned path is authoritative and is reported by the CLI.
5. Lifecycle close runs in `finally`. Harness or matrix validation then reads structured JSON and
   `evaluate_phase3_evidence_contract()` classifies errors, warnings, acceptance tier, and gate verdict.

## 8. Data flow and persistence

| Data | Source | Transformations | Storage | Format/schema | Notes |
|---|---|---|---|---|---|
| Input PDF | User CLI/GUI path | app-frame File/Open dialog -> page-count load -> viewer workflow; rendered for viewer; signed by pyHanko; inspected for certification/version | Original file remains at user path | PDF | Signing output must not target same resolved path. |
| Signed PDF output | pyHanko backend bytes | atomic temp-file replace | User-provided output path | PDF | `SigningResult` reports PDF version, signature subfilter, timestamp metadata. |
| PKCS#12 certificate | User path/passphrase | validated/loaded by pyHanko/cryptography | Not persisted by app | PKCS#12 | Passphrase can appear in CLI history for harness commands; README warns about this. |
| Managed certificate configuration | Certificate creation service, certificate import service, app-frame certificate management dialog, tests, or Qt shell selection | created self-signed PKCS#12 or imported PKCS#12 -> managed certificate record + certificate configuration -> optional `secret-tool` password save -> optional app-frame rename/notes/delete of configuration record -> optional app-frame export of managed certificate file -> optional app-frame delete of unreferenced managed certificate/file -> resolver -> runtime signing material -> signing draft | XDG data dir under `FoliaSeal/Certificates/certificates.json`; PKCS#12 files under `FoliaSeal/Certificates/Managed/`; saved passwords in Linux Secret Service via `secret-tool` | `CertificateCatalog` JSON plus PKCS#12 files plus external secret references | JSON stores secret references only; no plain certificate passwords. Qt app frame can create basic self-signed PKCS#12 files, import existing PKCS#12 files, optionally save passwords securely when `secret-tool` is available, rename/edit notes/delete configuration records, export managed certificate files, delete unreferenced managed certificate files, and Qt shell can select existing configurations. |
| App settings | Settings store callers, Qt app frame settings dialog, output file dialog | user preferences -> settings schema -> JSON -> app-frame and shell defaults | XDG config dir under `FoliaSeal/settings.json` | `AppSettings` JSON | Missing/blank settings load home-directory defaults; app-frame Settings dialog owns default-directory editing and loaded signing shells consume refreshed values. |
| Reusable signature presets | Qt shell refinement dialog or `Settings > Manage signing profiles...` -> `SignatureProfileLibrary` / `DefaultSignaturePropertiesCoordinator` | display-name selection -> catalog lookup -> domain appearance/placement plus optional certificate configuration reference -> split config schema -> JSON -> profile-library close -> mounted-shell port refresh | XDG data dir under historical `FoliaSeal/Signature Profiles/profiles.json` path | `SignaturePresetCatalog` JSON with appearance, placement, and preset lists | Missing/blank catalog becomes empty; obsolete profile-named preset methods have been removed; partial presets without certificate references preserve the active certificate selection, and the coordinator reconciles stale display-name selections on refresh. The app frame invokes `SigningWorkspacePort.refresh_signature_profiles()` after profile-library closure, so selectors reflect library mutations without reaching into the concrete widget. |
| Trust profile/timestamp policy | Config schema callers | JSON dicts <-> dataclasses -> runtime trust policy | Needs review | JSON schema in `infra/config/schemas.py` | Storage location outside profile catalog is not yet clearly documented in code. |
| Viewer render buffers | Render backend | PDF page -> RGBA bytes | Memory; optional render cache | `RenderPageResult` | Cache is in-memory LRU keyed by path/page/zoom. |
| Preview artifacts | Qt harness/matrix | widget/canonical preview capture, overlays, diagnostics | `artifacts/` run directories | PNG/JSON/markdown | Generated run outputs and local QA fixture workspaces are ignored. |
| Bundled fonts | Package resources | resolved by font registry and backend/preview | `src/foliaseal/resources/fonts/` in package data | TTF files | User-facing families map to bundled font faces. |

## 9. Dependency rules

| From | May depend on | Must not depend on | Notes |
|---|---|---|---|
| `domain` | Python stdlib and typing/dataclasses/enums. | `application`, `infra`, `presentation`, Qt, pyHanko. | Confirmed by current imports. |
| `application` | `domain`, small infra protocols/adapters where currently wired, Pillow for layout image probing. | Qt presentation widgets. | Some application modules import infra DTOs or backend concrete helpers; see debt. `signature_properties_coordinator.py` is the application-layer boundary for signing-properties reconciliation and may depend on config stores plus the certificate-material resolver. |
| `infra` | `domain`, application protocol DTOs where implementing adapters, external libraries such as pyHanko/PySide6/cryptography/Pillow, and the late-resolved `pdftoppm` runtime executable for interactive rasterisation. | Qt presentation widgets. | Rendering keeps QtPdf geometry separate from Poppler page pixels; diagnostics must preserve this distinction. |
| `presentation/qt` | `domain`, `application`, `infra` concrete adapters, dynamic PySide6 bindings. | Domain mutation rules duplicated outside workflows. | Qt shell should orchestrate, not reinterpret signing semantics; `signing_shell.py` should delegate signature-properties reconciliation to the application coordinator, the signing-action sidebar should own `SigningActionState` rendering, the preview card should delegate layout/lifecycle handoff to the dedicated Qt preview helpers, and Phase 3 reporting should stay behind the dedicated `phase3_harness_reporting.py` seam. |
| `tests` | All layers plus fakes/fixtures. | Production code depending on tests. | Tests intentionally inspect private helpers in some transitional layout areas. |
| `docs` / `artifacts` | N/A. | Runtime imports from production code. | Artifacts are evidence, not app dependencies. |

## 10. Extension points

| Extension point | Location | Intended use | Constraints |
|---|---|---|---|
| Signing backend ports | `application/sign_pdf_use_case.py` | Swap PDF inspector, certificate loader, signer, verifier, certification inspector in tests or future adapters. | Must return domain `SigningOutput` / `VerificationSummary` and preserve failure-code mapping. |
| Render backend protocol | `infra/render/base.py` | Replace a renderer or compose a geometry source with a pixel source. | Must provide page geometry and RGBA render bytes; a replacement for the live adapter must preserve QtPdf-compatible placement geometry or explicitly revise the coordinate contract. |
| Visible-signature semantics ports | `application/visible_signature_semantics.py` | Inject certificate field reading, signing clock, and fit validation. | Must keep preview and final-signing text/metadata behavior aligned. |
| Visible-signature layout ports | `application/visible_signature_layout.py` | Inject text measurement, image probing, and horizontal ink measurement. | Must preserve `SignatureLayoutPlan` semantics and fit-issue reporting. |
| Certificate secret provider | `application/signing_material_resolver.py`, `infra/secret_storage.py` | Resolve saved certificate passwords from the Linux Secret Service through `secret-tool`, with test fakes behind the same protocol. | Must not store plain passwords in ordinary config JSON; resolver must allow explicit passphrase fallback. |
| App settings store | `infra/config/app_settings_storage.py` | Persist and load global defaults such as open/output directories. | UI must still use explicit file dialogs; settings provide defaults only. |
| Timestamp factory | `phase3_signing_backend.py`, `infra/tsa/pyhanko_adapter.py` | Use dummy TSA in tests/matrices or HTTP TSA in real signing. | Production URLs must validate as HTTP(S). |
| Profile storage root | `SignaturePresetCatalogStore.default(app_name=...)` | Test/custom app-name storage location. | Default follows XDG data home. |
| Qt binding loaders | `presentation/qt/*` | Test with fake widgets or run with real PySide6. | Dynamic imports should fail with explicit unavailable errors/diagnostics. |
| PyInstaller support | `src/foliaseal/build/pyinstaller_support.py` | Collect runtime assets for bundles, including bundled visible-signature fonts. | The spec uses this helper and tests cover the bundled font asset list. |

## 11. Testing architecture

Tests live under `tests/unit/` with support builders in `tests/support/`. The suite is broad and includes unit tests plus focused integration-style tests that exercise pyHanko signing, Qt-shell behavior through fakes, and harness artifact generation.

| Test area | Location | What it protects | Expected when changing |
|---|---|---|---|
| Domain/config validation | `test_signature_appearance_models.py`, `test_config_schemas.py`, `test_signature_preset_storage.py`, `test_certificate_storage.py`, `test_signing_material_resolver.py` | Dataclass invariants, persisted JSON shape, and certificate-configuration resolution. | Add/update schema tests for persisted fields. |
| Signing use case | `test_sign_pdf_use_case.py` | Failure-code mapping, timestamp policy, certification restriction, atomic writes. | Preserve stable failure codes and output metadata. |
| pyHanko signing backend | `test_phase3_signing_backend.py` | Real signing, timestamping, visible signature layout, semantics adapter behavior, private layout helper behavior. | Run focused backend tests for signing/layout changes. |
| Visible semantics boundary | `test_visible_signature_semantics.py` | Visible field resolution, certificate fallback, signing-time text, escaped stamp text, metadata, and fit-validator propagation. | Add boundary tests for text/metadata behavior before changing workflow, preview, or backend signing. |
| Visible layout boundary | `test_visible_signature_layout.py` | `SignatureLayoutPlan` and adapter parity. | Add boundary tests before relying on private helper changes. |
| Preview rendering | `test_signing_preview_renderer.py` | Textual/canonical preview snapshots and preview/request parity. | Run with backend/layout tests for visible-signature changes. |
| Preview lifecycle | `test_signature_preview_lifecycle.py` | Canonical preview lifecycle boundary: render params, backend reuse, snapshot replacement/dispose cleanup, and fallback behavior without full shell widgets. | Add boundary tests here before changing the Qt preview adapter or its cleanup semantics. |
| Preview layout | `test_signature_preview_layout.py` | Preview geometry/layout boundary: card sizing, ancestor-width selection, padding, text/stamp band fitting, widget ordering, and canonical-render handoff without the full shell. | Add boundary tests here before changing preview-card sizing or widget-order rules. |
| Signature-properties coordinator | `test_signature_properties_coordinator.py` | Certificate/preset reconciliation, catalog refresh, validation text, and readiness state without Qt. | Add or update tests here before changing panel or store behavior. |
| Qt shell/viewer | `test_qt_signing_shell.py`, `test_qt_viewer_widget.py`, `test_qt_render_backend.py` | Widget behavior through fakes, selection geometry, render diagnostics, and thin integration of the preview lifecycle and preview layout boundaries into the shell card. | Use fakes; avoid requiring a live GUI unless intentionally running harnesses. |
| Poppler interactive rendering | `test_poppler_render_backend.py`, `test_qt_app_frame.py` | Poppler command/diagnostic failure behavior, opaque RGBA conversion, Qt-compatible geometry delegation, and the app-frame default renderer. | Run these focused tests plus a real signed-PDF reopen audit when changing the live render path. |
| Viewer geometry/workflow | `test_coordinate_transform.py`, `test_viewer_session.py`, `test_viewer_workflow.py` | Coordinate math and page/zoom workflow. | Add cases for rotations/page boxes when geometry changes. |
| Evidence/harnesses | `test_phase2_harness.py`, `test_phase3_harness.py`, `test_phase3_harness_reporting.py`, `test_phase2_evidence.py`, `test_preview_stress_fixtures.py` | Capture JSON, reporting-boundary behavior, checklist/evidence contract behavior, matrix diagnostics. | Keep generated outputs controlled and `.gitignore` aligned. |
| Packaging/build helpers | `test_pyinstaller_support.py`, `test_phase3_evidence_service.py`, CLI tests | Hidden imports, service-boundary behavior, and command dispatch. | Update when CLI commands, packaging runtime imports, or evidence-service seams change. |

Default local validation from README:

    ruff check .
    python -m pytest -q

## 12. Known architectural debt

| Issue | Impact | Current workaround | Preferred direction |
|---|---|---|---|
| The Phase 3 harness still spans several broad presentation helpers after the command-pipeline refactor. | Understanding or changing a full harness run still requires bouncing between the Qt adapter, session runner, matrix runners, scenario executors, and the live testing seam. | `Phase3MatrixOperations` keeps lazy matrix construction separate from the explicit interactive capture factory; workspace/session/matrix modules own narrower runtime boundaries and operation-local dependencies. | Continue deepening the harness in narrow slices. |
| Preview/headless, signed/Qt, and interactive Phase 3 adapters retain separate lifecycles and artifact semantics. | A single runner would couple incompatible Qt startup/cleanup, scenario, and summary behavior. | `Phase3EvidenceOrchestrator` unifies only tagged dispatch and validation; the service injects the existing adapters unchanged. | Revisit only when a concrete shared lifecycle/artifact contract emerges; do not merge contexts speculatively. |
| The Phase 3 command pipeline still has separate service execution and orchestrator dispatch modules. | A caller must understand the typed command boundary versus injected runner effects when extending evidence operations. | `phase3_evidence_core.py` and `phase3_evidence_ports.py` keep result truth and effects explicit while the orchestrator remains thin. | Add new operations through typed command/result and port changes together; do not reintroduce a generic gateway. |
| `phase3_signing_backend.py` still mixes concrete pyHanko adapter code with behavior-bearing fit policy. | The authoritative rendered-ink fallback and fit-gate acceptance rules remain close to signing orchestration. | `VisibleSignaturePreparation` captures the fit decision once; backend helpers remain implementation policy and are consumed only by preparation/evidence paths. | Extract fit-policy implementation only when a second concrete consumer justifies a new boundary; do not add compatibility facades. |
| Historical planner/boundary facades were removed in the prepare-once migration. | Stale callers would otherwise silently re-plan or fork layout policy. | Production consumers use `VisibleSignatureLayoutPort.prepare()` and memoized `VisibleSignaturePreparation` materializers. | Preserve the single boundary and reject optional-plan APIs that can trigger recomputation. |
| Preview and final signing still resolve the displayed signing time from separate system-clock reads. | A clock rollover between preview and submission can change the timestamp text while layout and fit remain identical. | `PreparedSigningPlan` freezes the final signing operation's semantics/layout; the public `SigningRequest` remains unchanged. | Add an explicit signing-time snapshot handoff from the draft preview into the prepared request when strict timestamp-text WYSIWYG becomes a product requirement. |
| `signing_shell.py` still concentrates top-level workspace lifecycle edges even after the runtime/controller extraction. | Changes still risk broader review scope even after constructor-time composition, the signature-properties panel, the narrow production shell surface, the thinner compatibility/testing seam, the runtime/controller, action/review/interaction bridges, canonical preview lifecycle, preview layout, production-sidebar composition, and sidebar render ownership moved behind dedicated boundaries. | Tests use fakes plus dedicated coordinator/preview-lifecycle/preview-layout/sidebar/panel/shell-surface/compatibility-surface/runtime boundary coverage. | Continue deepening around the remaining top-level workspace lifecycle surface and app-frame/shell seams rather than re-opening the composition, runtime/controller, preview, panel, or the stabilized `testing_adapter` seam. |
| Application layer imports some infra DTOs and concrete backend helpers. | Layer boundary is not perfectly clean. | Semantics decisions now live behind `VisibleSignatureSemanticsService`; remaining imports are primarily layout/backend compatibility, profile DTOs, and certificate config DTOs. | Move shared DTOs/interfaces upward or add adapter methods when it reduces coupling. |
| Certificate management is intentionally first-pass. | Users can create basic self-signed PKCS#12 files in-app, import existing PKCS#12 files, optionally save passwords through `secret-tool`, rename/edit notes/delete resulting certificate configurations, export/back up managed certificate files, delete unreferenced managed certificate files, and select configurations. The creation UI does not yet expose advanced subject, validity, algorithm, or CA/trust-chain controls. | Tests and lower-level stores can create catalogs; `CertificateLifecycleService` owns first-pass creation/import/configuration/export/managed-certificate deletion and saved-password cleanup, `app_frame_certificate_management.py` owns dialog construction/execution plus lifecycle delegation, `app_frame.py` owns Settings-action routing and compatibility exposure, and the shell consumes configurations through the resolver. | Add richer certificate-authoring options only when product requirements justify them, and consider cross-platform credential-store adapters if FoliaSeal expands beyond Linux Secret Service. |
| Historical profile terminology remains in storage path/module names. | `profile_storage.py` and `Signature Profiles/profiles.json` may still look broader than the current `SignaturePresetCatalog` responsibility. | Public methods and shell behavior use preset-oriented names; the historical path is documented. | Consider a storage-path/module rename only if it can be done without introducing unnecessary migration code. |
| `SignatureLayoutPlan.backend_reservation` | Removed from the public layout result. | Public layout boundary is now neutral; backend compatibility lives in evidence names. | Preserve pyHanko parity during migration. | Backend-facing evidence still uses `backend_reservation_snapshot` and `backend_reservation_error`. |
| PySide6 is dynamically imported and now listed only in the optional `gui` and `dev` extras, not the base runtime dependencies. | A fresh base install may still run CLI helpers but fail GUI/harness commands until the extra is installed. | Runtime diagnostics report unavailable Qt bindings; `foliaseal gui` is the supported launch path once the extra is present. | Keep the GUI dependency optional unless packaging work requires the desktop stack in every install. |
| Checked-in artifact docs include historical status and roadmap notes. | README warns some narrative notes may be stale. | Current gate status should come from latest checked-in summaries/artifacts. | Keep live status in generated summaries or curated release notes, not scattered narratives. |

## 13. Open questions

| Question | Why it matters | Options | Recommendation |
|---|---|---|---|
| Should `application` be strictly independent from `infra`? | Current imports include infra config DTOs and backend helper dependencies. | A: enforce strict dependency direction; B: allow pragmatic exceptions. | Prefer A for new work, retire existing exceptions gradually. |
| What is the public stability level of CLI harness commands? | They are documented and tested, but some are engineering acceptance tools. | A: stable developer contract; B: internal tool contract. | Treat command names/required args as stable unless a migration note is added. |
| Should PySide6 remain an optional package extra instead of a base dependency? | The real GUI now has a stable launch command, but headless CLI and evidence workflows still do not require Qt. | A: keep `gui` extra; B: move PySide6 into base dependencies. | Keep the `gui` extra for now and revisit only when full desktop packaging is defined. |
| Where should trust/timestamp policy config be persisted outside tests? | Schemas exist, but signature profile and certificate stores are the only obvious stores. | A: add a store; B: keep CLI/request-only for now. | Needs maintainer decision before documenting as settled. |
| How much of `phase3_harness.py` should become reusable analysis library code? | The file owns many PDF/render/diagnostic helpers. | A: keep as harness-local; B: extract evidence analyzers. | Pure signed-PDF evidence is now extracted into `phase3_pdf_signature_snapshotter.py`; preview/widget/render helpers remain harness-local until reuse pressure justifies another slice. |

## 14. Change log

| Date | Change | Reason |
|---|---|---|
| 2026-08-01 | Added the Phase 3 pure signed-PDF evidence snapshotter boundary. | Reconciled ownership of signature counting, metadata, verification/certification/timestamp projections, visible-appearance parsing, and JSON-safe PDF serialization; signed-output and capture assemblers now consume bound snapshotter methods, while recursive AP/timestamp-semantic debt remains explicitly deferred. |
| 2026-07-31 | Added the visible-signature planner/IR hybrid boundary (retired by the 2026-08-01 migration). | Historical record of the superseded `VisibleSignaturePlanner`/`VisibleSignaturePlan` seam. |
| 2026-08-01 | Replaced the planner/IR compatibility seam with prepare-once layout composition. | Documented `VisibleSignatureLayoutPort`, immutable `VisibleSignaturePreparation`, captured fit-gate/evidence, explicit preview stamp suppression, and retained backend fit helpers as behavior-bearing implementation policy. |
| 2026-07-31 | Added the prepared signing plan and explicit invisible headless signing path. | Reconciled the application/backend boundary: typed fit issues remain application-owned, PyHanko/Pillow materialization stays adapter-owned, and the existing `execute(request)` facade remains compatible. |
| 2026-07-31 | Reconciled typed Phase 3 evidence truth and authoritative aggregate paths. | `Phase3EvidenceService` now reports signed scenario-error rows as typed failures and preserves runner-provided `summary_json_path` values; validation completed with 23 focused tests and 1,011 full-suite tests. |
| 2026-08-01 | Added the typed Phase 3 evidence command pipeline. | Qt-free result truth and effect ports now sit beneath the canonical orchestrator/session; the obsolete gateway and raw `run_*` aliases were removed, CLI routing crosses the typed boundary, and preview/headless, signed/Qt, and interactive adapters retain their existing lifecycle and artifact contracts. |
| 2026-08-01 | Reconciled the headless-first Phase 3 composition slice. | Historical record: documented lazy `Phase3Composition` matrix/capture wiring, operation-local dependency injection, preserved CLI/JSON/artifact contracts, and removal of redundant matrix gateways and private forwarding wrappers before the later composition-facade removal. |
| 2026-08-01 | Replaced the redundant Phase 3 presentation composition facade. | Added dependency-light `Phase3MatrixOperations`, separated lazy interactive capture wiring, made Qt package exports lazy, removed obsolete composition/lazy/protocol seams, and preserved application/CLI/JSON/artifact contracts. |
| 2026-07-19 | Documented profile-library selector refresh through the production workspace port. | `Settings > Manage signing profiles...` closes through the app frame, which calls the newly exported `SigningWorkspacePort.refresh_signature_profiles()`; the port delegates to the action bridge/panel refresh instead of the frame reaching into the concrete close-aware widget. |
| 2026-07-19 | Added the Poppler-backed live viewer raster boundary. | Reconciled the reopened signed-PDF fidelity repair: `FoliaSealAppFrame` now defaults to `PopplerPdfRenderBackend`, which late-resolves `pdftoppm` for interactive RGBA pixels while deliberately retaining `QtPdfRenderBackend` page geometry; canonical preview and Phase 2/Phase 3 rendering remain QtPdf-scoped. |
| 2026-07-05 | Added the signing-workspace factory bundle and shell-local orchestrator. | Reconciled the architecture doc so `QtSigningWorkspaceFactory` now returns `SigningWorkspaceBundle`, `signing_workspace_orchestrator.py` owns bootstrap and ordered interaction-plan delegation, `signing_workspace_runtime.py` keeps the live workspace verbs, and `signing_workspace_compatibility_surface.py` stays limited to widget exports plus `testing_adapter`. |
| 2026-06-22 | Moved live-shell signature-rect priming choreography behind `signing_workspace_compatibility_surface.py`. | Reconciled the architecture doc so `phase3_harness_workspace.py` still owns scenario application, but the deeper viewer/page/sync/sign-button choreography now sits with the compatibility surface that already owns the related shell-local helpers. |
| 2026-06-22 | Moved signed-acceptance viewer priming behind `phase3_harness_workspace.py`. | Reconciled the architecture doc so the workspace boundary now owns the remaining live viewer refresh used before signed-acceptance scenario iteration, while `phase3_signed_acceptance_matrix_runner.py` no longer reaches to `compat_surface` directly. |
| 2026-06-11 | Moved the live Qt preview-capture shell extraction path behind `phase3_harness_workspace.py`. | Reconciled the architecture doc so the workspace boundary now owns the last direct live shell anatomy read used for preview capture, while `phase3_harness.py` retains only the lower-level preview-analysis payload builder. |
| 2026-06-11 | Re-anchored the signed-acceptance executor on `phase3_harness_workspace.py`. | Reconciled the architecture doc so the executor now reads request/result/capture state through the workspace boundary, while `phase3_harness_session_runner.py` intentionally continues to own the interactive Qt session lifecycle and callback wiring. |
| 2026-06-07 | Documented the extracted Phase 3 harness scenario-application boundary in `phase3_harness_workspace.py`. | Reconciled the architecture doc so `phase3_harness.py` now delegates duplicated live-shell and headless preview-matrix scenario mutation to the new module, while `phase3_harness_session_runner.py` intentionally continues to own the interactive Qt session lifecycle and callback wiring. |
| 2026-06-06 | Extracted the Phase 3 signed-acceptance matrix runner into `phase3_signed_acceptance_matrix_runner.py`. | Reconciled the architecture doc so `phase3_harness.py` keeps the top-level signed-acceptance entrypoint while the new helper owns the matrix-level lifecycle, `timestamping_mode` validation, scenario loop, acceptance evaluation, summary shaping, and `summary.json` writing. |
| 2026-06-06 | Extracted the Phase 3 signed-acceptance scenario executor into `phase3_signed_acceptance_scenario_executor.py`. | Reconciled the architecture doc so `phase3_harness.py` keeps thin composition helpers while the new boundary owns one scenario row from preview capture through optional signed-output snapshotting. |
| 2026-06-06 | Extracted the shared Phase 3 signed-output snapshotter into `phase3_signed_output_snapshotter.py`. | Reconciled the architecture doc so both `phase3_harness.py` and `phase3_harness_capture_assembler.py` delegate successful-output evidence shaping and compact preview-vs-output comparison projection to the same helper. |
| 2026-06-06 | Extracted the Phase 3 signed-output render snapshotter into `phase3_signed_output_render_snapshotter.py`. | Reconciled the architecture doc so `phase3_harness.py` keeps only a thin wrapper while the new boundary owns signed-output render analysis, crop normalization, text detection, appearance parity comparison, and render artifact writing. |
| 2026-06-06 | Extracted the Phase 3 appearance snapshotter into `phase3_appearance_snapshotter.py`. | Reconciled the architecture doc so `phase3_harness.py` keeps only thin wrappers while the new boundary owns preview-side and signed-output-side `SignatureAppearanceSnapshot` reconstruction for render parity. |
| 2026-06-06 | Extracted the Phase 3 sign-time diagnostics snapshotter into `phase3_sign_time_diagnostics_snapshotter.py`. | Reconciled the architecture doc so `phase3_harness.py` keeps only a thin wrapper while the new boundary owns the merged backend-fit and canonical-preview-geometry diagnostics payload used in preview evidence. |
| 2026-06-07 | Extracted the Phase 3 image comparison helper into `phase3_image_comparison_helper.py`. | Reconciled the architecture doc so `phase3_harness.py` keeps only thin wrappers while the new boundary owns the shared preview/output crop hashing, flattening, change-ratio calculations, aspect-ratio delta, and side-by-side comparison artifact writing. |
| 2026-06-07 | Extracted the Phase 3 text geometry helper into `phase3_text_geometry_helper.py`. | Reconciled the architecture doc so `phase3_harness.py` keeps only thin wrappers while the new boundary owns source-to-preview projection, rendered-text geometry detection, candidate filtering, and reference-label fallback capture. |
| 2026-06-05 | Extracted the Phase 3 preview-matrix runner into `phase3_preview_matrix_runner.py`. | Reconciled the architecture doc so `phase3_harness.py` keeps the top-level preview-matrix entrypoint while the new helper owns the headless scenario loop, summary shaping, and `summary.json` writing. |
| 2026-06-27 | Moved appearance-only signing-setup mutation fully behind the coordinator boundary. | Reconciled the architecture doc with `DefaultSignaturePropertiesCoordinator.set_signature_appearance()` owning programmatic appearance updates while `SigningSetupSession` stops mutating `workflow` directly. |
| 2026-06-07 | Documented the extracted app-frame certificate-management boundary. | Reconciled the architecture doc with `app_frame_certificate_management.py` now owning certificate dialog construction/execution and lifecycle delegation while `app_frame.py` remains the `QMainWindow` host, action router, and compatibility-exposure edge. |
| 2026-06-27 | Added the first `Phase3Harness` facade tracer bullet for preview- and signed-acceptance matrix runs. | Historical record: `phase3_harness.py` briefly exposed an interim deep-module seam before the later hybrid collapse moved the caller-facing contract into `Phase3EvidenceService`. |
| 2026-07-04 | Collapsed the Phase 3 hybrid contract to the application service boundary. | Historical record: `Phase3EvidenceService` became the only caller-facing Phase 3 contract while `Phase3Harness` served as a Qt-backed adapter/composition root; the later typed matrix-operations slice removed that facade. |
| 2026-07-07 | Rebuilt the Phase 3 harness internals around typed operation ports and dependency bundles. | Historical record: `Phase3Harness` kept explicit `capture()`, `preview_matrix()`, and `signed_acceptance_matrix()` verbs while session and matrix helpers moved to typed dependency bundles; the later headless-first composition removed the redundant gateway layer. |
| 2026-06-05 | Extracted the Phase 3 harness capture assembler into `phase3_harness_capture_assembler.py`. | Reconciled the architecture doc with the new helper that owns signed-run bundle assembly and final capture-payload shaping while `phase3_harness_session_runner.py` remains the Qt session runner and `phase3_harness_reporting.py` remains the reporting boundary. |
| 2026-06-05 | Extracted the Phase 3 harness session runner into `phase3_harness_session_runner.py`. | Reconciled the architecture doc so `phase3_harness.py` remains the top-level harness entrypoint, while the new helper owns the interactive Qt callback cluster and returns `Phase3HarnessSessionResult` for later capture assembly and reporting. |
| 2026-06-05 | Extracted the shell-local signing-workspace runtime/controller into `signing_workspace_runtime.py`. | Reconciled the architecture doc with the dedicated helper that now owns recurring viewer/panel/page routing, interaction-plan dispatch, placement-context application, overlay sync, and shell-edge error/status handling. |
| 2026-06-04 | Added the signing-workspace action bridge and narrowed the signing-action boundary. | Reflected the extracted dialog/state glue owner and the resulting policy-only role for `SigningActionBoundary`. |
| 2026-06-05 | Extracted the constructor-time workspace assembly into `signing_workspace_composition.py`. | Reconciled the architecture doc with the dedicated helper that now owns session/bridge/widget assembly and bootstrap ordering for the signing workspace. |
| 2026-06-05 | Split the signing-workspace outer surface into a narrow production shell surface and an explicit compatibility surface. | Reconciled the architecture doc with `signing_workspace_shell_surface.py` now owning only caller-facing verbs while `signing_workspace_compatibility_surface.py` owns widget exports, `compat_surface`, and deep harness/testing helpers. |
| 2026-06-04 | Extracted `SignaturePropertiesPanel` into `signing_workspace_properties_panel.py`. | Reconciled the architecture doc with the dedicated panel module and tightened the remaining `signing_shell.py` debt note. |
| 2026-07-17 | Documented contextual reusable-profile saving. | `SignaturePropertiesPanel` delegates named appearance and placement persistence through `SigningSetupSession` and `DefaultSignaturePropertiesCoordinator` to `SignaturePresetCatalogStore`; saving keeps the refinement dialog and live PDF draft unchanged until Apply, and placement storage retains only a reusable `current_page` rectangle. |
| 2026-07-18 | Added reusable profile management and sign confirmation boundaries. | `SignatureProfileLibrary` owns reference-safe profile queries and mutations above storage; the Settings dialog is a Qt adapter, the shell refreshes its quick selector after management changes, and `SigningWorkspaceActionBridge` owns the explicit final confirmation dialog before the action coordinator submits a signing request. |
| 2026-06-02 | Documented explicit `SigningSetupSelectionOutcome` handling for signing setup selection. | Reconciled the architecture doc with the current session/panel contract where selection outcomes carry both state and applied status. |
| 2026-06-02 | Documented the extracted Phase 3 reporting boundary. | Reconciled the architecture doc with the new `phase3_harness_reporting.py` seam and its direct test surface. |
| 2026-06-01 | Updated workspace-interaction documentation for ordered effects. | Reflected the implemented `WorkspaceInteractionPlan` boundary and thin shell executor. |
| 2026-05-30 | Removed internal signature-rect callback coupling from the shell interaction seam. | Reflected direct rect application and viewer-selection placement now using explicit workspace-interaction follow-up instead of routing back through the panel's generic change callback. |
| 2026-05-31 | Moved `SigningActionState` rendering into the sidebar. | Reflected the completed ownership split where the sidebar mutates the `Sign PDF` widgets and the shell keeps orchestration, callback emission, and public surface ownership. |
| 2026-05-31 | Added a sidebar width fallback for the action-panel detail label. | Reflected the test-harness and early-layout case where the sidebar container can report zero width before layout stabilizes. |
| 2026-06-01 | Inserted `SigningActionBoundary` between the shell and signing-action coordinator. | Reflected the shell-facing orchestration split, the guarded open-signed-output path, and the compliance-reviewed boundary test coverage. |
| 2026-05-30 | Added the workspace-interaction session boundary above the review and viewer helpers. | Reflected `WorkspaceInteractionSession` taking ownership of recurring selection/page/refresh transition sequencing in the shell. |
| 2026-05-30 | Moved programmatic signature-appearance updates behind `SigningSetupSession`. | Reflected the panel delegating `set_signature_appearance()` to the setup session instead of mutating the workflow and clearing presets directly; later slices deepened that mutation path into the coordinator boundary. |
| 2026-05-29 | Moved preset save/delete orchestration behind `SigningSetupSession`. | Reflected the panel delegating preset mutation to the setup session while keeping overwrite/delete confirmation dialogs in Qt. |
| 2026-05-29 | Added the signing-setup session boundary above the coordinator. | Reflected `SigningSetupSession` taking ownership of common setup orchestration plus manual certificate-password retry/cancel/cache policy, leaving `SignaturePropertiesPanel` as a thinner Qt adapter. |
| 2026-05-29 | Added the explicit shell-owned signing-workspace port/factory boundary. | Reflected the typed `SigningWorkspaceBootstrap`, `SigningWorkspacePort`, `SigningWorkspaceFactory`, `QtSigningWorkspacePort`, and `QtSigningWorkspaceFactory` seam now used by `FoliaSealAppFrame` for workspace bootstrap and live shell refresh hooks. |
| 2026-05-27 | Removed the misleading review-card verify affordance and kept reopen in the primary sign panel only. | Reflected the read-only document review card and the one-button reopen flow now owned solely by the sign panel. |
| 2026-05-26 | Added the explicit certificate-application coordinator entrypoint and routed the Qt panel's certificate-application path through it. | Reflected the public `apply_certificate_configuration()` path now used by `SignaturePropertiesPanel.apply_selected_certificate_configuration()`. |
| 2026-05-25 | Added the explicit preset-application coordinator entrypoint and routed the Qt panel's nonblank preset-selection path through it. | Reflected the public `apply_signature_preset()` path now used by `SignaturePropertiesPanel._on_signature_preset_selected()`. |
| 2026-05-25 | Added the explicit visible-setup coordinator entrypoint and routed the Qt panel through it. | Reflected the public `apply_visible_setup()` path now used by `SignaturePropertiesPanel.apply_changes()`. |
| 2026-05-25 | Added the signing-action coordinator boundary. | Reflected the extraction of action/result/reopen state into `signing_action_coordinator.py` and the thin-shell adapter behavior. |
| 2026-05-22 | Added the Qt preview-layout boundary and narrowed shell tests to thin preview integration coverage. | Reflected `signature_preview_layout.py` extraction and close-aware preview cleanup wiring. |
| 2026-05-21 | Added the application-layer signature-properties coordinator and narrowed the Qt signing shell boundary to preview/presentation work. | Reflected the current coordinator-backed implementation. |
| 2026-05-06 | Added draft reusable-object references and certificate preview reader seam. | Reflected schema model alignment Slice 3A implementation. |
| 2026-05-06 | Wired existing certificate configurations into the Qt signing shell. | Reflected schema model alignment Slice 3B implementation. |
| 2026-05-06 | Renamed primary signature preset APIs and Qt shell wording away from generic profile terminology. | Reflected schema model alignment Slice 3C implementation. |
| 2026-05-07 | Removed obsolete profile compatibility wrappers for signature preset operations. | Reflected schema model alignment Slice 3D implementation. |
| 2026-05-07 | Added first-class AppSettings schema and storage. | Reflected schema model alignment Slice 4 persistence implementation; Qt Settings menu integration remains pending. |
| 2026-05-07 | Wired AppSettings into the Qt signing shell. | Documented settings controls and save-output dialog default-directory behavior; true application-frame menu/Open-file integration remains pending. |
| 2026-05-07 | Added a Qt application-frame wrapper. | Documented File/Open and Settings menu ownership plus default-directory flow into the signing shell. |
| 2026-05-07 | Replaced informational Settings menu action with an editable settings dialog. | Documented app-frame settings ownership and remaining duplicate shell controls. |
| 2026-05-09 | Removed duplicate signing-shell settings controls. | Documented app-frame settings dialog as the sole default-directory editor while the signing shell remains a settings consumer. |
| 2026-05-09 | Added first-pass PKCS#12 certificate import. | Documented app-frame import ownership, managed certificate copy behavior, and remaining certificate-management gaps. |
| 2026-05-10 | Added unreferenced managed certificate deletion. | Documented app-frame deletion ownership, managed PKCS#12 file removal, and the reference guard that requires deleting configurations first. |
| 2026-05-10 | Added managed certificate export. | Documented app-frame export ownership and non-mutating managed PKCS#12 backup behavior. |
| 2026-05-10 | Added Linux Secret Service saved-password support. | Documented `secret-tool` storage, import-time password saving, signing resolver wiring, and saved-secret cleanup on configuration deletion. |
| 2026-05-13 | Added first-pass in-app certificate creation. | Documented the self-signed PKCS#12 creation service, Settings/Create certificate flow, created managed-certificate records, and optional saved-password reuse. |
| 2026-05-15 | Hardened AppSettings save failure cleanup. | Documented `settings.json.tmp` cleanup behavior and preservation of the original filesystem failure. |
| 2026-05-15 | Added a state-driven signing-flow summary. | Reflected the first Brief F shell-architecture slice toward an explicitly staged V1 signing workflow. |
| 2026-05-23 | Extracted a production signing-workspace sidebar and removed the staged top rail from the real GUI layout. | Documented the new document-left / sidebar-right shell composition and the dedicated sidebar boundary. |
| 2026-05-23 | Consolidated output/sign/reopen/result controls into one `Sign PDF` sidebar panel. | Documented the remaining staged guidance as part of a cohesive action panel instead of loose sidebar controls. |
| 2026-05-06 | Added certificate catalog and signing-material resolver architecture. | Reflected schema model alignment Slice 2 implementation. |
| 2026-04-30 | Replaced skeleton with first-pass architecture map. | Documented current repository structure, contracts, flows, persistence, tests, debts, and open questions from code inspection. |
| 2026-04-30 | Created architecture document skeleton. | Establish canonical architecture documentation path referenced by agent instructions. |
