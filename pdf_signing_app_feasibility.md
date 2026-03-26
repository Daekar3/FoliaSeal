# Python PDF Signing Implementation Plan (Linux Mint 22.3)

## Locked technology choices (confirmed)
This proposal now assumes the following fixed decisions:
1. **Runtime:** Python **3.11+**
2. **Desktop UI:** **PySide6 / Qt for Python**
3. **Distribution:** **PyInstaller one-dir** bundle
4. **Signing engine:** **pyHanko**

No alternative UI/distribution options are considered in this version.

---

## Project goal
Build a Linux desktop app that signs existing PDFs using an existing `.p12/.pfx` certificate, applies a visible signature appearance, embeds an RFC 3161 timestamp token, and outputs Acrobat-compatible signed PDFs.

Usability target for initial scope: provide an easy, intuitive PDF viewing + signing flow for non-technical users while keeping runtime footprint and startup time suitable for everyday desktop use.

---

## Review update: key gaps found and addressed
After re-reviewing feasibility assumptions and architecture, these were the main misses:
1. **PDF rendering dependency was implicit**: pyHanko signs PDFs but does not serve as an interactive page renderer for GUI rectangle drawing.
2. **Coordinate transform risk was under-specified**: GUI coordinates (top-left origin) must map correctly to PDF coordinates (bottom-left origin).
3. **Existing signatures/certification behavior needed explicit requirements**: incremental signing must preserve prior revisions and respect certification constraints.
4. **Trust configuration for TSA/verification was under-defined**: system trust + optional custom trust anchors should be configurable.
5. **Operational controls** (file locking, temp files, crash-safe output strategy) needed explicit coverage.
6. **PDF version/standards scope was implicit**: supported ISO PDF versions and conformance profiles for open/save needed explicit policy.

The sections below now include those requirements and architecture improvements.

---

## PDF standards and version compatibility profile

This implementation plan adopts an explicit compatibility policy for both **opening** and **saving** PDFs:

- **Normative base standards**
  - ISO 32000-1 (PDF 1.7)
  - ISO 32000-2 (PDF 2.0) for baseline structural parsing where accepted by the signing stack
  - PAdES baseline profiles as implemented by pyHanko (for signature container semantics)

- **Open/read support (input documents)**
  - Target support: `%PDF-1.4` through `%PDF-2.0`.
  - Files with **valid cross-reference tables/streams** and standard incremental update chains are in scope.
  - Documents may already contain approval signatures and/or certification signatures; app will open and inspect permission constraints before allowing edits.
  - Encrypted files are supported **only** when encryption mode is compatible with the selected PDF processing/signing libraries and the user can provide required credentials; unsupported encryption variants are rejected with explicit diagnostics.
  - Malformed or repair-required files are out of scope for auto-healing; app rejects rather than silently rewriting structure.

- **Save/write support (output documents)**
  - Output is always written as an **incremental update** to preserve existing revisions/signatures.
  - Output PDF header/version is preserved from input where possible; app does not perform full-document down-conversion/up-conversion as a feature.
  - New signature revisions must be Acrobat-compatible for detached CMS signatures and RFC 3161 document timestamps.
  - App writes standards-compliant signature dictionaries, ByteRange, and related objects expected by ISO PDF signature workflows.

- **Conformance exclusions (initial release)**
  - No guaranteed archival conformance transformation/validation (e.g., automatic PDF/A conversion).
  - No guaranteed generation or remediation for PDF/UA tagging compliance.
  - No support promise for non-standard vendor-private extensions unless pass-through incremental signing works without structural rewrite.

This profile should be treated as a release-gating contract and reflected in QA compatibility matrices.

---

## Specific functional requirements (expanded)

## FR-1: Input and output handling
- User can select exactly one input PDF.
- User must choose a save location for output PDF.
- App must never overwrite the input file in place.
- App must block signing if input PDF is unreadable, encrypted in unsupported mode, or malformed.
- App must validate that input PDF version is within supported open range (`PDF 1.4` to `PDF 2.0`) before enabling signing workflow.

## FR-2: Certificate handling
- User can select `.p12` or `.pfx` file.
- User enters passphrase in masked field.
- App validates that:
  - private key exists,
  - signing certificate exists,
  - certificate validity dates are current (or warning if not),
  - key usage is compatible with digital signatures where extension exists.
