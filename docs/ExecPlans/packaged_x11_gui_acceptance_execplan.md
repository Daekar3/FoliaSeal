# Exercise the packaged GUI on the supported Cinnamon/X11 display

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an evidence child of
`docs/ExecPlans/ui_packaged_release_acceptance_execplan.md`,
`docs/ExecPlans/ui_product_support_and_release_execplan.md`, and
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`.

## Purpose / Big Picture

The package acceptance plan already proves the Debian payload, offline Help,
fonts, Poppler, and private install-root behavior, but its GUI probe always
uses Qt's offscreen platform. That proves startup only in a headless
environment and cannot show that an installed package creates a real desktop
window. This slice adds an explicit, opt-in Cinnamon/X11 mode to the existing
package audit. A fresh `.deb` can then be extracted and launched with temporary
XDG configuration on the supported display; the audit records whether the
packaged GUI reaches a live-window startup boundary and terminates its owned
process without changing the default offline audit or attempting Wayland.

The result is release evidence, not a claim of human usability. It does not
certify screen-reader speech, high contrast, physical-DPI interpretation,
packaged signing, privileged host installation, or final release acceptance.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` define the packaged Linux GUI and
  offline release contract.
- [x] `docs/ExecPlans/ui_packaged_release_acceptance_execplan.md` owns the
  extracted package audit and keeps generated packages temporary.
- [x] `docs/ExecPlans/x11_display_accessibility_audit_execplan.md` established
  the supported Cinnamon/X11 session and cleanup boundary.
- [x] Wayland is explicitly deferred for Mint 22.3 by user direction.

## Progress

- [x] (2026-08-16) Explorer audit found no dependency-ready AFK product behavior
  gap; the remaining release work is evidence and human/environment gates.
- [x] (2026-08-16) Added an opt-in `--display-backed` mode to
  `scripts/deb_package_audit.py`; default extraction and package-manager paths
  remain offscreen and the report records the selected Qt platform.
- [x] (2026-08-16) The first real-X11 package run exposed an environment
  propagation overwrite and missing bundled `copy.svg`/`text-select.svg`
  assets. The audit now preserves `xcb`, requires the canonical icon set, and
  `collect_runtime_assets` packages those SVGs.
- [x] (2026-08-16) Built a fresh `.deb` and ran the extracted audit against
  `DISPLAY=:0`: payload, five offline Help topics, 18 fonts, two icons,
  Poppler fixture conversion, and GUI startup all passed; the report showed
  `gui_environment.qt_platform=xcb` and `gui_startup.status=started`.
- [x] (2026-08-16) Verified the audit-owned package/build roots and child
  process were removed; unrelated desktop windows were left untouched.
- [x] (2026-08-16) Current-HEAD validation is `1543 passed, 20 skipped, 1
  warning`; Ruff, compile, and diff checks are clean.
- [x] (2026-08-16) Reconciled package/release/parent/architecture status and
  obtained two independent GO reviews. The focused slice is committed as
  `14b21061b` (`test: validate packaged X11 startup`).
- [x] (2026-08-16) Re-ran the fresh package audit from the current checkout in the
  supported Cinnamon/X11 session. The report passed with `display_backed=true`,
  `qt_platform=xcb`, `gui_startup.status=started`, five offline Help topics,
  18 fonts, two runtime icons, Poppler fixture conversion, and clean owned-root/
  child-process teardown. This is packaged-X11 startup evidence only; human
  accessibility, privileged installation, final release acceptance, and Wayland
  remain outside this child.

## Surprises & Discoveries

- Observation: the existing `_run_gui` helper hardcodes `QT_QPA_PLATFORM` to
  `offscreen`, so the package plan's GUI result cannot be display-backed.
  Evidence: `scripts/deb_package_audit.py` constructs the audit environment with
  `env["QT_QPA_PLATFORM"] = "offscreen"` before invoking the wrapper.
- Observation: the package wrapper uses the temporary XDG configuration roots
  supplied by the audit, so a real X11 launch can avoid the user's endpoint and
  credentials while still exercising the installed executable.
  Evidence: `scripts/deb_package_audit.py` sets `HOME`, `XDG_CONFIG_HOME`,
  `XDG_DATA_HOME`, and `XDG_CACHE_HOME` below its owned extraction root.
