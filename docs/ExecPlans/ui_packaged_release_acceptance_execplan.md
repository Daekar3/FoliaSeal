# Validate the packaged offline release path

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK child of
`docs/ExecPlans/ui_product_support_and_release_execplan.md` and
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`.

## Purpose / Big Picture

SPEC.md says V1 is complete only when a non-expert can use a packaged Linux desktop application to
review, sign, save, verify, and reopen a PDF offline. The repository already builds a PyInstaller
one-directory bundle and wraps it in a Debian package, but the existing audit checks only a subset of
that contract and still invokes a legacy `phase3` command. This slice makes the package audit truthful
and repeatable: a fresh package is extracted into a disposable root, the installed wrapper is used to
discover Help and bundled resources, the desktop entry and Poppler dependency are inspected, and the
GUI endpoint is reported as either started or the known isolated single-instance limitation.

After this slice, one command from a checkout produces a concise JSON report proving package payload,
desktop metadata, offline Help parity, bundled fonts/help assets, `pdftoppm` availability, and cleanup.
It never uploads data, needs a Python checkout on the installed path, or claims display-backed GUI
success when the environment cannot provide it.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are the governing V1 release and Help contracts.
- [x] `docs/ExecPlans/ui_help_support_execplan.md` owns canonical packaged Markdown and CLI Help.
- [x] `docs/ExecPlans/ui_support_surfaces_execplan.md` owns product diagnostics and Settings support.
- [x] `docs/ExecPlans/ui_accessibility_acceptance_execplan.md` owns offscreen keyboard/name metadata;
  this child owns installed-package evidence only.
- [ ] A real display-backed desktop launch and screen-reader/DPI run; this is an external evidence
  gate and is intentionally classified rather than faked here.

## Progress

- [x] (2026-08-10) Fresh explorer audit confirmed package builders and structural tests exist, but no
  installed-package integration smoke suite exists and `scripts/deb_package_audit.py` still calls a
  legacy `phase3-signing-acceptance-evidence` command.
- [x] (2026-08-10) Created this bounded neutral package-audit plan; generated bundles/packages remain
  temporary and must never be committed.
- [ ] Replace the legacy audit command path with offline Help/resource/desktop/dependency checks and
  explicit classification of the isolated GUI endpoint.
- [ ] Add focused tests for audit report parsing and package metadata/resource assertions without
  forcing a full PyInstaller build in ordinary unit runs.
- [ ] Build a fresh bundle and `.deb`, run the audit, clean all owned roots/processes, reconcile
  release/architecture status, and commit the complete slice.

## Surprises & Discoveries

- Observation: `scripts/deb_package_audit.py` extracts the package and runs `--help`, but then invokes
  `phase3-signing-acceptance-evidence` instead of the documented product Help surface. Evidence:
  `scripts/deb_package_audit.py` and `docs/UI_SPEC.md` sections 7 and 14.
- Observation: package unit tests cover staging metadata but do not build/extract a real artifact or
  verify Help resources, desktop entry, Poppler, or installed wrapper behavior. Evidence:
  `tests/unit/test_pyinstaller_support.py` and `tests/unit/test_debian_packaging.py`.
- Observation: the extracted GUI attempt can terminate before window creation with
  `SingleInstanceUnavailable` because this environment cannot claim the per-user endpoint. This is
  an environment limitation, not a package pass; the report must distinguish it from other failures.
- Observation: PyInstaller may warn about an optional Qt TIFF library (`libtiff.so.5`). The audit must
  record the warning and verify that required PDF rendering/help resources still exist rather than
  silently discarding it.

## Decision Log

- Decision: keep the package audit as a script-level acceptance boundary and add unit tests for its
  pure report/metadata helpers; do not run a multi-minute build during every full pytest invocation.
  Rationale: package construction is an explicit release action and generated outputs are ignored,
  while helper logic remains fast and deterministic.
  Date/Author: 2026-08-10 / Codex.
- Decision: replace the legacy evidence command with `help --list`, `help signing-basics --format
  markdown`, and `help signing-basics --path`; do not add a new product command just for packaging.
  Rationale: UI_SPEC makes the canonical Markdown Help path the product contract and the old command
  exposes obsolete phase terminology.
  Date/Author: 2026-08-10 / Codex.
- Decision: use extraction into a `TemporaryDirectory` by default, and reserve real Debian install
  for a separately documented privileged/manual gate.
  Rationale: extraction proves the package payload and wrapper without mutating the host package
  database; the V1 release report must state that distinction.
  Date/Author: 2026-08-10 / Codex.
- Decision: classify only the exact `SingleInstanceUnavailable` startup signature as an environment-
  limited GUI result; any other packaged startup error fails the audit.
  Rationale: broad allowlists would hide missing Qt libraries, resources, or wrapper defects.
  Date/Author: 2026-08-10 / Codex.

## Outcomes & Retrospective

Not started. At completion, record the fresh package path (without committing it), package metadata,
offline Help outputs, resource/dependency checks, GUI classification, warnings, cleanup, and the
remaining display-backed/manual installation gates.

## Context and Orientation

`src/foliaseal/build/pyinstaller_support.py` collects fonts and packaged Help files into the
PyInstaller bundle described by `foliaseal.spec`. `src/foliaseal/build/debian_packaging.py` stages
that bundle under `/usr/lib/foliaseal`, writes `/usr/bin/foliaseal`, a desktop entry, icon, and
`Depends: poppler-utils`, then invokes `dpkg-deb`. `scripts/build_pyinstaller.sh` and
`scripts/build_deb.sh` are the checkout entry points. `scripts/deb_package_audit.py` is the current
extracted-package audit and is the only file this slice needs to change for audit behavior.

The installed wrapper must be invoked with `PYTHONPATH` removed and temporary HOME/XDG roots so it
cannot accidentally import the checkout or mutate a user's state. “Offline Help parity” means the
installed wrapper returns the same topic list, Markdown topic, and local topic path as the checkout
CLI without network access. “GUI limited” means the process returned the exact known single-instance
endpoint exception before a window was created; it is not a successful GUI acceptance result.

## Change Slice

Primary change class: evidence/acceptance behavior plus release documentation. Allowed files are
`scripts/deb_package_audit.py`, focused audit tests, this plan, architecture/release/parent plan
updates, and bounded ignored `/tmp` or `artifacts/` evidence. Do not commit `.deb` files, PyInstaller
directories, PDFs, private keys, logs, or a broad package-manager installation. Do not introduce
new phase3 labels or use the old phase3 evidence command in the installed product audit.

## Plan of Work

Refactor `scripts/deb_package_audit.py` so `audit(package, artifacts_dir)` extracts the package into
one owned temporary root and validates the wrapper, executable, desktop entry, icon, and control
metadata. Add helpers that run the installed wrapper with no `PYTHONPATH` and temporary XDG roots,
then assert `--help`, `help --list`, `help signing-basics --format markdown`, and `help signing-basics
--path`. Assert the returned path is inside the extracted package and the Markdown is non-empty and
free of JavaScript/remote-asset markers. Run `pdftoppm -h` (and a tiny fixture conversion when a
fixture can be created safely) to prove the declared dependency is available.

Change GUI startup to capture stdout/stderr and return a report object rather than raising for the
exact `SingleInstanceUnavailable` text. Keep nonzero returns and unrelated tracebacks as failures.
Record PyInstaller stderr warnings in the JSON report, especially missing optional TIFF libraries.
Ensure `TemporaryDirectory` cleanup happens even when a check fails and never leave a child process.

Add fast unit tests for metadata parsing, Help output marker checks, GUI-result classification, and
report serialization. Do not duplicate PyInstaller's build in ordinary tests. Run the real build and
audit manually from a disposable output directory as the acceptance milestone.

## Milestones

### Milestone 1: neutral audit contract

Add pure helpers and tests for package metadata, installed Help parity, dependency checks, and exact
GUI-limitation classification. The result is a script that no longer depends on obsolete phase3
commands and fails loudly on unrelated package/runtime errors.

### Milestone 2: fresh artifact evidence

Build a fresh PyInstaller bundle and Debian package, run the audit with network access disabled and
owned temporary roots, inspect the JSON report, then remove generated outputs and verify no process or
temporary root remains. Update release documentation with exact results and remaining manual gates.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/unit/test_deb_package_audit.py
    .venv/bin/ruff check src tests scripts
    .venv/bin/python -m pip check
    package_root=$(mktemp -d /tmp/foliaseal-package-acceptance-XXXXXX)
    .venv/bin/python -m foliaseal.build.debian_packaging --output-dir "$package_root/dist"
    deb=$(find "$package_root/dist" -name 'foliaseal_*.deb' -type f -print -quit)
    test -n "$deb"
    .venv/bin/python scripts/deb_package_audit.py "$deb" --artifacts-dir "$package_root/evidence"
    rm -rf "$package_root" build/foliaseal build/deb-staging dist/foliaseal
    test ! -e "$package_root"
    ps -eo pid=,cmd= | rg 'FoliaSeal|foliaseal|PySide6|pytest|pyinstaller|dpkg-deb' | rg -v 'rg ' || true

The audit report must show installed wrapper/executable, desktop entry, icon, `poppler-utils`
metadata, all three offline Help checks, bundled font/help resources, and either `gui: started` or
`gui: limited` with the exact single-instance reason. Any other GUI failure is a failed acceptance.

## Validation and Acceptance

The slice is accepted when the focused audit helper tests pass; a fresh `.deb` is built and extracted;
the installed wrapper works without `PYTHONPATH`; offline Help list/topic/path parity succeeds; the
desktop entry points at `/usr/bin/foliaseal gui`; the icon and bundled fonts/Help index exist; the
control file declares `poppler-utils`; `pdftoppm` is available; and the JSON report classifies GUI
startup accurately. The package is not claimed fully display-accepted when the exact endpoint
limitation occurs. Generated package/evidence roots and child processes must be removed.

## Idempotence and Recovery

All builds target an owned temporary output directory. If PyInstaller or `dpkg-deb` fails, retain the
source checkout, record stderr, remove only the named package root and generated build directories,
and retry. Never run `dpkg -i` against the host database without an explicit manual release gate.

## Artifacts and Notes

Keep only a concise JSON/transcript under ignored `/tmp` or `artifacts/` while auditing. Do not commit
the `.deb`, extracted root, PDFs, signing credentials, PyInstaller warnings, or machine-local paths.
Record package version, architecture, check names, GUI classification, cleanup, and any nonblocking
optional-library warning in the release ExecPlan.

## Interfaces and Dependencies

Use `subprocess.run` with explicit `cwd`, `env`, `capture_output`, and timeouts. The audit must expose
stable pure helpers for marker validation and GUI classification so tests can use synthetic results.
The installed wrapper is `/usr/bin/foliaseal`; its executable is `/usr/lib/foliaseal/foliaseal`.
The supported Help commands are `help --list`, `help signing-basics --format markdown`, and
`help signing-basics --path`. The dependency probe is `pdftoppm -h`. No network, Qt display server,
Python checkout imports, credential store, or user state is permitted.

Revision note: 2026-08-10 / Codex
Created after a fresh release audit found structural package tests but no installed-package smoke
suite and a stale extracted audit invoking the obsolete phase3 evidence command.
