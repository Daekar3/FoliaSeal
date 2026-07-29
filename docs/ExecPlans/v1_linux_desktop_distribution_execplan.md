# Ship an installable Debian-family FoliaSeal desktop package

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, a Linux user can install one FoliaSeal package, find FoliaSeal in the desktop application menu, and launch the same GUI used by the acceptance audit. The package declares its `poppler-utils` dependency so the signed-PDF viewer does not silently lose pixel rendering on a fresh system.

## Child ExecPlan Dependencies

- [x] `foliaseal.spec` and `scripts/build_pyinstaller.sh` produce a one-dir PyInstaller bundle with bundled font assets.
- [x] This child has no further child ExecPlans.

## Progress

- [x] (2026-07-20) Selected Debian-family `.deb` as the first supported distribution mode and identified Poppler as a package dependency.
- [x] (2026-07-28) Explorer review confirmed that only the PyInstaller bundle exists; `dpkg-deb` and `pdftoppm` are available, while no Debian builder, desktop metadata, package icon, or package-owned audit exists.
- [x] (2026-07-28) Added a reproducible package staging/build script, desktop entry, icon, and package metadata.
- [x] (2026-07-28) Added the deterministic Debian builder, relocatable wrapper, desktop entry, icon, and Poppler dependency metadata.
- [x] (2026-07-28) Added `tests/unit/test_debian_packaging.py` for package content, control fields, desktop entry, wrapper relocation, and deterministic naming.
- [x] (2026-07-28) Built and inspected `dist/foliaseal_0.1.0_amd64.deb`; extracted wrapper `--help` and isolated Qt GUI startup passed.
- [x] (2026-07-28) Package-owned signed-acceptance evidence passed from the extracted bundle: 10 scenarios/7 successful signings, 18/18 parity scenarios, and 3/3 fit-rejection scenarios.
- [x] (2026-07-28) Focused regression suite passed (`238 passed` across packaging, PyInstaller, signing backend, review, certification, and Qt shell tests); `ruff`, `bash -n`, and `git diff --check` passed.
- [x] (2026-07-28) Independent architecture/SPEC review found one documentation-only mismatch: the architecture text still called desktop packaging open work; no SPEC contradiction was found.
- [x] (2026-07-28) Reconciled README, architecture, and SPEC packaging statements; completed the compliance review. Commit remains the parent agent's responsibility.

## Surprises & Discoveries

- Observation: the current PyInstaller spec has `console=True` and only collects Python/runtime font assets.
  Evidence: `foliaseal.spec` and `src/foliaseal/build/pyinstaller_support.py`.
- Observation: the interactive renderer late-resolves `pdftoppm`.
  Evidence: `PopplerPdfRenderBackend` and the README installation note.
- Observation: the environment has `/usr/bin/dpkg-deb` and `/usr/bin/pdftoppm`, and the repository virtual environment has PyInstaller, but those tools are not all on the ambient `PATH`.
  Evidence: explorer command checks and `.venv/bin/pyinstaller`.
- Observation: no package-owned acceptance command can currently launch the extracted bundle or prove that it avoids checkout imports.
  Evidence: no `scripts/build_deb.sh`, Debian metadata, or `tests/unit/test_debian_packaging.py` exists yet.
- Observation: the first builder run exposed a path-handling defect in the version reader, which treated the repository directory as the TOML file.
  Evidence: `IsADirectoryError` from `project_version()` during `./scripts/build_deb.sh`; fixed before continuing.
- Observation: the existing PyInstaller spec could not actually build because PyInstaller executes spec files without `__file__`.
  Evidence: the first package build failed with `NameError: name '__file__' is not defined`; the spec now uses PyInstaller's `SPECPATH` variable.
- Observation: an extracted package cannot resolve an absolute `/usr/lib/foliaseal` target even though a system install can.
  Evidence: the first extracted `--help` smoke exited 127; the installed wrapper now uses its own `/usr/bin` location as a safe extracted-prefix fallback.
- Observation: the first package GUI launch failed because PyInstaller did not infer dynamically imported `PySide6.QtWidgets`.
  Evidence: extracted `gui` exited with `ModuleNotFoundError: No module named 'PySide6.QtWidgets'`; the spec now declares the dynamically imported Qt modules explicitly.
- Observation: this audit host advertises `DISPLAY=:0` but cannot load its X11 cursor dependency, so a package audit must use Qt's bundled offscreen platform plugin.
  Evidence: packaged GUI exited with the xcb diagnostic; the audit now sets `QT_QPA_PLATFORM=offscreen` and still exercises the real Qt application and signing matrix.

## Decision Log

- Decision: package the existing PyInstaller one-dir output inside a `.deb` rather than inventing a second application build path.
  Rationale: the existing bundle already contains Python, Qt, and font collection behavior; the Debian package supplies installation layout, launcher metadata, and OS dependencies.
  Date/Author: 2026-07-20 / Codex
- Decision: retain `console=True` in the shared PyInstaller executable and make the desktop entry invoke the explicit `gui` subcommand.
  Rationale: the same executable remains useful for headless evidence commands, while the desktop launcher gets the real Qt GUI without creating a second build definition.
  Date/Author: 2026-07-28 / Codex

## Outcomes & Retrospective