- Observation: the supported session is Cinnamon/X11 with two 1920x1080
  monitors; no Wayland command is part of this plan.
  Evidence: the completed X11 display audit and current `DISPLAY=:0` session.
- Observation: the first display-backed package launch reached a window but
  emitted missing SVG-resource warnings because PyInstaller did not collect the
  source icon directory.
  Evidence: the first audit output named `copy.svg` and `text-select.svg`; both
  files existed under `src/foliaseal/resources/icons`.

## Decision Log

- Decision: add an explicit `--display-backed` audit option instead of changing
  the default package audit to require a desktop.
  Rationale: CI and offline release checks must remain deterministic and
  headless, while a human or release agent can opt into the X11 gate.
  Date/Author: 2026-08-16 / Codex.
- Decision: require an existing `DISPLAY` and use `QT_QPA_PLATFORM=xcb` in
  display-backed mode; reject Wayland and do not synthesize a display.
  Rationale: this evidence is specifically for the supported Mint 22.3
  Cinnamon/X11 session and must not imply unsupported transport coverage.
  Date/Author: 2026-08-16 / Codex.
- Decision: preserve the existing three-second startup boundary and terminate
  only the audit-owned wrapper process after it reaches that boundary.
  Rationale: the package audit proves launch/window creation without leaving a
  desktop application open; human interaction belongs to the separate HITL
  release gate.
  Date/Author: 2026-08-16 / Codex.
- Decision: permit a narrowly scoped packaging behavior correction in this
  evidence slice: collect and validate the two runtime SVG icons used by the
  existing Qt menus and toolbar.
  Rationale: the first real packaged launch proved the icons were required at
  runtime; leaving the warning would make the installed GUI incomplete.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The corrected package audit passed on Cinnamon/X11. A fresh `.deb` reached the
real Qt `xcb` startup boundary, and its extracted payload contained the
canonical 18 fonts and two runtime SVG icons; Help, Poppler, desktop metadata,
and cleanup also passed. Focused package/resource tests passed (`28 passed`).
The full suite is `1543 passed, 20 skipped, 1 warning`, and two independent
reviews returned GO. The final commit is `14b21061b`; post-commit status and
owned package/build/process cleanup are clean.
Screen-reader speech, high contrast, physical-DPI interpretation, human GUI
workflow, privileged installation, final release matrix, and Wayland remain
open or deferred.

## Context and Orientation

`src/foliaseal/build/debian_packaging.py` creates the Debian payload. The
checkout entry points are `scripts/build_pyinstaller.sh` and
`scripts/build_deb.sh`. `scripts/deb_package_audit.py` extracts a package,
creates temporary HOME/XDG roots, validates the installed wrapper and bundled
resources, runs the installed Help and Poppler checks, and currently launches
the GUI with a headless Qt platform. Its `classify_gui_result` function must
continue to distinguish a successful startup boundary, the known isolated
single-instance limitation, and unrelated failures.

“Display-backed” means that Qt connects to the existing desktop display and
creates a real top-level window. It does not mean a person has judged every
visual or assistive-technology requirement. “Startup boundary” means that the
wrapper remains alive beyond the bounded initial `communicate` timeout, after
which this audit terminates that exact child process.

## Change Slice

Primary change class: evidence/acceptance behavior plus the narrowly necessary
packaging asset correction and release documentation. Allowed changes are
`scripts/deb_package_audit.py`, `src/foliaseal/build/pyinstaller_support.py`,
`pyproject.toml`, focused package/resource tests, this plan, and status updates in the owning
release/parent plans. Generated
`.deb` files, PyInstaller directories, PDFs, credentials, screenshots, and
user configuration are forbidden from the commit. No production Qt behavior,
schema, CLI command, Wayland code, or default headless behavior may change.

## Plan of Work