- App supports alias selection if multiple identities are present.

## FR-3: Signature placement and appearance
- User can select target page index.
- User can define signature rectangle by **click-and-drag with the mouse** directly on a rendered PDF page preview.
- UI must provide live rectangle preview while dragging, with resize/reposition handles after placement.
- UI should allow optional numeric fine-tuning (x, y, width, height) after mouse placement, but mouse placement is the primary workflow.
- Visible signature appearance must support:
  - signer display name,
  - signing date/time,
  - reason,
  - location,
  - optional image stamp (PNG/JPEG).

## FR-4: Cryptographic signing
- App generates detached CMS signature over PDF ByteRange.
- App writes signature as incremental update.
- Signing algorithm is selected based on key type (RSA/ECDSA).
- Hash algorithm defaults to SHA-256 or stronger.

## FR-5: RFC 3161 timestamping
- App requires TSA URL configuration.
- App requests timestamp token during signing.
- If timestamp is required and unavailable, signing must fail with a clear error.
- If timestamp optional mode is enabled (admin/dev setting), app may sign without TSA and emit warning.

## FR-6: Post-sign verification and reporting
- App verifies signature presence and basic integrity immediately after signing.
- App confirms timestamp token presence when required.
- App displays structured result: success, warnings, errors, signer subject, signing time, output path.

## FR-7: Auditability and logs
- App logs operational events (without secrets):
  - input/output file names,
  - cert fingerprint,
  - TSA URL,
  - success/failure code.
- App must never log passphrase or private key material.

## FR-8: Packaging/runtime requirements (PyInstaller one-dir)
- Release artifact is a one-dir folder produced by PyInstaller.
- Bundle must run on Linux Mint 22.3 without requiring system Python package installation.
- Bundle must include all Python deps and Qt plugins required for startup.

## FR-9: PDF rendering and coordinate mapping
- App must render the target PDF page in the UI using a dedicated rendering component (e.g., Qt PDF module or pdfium-based adapter).
- App must maintain deterministic transform utilities between view coordinates and PDF coordinates.
- App must account for zoom, pan, rotation, crop/media box differences when mapping signature rectangle bounds.
- App must validate rectangle bounds against final PDF page box before signing.

## FR-10: Existing signatures and certification compatibility
- If the input PDF already contains signatures, app must preserve previous signatures via incremental updates.
- App must detect certification restrictions (DocMDP / permissions) and block disallowed operations with clear diagnostics.
- App must provide user-visible warnings when adding another signature may invalidate certain workflows.

## FR-11: Trust and verification configuration
- App must support a trust configuration profile for TSA and certificate path validation.
- Profile must allow:
  - system trust store usage,
  - optional additional CA bundle path,
  - optional revocation-check mode toggles (offline/online policy).

## FR-12: Output integrity and crash safety
- App must sign to a temporary output file and perform atomic move/replace on success.
- App must avoid partial/corrupt output files on interrupted signing attempts.
- App must surface file-lock or permission failures with actionable error messages.

## FR-13: Performance and UX constraints
- UI remains responsive during signing, timestamping, and verification operations.
- Long operations (>500 ms) show progress status.
- User can cancel before final write step; cancellation is reported cleanly.
- Initial viewer open (first page render) should complete within a practical desktop target budget on typical user hardware, and startup/first-render timings must be measured in QA.

## FR-14: PDF standards and version compatibility requirements
- App must implement and expose a compatibility policy for PDF standards support in user-visible help/docs.
- **Opening support**:
  - Must accept input PDFs declaring version `1.4` to `2.0`, subject to structural validity checks.
  - Must support both classic xref tables and xref streams when parsing input.
  - Must reject unsupported encryption/security handlers with actionable error text naming the unsupported mode.
- **Saving support**:
  - Must save signed output using incremental updates only; full rewrite mode is not permitted in default signing flow.
  - Must preserve original input PDF version header unless a version bump is strictly required by signature features in use; any bump must be logged.
  - Must generate PDF signatures compatible with ISO digital signature model (signature dictionary + ByteRange + CMS object embedding).
- **Standards profile declarations**:
  - Must declare PAdES baseline level targeted by the implementation (at minimum B-B/B-T equivalent behavior depending on timestamp policy).
  - Must explicitly state that PDF/A and PDF/UA compliance conversion/repair is out of scope unless a future module is added.
