# Capture supported-X11 visual and geometry evidence

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is a documentation/evidence child
of `docs/ExecPlans/x11_display_accessibility_audit_execplan.md`,
`docs/ExecPlans/ui_accessibility_acceptance_execplan.md`, and
`docs/ExecPlans/ui_product_support_and_release_execplan.md`.

## Purpose / Big Picture

The existing X11 audit proves native F1 delivery and semantic widget metadata,
but it does not preserve a view of the real no-document frame or record the
display geometry that determines whether the minimum 1100x700 layout is usable.
This slice adds an opt-in screenshot and geometry report to the existing audit.
The screenshot is stored only under a caller-owned temporary directory and is
inspected during the run; no image is committed. The result provides concrete
evidence about frame size, available monitor space, device-pixel ratio, logical
DPI, theme/scaling context, and the visible primary controls.

This is not a screen-reader, high-contrast, or subjective human-usability
certification. Orca availability is context only; speech output, focus
announcements, high-contrast legibility, physical readability, monitor moves,
and final visual approval remain HITL gates.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/x11_display_accessibility_audit_execplan.md` supplies the
  real Cinnamon/X11 frame, native F1 path, timeout, and cleanup boundary.
- [x] `docs/UI_SPEC.md` §12-13 defines minimum geometry, scaling, theme, and
  accessibility expectations.
- [x] Current supported session is Cinnamon/X11; Wayland is deferred for Mint
  22.3 by explicit user direction.

## Progress

- [x] (2026-08-16) Explorer audit identified the existing frame and public
  geometry/screenshot seams; AT-SPI is not a reliable venv audit dependency.
- [x] (2026-08-16) Added opt-in geometry and screenshot capture to the audit runner without
  changing default evidence behavior or runtime product code.
- [x] (2026-08-16) Ran the real display audit, inspected the Qt-captured client
  frame, and recorded concrete observations without claiming subjective approval.
- [x] (2026-08-16) Reconciled the accessibility/release/parent/architecture
  plans and obtained independent compliance/documentation reviews; the bounded
  evidence slice is ready for commit.

## Surprises & Discoveries

- Observation: the venv cannot reliably import AT-SPI bindings, while Orca is
  installed. Evidence: the display environment reports Orca 46.1, but the
  project venv lacks a dependable `pyatspi`/GI path.
- Observation: the existing no-document frame already exposes a minimum-size
  contract and named Open/Library controls. Evidence:
  `tests/integration/test_accessibility_acceptance.py` and
  `QtAppFrameAdapter.create_frame`.
- Observation: the first display screenshot helper (`gnome-screenshot -w`)
  returned the audit title bar over the underlying editor, so it was rejected
  as invalid evidence. Qt `QWidget.grab()` captured the owned client widget
  deterministically on the rerun. Evidence: the inspected `frame.png` showed
  the menu, no-document message, and both primary buttons on the 1100x700
  client frame.

## Decision Log

- Decision: extend the existing audit with an opt-in `--capture-screenshot`
  mode instead of adding a second GUI bootstrap path.
  Rationale: the existing runner already owns temporary stores, native input,
  timeout, and cleanup; a second path would create divergent evidence.
  Date/Author: 2026-08-16 / Codex.
- Decision: capture geometry and screenshot only after the audit window is
  shown and activated, and store the PNG under the caller's artifact directory.
  Rationale: a hidden/offscreen widget would not prove display-backed layout;
  repository artifacts must never contain machine-local screenshots.
  Date/Author: 2026-08-16 / Codex.
- Decision: report measurements and observed topology, not a pass judgment on
  visual accessibility.
  Rationale: screenshots and DPI metadata inform human review but cannot prove
  screen-reader speech, contrast perception, or subjective usability.
  Date/Author: 2026-08-16 / Codex.
- Decision: prefer `QWidget.grab()` and retain `QScreen.grabWindow()` only as a
  fallback; do not use a desktop screenshot helper that can select another
  active client.
  Rationale: the audit owns the Qt widget and must capture that exact surface;
  the first helper-produced image was demonstrably contaminated by the
  developer desktop.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The audit passed on `DISPLAY=:0` with `QT_QPA_PLATFORM=xcb` and produced an
inspected Qt client screenshot under the disposable report root. The owned
client frame was 1100x700 at x=42,y=32 on primary screen `DP-4`; the menu bar
was 1100x20, the central widget 1100x680, and the named Open/Library buttons
were full-width 1082x23 rows at y=30 and y=59. The screen reported 1920x1080
available geometry, 2 screens, DPR 1.0, and 96 DPI in both axes. The image
showed the File/Edit/View/Signing/Settings/Help menu row, the no-document
message, and both primary controls without clipping. Native X11 F1 and direct
Help QAction checks remained green, and cleanup reported no owned window,
child process, or temporary root. This is concrete source-tree X11 geometry
and visual evidence, not subjective accessibility approval: screen-reader
speech, high-contrast, physical-DPI interpretation, monitor moves, packaged
GUI, privileged installation, final release, and Wayland remain open or
deferred.

The bounded evidence slice was committed as `063bd5618` (`test: capture X11
visual layout evidence`) after independent compliance and documentation
reviews; the post-commit worktree was clean.

## Context and Orientation

`scripts/live_gui_accessibility_audit.py` builds the production no-document
`QtAppFrameAdapter` with temporary stores, shows a uniquely titled window,
records semantic controls, and sends native F1 through XTest. PySide6's
`QWidget.grab()`/`QScreen.grabWindow()` captures the visible frame; `QScreen`
also supplies available monitor geometry, device-pixel ratio, logical DPI, and
screen name. The runner already writes ignored JSON under an explicit artifact
directory and closes all owned widgets in `finally` blocks.

## Change Slice

Primary change class: evidence refresh. Allowed files are the audit runner,
this plan, and status/architecture documentation. Generated PNG/JSON files are
temporary and forbidden from the commit. No product Qt behavior, schema, CLI
contract, package payload, or Wayland code may change.

## Plan of Work

1. Add an optional screenshot flag and record frame geometry, screen available
   geometry, monitor count/name, device-pixel ratio, logical DPI, and the
   geometry of named primary buttons/menu bar/central widget when available.
2. Capture the audit-owned window into `<artifacts-dir>/frame.png` only when
   requested. Keep PNG failure explicit, but do not make ordinary headless
   audits depend on it.
3. Run the audit on `DISPLAY=:0 QT_QPA_PLATFORM=xcb`, inspect the PNG with the
   local image viewer, and write only concrete observations into this plan.
4. Run existing accessibility tests, lint/compile checks, reconcile status
   documents, obtain independent review, and commit the bounded evidence.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    audit_root=$(mktemp -d /tmp/foliaseal-x11-visual-XXXXXX)
    DISPLAY=:0 QT_QPA_PLATFORM=xcb .venv/bin/python scripts/live_gui_accessibility_audit.py \
      --artifacts-dir "$audit_root/report" --capture-screenshot --timeout-seconds 15
    cat "$audit_root/report/audit.json"
    test -s "$audit_root/report/frame.png"
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Inspect `frame.png` before removing the root. The report must contain actual
geometry and a screenshot path under the artifact directory; no absolute
machine path may be copied into committed documentation.

## Validation and Acceptance

Acceptance requires the existing native-X11 semantic audit to pass, geometry
and screenshot capture to succeed on the supported display, the screenshot to
show the complete no-document frame at the 1100x700 minimum without an obvious
clipped primary control, and all owned windows/processes/roots to be cleaned.
The existing offscreen accessibility test and full suite must remain green.
This evidence does not close screen-reader speech, high contrast, physical-DPI
readability, monitor-move behavior, final human workflow, privileged install,
final release, or Wayland.

## Idempotence and Recovery

Use a unique temporary artifact root and remove it after inspection. If Qt
cannot connect to X11 or screenshot capture fails, retain the error in the
plan, clean the owned frame/root, and do not claim visual evidence. Never close
unrelated desktop windows or delete a user configuration directory.

## Artifacts and Notes

Only temporary `audit.json` and `frame.png` are allowed. Do not commit the PNG,
PDFs, credentials, or machine-local display paths. Record concise measurements
and observations, not a screenshot hash or subjective approval label.

## Interfaces and Dependencies

Use PySide6 `QScreen`, `QWidget.geometry()`, `QWidget.grab()`, and existing
public frame/widget properties. No new runtime dependency is permitted. The
supported display realization is Qt `xcb` on Cinnamon/X11.

Revision note: 2026-08-16 / Codex: created after the packaged-X11 slice and
explorer review identified screenshot/geometry as the strongest remaining local
evidence slice while AT-SPI and subjective accessibility remain HITL.

Revision note: 2026-08-16 / Codex: completed the X11 geometry/screenshot run;
rejected the desktop-helper capture and switched to exact Qt widget capture.
