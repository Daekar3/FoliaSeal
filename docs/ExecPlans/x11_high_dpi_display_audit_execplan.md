# Verify the supported X11 frame at high Qt scale

This ExecPlan is a living document and must be maintained in accordance with
`/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The existing Cinnamon/X11 audit proves the normal 1100x700 no-document frame,
native F1 delivery, and semantic Qt metadata at device-pixel ratio 1.0. This
evidence child repeats that owned audit with Qt's scale factor set to 2.0 and
inspects the exact Qt-owned screenshot. The user-visible result is evidence
that the fixed minimum frame, menu row, empty-state message, and primary Open
and Library controls remain visible and unclipped when Qt renders at high
scale on the supported X11 desktop.

This is display geometry evidence, not a claim about physical readability,
screen-reader speech, high-contrast perception, or general human usability.
At 2x the desktop exposes only 960x540 available logical geometry while the
product minimum is 1100x700, so this run does not prove that the whole frame
fits on the monitor or that geometry restoration is usable. Wayland is
intentionally excluded for Mint 22.3.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/x11_display_accessibility_audit_execplan.md` supplies the
  real Cinnamon/X11 window, XTest F1 path, timeout, and cleanup boundary.
- [x] `docs/ExecPlans/x11_visual_layout_audit_execplan.md` supplies the exact
  `QWidget.grab()` screenshot and geometry report.
- [x] `docs/UI_SPEC.md` §§12–13 require minimum geometry, scale handling, and
  accessible primary controls.
- [x] Wayland is deferred by explicit user direction.

## Progress

- [x] (2026-08-16) Ran the existing audit with
  `QT_SCALE_FACTOR=2 QT_AUTO_SCREEN_SCALE_FACTOR=0` on `DISPLAY=:0` using
  `QT_QPA_PLATFORM=xcb`; the report passed with DPR 2.0, two screens, a
  1100x700 logical window, native F1, and owned cleanup. The desktop's
  available logical geometry was 960x540, so monitor fit remains open.
- [x] (2026-08-16) Retained a disposable screenshot long enough to inspect it
  directly. The image showed the complete File/Edit/View/Signing/Settings/Help
  menu row, no-document message, and full-width Open and Manage Signature
  Library controls without clipping.
- [x] (2026-08-16) Removed the exact audit root and confirmed no matching
  FoliaSeal process or temporary root remains.
- [x] (2026-08-16) Reconciled the accessibility, release, parent, and
  architecture status records and prepared this plan for the focused
  evidence/status commit.

## Surprises & Discoveries

- Observation: at 2x Qt scale the screen reports 960x540 available logical
  geometry while the application retains its 1100x700 minimum logical frame.
  Evidence: the audit report records DPR `2.0`, window size `[1100, 700]`, and
  screen geometry `960x540`; the owned screenshot still contains the complete
  primary surface.
- Observation: Qt's `text_scaling_factor` context remains `1.0`; the test
  changes device-pixel scaling, not the desktop's font accessibility setting.
  Evidence: the report context records the existing Cinnamon setting and the
  explicit `QT_SCALE_FACTOR=2` environment.

## Decision Log

- Decision: use the existing audit runner with an environment-only scale
  override rather than adding a product setting or a second GUI bootstrap.
  Rationale: the runner already owns the frame, native input, screenshot, and
  teardown; the evidence must not alter product behavior.
  Date/Author: 2026-08-16 / Codex.
- Decision: classify the run as high-DPI geometry evidence only.
  Rationale: a screenshot and DPR do not prove physical-DPI readability,
  contrast perception, assistive-technology speech, or human workflow quality.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The high-DPI X11 audit passed for widget-content rendering. At DPR 2.0, the
report retained the 1100x700 logical frame, two-monitor context, accessible
primary controls, and native F1/Help behavior; direct inspection of the
Qt-owned screenshot showed the complete menu row, empty-state message, and
both primary controls without internal clipping. Because the available logical
desktop geometry was only 960x540, this does not prove full monitor fit or
geometry-restoration usability. The exact temporary root and owned window were
removed.

