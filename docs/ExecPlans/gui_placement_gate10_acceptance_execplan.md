# Verify repaired placement behavior in the packaged X11 GUI


This is a living ExecPlan maintained under /home/daekar/.codex/skills/write-execplan/PLANS.md. Update Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective during execution.

## Purpose / Big Picture


Prove the repaired controls work as rendered and through normal desktop event delivery, then give the user a short installed-app retest. This closes Gate 2 item 10 only after observed results, preserving the already reported successful signing gates.

## Child ExecPlan Dependencies


This is the final child of gui_placement_gate10_recovery_parent_execplan.md. `gui_placement_mode_focus_cancel_execplan.md`, `gui_placement_history_recovery_execplan.md`, and `gui_placement_keyboard_repeat_performance_execplan.md` must pass their behavior tests before package acceptance.

## Current authoritative evidence (2026-09-08)

Package `f800e6c...`, built from commit `8903512c9`, is the authoritative installed artifact for
this plan. The source validation is 199 focused tests and 1660 full-suite tests with 20 skipped and
one existing warning. The installed Cinnamon/X11 HITL retest passed held movement, Ctrl resize,
Ctrl+Shift accelerated resize, responsiveness, one-step Undo/Redo, and sustained CPU/disk behavior.
The package `882198...`, payload `eed669...`, commit `c752c06...`, and their pending-install claims
below are superseded historical evidence from before the final autorepeat repair.

## Progress


- [x] (2026-09-07) Recorded user failures and inspected relevant source paths; authored plan.
- [x] (2026-09-07) Incorporated three-agent review corrections and strengthened composed-event, history and package acceptance coverage.
- [x] (2026-09-07) Behavior children completed their source and composed regression work; authoritative validation is 199 focused tests and 1660 full-suite tests with 20 skips and one existing warning.
- [x] (2026-09-07, superseded historical evidence) Built a pre-final-repair package from the worktree at `/tmp/foliaseal-gate10-mAkhdQ/dist/foliaseal_0.1.0_amd64.deb`; SHA-256 was `882198337ac2e454a0e1f83b187d389f4d1203e82e46b311a41cd126a23a7a21`, and its payload included `eed669...`. Offscreen and escalated display-backed package audits passed. This artifact is superseded by package `f800e6c...` from commit `8903512c9`.
- [x] (2026-09-07, superseded historical evidence) Installed the pre-final-repair package and confirmed its then-current installed-byte identity. That installation is not the authoritative current artifact; use package `f800e6c...` from commit `8903512c9` for current acceptance.
- [x] (2026-09-07) Added the autorepeat performance child after the installed human retest reported significant CPU spin-up while holding adjustment keys during resize; package acceptance must wait for its source tests and a fresh package.
- [x] (2026-09-07) The autorepeat implementation and focused real Qt event tests pass. The previously installed package predated this repair; the final package/install and held-key CPU observation are recorded below.
- [x] (2026-09-07, superseded historical status) Compliance remediation is covered by typed-session, explicit synthetic-release, cancellation/failure, key-boundary, action/page-boundary, direct viewer navigation, mounted configured-PKCS12 counter, and real Qt Ctrl/Ctrl+Shift resize tests. Targeted validation is 199 passed; the full suite is 1660 passed with 20 skips and one existing warning. At that point a fresh package rebuild/install and rendered Cinnamon/X11 human observation remained pending; the current evidence block records their completion.
- [x] (2026-09-08) Completed rendered Cinnamon/X11 acceptance against installed package `f800e6c...` from commit `8903512c9`: held movement, Ctrl resize, Ctrl+Shift accelerated resize, responsiveness, one-step Undo/Redo, and sustained CPU/disk behavior all passed.
- [x] (2026-09-08) Reconciled the family and recorded Gate 2 item 10 as PASS.

## Surprises & Discoveries


The September 7 failures occurred in the installed application despite prior lower-level coverage. Source-only tests could not establish that the installed build receives focus or displays the right mode. The final installed Cinnamon/X11 retest below closes that evidence gap. The earlier gui_placement_interaction_stability_execplan.md remains historical evidence and is not a competing implementation plan.

Acceptance evidence (2026-09-07, superseded historical evidence): the focused/composed placement suite passed 199 tests and the full repository suite passed 1660 tests with 20 skips and one existing warning. The pre-final-repair source HEAD was `c752c06...` and its package hash was `882198...`; the package audit passed, but the installed package predated the final autorepeat repair. The configured disposable PKCS#12 counter test already proved five autorepeat Ctrl-resize events perform zero certificate-readiness reads and physical release performs four bounded reads through the current shell projection. The current installed result is recorded in the authoritative evidence block above.

