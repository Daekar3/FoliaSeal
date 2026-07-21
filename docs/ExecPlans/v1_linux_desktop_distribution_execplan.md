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
- [ ] Add a reproducible package staging/build script, desktop entry, icon, and package metadata.
- [ ] Add `tests/unit/test_debian_packaging.py` package-content, control-field, desktop-entry, and deterministic-name tests.
- [ ] Build, inspect, extract, and launch the package in an isolated local prefix.
- [ ] Run the representative GUI acceptance path from the extracted package, reconcile docs, and commit.

## Surprises & Discoveries

- Observation: the current PyInstaller spec has `console=True` and only collects Python/runtime font assets.
  Evidence: `foliaseal.spec` and `src/foliaseal/build/pyinstaller_support.py`.
- Observation: the interactive renderer late-resolves `pdftoppm`.
  Evidence: `PopplerPdfRenderBackend` and the README installation note.

## Decision Log

- Decision: package the existing PyInstaller one-dir output inside a `.deb` rather than inventing a second application build path.
  Rationale: the existing bundle already contains Python, Qt, and font collection behavior; the Debian package supplies installation layout, launcher metadata, and OS dependencies.
  Date/Author: 2026-07-20 / Codex

## Outcomes & Retrospective

At creation, the repository can build a development one-dir folder but cannot yet claim a supported desktop distribution. Record the built package name, architecture, dependency metadata, extraction/launch result, and any external dependency limitation at completion.

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
    dpkg-deb --fsys-tarfile dist/foliaseal_<version>_<architecture>.deb | tar -x -C /tmp/foliaseal-deb-root

Expected inspection: a `Depends` field including `poppler-utils`, `/usr/bin/foliaseal`, `/usr/lib/foliaseal/foliaseal`, and `/usr/share/applications/foliaseal.desktop`.

## Validation and Acceptance

From an empty working directory with `PYTHONPATH` unset, run the extracted wrapper’s `--help`, then run the new package-owned audit against a representative PDF. It must record that the executable is under `/tmp/foliaseal-deb-root/usr`, create/select a certificate, sign, reopen, and verify without a missing-`pdftoppm` diagnostic or imports from the checkout/.venv. The package must expose a desktop entry with `Exec=/usr/bin/foliaseal`, correct icon path and permissions, and must not depend on the development virtual environment.

## Idempotence and Recovery

Build only under `build/` and `dist/`; delete and recreate a package-specific staging directory on each run. Never install the package system-wide during automated validation. If `dpkg-deb` is absent, record that external blocker and still run unit/staging checks; do not claim distribution acceptance.

## Artifacts and Notes

Record package SHA-256, `dpkg-deb --info` output, and extracted launch transcript in this plan or a release evidence file. Do not commit generated `.deb` files unless repository policy changes.

## Interfaces and Dependencies

Use `foliaseal.spec`, `scripts/build_pyinstaller.sh`, `src/foliaseal/build/pyinstaller_support.py`, package metadata in `pyproject.toml`, and `PopplerPdfRenderBackend`. The package may declare system dependencies but must not copy arbitrary host libraries into the bundle.

Revision note: 2026-07-20 / Codex
Created as the packaging-change child of `v1_release_compliance_parent_execplan.md`.
