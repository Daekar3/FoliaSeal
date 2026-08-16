# Add an isolated package-manager install smoke gate

This ExecPlan is a living document and must be maintained in accordance with
`/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The packaged-release evidence currently extracts a Debian package with `dpkg-deb`, which proves
payload layout but not that the package manager can install the package into its normal filesystem
shape. This slice adds an isolated install-root smoke gate: `dpkg` (preferably in an unprivileged
user namespace, with `fakeroot` as a runtime fallback) installs the generated `.deb` into a disposable root with a private package
database, and the installed wrapper then proves `--help`, offline Help, bundled resources, and the
declared Poppler dependency. The host package database and user filesystem are never touched.

After this change, a release engineer can distinguish “package payload extracts” from “package
manager installs and the installed launcher runs.” The gate remains headless and does not claim a
display-backed GUI or real desktop-session acceptance.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/ui_packaged_release_acceptance_execplan.md` established the extracted-package
  audit, offline Help/resource checks, and exact GUI limitation classification.
- [x] `scripts/deb_package_audit.py` already validates the extracted wrapper, desktop entry, fonts,
  Help, and `pdftoppm` conversion.
- [x] A fresh package build and install-root smoke run passed; final reconciliation and regression
  validation remain before this child can close.

## Progress

- [x] (2026-08-16) Explorer review identified isolated package-manager installation as the next
  headless-capable release gap; ordinary GUI/lifecycle children are already implemented offscreen.
- [x] (2026-08-16) Confirmed the environment has `dpkg` and `/usr/bin/fakeroot`, while the current
  user is unprivileged; the smoke gate can therefore avoid host package-database mutation.
- [x] (2026-08-16) Added a private install-root helper and report section to
  `scripts/deb_package_audit.py`. Unprivileged runs prefer `unshare --user --map-root-user` and
  fall back to `fakeroot`; dpkg logs and database state stay under the disposable root.
- [x] (2026-08-16) Added focused unit tests for command construction, unshare/fakeroot selection,
  private database initialization, and failure behavior (`17 passed`).
- [x] (2026-08-16) Built a fresh `.deb` and ran both extracted and package-manager smoke gates. Both
  reports passed; the installed wrapper returned Help parity, 18 fonts, `pdftoppm` conversion, and
  GUI status `limited` with the known isolated endpoint signature. The install gate returned dpkg
  code `0` and cleaned its private root.
- [x] (2026-08-16) Closed the compliance findings: install roots must be strict dedicated children,
  an `unshare` runtime failure retries once with `fakeroot` when available, and dependency reports
  identify `pdftoppm` as a host-runtime probe rather than private-database dependency installation.
- [x] (2026-08-16) Reconciled release/architecture/parent status, ran full validation (`1504 passed,
  20 skipped, 1 warning`), passed Ruff/compileall/diff checks, removed generated build/package roots,
  and confirmed no owned package-manager or GUI processes remain.

## Surprises & Discoveries

- Observation: the current audit's use of `dpkg-deb --extract` does not exercise package-manager
  database installation or file ownership/path sequencing.
  Evidence: `scripts/deb_package_audit.py::audit()` invokes only `dpkg-deb --extract` and
  `dpkg-deb --control` before running the extracted wrapper.
- Observation: the checkout user is `uid=1000`, but `fakeroot` is installed.
  Evidence: `id` reports an unprivileged user and `command -v fakeroot` returns `/usr/bin/fakeroot`.
- Observation: the package wrapper intentionally has a relative-prefix fallback when `/usr/lib` is
  not the host path, so an isolated install root can execute it without bind-mounting `/usr`.
  Evidence: `src/foliaseal/build/debian_packaging.py::stage_package()` writes the fallback based on
  the wrapper's own location.
- Observation: `fakeroot dpkg --install` cannot complete on this filesystem because its ownership
  shim returns `EINVAL`, and a private dpkg database has no installed `poppler-utils` dependency.
  Evidence: the first real run failed on `/var/log/dpkg.log`, then on tar ownership, and finally on
  dependency configuration after the log path was fixed.