Human autorepeat finding (2026-09-07): the installed retest passed individual Arrow behavior but reported significant CPU spin-up when holding adjustment keys during resize. The typed batching repair and final installed retest closed this finding: held movement and Ctrl/Ctrl+Shift resize remained responsive, one held sequence produced one Undo/Redo step, and no unacceptable sustained CPU/disk behavior occurred.

The final installed acceptance used package `f800e6c...` built from commit `8903512c9` on Cinnamon/X11. The user confirmed held Arrow movement, Ctrl resize, Ctrl+Shift accelerated resize, one-step Undo/Redo, responsive interaction, and no unacceptable sustained CPU/disk activity. This is the authoritative HITL result for Gate 2 item 10.

Governing-document review (2026-09-07): `docs/SPEC.md`, `docs/SCHEMAS.md`, and `docs/UI_SPEC.md`
remain consistent with the repaired source contract. No specification or schema edit is needed; this
child tracks only the missing installed-byte identity and rendered Cinnamon/X11 evidence.

## Decision Log


Decision (2026-09-07): Accept source-supported review findings while rejecting overstated startup and replay claims. Rationale: composition initializes Pan, and synchronization to an identical replay target does not itself clear history. Author: Codex.

Decision (2026-09-07): Repair the existing placement contract without redesigning the signing workflow. Rationale: reported failures contradict docs/UI_SPEC.md and require focused corrections. Author: Codex.

Decision (2026-09-07): Separate behavior repair from package evidence and human acceptance. Rationale: prior isolated tests did not predict installed behavior, so completion needs composed events and rendered evidence.

## Outcomes & Retrospective


Planning, source investigation, implementation, composed behavior validation, package audit, fresh installation, and rendered Cinnamon/X11 human acceptance are complete. Authoritative source validation is 199 focused tests and 1660 full-suite tests with 20 skips and one existing warning; configured PKCS#12 evidence confirms readiness work is deferred from repeats to the physical-release flush. Gate 2 item 10 is PASS for installed package `f800e6c...` from commit `8903512c9`.

Three-agent review corrections are incorporated. Keyboard commit-after-projection, pointer recording, focus delivery, authoritative mode projection, cancellation, and history behavior are covered by the completed behavior children. The external package/rendered acceptance is now complete for package `f800e6c...` from commit `8903512c9`.

## Context and Orientation


Use scripts/build_deb.sh and scripts/deb_package_audit.py, with existing build tooling in src/foliaseal/build/. The supported desktop is Cinnamon/X11; Wayland is deferred. tests/integration/test_placement_gate10.py is the composed regression created by the behavior children. Existing package and human release tracking lives in docs/ExecPlans/ui_packaged_release_acceptance_execplan.md and gui_placement_interaction_stability_execplan.md. Keep package identity (source commit, hash and installed payload) separate from the unchanged 0.1.0 version string.

## Change Slice


Evidence refresh and documentation/status commits, separate from behavior fixes. Screenshots, packages and disposable PDFs remain in /tmp; commit only concise redacted evidence summaries and plan status. Do not include user's document text, certificate secrets or full environment dumps.

## Plan of Work


Milestone 1 run the focused and full tests and build a fresh .deb into an explicit /tmp task directory using the build command's supported output option. Record source commit, build arguments, package SHA-256 and payload identity. Verify the running executable and package-manager-installed files before comparing results; do not infer freshness from version alone.

Milestone 2 launch the built payload with disposable PDF and isolated test configuration on real X11. Inspect screenshots before placement, during a held drag, after Escape, and after Undo/Redo. Use actual menu and keyboard events. Record every step of the A/B/remove sequence specified below, visible focus/mode and actual geometry. Monitor for renewed sustained CPU/disk activity during adjustment, including held Arrow and resize keys; if reproduced, collect bounded evidence and reopen the responsible behavior child instead of certifying acceptance.

Milestone 3 install the exact verified package using the session's authorized installation workflow and required sandbox approval mechanism. Preserve user-created certificates and presets. Hand off one identified running version for the bounded HITL retest. Record Pass, Fail, Not tested or genuinely inapplicable N/A for each subcase. Correct any failure through its behavior child, rebuild and repeat the affected checks. Final human acceptance is an explicit external dependency; never mark it passed based on automated screenshots.

## Concrete Steps