- **Validation and reporting**:
  - Post-sign verification must report effective output PDF version, signature subfilter, and timestamp presence.
  - Result dialog/log must include a standards-compatibility summary (e.g., "Opened as PDF 1.7, saved incrementally as PDF 1.7, PAdES-B-T style timestamped signature").

## FR-15: Viewer usability and intuitive interaction requirements
- App must provide core viewer controls expected by end users:
  - page navigation (next/previous, jump-to-page),
  - zoom in/out/reset and fit-to-width / fit-to-page,
  - scroll and pan behavior consistent with desktop PDF readers.
- Signature placement workflow should require minimal steps:
  - select certificate,
  - place box on page,
  - confirm metadata,
  - sign and save.
- App must provide inline guidance and validation hints near the fields that commonly fail (certificate password, TSA URL, output path, rectangle bounds).
- Keyboard accessibility must cover primary actions (open file, navigate pages, zoom, sign, cancel).
- Error messages must be written in user-facing language first, with optional expandable technical details.

## FR-16: Lightweight runtime and deployment requirements
- Packaging must avoid unnecessary heavy dependencies beyond UI/rendering/signing requirements.
- App must support a low-memory mode for large PDFs in preview (render current/nearby pages only, avoid full-document rasterization).
- Preview rendering must use caching with bounded memory policy and predictable eviction behavior.
- Bundle size, startup latency, and baseline idle memory usage must be measured and tracked as release metrics.

## FR-17: Extensible document operations architecture requirements
- Signing workflow must be isolated from generic document-editing operations through a stable `DocumentOperation` interface.
- Document operations must be modeled as capability modules (e.g., `SignOperation`, future `AddPageOperation`, `RemovePageOperation`, `MovePageOperation`, `CropPageOperation`) with shared validation and permission checks.
- Command orchestration layer must support registering/enabling/disabling operations without changing core UI navigation components.
- Save pipeline must define operation compatibility rules with signature preservation (e.g., page edits may require full rewrite and may invalidate prior signatures, whereas signing remains incremental).
- UI must be structured so future page-edit tools can be added as new toolbar panels/dialogs without rewriting the signing form.
- Audit/log schema must include operation type and revision strategy (incremental vs full rewrite) to support future mixed-operation workflows.

---

## Architecture (detailed for PySide6 + pyHanko)

## 1) `presentation.qt` (PySide6 UI layer)
Main classes:
- `MainWindow`
- `SigningFormWidget`
- `SignaturePreviewWidget`
- `ResultDialog`

Responsibilities:
- Form input, validation feedback, and workflow state.
- Rendering PDF page preview and interactive rectangle overlay.
- Handling mouse-driven rectangle creation (drag to place, drag handles to resize, drag body to move).
- Progress/cancel UX during signing task.
- User-friendly mapping from domain errors to messages.

Notes:
- Keep UI thread responsive by running signing in worker thread (`QThreadPool` / `QRunnable`).
- Centralize styles/themes to avoid duplicated UI logic.
- Keep preview rendering and coordinate transforms in dedicated helper components, not in widget event handlers.

## 2) `application` (use-case orchestration)
Primary service:
- `SignPdfUseCase.execute(request: SigningRequest) -> SigningResult`
- `RunDocumentOperationUseCase.execute(request: DocumentOperationRequest) -> DocumentOperationResult`

Responsibilities:
- Coordinate calls across cert loading, PDF signing, TSA, and verification.
- Enforce policy (timestamp required, allowed algorithms, output path rules).
- Produce deterministic result objects for UI and CLI reuse.
- Route operation requests through a capability registry so additional page-edit operations can be introduced without rewriting signing orchestration.

## 3) `domain` (entities and policy)
Core dataclasses/enums:
- `SigningRequest`
- `SignatureAppearance`
- `TimestampPolicy`
- `PdfCompatibilityProfile`
- `DocumentOperationType`
- `DocumentOperationRequest`
- `DocumentOperationResult`
- `SigningResult`
- `FailureCode` enum

Responsibilities:
- Define pure business types and validation rules.
- Keep domain free of UI and library-specific objects.
- Include `TrustProfile` and `CoordinateTransformResult` value objects used by application policy checks.
- Encode operation compatibility policies (e.g., preserves signatures vs rewrites file).

