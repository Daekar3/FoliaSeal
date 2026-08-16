# Add a bounded X11 AT-SPI accessibility inspection

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an evidence child of
`docs/ExecPlans/x11_display_accessibility_audit_execplan.md`,
`docs/ExecPlans/ui_accessibility_acceptance_execplan.md`, and
`docs/ExecPlans/ui_product_support_and_release_execplan.md`.

## Purpose / Big Picture

The existing X11 audit proves Qt semantic metadata and native F1 delivery, but
it does not prove that an assistive-technology client can discover the
production window through the desktop accessibility bridge. This slice adds an
optional, read-only AT-SPI inspection performed by the host system Python while
the existing production Qt audit window is alive.

The user-visible evidence gain is precise: a report can show that the owned
FoliaSeal process/window is exposed through AT-SPI with the expected name,
roles, state bits, action names, and screen extents. This is stronger than
recording that Orca is installed, but it is not a claim about Orca speech,
contrast perception, physical-DPI readability, monitor moves, or human
usability.

## Child ExecPlan Dependencies

- [x] `scripts/live_gui_accessibility_audit.py` owns the production Qt frame,
  X11 activation, native F1 path, timeout, and cleanup.
- [x] Host `/usr/bin/python3` provides `gi` and `pyatspi`; the project
  venv deliberately does not require them.
- [x] Current session is Cinnamon/X11; Wayland remains deferred for Mint 22.3.

## Progress

- [x] (2026-08-16) Explorer feasibility review confirmed host AT-SPI APIs and
  a process/window-owned traversal design.
- [x] (2026-08-16) Added the optional host-Python probe and integrated its
  bounded JSON result into the existing audit without adding a runtime product
  dependency. A session-bus preflight avoids creating AT-SPI sockets when the
  accessibility bus launcher is absent.
- [x] (2026-08-16) Ran and inspected the real X11 report: native F1 and owned
  cleanup passed, while the initial AT-SPI preflight incorrectly classified
  the dedicated registry as absent from the user session bus. Status docs were
  reconciled, reviewed GO, and committed in the focused AT-SPI slice; the
  corrected follow-up is recorded below.
- [x] (2026-08-16) Corrected the AT-SPI2 preflight after inspecting the live
  Cinnamon bus. The user session exposes `org.a11y.Bus`; the dedicated AT-SPI
  address is returned by `GetAddress` and must be placed in `AT_SPI_BUS_ADDRESS`
  before importing host `pyatspi`. Focused probe tests now cover launcher
  detection, address resolution, registry failures, and owned-frame traversal.
  A fresh display-backed run reached the dedicated bus but timed out while
  discovering the owned Qt frame and emitted Qt's
  `GetApplicationBusAddress` warning; this supersedes the earlier false
  "registry absent" classification.

## Surprises & Discoveries

- Observation (superseded): the first implementation treated the absence of
  `org.a11y.atspi.Registry` on the user session bus as unavailable. AT-SPI2
  publishes `org.a11y.Bus` there and exposes the registry on its dedicated bus.
  The corrected helper resolves that address before importing `pyatspi`; the
  current Qt frame still does not become discoverable within the bounded probe.
- Observation: AT-SPI warnings may appear while the registry discovers the
  session socket. The probe must classify an unavailable registry as an
  evidence limitation, not as a product failure.
- Observation: earlier host-side discovery attempts left empty
  `/run/user/1000/at-spi2-*` IPC directories. Their ownership cannot be
  proven from the repository, so they were not bulk-deleted; any cleanup of
  shared desktop accessibility state requires an explicit host-owner/HITL
  decision.
- Observation: selecting the audit application by process ID and the frame by
  exact title prevents traversal or mutation of unrelated desktop windows.

## Decision Log

- Decision: keep AT-SPI in an audit-only host helper and do not add it to
  FoliaSeal dependencies.
  Rationale: the binding is an environment/tooling boundary, not a product
  runtime requirement; the venv and packaged app must remain unchanged.
  Date/Author: 2026-08-16 / Codex.
- Decision: make the probe optional and read-only.
  Rationale: ordinary audits must retain their existing behavior, and an
  unavailable accessibility bus must not cause a false product regression.
  Date/Author: 2026-08-16 / Codex.
- Decision: select only the exact audit PID/title and record names, roles,
  states, actions, and extents.
  Rationale: process/window ownership bounds the evidence and avoids focus,
  activation, or mutation of unrelated desktop clients.
  Date/Author: 2026-08-16 / Codex.
- Decision: report AT-SPI inspection separately from human screen-reader
  acceptance.
  Rationale: accessibility-tree exposure is necessary evidence but cannot
  demonstrate speech announcements, contrast, physical readability, or
  subjective workflow quality.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The optional audit run passes native X11 F1 and cleanup. The corrected helper
now detects the session-bus launcher and resolves the dedicated AT-SPI address,
but the owned Qt frame is not discoverable before the bounded timeout and Qt
reports that its application interface lacks `GetApplicationBusAddress`; no
accessible-tree claim is made. Focused probe/audit tests, Ruff, compile, and
diff checks pass. The human screen-reader, high-contrast, physical-DPI,
monitor, privileged, final release, and Wayland gates remain open or deferred.

## Context and Orientation