From /home/daekar/FoliaSeal:

    .venv/bin/pytest -q
    bash scripts/build_deb.sh --help
    .venv/bin/python scripts/deb_package_audit.py --help
    git diff --check

Use the help output to record supported output-directory and display-backed audit arguments in this living plan before executing the build. Inspect dpkg-query -W foliaseal and dpkg -L foliaseal for installation identity. Record the exact artifact path and sha256sum command once the artifact exists.

The concrete build/audit sequence is below. mktemp creates a fresh directory; retain its value for the session and record the resolved paths. Replace the package filename if the build reports a different architecture or version.

    audit_root=$(mktemp -d /tmp/foliaseal-gate10-XXXXXX)
    git rev-parse HEAD
    git status --short
    bash scripts/build_deb.sh --output-dir "$audit_root/dist"
    sha256sum "$audit_root/dist/foliaseal_0.1.0_amd64.deb"
    .venv/bin/python scripts/deb_package_audit.py "$audit_root/dist/foliaseal_0.1.0_amd64.deb" --artifacts-dir "$audit_root/audit" --display-backed

The audit extracts and tests the package; it does not install it and does not replace the interactive behavioral audit. After successful package checks, use the authorized sudo dpkg -i workflow on that exact artifact with any required tool escalation. Extract the same package using dpkg-deb -x into a fresh temporary directory, then compare hashes of the packaged application payload against the corresponding installed files identified by dpkg -L foliaseal. Record the running process executable/command and verify that it uses those installed files. Package hash, contents listing and version alone do not establish installed-byte identity. Do not reuse an already running older process for HITL.

## Validation and Acceptance


On a disposable unsigned PDF create rectangle A. Focus a rail field, choose Signing → Adjust Placement and use keyboard move/resize to produce B. Undo returns A; Redo returns B. Start a handle drag, keep the mouse held and press Escape, then release: B remains and no history step is added. Idle Escape yields Pan, no handles, unchanged B and panning on drag. Re-enter Adjust, commit a pointer edit to C, Undo to B and Redo to C. Remove Placement disappears; Undo restores C and Redo removes it. Check label, checked tools and interaction agree throughout. Capture results from actual rendered application, followed by the user's short installed retest.

Include initial creation Undo/Redo, Delete/Undo independently of menu removal, and cancellation of a new-rectangle drag as well as a handle drag. Check the mouse grab is released after cancellation and no edit occurs on later release. With a text field focused, Undo must affect text only; after Adjust focuses the canvas, menu and shortcut Undo must affect placement. Capture Text mode too: completed rectangle visible, handles absent and text selection functional. Record a bounded 30-second CPU and disk-I/O observation after pointer adjustment, distinguishing brief activity from sustained growth; a renewed sustained spike is a failure requiring investigation. Automated callback counters from the history child remain mandatory and complement this observation.

For Gate 2 item 10, gui_placement_interaction_stability_execplan.md is historical evidence only; this family was the sole implementation/retest owner. The final retest included a held-key sequence long enough to expose the reported CPU spin-up and recorded one-step Undo/Redo with no unacceptable sustained CPU/disk behavior. Ctrl+Y is outside this completed scope and remains a separate future UX opportunity.

## Idempotence and Recovery


Inspect git status before edits and preserve unrelated changes. Use disposable fixtures and isolated configuration. Record owned process IDs and temporary paths; close owned dialogs and stop owned audit processes on success or failure. Do not terminate the user's existing session or delete user PDFs, profiles or certificates. Repeated tests should begin with fresh fixture state. If desktop access is unavailable, finish all independent checks and record the exact missing access; leave the live gate open.

## Artifacts and Notes


The source findings above were obtained by read-only inspection on 2026-09-07. Store new concise test evidence and exact reproduction steps here during execution. Keep the parent and owning child synchronized when a failure is discovered. Avoid historical test counts as claims about the current build.

## Interfaces and Dependencies


Use existing packaging, PySide6 and X11 tooling. No new bespoke accessibility harness, Wayland effort or dependency upgrade. Signing smoke checks should be bounded regressions if behavior changes touch readiness; preserve earlier user passes while distinguishing their package identity from new evidence.

Revision note (2026-09-07): Created from installed Gate 2 item 10 failures and current source inspection to prevent passing low-level tests from substituting for usable placement behavior.

Revision note (2026-09-07, review wave): Incorporated validated explorer observations, strengthened production callback and rendered acceptance requirements, and rejected unsupported startup/replay conclusions. The integration test remains an intentionally new artifact.