## 4) `infra.cert` (PKCS#12 adapter)
Responsibilities:
- Parse `.p12/.pfx` and extract key + certificate chain.
- Resolve alias/identity selection.
- Provide certificate metadata (subject, issuer, serial, validity, fingerprint).

Design:
- Return normalized `SignerIdentity` object consumed by signing layer.
- Raise explicit typed exceptions (`WrongPasswordError`, `NoPrivateKeyError`, etc.).

## 5) `infra.pdf` (pyHanko integration)
Responsibilities:
- Map domain request -> pyHanko signing objects.
- Manage signature field creation/reuse.
- Build visible appearance stamp style.
- Execute incremental save signing operation.

Key design rule:
- This module is the **only** place that imports pyHanko APIs directly.

## 5b) `infra.render` (PDF preview adapter)
Responsibilities:
- Render PDF pages to pixmap/image for on-screen preview.
- Expose page box/rotation metadata for transform calculations.
- Provide utility hooks for zoom/pan aware coordinate conversion.

Design notes:
- Keep rendering backend replaceable (QtPdf vs pdfium adapter) behind one interface.
- Expose navigation/zoom primitives reusable by both signing overlays and future page-edit tools.

## 5c) `infra.pdf_ops` (future document operation adapters)
Responsibilities:
- Provide backend adapters for non-signing operations such as add/remove/move/crop page workflows.
- Surface capability constraints (requires rewrite, may invalidate signatures, unsupported for certified docs).
- Reuse shared parse/validate/write primitives with explicit strategy selection (incremental vs full rewrite).

## 6) `infra.tsa` (RFC 3161 client configuration)
Responsibilities:
- Configure and instantiate timestamper objects.
- Apply timeout and retry policy.
- Translate timestamp failures into domain failure codes.

## 7) `infra.verify` (post-sign checks)
Responsibilities:
- Confirm signed output contains expected signature field.
- Confirm timestamp token presence according to policy.
- Return verification summary for UI display.
- Check for warnings related to existing signatures/certification restrictions.

## 8) `infra.logging`
Responsibilities:
- Structured logging with correlation id per signing attempt.
- Redaction filter for sensitive input.

## 9) `packaging`
Responsibilities:
- Maintain PyInstaller spec file.
- Include Qt plugin/data collection configuration.
- Produce reproducible one-dir release artifact + checksum.
- Ensure renderer backend runtime dependencies are bundled and validated at startup.

---

## Proposed repository layout

```text
pdf-signer/
  pyproject.toml
  README.md
  src/pdf_signer/
    presentation/qt/
      main_window.py
      signing_form.py
      preview_widget.py
      result_dialog.py
    application/
      sign_pdf_use_case.py
      run_document_operation_use_case.py
      operation_registry.py
    domain/
      models.py
      policies.py
      errors.py
    infra/
      cert/pkcs12_loader.py
      pdf/pyhanko_signer.py
      pdf_ops/page_operations_adapter.py
      render/pdf_preview_adapter.py
      render/coord_transform.py
      tsa/timestamper_factory.py
      trust/trust_profile_loader.py
      verify/signature_verifier.py
      logging/config.py
  packaging/
    pyinstaller.spec
    build_release.sh
  tests/
    unit/
    integration/
```

---

## End-to-end sequence
1. User opens app and selects input PDF/output path.
2. User selects `.p12/.pfx`, enters passphrase, chooses alias (if needed).
3. User configures page and draws signature rectangle with mouse; optional fine-tuning and appearance/TSA settings are applied.
4. UI validates basic inputs and dispatches `SigningRequest`.
5. Use case loads trust profile, identity, and validates certificate constraints.
6. Rectangle coordinates are transformed/validated against PDF page metadata.
7. pyHanko signing adapter signs PDF with visible appearance.
8. Timestamper is invoked and token embedded.
9. Signed file is written through temp-file + atomic move strategy.
10. Verification adapter runs post-sign checks (including prior-signature/certification warnings).
11. UI displays success/warning/error with detailed diagnostics.

---

