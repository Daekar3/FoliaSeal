# FoliaSeal

FoliaSeal is a Linux desktop application for reviewing PDF documents, placing visible approval
signatures, signing with a local certificate, saving the result, and reopening it for verification.
The repository also contains headless signing components and repeatable developer/QA evidence
tools.

> **Project status:** FoliaSeal is an early V1 development build. The end-to-end signing workflow
> exists and is covered by automated checks, but the GUI is still undergoing usability work and
> the product has not completed final manual acceptance or release review. Do not treat this
> repository as a production release or as a replacement for your organisation's signing and
> trust policies.

## What it does

The current application is centered on one document at a time and supports:

- opening and reviewing PDF pages with navigation, zoom, pan, text search, and text selection;
- inspecting signatures already present in a document;
- importing a PKCS#12 certificate or creating a locally managed signing certificate;
- saving and reusing certificate configurations, appearance profiles, placement profiles, and
  signature presets;
- placing, resizing, repositioning, and numerically fine-tuning a visible signature;
- previewing the signed appearance on the document page with readiness and fit feedback;
- signing to a user-selected output path and reopening the signed PDF for review; and
- adding another approval signature when the document permits incremental signing.

The core signing path is designed to work offline. Verification reports the local assessment and
does not claim trust that requires an external policy or service.

## Scope and non-goals

FoliaSeal V1 is a signing-and-review application, not a general PDF editor. It does not aim to be:

- a page editor or multi-document workspace;
- a cloud document-management or workflow product;
- an enterprise certificate lifecycle or trust-policy management system; or
- a general-purpose signature-card, rich-text, or page-composition tool.

Timestamping and broad trust-policy controls are engineering capabilities outside the normal V1
GUI path. They should not be interpreted as release-ready product features.

## Requirements

- Linux desktop environment.
- Python 3.11 or newer for a source installation.
- `pdftoppm` from Poppler for interactive PDF page pixels. On Debian-family systems it is supplied
  by `poppler-utils`.
- A desktop session for the interactive Qt GUI. Some validation and evidence commands can run
  headlessly.
- Optional: `secret-tool` and a running Linux Secret Service if certificate passwords should be
  saved by the application.

## Install and run from a checkout

Create an isolated environment and install the GUI extra:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[gui]'
```

Launch the application, optionally opening a PDF immediately:

```bash
foliaseal gui
foliaseal gui --pdf-path /path/to/document.pdf
```

For development, install the additional test, lint, and packaging tools:

```bash
python -m pip install -e '.[dev]'
```

## Development checks

From the repository root:

```bash
ruff check .
python -m pytest -q
```

Use `foliaseal --help` for the current command-line surface. The GUI and acceptance harnesses are
developer tools while the product workflow is still being refined; they are not separate end-user
applications.

### Offline Help

Help is available from the packaged, offline topic catalog:

```bash
foliaseal help --list
foliaseal help signing-basics --format markdown
foliaseal help signing-basics --path
```

The same topics are available from the GUI Help menu or F1. `--path` prints the installed Markdown
file location when the resource loader provides a filesystem path.

## Evidence and QA commands

Generated evidence belongs under the ignored `artifacts/` directory or another explicit temporary
directory. It is local run output, not a required input to a fresh clone.

Validate an existing harness capture without launching Qt:

```bash
foliaseal acceptance-harness-validate \
  --summary-json-path artifacts/interactive_harness_capture.json
```

Run the bundled signed-acceptance evidence workflow, which regenerates local fixture assets and
writes a concise summary. This workflow is deterministic evidence and may run with
`QT_QPA_PLATFORM=offscreen`; it does not constitute human visual acceptance:

```bash
foliaseal signed-acceptance-evidence
```

For explicit scenario sweeps, the preview and signed-output matrix commands require a PDF,
PKCS#12 identity, passphrase, JSON manifest, and artifact directory:

```bash
foliaseal preview-matrix \
  --pdf-path /path/to/document.pdf \
  --certificate-path /path/to/identity.p12 \
  --passphrase 'test-passphrase' \
  --scenario-manifest-path /path/to/preview-manifest.json \
  --artifacts-dir artifacts/preview-matrix
```

The interactive harnesses launch Qt and are intended for display-backed manual review. An
offscreen run can exercise the Qt path and generate artifacts, but it cannot prove what an
operator sees on a real display:

```bash
foliaseal interactive-harness \
  --pdf-path /path/to/document.pdf \
  --certificate-path /path/to/identity.p12 \
  --passphrase 'test-passphrase' \
  --artifacts-dir artifacts/acceptance_preview_debug
```

On Linux Mint 22.3, the supported live-review session for this project is the normal Cinnamon/X11
desktop session. Wayland review is intentionally deferred until the OS treats Wayland as a
first-class supported session.

Do not put production passphrases in shell history or checked-in manifests. Use test identities
for local QA. Harness completion is not a release gate by itself; review the generated evidence,
the applicable checklist, and representative signed output.

## Build Linux packages

Build the PyInstaller one-directory bundle:

```bash
python -m pip install -e '.[dev]'
./scripts/build_pyinstaller.sh
```

Build the Debian-family package from that environment:

```bash
./scripts/build_deb.sh
```

Build output is written under `dist/`. The package includes the Python and Qt runtime and declares
`poppler-utils` as its runtime dependency. Package artifacts are engineering outputs until a
dated release has been manually accepted.

## Documentation

- [Product specification](docs/SPEC.md) — V1 goals, workflow, and anti-goals.
- [Persistent schemas](docs/SCHEMAS.md) — certificate, profile, placement, and preset objects.
- [Architecture](docs/ARCHITECTURE.md) — current module boundaries and implementation contracts.
- [Execution plans](docs/ExecPlans/) — detailed implementation and QA work.

The README intentionally omits historical test counts, matrix scoreboards, generated artifact
paths, and implementation-history notes. Those details belong in the relevant plan or run summary
so this page remains a reliable introduction for a fresh checkout.