The production audit constructs `QtAppFrameAdapter` through temporary stores,
shows a uniquely titled `QMainWindow`, records semantic Qt metadata, activates
only that window through `wmctrl`, sends native F1 through XTest, and closes
all owned objects. The new helper will run as host `/usr/bin/python3`, because
`pyatspi` is not a project dependency. It receives the audit process ID and
exact title, traverses `pyatspi.Registry.getDesktop(0)`, selects the
application whose `get_process_id()` matches, and then selects the exact
frame. It must never call focus, activation, action invocation, or mutation
APIs.

The helper should read `Accessible.getRoleName()`, `getState()`,
`queryAction()`, `queryComponent().get_extents(...)`, child names/roles, and
process ID. The parent audit should write a bounded JSON object under the
caller-owned ignored artifact directory and preserve the existing report
failure/cleanup semantics.

## Change Slice

Primary change class: evidence refresh. Allowed files are the existing audit
runner, a small host-only probe helper, this plan, the X11/accessibility/release
status plans, and `docs/ARCHITECTURE.md`. No Qt product behavior, schema,
CLI, package payload, runtime dependency, Wayland code, or subjective
acceptance claim may be mixed in. Generated JSON is temporary and never
committed.

## Plan of Work

1. Add `scripts/x11_atspi_probe.py` as a bounded host-Python helper with
   explicit PID/title arguments, a timeout, and JSON output. It must fail
   closed for an unavailable registry, select only the owned application/frame,
   and return a classified unavailable result rather than scanning or touching
   unrelated windows.
2. Extend `scripts/live_gui_accessibility_audit.py` with an opt-in
   `--probe-atspi` flag. After the native F1/help check, invoke the helper while
   the owned frame remains alive, parse its bounded JSON, and include it under
   an `atspi` report key before marking the report passed. This ordering keeps
   an unavailable or slow bridge from perturbing keyboard evidence. Keep the
   normal audit path unchanged.
3. Run the combined audit on `DISPLAY=:0 QT_QPA_PLATFORM=xcb` using host
   Python for the helper. Inspect the report and verify the accessible frame,
   primary controls, names/roles, states/actions/extents, and cleanup. If the
   bus is unavailable, record that limitation and do not claim AT-SPI evidence.
   4. Update the five status/architecture documents with exact evidence and
   explicit human limitations. Obtain independent compliance and
   documentation/architecture review, run focused/full validation, commit,
   and verify no process/window/root remains.

## Milestones

### Milestone 1: bounded helper

The helper can inspect exactly one owned process/window and return bounded JSON
or an explicit unavailable classification without mutating the desktop.

### Milestone 2: integrated X11 evidence

The opt-in production audit records AT-SPI evidence alongside existing Qt/X11
evidence while default behavior and cleanup remain unchanged.

### Milestone 3: closeout

The report is inspected, plans/docs are reconciled, tests/reviews pass, the
slice is committed, and all owned resources are gone.

## Concrete Steps

Run from `/home/daekar/FoliaSeal` in an escalated host X11 session:

    audit_root=$(mktemp -d /tmp/foliaseal-x11-atspi-XXXXXX)
    DISPLAY=:0 QT_QPA_PLATFORM=xcb .venv/bin/python scripts/live_gui_accessibility_audit.py \
      --artifacts-dir "$audit_root/report" --probe-atspi --timeout-seconds 15
    cat "$audit_root/report/audit.json"
    rm -rf "$audit_root"
    test ! -e "$audit_root"

The helper uses `/usr/bin/python3` and must report either an owned frame with
accessible evidence or `status=unavailable` plus a reason. The parent report
must still prove native F1 and cleanup. Never run this under Wayland or against
the user's configuration directory.

## Validation and Acceptance

Acceptance requires:

- ordinary audits without `--probe-atspi` retain their existing report and
  behavior;
- the opt-in probe selects only the audit PID and exact title;
- the report records AT-SPI frame/application identity, names, roles, state
  bits, action names, and extents when the registry is available;
- no focus, activation, action invocation, or unrelated window mutation occurs;
- native F1, existing semantic Qt checks, timeout, and cleanup remain green;
- focused tests, full suite, Ruff, compile, and diff checks pass;
- docs state clearly that AT-SPI exposure is not screen-reader speech or human
  visual acceptance; Wayland remains deferred.

## Idempotence and Recovery

The helper is read-only and safe to retry. If registry discovery fails, return
an unavailable result and let the parent audit continue; never broaden the
window search or kill unrelated processes. The parent owns the temporary
stores/window and removes only its exact artifact root. Do not start Orca or
close any unrelated desktop window.

## Artifacts and Notes

Only temporary `audit.json` and any helper JSON are permitted. Record concise
evidence, not machine-local absolute paths, screenshots, credentials, or PDFs.

## Interfaces and Dependencies

`scripts/x11_atspi_probe.py` uses only host `pyatspi` and standard library
interfaces. The production runner invokes it as a subprocess only when
`--probe-atspi` is supplied. No import of `pyatspi` is added to
`src/foliaseal` or the project dependency set.

Revision note: 2026-08-16 / Codex: created after host Python exposed
`pyatspi`; the helper resolves the dedicated bus address from `org.a11y.Bus` and
records a bounded unavailable classification if the owned Qt frame cannot be
discovered, without claiming tree or speech evidence.