1. Extend `_run_gui` and `audit` with a clearly named `display_backed` option.
   The normal path must continue setting `QT_QPA_PLATFORM=offscreen`; the opt-in
   path must require `DISPLAY`, set `QT_QPA_PLATFORM=xcb`, and retain temporary
   HOME/XDG roots. Propagate the option only through the extracted-package
   audit, not the private package-manager smoke unless explicitly requested.
2. Add a CLI flag such as `--display-backed` with a useful error when no
   `DISPLAY` is available. Include the selected mode in the JSON report while
   preserving exact `started`, `limited`, and `failed` classification.
3. Add fast unit tests for mode/environment construction and CLI/report behavior
   without building a package. Keep the existing known single-instance and
   unrelated-failure tests.
4. Build a fresh package into an owned `/tmp` root, run the audit with
   `DISPLAY=:0 QT_QPA_PLATFORM=xcb`, inspect the JSON, and remove the package,
   extraction, process, and temporary roots. Never activate or close unrelated
   desktop windows.
5. Update the package, release, and parent ExecPlans with the exact result and
   remaining HITL gates. Obtain independent architecture/compliance review,
   then commit only the bounded files.

## Concrete Steps

Run from `/home/daekar/FoliaSeal` in the supported Cinnamon/X11 session:

    package_root=$(mktemp -d /tmp/foliaseal-packaged-x11-XXXXXX)
    .venv/bin/python -m foliaseal.build.debian_packaging --output-dir "$package_root/dist"
    deb=$(find "$package_root/dist" -name 'foliaseal_*.deb' -type f -print -quit)
    test -n "$deb"
    DISPLAY=:0 QT_QPA_PLATFORM=xcb .venv/bin/python scripts/deb_package_audit.py \
      "$deb" --artifacts-dir "$package_root/evidence" --display-backed
    cat "$package_root/evidence/audit.json"
    ps -eo pid=,cmd= | rg 'foliaseal|PySide6|pyinstaller|dpkg-deb' | rg -v 'rg ' || true
    rm -rf "$package_root"
    test ! -e "$package_root"

The JSON must report the display-backed mode and either `gui_startup.status`
`started` or the exact known `limited` endpoint signature. Any other GUI
failure is a failed audit. The command must not be run under Wayland.

## Validation and Acceptance

Acceptance requires the focused package-audit tests to pass, Ruff and compile
checks to pass, and the existing full suite to remain green. A fresh package
must pass the existing payload/Help/font/Poppler checks in display-backed mode
and report whether the installed GUI reached a live X11 startup boundary. The
wrapper child, temporary package root, extraction root, and audit evidence must
be removed after inspection. This slice may close only the packaged X11 launch
evidence gate; screen-reader, high-contrast, physical-DPI, human GUI workflow,
privileged installation, final release matrix, and Wayland remain open unless
separately proven.

## Idempotence and Recovery

All generated files live under one unique temporary root. If a build or audit
fails, preserve source changes, record stderr in the plan, terminate only the
known audit child, remove that root and generated build directories, and retry.
If no display exists, run the default headless audit and record the display gate
as unavailable; do not substitute Wayland or claim success.

## Artifacts and Notes

Keep only concise ignored JSON/transcripts during the run. Never commit a
package, extracted filesystem, PDF, credential, screenshot, or machine-local
absolute path. Record package version, selected display mode, GUI status,
cleanup result, and any nonblocking build warnings in the owning plans.

## Interfaces and Dependencies

Use `subprocess.run`/`Popen` with explicit environment dictionaries and bounded
timeouts. The installed wrapper remains `/usr/bin/foliaseal`; no new runtime
dependency is permitted. The supported display realization is X11 via Qt's
`xcb` platform plugin. The audit must preserve
`classify_gui_result(returncode, output, started=...)` semantics and the
existing exact `SingleInstanceUnavailable` allowlist.

Revision note: 2026-08-16 / Codex: created after the current-plan audit found
that source-tree X11 evidence was complete but the packaged GUI probe was still
hardcoded to offscreen; this plan adds only an opt-in supported-X11 release
evidence path.

Revision note: 2026-08-16 / Codex: the first display-backed build exposed the
hardcoded platform overwrite and missing runtime SVGs. The plan was expanded
only to correct those package assets and validate the resulting installed GUI.