- Observation: launcher availability does not guarantee that an unprivileged user namespace is
  permitted by runtime policy.
  Evidence: the audit retries a failed `unshare` invocation with `fakeroot` when available and
  reports the final command; a failed fallback still fails the audit rather than hiding the error.
- Observation: `unshare --user --map-root-user dpkg --unpack` provides the needed package-manager
  payload installation without requiring host dependencies or privileged ownership.
  Evidence: the final fresh-package run passed both audits; the install report recorded `dpkg_returncode=0`
  and `temporary_install_root_cleaned=true`.

## Decision Log

- Decision: add an opt-in `--package-manager-root` smoke mode rather than making every audit run a
  package-manager install.
  Rationale: release audits need the stronger gate, but unit/ordinary evidence runs must remain fast,
  idempotent, and free of package-manager side effects; an explicit root path makes scope auditable.
  Date/Author: 2026-08-16 / Codex.
- Decision: use `dpkg --root`/`--admindir`/`--instdir` with a private status database and run it in
  an unprivileged user namespace (`unshare --user --map-root-user`) when available, falling back to
  `fakeroot` only where necessary. Use `dpkg --unpack` rather than `--install`: the private database
  intentionally does not contain the host's `poppler-utils` dependency, while the existing control
  metadata and `pdftoppm` probes still verify that dependency contract.
  Rationale: the user namespace permits package ownership operations against the temporary root on
  this filesystem while keeping all mutable state under one directory; invoking host `dpkg -i` is
  out of scope and unsafe for an automated audit.
  Date/Author: 2026-08-16 / Codex.
- Decision: reuse the installed-wrapper Help/resource/dependency checks instead of creating a second
  report schema.
  Rationale: the package-manager and extraction paths should prove the same product contract, with
  only the installation provenance differing.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The 2026-08-16 fresh-package run completed both the existing extraction audit and the new isolated
package-manager audit. Each report was `status=passed`, with five Help topics, the complete 18-font
set, successful `pdftoppm` fixture conversion, and GUI status `limited` for the known
`SingleInstanceUnavailable: Unable to claim or reach the FoliaSeal instance endpoint:` signature.
The package-manager report recorded `dpkg_returncode=0`, `--unpack` under an `unshare` user namespace,
and `temporary_install_root_cleaned=true`. The host package database was never used. PyInstaller
warnings for optional `pycparser` tables and `libtiff.so.5` were recorded but did not affect required
payload checks.

The implementation slice is complete. Privileged host installation and display-backed desktop
acceptance remain separate release gates; this plan is ready for commit and handoff.

## Context and Orientation

`src/foliaseal/build/debian_packaging.py` stages `/usr/bin/foliaseal`, `/usr/lib/foliaseal`, the
desktop entry, icon, and Debian control metadata. `scripts/deb_package_audit.py` currently extracts
those paths and runs the installed wrapper with private HOME/XDG directories. A package-manager
install root is a directory containing its own `var/lib/dpkg` database and `usr/` payload; it is not
the host root and must be removed after the run. The installed wrapper's relative-prefix fallback
allows it to find the bundle inside this temporary root.

## Plan of Work

Add pure helpers in `scripts/deb_package_audit.py` to initialize a private dpkg database, choose the
`unshare`/`fakeroot` prefix when the current user is unprivileged, retry with `fakeroot` when an
available `unshare` launcher fails at runtime, run `dpkg --root=<root> --admindir=<root>/var/lib/dpkg
--instdir=<root> --unpack <package>`, and assert that the package-manager command succeeds. Reject install
roots that resolve outside or equal to the caller-owned artifact directory; the root must be a
dedicated child. Reuse the existing Help/resource/
dependency probes against `<install-root>/usr/bin/foliaseal`, and return a bounded report containing
the install root relative paths, dpkg return code, wrapper Help result, and cleanup status.

