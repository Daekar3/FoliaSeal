# Re-run the installed GUI acceptance matrix after HITL defect corrections

This ExecPlan is a living document and must remain self-contained under
`/home/daekar/.codex/skills/write-execplan/PLANS.md`. It is Child 4 of
`docs/ExecPlans/gui_hitl_defect_recovery_parent_execplan.md` and must run only after Children 1–3 are
complete.

## Purpose / Big Picture

This slice proves that the corrected source is useful as the installed product, not merely green in
offscreen tests. It rebuilds a fresh Debian package, repeats the deterministic payload/offline/private
install-root/X11 checks, then asks a human to revisit the observed gates and the remaining UI_SPEC/SPEC
release-bar workflow. It records defects honestly, cleans up every session-owned process and temporary
root, and reconciles the governing status plans.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/ui_installed_package_hitl_release_matrix_execplan.md` defines the host-install
  procedure, rollback, ten UI_SPEC scenarios, and ownership-aware cleanup.
- [x] `docs/ExecPlans/ui_packaged_release_acceptance_execplan.md` defines the deterministic package
  payload and offline checks.
- [ ] `docs/ExecPlans/gui_certificate_and_preset_recovery_execplan.md` is complete and committed.
- [ ] `docs/ExecPlans/gui_appearance_and_signing_rail_layout_execplan.md` is complete and committed.
- [ ] `docs/ExecPlans/gui_placement_interaction_stability_execplan.md` is complete and committed.
- [ ] The user explicitly authorizes host package installation immediately before the privileged
  command; ordinary preparation must not mutate the host package database.

## Progress

- [x] (2026-08-20) Capture the source baseline: focused recovery/GUI/package tests pass, full suite is
  `1603 passed, 20 skipped, 1 warning`, Ruff/compileall/diff checks are clean, and the worktree remains
  intentionally dirty with this implementation plus its living-plan updates.
- [x] (2026-08-20) Build a fresh `foliaseal_0.1.0_amd64.deb`; offline extraction and private
  `dpkg --unpack` audits pass, including corrected relative-wrapper isolation behavior.
- [x] (2026-08-23) Rebuilt the package from `f6e431cc4`, passed offline, private-install-root, and
  display-backed Cinnamon/X11 audits, and recorded the package checksum in the installed-package
  matrix. Desktop-authenticated installation succeeded and `dpkg --audit` is clean.
- [x] (2026-08-23) Confirmed the installed wrapper's no-document frame and keyboard reachability in
  the bounded X11 session. The human matrix is now paused at the first document-open review because
  `Copy Result`, disabled signature review, right-rail space allocation, and `Choose output...` wording
  need focused follow-up recording before later gates continue.
- [ ] Install-state regression matrix: continue with the human matrix after the new document-review
  findings are assigned to a focused correction slice; then complete Gates 4–12.
- [ ] Record any remaining product defect as a focused child plan or environment limitation.
- [ ] Restore theme/scaling, close FoliaSeal and the audit terminal, remove only owned temporary roots,
  and verify no FoliaSeal process/window remains.
- [ ] Update parent/release/compliance plans and create the final acceptance documentation commit.

## Surprises & Discoveries

- Observation: the first installed session passed launch and shell behavior but stopped before existing
  fields, signing output, safety, accessibility, Help, reopen/verify, and second approval.
  Evidence: the user’s recorded Gates 0–3 results in the HITL checklist.
- Observation: successful source-tree or offscreen tests cannot certify the installed package’s window
  geometry, Orca speech, high contrast, monitor movement, or human understanding.
  Evidence: the existing package audit checks payload/startup/resources but does not interpret speech or
  drive the full signing story.
- Observation: the first fresh-package audit exposed a packaging-wrapper isolation bug when an older
  host installation already exists: the extracted wrapper preferred `/usr/lib/foliaseal/foliaseal`
  instead of its own relative bundle, causing Help-path validation to escape the extracted package.
  Correction: the generated wrapper now always resolves its sibling package root relative to its own
  path, which works both installed and under extraction/private-install audits.
- Observation: the first current-release installed review found no-document and keyboard acceptance
  clean, but the document-open rail is not yet ready for release acceptance. Search-match copy is
  labeled `Copy Result` while selected-text copy is a separate toolbar/Edit action; the unsigned
  signature selector is disabled because there are no embedded signatures; and long status/review
  blocks plus a 200-pixel status minimum consume too much vertical rail space at the default window
  size. The output-path command is also unclear to first-time users.
  Evidence: human observation on 2026-08-23 and the current sidebar/review/search implementations.

## Decision Log

- Decision: repeat the installed-package session rather than accepting the source tree after fixes.
  Rationale: the release target is the Debian-installed `/usr/bin/foliaseal`; package relocation and
  desktop/runtime resources are part of the user-visible product.
  Date/Author: 2026-08-20 / Codex.
- Decision: keep Cinnamon/X11 as V1 acceptance and defer Wayland.
  Rationale: the current project target and prior audit evidence are X11; this family must not expand
  into an unrelated platform tranche.
  Date/Author: 2026-08-20 / Codex.
- Decision: treat Qt AT-SPI bridge warnings as contextual unless the human observes an accessibility
  failure.
  Rationale: the stock PySide6 Orca baseline produced the same warnings while remaining usable.
  Date/Author: 2026-08-20 / Codex.
- Decision: do not uninstall or roll back the host package until the human session and evidence capture
  are complete; after acceptance, follow the recorded prior-package state and cleanup procedure.
  Rationale: uninstalling early would remove the actual acceptance target and force an unnecessary
  reinstall.
  Date/Author: 2026-08-20 / Codex.

## Outcomes & Retrospective

At the beginning, the package is installed but the first human pass is incomplete and contains release-
blocking defects. At completion, this child must state exactly which UI_SPEC scenarios passed, which
remain blocked, what package/version was tested, and whether rollback occurred. A green automated audit
without human observations is not completion.

## Context and Orientation

The package builder is `src/foliaseal/build/debian_packaging.py`; deterministic package evidence is
collected by `scripts/deb_package_audit.py`. The source-tree X11 audit is
`scripts/live_gui_accessibility_audit.py`. The release plan’s ten scenario matrix is
`docs/ExecPlans/ui_installed_package_hitl_release_matrix_execplan.md`. The governing behavior is in
`docs/SPEC.md` and `docs/UI_SPEC.md`; the final acceptance must preserve PDF-first signing, explicit
preset/certificate/placement choices, lossless failure recovery, offline Help, and the fixed right rail.

## Plan of Work

Begin with read-only baseline capture: package status, `dpkg --audit`, Python/PySide6/Qt versions,
DISPLAY/X11 session, monitor layout, theme/text scale, Orca version/process ownership, and current
worktree. Build one fresh package under an owned `/tmp/foliaseal-*` root. Run the offline extraction,
private package-manager-root, and display-backed audits and retain their concise JSON reports.

After explicit authorization, install the exact package through the host’s interactive authentication
path. Verify the installed wrapper, Help topics, package files, and clean package database. Launch with a
disposable PDF and isolated HOME/XDG config/cache roots. Keep pre-existing Orca and unrelated windows
untouched.

The human repeats Gates 0–3 with the corrected defects first: readable Create Certificate, optional
Display name, Appearance editor preview/geometry, stable signing rail, wrong-password recovery, pointer
performance, keyboard placement, and Adjust Placement. Then complete existing fields, preview/output
equivalence, safety/protected PDFs, Orca/keyboard-only operation, minimum/high-contrast/DPI/monitor
checks, Help/offline operation, reopen/verify, and second approval where permitted.

Record each gate as PASS, FAIL, or BLOCKED with a short observation and safe evidence path. A failure
becomes a focused follow-up plan; do not downgrade it by citing a passing unit test. Restore theme and
scaling, close only session-owned processes/windows, remove exact temporary roots, and verify cleanup.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`.

    git status --short
    dpkg-query -W -f='${Status} ${Version}\n' foliaseal 2>/dev/null || true
    dpkg --audit
    .venv/bin/python -c 'import PySide6,sys; from PySide6.QtCore import qVersion; print(sys.version.split()[0]); print(PySide6.__version__); print(qVersion())'
    printf 'DISPLAY=%s XDG_SESSION_TYPE=%s QT_QPA_PLATFORM=%s\n' "$DISPLAY" "$XDG_SESSION_TYPE" "$QT_QPA_PLATFORM"
    xrandr --query
    gsettings get org.cinnamon.desktop.interface gtk-theme
    gsettings get org.cinnamon.desktop.interface text-scaling-factor
    orca --version
    pgrep -af '^orca([[:space:]]|$)' || true