This closes concrete high-DPI geometry evidence only. Human screen-reader,
high-contrast, physical-monitor readability, privileged installation, final
release, and Wayland acceptance remain separate gates.

## Context and Orientation

`scripts/live_gui_accessibility_audit.py` builds a uniquely titled production
Qt frame, activates only that window through the existing X11 path, sends F1,
and writes JSON plus an optional exact-widget screenshot under a caller-owned
temporary root. `QT_SCALE_FACTOR=2` tells Qt to render at two device pixels
per logical pixel; it does not change FoliaSeal's 1100x700 logical minimum.

The existing visual plan records normal-scale evidence. This child adds only
the high-scale observation and must not modify `src/foliaseal`, schemas, CLI
contracts, package payload, or Wayland behavior.

## Change Slice

Primary change class: evidence refresh and status documentation. Generated
JSON/PNG files are temporary and forbidden from the commit. No runtime source
or product behavior changes are allowed in this slice.

## Plan of Work

Run the existing audit twice if necessary: first with an owned temporary root
to obtain the report, then once with the root retained long enough to inspect
`frame.png`. Confirm DPR, logical window size, screen count, native F1, and
cleanup in `audit.json`. Inspect the image with the local image viewer and
remove only the exact temporary root. Update the owning plans and architecture
history with measurements and explicit non-claims, then run static checks and
commit the evidence/status change.

## Milestones

The first milestone is a passing 2x X11 report. The second is direct screenshot
inspection and exact-root cleanup. The final milestone is documentation
reconciliation, review, validation, and a clean commit.

## Concrete Steps

Run from `/home/daekar/FoliaSeal` in the supported Cinnamon/X11 session:

    audit_root=$(mktemp -d /tmp/foliaseal-x11-dpi-XXXXXX)
    DISPLAY=:0 QT_QPA_PLATFORM=xcb QT_SCALE_FACTOR=2 QT_AUTO_SCREEN_SCALE_FACTOR=0 \
      .venv/bin/python scripts/live_gui_accessibility_audit.py \
      --artifacts-dir "$audit_root/report" --capture-screenshot --timeout-seconds 15
    cat "$audit_root/report/audit.json"
    test -s "$audit_root/report/frame.png"
    rm -rf -- "$audit_root"
    test ! -e "$audit_root"

Expected evidence includes `status: "passed"`, `qt_platform: "xcb"`,
`device_pixel_ratio: 2.0`, `window_size: [1100, 700]`, two screens, successful
native F1, and `cleanup.passed: true`. The screenshot must be inspected before
the root is removed.

## Validation and Acceptance

Acceptance is behavioral evidence: the real X11 audit exits zero; the report
records DPR 2.0, the logical frame, two-monitor context, native F1, and
successful cleanup; and the exact Qt-owned screenshot visibly contains the
complete menu, message, Open button, and Library button without internal
clipping. The 960x540 available logical desktop geometry keeps whole-window
monitor fit and restoration open. Run the existing focused accessibility tests,
Ruff, compilation, and diff checks. Do not convert this evidence into a
screen-reader, contrast, physical-DPI, or subjective usability claim.

## Idempotence and Recovery

The audit is safe to repeat with a new temporary root. If X11 or Qt scaling
fails, preserve the report for diagnosis, close only the audit-owned frame,
remove only its exact root, and record the external limitation. Never use a
broad process kill or close unrelated windows. Never run this plan under
Wayland.

## Artifacts and Notes

Only temporary `audit.json` and `frame.png` are allowed. The inspected image is
not committed; committed notes contain measurements and observations only.

## Interfaces and Dependencies

This plan uses the existing PySide6/xcb audit runner, X11 `wmctrl`/XTest
activation path, and Qt `QWidget.grab()` capture. It adds no dependency and no
new public interface.

Revision note: 2026-08-16 / Codex — created and completed after the 2x X11
report and exact screenshot inspection passed.
