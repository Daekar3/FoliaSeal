# PDF Signer

Foundations for a Linux desktop PDF signing app.

## What is included
- package skeleton with architecture-aligned module boundaries (`presentation`, `application`, `domain`, `infra`)
- `DocumentOperation` domain contract and operation registry with capability enable/disable flags
- initial config schemas for trust profile, timestamp policy, and signature presets
- Phase 1 headless signing orchestration (`SignPdfUseCase`) with:
  - compatibility policy enforcement for PDF `1.4` to `2.0`
  - strict PDF version parsing (rejects invalid/non-finite version strings)
  - incremental-signing version-preservation checks
  - stable failure-code mapping and structured signing results
  - output-path conflict detection using normalized filesystem paths
  - temp-file + atomic replace output writes with temp-file cleanup
- unit tests for schema validation, compatibility policy, operation registry behavior, and signing orchestration
  - signing orchestration tests include success path plus explicit failure-code mapping checks
    (`OUTPUT_PATH_INVALID`, `PKCS12_WRONG_PASSWORD`, `PKCS12_LOAD_FAILED`,
    `TSA_UNREACHABLE`, `TIMESTAMP_REQUIRED_BUT_MISSING`, `POST_VERIFY_FAILED`,
    `PDF_SIGNING_FAILED`, `ATOMIC_WRITE_FAILED`, `UNEXPECTED_INTERNAL_ERROR`)
- Phase 2 kickoff viewer foundations with:
  - render adapter abstraction (`infra.render`) and fallback backend diagnostics
  - deterministic view↔PDF coordinate transform utilities (zoom, pan, rotation, page-box offsets)
  - pre-sign PDF rectangle bounds validation helper
  - page render LRU cache policy primitives for upcoming viewer integration
  - Qt render backend scaffold with graceful diagnostics when Qt bindings are unavailable
  - `ViewerSession` helper for page navigation and zoom/fit interactions
  - `ViewerPerformanceTracker` helper for first-render and navigation timing metrics
  - Phase 2 evidence formatter utilities to capture timing snapshots alongside runtime environment details
  - CLI helper (`python -m pdf_signer phase2-evidence ...`) to generate Phase 2 markdown timing evidence snippets, including optional auto-capture of startup latency (from a probe command), idle memory, and bundle-size metrics for FR-16 evidence
  - `ViewerWorkflow` helper that wires renderer output, page geometry, selection transforms, and timing capture for Qt widget integration
  - Qt preview widget adapter (`presentation.qt`) with wheel zoom + drag-selection wiring to viewer workflow
- unit tests expanded for render adapter fallback behavior, coordinate transforms, cache policy, viewer session behavior, and Qt widget dependency diagnostics

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
ruff check .
pytest -q
python -m pdf_signer
```

## PyInstaller build

Build a one-dir bundle for FR-16 evidence capture:

```bash
.venv/bin/pip install -e .[dev]
./scripts/build_pyinstaller.sh
```

This produces:

- bundle directory: `dist/pdf-signer`
- executable: `dist/pdf-signer/pdf-signer`

You can then generate a fuller Phase 2 evidence block against the packaged app:

```bash
python3 -m pdf_signer phase2-evidence \
  --first-render-ms 47.54 \
  --navigation-ms 49.35 \
  --navigation-ms 45.06 \
  --navigation-ms 47.68 \
  --navigation-ms 49.00 \
  --navigation-ms 47.79 \
  --navigation-ms 41.84 \
  --navigation-ms 47.68 \
  --navigation-ms 48.70 \
  --navigation-ms 47.14 \
  --navigation-ms 42.44 \
  --navigation-ms 47.98 \
  --navigation-ms 48.33 \
  --navigation-ms 53.64 \
  --navigation-ms 42.77 \
  --navigation-ms 47.17 \
  --navigation-ms 48.19 \
  --navigation-ms 54.07 \
  --navigation-ms 43.07 \
  --navigation-ms 46.57 \
  --navigation-ms 52.18 \
  --measure-startup-command dist/pdf-signer/pdf-signer \
  --collect-runtime-footprint \
  --bundle-dir dist/pdf-signer \
  --check-qt-runtime
```