Build and audit in one owned root:

    package_root=$(mktemp -d /tmp/foliaseal-hitl-regression-XXXXXX)
    .venv/bin/python -m foliaseal.build.debian_packaging --output-dir "$package_root/dist"
    deb=$(find "$package_root/dist" -maxdepth 1 -type f -name 'foliaseal_*.deb' -print -quit)
    test -n "$deb"
    .venv/bin/python scripts/deb_package_audit.py "$deb" --artifacts-dir "$package_root/offline"
    .venv/bin/python scripts/deb_package_audit.py "$deb" --artifacts-dir "$package_root/install-root" --package-manager-root "$package_root/dpkg-root"
    DISPLAY=:0 QT_QPA_PLATFORM=xcb .venv/bin/python scripts/deb_package_audit.py "$deb" --artifacts-dir "$package_root/x11" --display-backed

After authorization, install and verify using the exact procedure in the installed-package plan. Do
not run `apt-get -f install` automatically; record dependency failures before changing anything else.
Use `/usr/bin/foliaseal help --list` and `/usr/bin/foliaseal help signing-basics --path` as installed
wrapper checks.

## Validation and Acceptance

The child passes when the fresh package passes all three automated audits, the installed wrapper and
Help work without `PYTHONPATH`, `dpkg --audit` is clean, and the human records a result for every Gate
0–12. Gates 1–3 must specifically show the corrected dialog geometry, Appearance/rail usability,
password recovery, placement stability, keyboard path, and no Adjust Placement crash. Gates 4–12 must
cover existing fields, signing equivalence, safety/protection, Orca/keyboard-only use, responsive/high-
contrast/DPI/monitor behavior, offline Help, reopen/verify, and second approval. Cleanup must leave no
session-owned FoliaSeal process/window or temporary root.

## Idempotence and Recovery

Use a new package root for each attempt. Record the prior installed package state before `pkexec`/`sudo`;
if no prior package existed, rollback is `sudo dpkg -r foliaseal`, while a prior version requires the
recorded exact package or a snapshot. Never delete user configuration, certificate files, or unrelated
Orca processes. If a GUI test crashes, preserve the terminal output, close the owned process, and stop
the matrix at that gate until a focused child plan exists.

## Artifacts and Notes

The final evidence may include package filename/version, audit JSON summaries, gate results, safe
screenshots, and cleanup verification. Do not commit the `.deb`, PDFs, private keys, passwords, full
desktop dumps, or absolute machine-local temporary paths. Update the installed-package, packaged-release,
and UI compliance plans with concise outcomes and exact remaining blockers.

## Interfaces and Dependencies

Use the existing builder/audit scripts and the installed wrapper. Use the human as the authority for
Orca speech, physical readability, and workflow comprehension. Use `UI_SPEC.md` §19 as the scenario
index and `SPEC.md`’s release bar for certificate management, review, explicit setup, placement,
offline signing, chosen output, reopen/verify, and second approval. No new runtime dependency or
acceptance-only product behavior may be introduced by this child.