Expose the mode through an optional CLI argument such as `--package-manager-root`; without it,
preserve the existing extraction-only audit contract. The smoke mode must never use `/var/lib/dpkg`,
`/usr`, or a user XDG directory. Ensure subprocesses have explicit environment, timeout, and captured
output, and ensure cleanup happens in `finally` even when dpkg fails.

Add focused tests using temporary fake package-manager commands or synthetic package roots to prove
command argument construction, private database initialization, path containment, failure reporting,
and JSON serialization. Do not require a real `.deb` or fakeroot in ordinary unit tests.

## Milestones

### Milestone 1: isolated install-root contract

The script exposes tested helpers that can install into a caller-owned root, invoke the wrapper there,
and report package-manager status without touching the host. Unit tests prove the command is bounded
and rejects unsafe roots.

### Milestone 2: real package-manager evidence

Build a fresh package, run the existing extraction audit and the new install-root mode, inspect Help,
resources, and `pdftoppm` results, then delete the package, install root, build directories, and
processes. Update the parent release plan with exact counters and the distinction between install-root
and privileged real-host installation.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/python -m pytest -q tests/unit/test_deb_package_audit.py
    .venv/bin/ruff check src tests scripts
    package_root=$(mktemp -d /tmp/foliaseal-package-manager-XXXXXX)
    .venv/bin/python -m foliaseal.build.debian_packaging --output-dir "$package_root/dist"
    deb=$(find "$package_root/dist" -name 'foliaseal_*.deb' -type f -print -quit)
    test -n "$deb"
    .venv/bin/python scripts/deb_package_audit.py "$deb" \
      --artifacts-dir "$package_root/extraction-evidence"
    .venv/bin/python scripts/deb_package_audit.py "$deb" \
      --artifacts-dir "$package_root/install-evidence" \
      --package-manager-root "$package_root/install-root"

The install-mode report must show a successful private `dpkg` installation, installed wrapper Help
parity, bundled resource checks, and Poppler conversion. If the GUI probe reports the known isolated
endpoint limitation, record it as limited rather than failed. Remove `$package_root`, `build/`, and
`dist/` outputs owned by the run and audit for leftover `dpkg`, `fakeroot`, `foliaseal`, `PySide6`, or
`pytest` processes.

## Validation and Acceptance

The slice is accepted when focused tests, Ruff, compileall, and the full suite pass; the extraction
audit remains green; the install-root audit proves `dpkg` installation and executes the installed
wrapper with no checkout `PYTHONPATH`; Help list/topic/path parity, fonts, resources, desktop/control
metadata, and `pdftoppm` conversion remain green; and all generated roots/processes are cleaned.
The report must label the dependency check `scope=host-runtime`; an isolated install root is not a
privileged host package-manager install or display-backed desktop acceptance.
Acceptance must explicitly state that a fakeroot install root is not the same as a privileged host
package-manager install or display-backed desktop acceptance.

## Idempotence and Recovery

Every run uses a new explicit temporary root and private dpkg database. If installation fails, retain
the captured stderr long enough to classify it, then remove only the named temporary root and generated
build outputs. Never invoke `dpkg -i` against the host database and never delete an unresolved path.

## Artifacts and Notes

Keep only concise JSON/report counters under ignored temporary roots while validating. Do not commit
`.deb` files, extracted payloads, package databases, PDFs, credentials, or build logs.

## Interfaces and Dependencies

Use `subprocess.run` with explicit `cwd`, environment, captured output, and timeouts. Reuse the existing
`_audit_help()`, `_audit_dependency()`, and package resource checks. The new install mode must expose a
stable report field naming the package-manager command, install-root-relative wrapper, and status so
release documentation can distinguish it from extraction-only evidence.

Revision note: 2026-08-16 / Codex
Created after the UI release-plan review identified real package-manager installation as the remaining
headless-capable gap after the extracted-package audit passed. Updated the same day with strict
dedicated-root cleanup, runtime unshare/fakeroot fallback, host-runtime dependency scope, fresh
package evidence, and release-plan reconciliation.
