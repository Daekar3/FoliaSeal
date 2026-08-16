# Complete the parent signing workflow on Cinnamon/X11

## Purpose

The repository's parent compliance plan names `scripts/live_gui_parent_audit.py` as the canonical
display-backed semantic audit for the shared signing workflow. The earlier sandbox boundary blocked
that runner before Qt window creation; the current Mint 22.3 Cinnamon/X11 session is reachable.
This slice runs the existing audit against the live source-tree workflow and records whether the full
workflow is demonstrably healthy on X11. Any narrowly reproducible product defect exposed by the
audit is corrected and covered rather than waived.

## Scope and explicit exclusions

In scope:

- real X11 semantic GUI audit of the parent workflow;
- screenshots and `audit.json` inspection for setup, placement, readiness, signing, reopen, and
  second-signature checkpoints;
- exact temporary-root, process, window, and generated-artifact cleanup;
- reconciliation of the manual-harness and parent ExecPlans with the result.

Out of scope:

- Wayland, intentionally deferred until Mint treats it as a first-class supported session;
- screen-reader, high-contrast, physical-DPI, and multi-monitor certification;
- packaged GUI launch, privileged host package installation, and final release closure;
- targeted source/harness corrections required to represent the current production Qt surface and
  repair reproducible defects exposed by this audit; no unrelated feature work.

## Progress

- [x] (2026-08-16) Explorer review confirmed this is the parent plan's canonical semantic GUI driver
  and identified its owned temporary stores, screenshot/report outputs, and cleanup behavior.
- [x] (2026-08-16) Ran the complete audit under the active Cinnamon/X11 session. The report passed
  with 19 checkpoints and `output_signature_count=2`; representative screenshots and both retained
  signed outputs were inspected before cleanup.
- [x] (2026-08-16) Corrected stale audit assumptions and one reproducible product-state defect,
  then reran focused tests and the full audit successfully.
- [x] (2026-08-16) Reconciled the parent/manual/release plans and architecture notes, completed the
  post-implementation compliance review, validated the repository, and committed the slice.
- [x] (2026-08-16) Re-ran the canonical audit from the current checkout on Cinnamon/X11. All 19
  checkpoints passed through placement, readiness, signing, reopen, and a second locally verified
  signature (`output_signature_count=2`); representative screenshots were inspected and the exact
  audit root, generated outputs, windows, and child processes were removed. This refreshes source-
  tree semantic workflow evidence only and does not close human accessibility, packaged/privileged,
  final-release, or deferred Wayland gates.

## Concrete execution

Run from `/home/daekar/FoliaSeal` with a dedicated root:

```bash
audit_root=$(mktemp -d /tmp/foliaseal-parent-audit-XXXXXX)
DISPLAY=:0 XAUTHORITY=/home/daekar/.Xauthority XDG_RUNTIME_DIR=/run/user/1000 QT_QPA_PLATFORM=xcb \
  timeout --foreground 300s \
  .venv/bin/python scripts/live_gui_parent_audit.py \
  --artifacts-dir "$audit_root/live-gui"
audit_rc=$?
```

Before deleting the exact root, require `audit_rc=0`, `live-gui/audit.json` status `passed`, two
verified output signatures, all expected checkpoints, and readable signed-output evidence. Inspect
representative screenshots with `view_image`. The runner's own `finally` cleanup is authoritative;
terminate only an owned process/window if recovery is needed. Do not use broad `pkill` patterns.

The final successful run used disposable root `/tmp/foliaseal-parent-audit-skr5WY`, removed after
inspection. Its report recorded `status=passed`, all 19 checkpoints, and two locally verified
signatures. The first retained output contained one signature and the second contained two; both
were readable before the root was removed.

## Acceptance

- The audit exits `0` and reports `status=passed`.
- The report records the expected setup, placement, readiness, signing, reopen, and second-signature
  checkpoints, with `output_signature_count=2` and no unexpected error.
- Screenshots show the real X11 application states named by the report.
- The exact audit root is removed after inspection, with no owned FoliaSeal/PySide6/pytest process,
  dialog, or window remaining.
- Wayland and the remaining human accessibility/package/release gates remain explicitly open.

## Friction and recovery

The canonical script creates a frame directly, so an unrelated existing FoliaSeal owner should not
interfere. If it fails, preserve the report until the failure is classified; a reproducible source
failure becomes a targeted child plan, while a display/session failure remains an explicit external
blocker. Never waive a product assertion as environmental without evidence.

### Friction recorded and resolved in this slice

- The shell exposes the concrete `SigningWorkspaceWidget` behind the opaque workspace view; the
  audit now uses that explicit internal semantic seam and its mounted QWidget root.
- Current helper copy is state-specific (`Select a certificate configuration...` and `No saved
  presets yet...`), so the audit accepts the governing current-state variants rather than retired
  static copy.
- Certificate creation requires Full name and Confirm password, and its nested information box is
  handled through the audit's injected message-box port.
- The production confirmation uses a consequence-labeled `Sign and save` button rather than a
  standard QMessageBox `Yes`; the audit asserts and clicks that semantic button.
- Signing is asynchronous. The audit polls the real shell transaction until both the output file and
  `last_signing_result` are present, preventing a premature signed checkpoint.
- A real state defect was exposed: confirmation synchronization called `apply_changes()` and
  cleared an unchanged selected preset, producing `Current-document custom setup` in the summary.
  The coordinator now preserves the selected preset when the visible draft still exactly matches
  the workflow and clears it only after an actual appearance/placement edit. Existing edit
  invalidation tests remain green.
- Generic top-level `close()` cleanup could raise the product discard prompt after a successful dirty
  workflow. The runner now explicitly discards the audit-owned workspace draft before closing
  windows, so successful and failed runs cannot leave a dialog behind.

These changes are limited to the canonical semantic audit and the reproducible state defect it
found; they do not claim human accessibility, packaged installation, privileged package, or Wayland
acceptance.

Validation after the final rerun: focused coordinator/shell tests `150 passed`; full regression
`1537 passed, 20 skipped, 1 warning`; Ruff, compileall, and `git diff --check` passed. The final
X11 run exited `0`, reported `status=passed` with 19 checkpoints and two signatures, and its exact
temporary root was removed with no audit-owned process or dialog remaining.

Revision note: 2026-08-16 / Codex
Created after the bounded X11 transport/harness slice proved real desktop access and the explorer
confirmed the parent semantic audit as the next canonical acceptance path.