## Error model (explicit)
Failure codes to expose in UI and logs:
- `INPUT_PDF_INVALID`
- `OUTPUT_PATH_INVALID`
- `PKCS12_LOAD_FAILED`
- `PKCS12_WRONG_PASSWORD`
- `CERT_NOT_VALID_YET`
- `CERT_EXPIRED`
- `CERT_KEY_USAGE_INCOMPATIBLE`
- `SIGNATURE_RECT_INVALID`
- `COORDINATE_TRANSFORM_FAILED`
- `PDF_CERTIFICATION_RESTRICTS_SIGNING`
- `PDF_SIGNING_FAILED`
- `TSA_UNREACHABLE`
- `TIMESTAMP_REQUIRED_BUT_MISSING`
- `POST_VERIFY_FAILED`
- `TRUST_PROFILE_INVALID`
- `ATOMIC_WRITE_FAILED`
- `UNEXPECTED_INTERNAL_ERROR`

---

## Security baseline
- Passphrases handled in memory only and cleared ASAP.
- No secret material in logs or UI traces.
- Output file permissions follow least-privilege defaults.
- Timestamp required by default in production profile.
- Certificate fingerprint logged for traceability.
- Temp-file output + atomic move prevents partial signed artifacts.
- Trust profile changes are audit-logged.

---

## PyInstaller one-dir packaging plan (specific)

## Build approach
- Build releases on Linux Mint 22.3 CI/runner (or compatible Ubuntu base).
- Use pinned dependency versions.
- Generate bundle with:
  - Python runtime,
  - app code,
  - pyHanko deps,
  - Qt platform plugins (`xcb`, etc.),
  - renderer backend dependencies,
  - required SSL/cert resources.

## Artifact shape
- `dist/pdf-signer/` directory containing executable + bundled libs.
- Add release checksum file (`SHA256SUMS`).

## Packaging checklist
- App starts on clean Mint 22.3 VM.
- File picker, preview, and signing flow all function.
- No missing Qt plugin runtime errors.
- Timestamp flow works against configured TSA endpoint.

---

## Testing plan (aligned to chosen stack)

## Unit tests
- Domain validation (paths, coordinates, policy flags).
- PKCS#12 loader edge cases.
- Error mapping from infra exceptions -> `FailureCode`.
- Coordinate transform math (zoom/pan/rotation/crop cases).
- Trust profile parsing/validation.

## Integration tests
- Sign sample PDFs (single page, multi-page, form-filled, scanned).
- Validate visible signature placement bounds.
- Validate TSA required vs optional behavior.
- Validate outputs in Acrobat and Okular.
- Validate incremental signing on already-signed PDFs.
- Validate blocking behavior on certification-restricted PDFs.

## UI tests
- Basic PySide6 form validation and worker-thread behavior.
- Preview widget coordinate transformation tests.
- Mouse interaction tests for draw/resize/move of signature rectangle.

## Packaging tests
- Smoke test executable from one-dir bundle on fresh Mint image.
- Startup test with missing network (TSA unreachable error path).
- Startup/render test confirms preview backend is available in bundle.

---

## Delivery milestones

## Milestone 1 (Week 1–2): Signing core
- Implement domain/application/infra signing path (headless).
- CLI harness for rapid validation.
- Pass integration tests for basic sign + timestamp.

## Milestone 2 (Week 3–4): PySide6 desktop MVP
- Build full signing workflow UI.
- Add preview and result diagnostics.
- Stabilize error handling and logs.

## Milestone 3 (Week 5): PyInstaller distribution
- Finalize `.spec` and build scripts.
- Produce one-dir release and smoke-test on clean Mint.

## Milestone 4 (Week 6): Hardening
- Improve verification diagnostics.
- Expand certificate edge-case handling.
- Final QA across document varieties.

---

## Final recommendation
Proceed with a **Python 3.11+ + PySide6 + pyHanko + PyInstaller one-dir** implementation exactly as specified above. This is the most practical path for your current requirements and gives strong control over UX plus signing correctness without forcing AppImage complexity.

---

## Research sources used
- pyHanko signing guide:
  - https://docs.pyhanko.eu/en/v0.25.1/cli-guide/signing.html
- pyHanko configuration and PKCS#12 notes:
  - https://docs.pyhanko.eu/en/v0.28.0/cli-guide/config.html
- pyHanko library signing docs:
  - https://pyhanko.readthedocs.io/en/v0.27.1/lib-guide/signing.html
- PyInstaller usage docs:
  - https://www.pyinstaller.org/en/stable/usage.html