The supported Debian-family distribution slice is complete. `./scripts/build_deb.sh` produced
`dist/foliaseal_0.1.0_amd64.deb` (SHA-256
`14403f944861636ca8729893eb4be721668f197e07ae733154e493b70b6a8d95`). `dpkg-deb --info`
confirmed `Package: foliaseal`, `Version: 0.1.0`, `Architecture: amd64`, and `Depends:
poppler-utils`; package contents include `/usr/bin/foliaseal`, `/usr/lib/foliaseal/foliaseal`,
`/usr/share/applications/foliaseal.desktop`, and the packaged SVG icon. The retained package-owned
audit is `/tmp/foliaseal-deb-audit/audit.json`: extracted `--help`, offscreen Qt startup, and
signed-acceptance evidence passed with 10 scenarios/7 successful signings, 18/18 parity scenarios,
and 3/3 fit-rejection scenarios. The package deliberately leaves `pdftoppm` as the declared host
`poppler-utils` dependency; no unresolved external dependency limitation remains for this slice.

## Context and Orientation

PyInstaller creates `dist/foliaseal/foliaseal` from `foliaseal.spec`. A Debian package is a `.deb` archive installed by Debian-family Linux systems; it contains a payload under `/usr`, package metadata under `DEBIAN/control`, and desktop integration under `/usr/share/applications`. The desktop entry is the small `.desktop` file that lets a graphical shell list and launch FoliaSeal. The final package must depend on `poppler-utils` because that provides `pdftoppm`.

## Plan of Work

Add a repository-owned packaging directory and a `scripts/build_deb.sh` wrapper. It must call the existing PyInstaller build, stage the bundle under `/usr/lib/foliaseal`, install a relocatable wrapper at `/usr/bin/foliaseal` that resolves its own installed directory rather than the checkout, add `foliaseal.desktop` and a repository-owned icon, and generate `DEBIAN/control` with Package, Debian-safe Version, Architecture from `dpkg --print-architecture`, Maintainer, Description, and `Depends: poppler-utils`. Record other discovered runtime dependencies rather than assuming Poppler is sufficient. Keep the PyInstaller spec as the only executable build definition, but make an explicit decision whether `console=True` changes for desktop launch. Use one deterministic output path derived from the normalized package version and architecture; fail if stale or multiple package artifacts could be selected. Add `tests/unit/test_debian_packaging.py` to inspect staging paths, control fields, desktop entry, wrapper relocation, and naming without installing a package. Add a package-owned audit entrypoint or an `--app-command` audit seam that runs the extracted executable, records its real path under extracted `/usr`, and cannot import the checkout or `.venv`; the current source-importing GUI audit is not sufficient.

## Concrete Steps

From `/home/daekar/FoliaSeal`:

    .venv/bin/python -m pytest -q tests/unit/test_pyinstaller_support.py tests/unit/test_debian_packaging.py
    .venv/bin/ruff check src/foliaseal/build tests/unit/test_debian_packaging.py
    bash -n scripts/build_deb.sh
    command -v shellcheck >/dev/null && shellcheck scripts/build_deb.sh || true
    ./scripts/build_deb.sh
    dpkg-deb --info dist/foliaseal_<version>_<architecture>.deb
    dpkg-deb --contents dist/foliaseal_<version>_<architecture>.deb
    sha256sum dist/foliaseal_<version>_<architecture>.deb
    .venv/bin/python scripts/deb_package_audit.py dist/foliaseal_<version>_<architecture>.deb --artifacts-dir /tmp/foliaseal-deb-audit

Expected inspection: a `Depends` field including `poppler-utils`, `/usr/bin/foliaseal`, `/usr/lib/foliaseal/foliaseal`, and `/usr/share/applications/foliaseal.desktop`.

## Validation and Acceptance

From an empty working directory with `PYTHONPATH` unset, run the extracted wrapper’s `--help`, then run the new package-owned audit against its generated representative PDF. It records the executable under the audit’s temporary extracted `/usr` tree, creates certificate material, signs, reopens, and verifies without a missing-`pdftoppm` diagnostic or imports from the checkout/.venv. The package exposes a desktop entry with `Exec=/usr/bin/foliaseal`, correct icon path and permissions, and does not depend on the development virtual environment.

## Idempotence and Recovery

Build only under `build/` and `dist/`; delete and recreate a package-specific staging directory on each run. Never install the package system-wide during automated validation. If `dpkg-deb` is absent, record that external blocker and still run unit/staging checks; do not claim distribution acceptance.

## Artifacts and Notes

Recorded package SHA-256, `dpkg-deb --info` metadata, package-owned extracted launch transcript,
and signed-acceptance summary in Outcomes above and `/tmp/foliaseal-deb-audit/audit.json`. Do not
commit generated `.deb` files unless repository policy changes.

## Interfaces and Dependencies

Use `foliaseal.spec`, `scripts/build_pyinstaller.sh`, `src/foliaseal/build/pyinstaller_support.py`, package metadata in `pyproject.toml`, and `PopplerPdfRenderBackend`. The package may declare system dependencies but must not copy arbitrary host libraries into the bundle.

Revision note: 2026-07-20 / Codex
Created as the packaging-change child of `v1_release_compliance_parent_execplan.md`.
