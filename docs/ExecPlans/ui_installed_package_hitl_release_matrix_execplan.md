# Prepare and execute the installed-package V1 release matrix

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is a child of
`docs/ExecPlans/ui_product_support_and_release_execplan.md` and
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`.

## Purpose / Big Picture

The remaining V1 release question is no longer whether FoliaSeal can be
tested headlessly or whether Qt emits an AT-SPI warning. A minimal stock
PySide6 application was usable with Mint Screen Reader and Orca despite the
same warnings, so those warnings are environmental diagnostics rather than
release failures by themselves.

This plan prepares one reproducible human acceptance session against a fresh
Debian package built from the current checkout. A reviewer will use the actual
packaged application to review, sign, save, reopen, and verify a PDF while
checking screen-reader speech, keyboard operation, contrast, scaling, monitor
movement, and offline Help. Package preparation, installation, accessibility,
visual, and workflow checks are one ordered release session rather than
separate duplicate source-tree and packaged-app reviews. The session is the
evidence required by SPEC.md and UI_SPEC.md; automated package audits remain
supporting evidence only.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` Release Bar and `docs/UI_SPEC.md` scenarios 1–10 are the
  governing acceptance contract.
- [x] `docs/ExecPlans/ui_product_support_and_release_execplan.md` owns the
  cross-surface release gate.
- [x] `docs/ExecPlans/ui_packaged_release_acceptance_execplan.md` and
  `docs/ExecPlans/packaged_x11_gui_acceptance_execplan.md` prove package
  payload, offline Help, Poppler, and X11 startup boundaries.
- [x] The controlled AT-SPI slice established that normal, forced, Orca-active,
  and minimal-Qt runs share the same bridge warnings/timeouts; no further
  AT-SPI harness work is a prerequisite.
- [ ] A human with Mint Screen Reader and Orca must perform the installed-package
  session. This is the intentional HITL boundary and cannot be checked off by
  an AFK agent.

## Progress

- [x] (2026-08-16) Created this child to consolidate the remaining installed
  package, accessibility, visual, and workflow evidence without treating the
  optional AT-SPI probe as a release gate.
- [x] (2026-08-16) Recorded the minimal PySide6/Orca baseline: stock Qt controls
  are announced during keyboard use while Qt emits `Window:Destroy`,
  `GetApplicationBusAddress`, invalid text-interface, and unresolved-path
  warnings. These warnings are actionable only if FoliaSeal exhibits a
  corresponding user-visible announcement failure.
- [x] (2026-08-16) Defined the installed-package evidence record and mapped all
  ten UI_SPEC scenarios to observable observations below.
- [x] (2026-08-16) Built fresh `foliaseal_0.1.0_amd64.deb` and ran both offline
  and Cinnamon/X11 display-backed audits. Both passed with five Help topics,
  18 fonts, two runtime icons, Poppler fixture conversion, and packaged GUI
  startup `started` (`offscreen` and `xcb` respectively). The package, reports,
  PyInstaller outputs, staging roots, and child processes were removed after
  inspection. The build emitted the known nonblocking `pycparser.lextab`,
  `pycparser.yacctab`, and optional `libtiff.so.5` warnings.
- [x] (2026-08-16) Repeated the AFK package preparation with the private
  `dpkg --unpack` install-root audit. Extraction and install-root reports both
  passed with five Help topics, 18 fonts, two icons, Poppler conversion,
  `gui_startup.status=started`, and owned-root cleanup. No host package database
  was modified; no generated package/build root or child process remains.
- [x] (2026-08-20) Rebuilt and retained `/tmp/foliaseal-host-install-RJdYxq/foliaseal_0.1.0_amd64.deb`,
  passed the offline, private-install-root, and real Cinnamon/X11 audits, then
  installed it on the approved host through the desktop `pkexec` authentication
  path. The host reports `install ok installed 0.1.0`, `dpkg --audit` is clean,
  and the installed wrapper exposes all five Help topics. A non-interactive
  `sudo dpkg -i` attempt was rejected because this execution context cannot
  read a password; it made no package change and was abandoned before using
  the successful desktop-authenticated path.
- [x] (2026-08-20) Confirmed no session-owned FoliaSeal GUI process remains from
  the earlier interrupted pass; the package audit’s isolated GUI launch could not
  reach a display in this execution context.
- [x] (2026-08-20) Rebuilt the corrected package and passed fresh offline extraction and private
  install-root audits; Help/resources/font/icon checks and host `pdftoppm` conversion passed. The
  display-backed audit remains blocked solely because this execution context cannot open `DISPLAY=:0`.
- [x] (2026-08-23) Rebuild the package from current checkout `f6e431cc4`, record the package checksum
  and commit identity, and rerun the offline, private-install-root, and supported Cinnamon/X11 audits.
- [ ] (2026-08-23) Execute the combined installed-package session in this order: install and launch the
  exact fresh package; run the normal visual signing workflow; repeat the critical path keyboard-only;
  repeat it with Orca; exercise high contrast, scaling, minimum size, and monitor movement; then run
  the additional PDF fixtures and installed Help checks before cleanup.
- [x] (2026-08-23) Built `foliaseal_0.1.0_amd64.deb` from `f6e431cc4d1272782ff26664b57965fa4b720afc`
  with SHA-256 `3fbd21c8df43986204dd7bbdc3f6ba01547309da454f856c6860f16fe2bdec35`. Offline and
  private-install-root audits passed with five Help topics, 18 fonts, two icons, Poppler conversion,
  and clean owned-root teardown. The display-backed audit passed with `qt_platform=xcb` and
  `gui_startup.status=started`; its temporary extraction root was cleaned.
- [x] (2026-08-23) Installed that exact package through desktop-authenticated `pkexec dpkg -i` over
  the existing `0.1.0`; `dpkg --audit` is clean. Launched `/usr/bin/foliaseal gui` on `DISPLAY=:0`
  with disposable HOME/XDG roots; the owned process is running for the human acceptance session.
- [x] (2026-08-23) Confirmed the installed wrapper remains visible in a bounded interactive X11
  session and captured the 1100x732 no-document frame. The frame shows the stable disabled-document
  state, `Open a PDF...`, `Manage Signature Library...`, the top-level menus, and no recent-file data.
  This is machine-observed rendering evidence; the scenario remains open until the human observer
  confirms the normal visual workflow and keyboard reachability.
- [x] (2026-08-23) Human Gate 1 confirmed the no-document frame and keyboard reachability for menus
  and buttons. The first document-open review then exposed a `Copy Result` meaning/copy-surface
  ambiguity and substantial default-rail density/space-allocation concerns; the matrix is paused for
  defect recording before continuing into signing-state gates.
- [x] (2026-08-23) Closed the owned interactive package session after the observation, removed its
  temporary HOME/XDG root, package/build roots, screenshots, and session markers, and verified that
  no session-owned FoliaSeal process or window remained. The installed package itself remains in place
  for the next corrected-package acceptance pass.
- [x] (2026-08-23) The focused correction plan
  `gui_document_review_copy_and_rail_density_execplan.md` completed: the duplicate sidebar copy
  surface is retired, unsigned review is compact and explanatory, the rail is content-driven at the
  legal minimum, and primary signing requests Save As before mutation when needed. Commit
  implementation commit `29b27916fa0cbaa77d8faf3503701b559b074479` was rebuilt as a final `.deb`,
  SHA-256 `ade4ba16ac25b498c5bb048ebe20f06fff807cf34472ece46984881ef63abc68`; offline, private-install,
  display-backed, authenticated-install, and installed Help checks passed. The remaining work is the
  ordered human release matrix, not AFK correction of this document-open slice.
- [ ] Perform the installed-package HITL matrix and record pass/fail notes,
  screenshots or speech observations where appropriate, and exact cleanup.
- [ ] Resolve any user-visible failures in narrowly scoped child plans; do not
  create fixes for Qt warnings that do not affect observed behavior.
- [ ] Reconcile the parent/release plans and commit the final release corpus.

## Surprises & Discoveries

- Observation: stock PySide6 controls remained usable with Mint Screen Reader
  and Orca even while Qt printed AT-SPI bridge warnings.
  Evidence: the controlled minimal application announced text entry, checkbox,
  button, state/navigation behavior, and dialog interaction; the same warning
  families appeared in FoliaSeal's optional probe.
- Observation: the automated packaged audit proves payload and startup but not
  scenarios 1–9 or human speech.
  Evidence: `scripts/deb_package_audit.py` checks wrapper, desktop metadata,
  Help, fonts, icons, Poppler, and startup classification; it does not drive a
  packaged signing workflow or interpret speech.
- Observation: host installation requires an interactive authentication path
  in this environment.
  Evidence: `sudo dpkg -i` could not read a password without a terminal;
  desktop `pkexec` authentication completed the exact same install and left a
  clean package database.
- Observation: the fresh package audit passed in both modes, but the build
  still emits optional PyInstaller warnings for missing `pycparser` generated
  tables and `libtiff.so.5`. Evidence: the package audit report and build log;
  required Help, font, icon, Poppler, and GUI checks remained green.
- Observation: privileged host installation is a separate gate from this
  session. A disposable VM/snapshot is preferred; host `dpkg` mutation requires
  explicit authorization and a rollback record.
- Observation: the recorded audit commands must include both offline and
  display-backed extraction, plus the private install-root smoke, because each
  proves a different package boundary. None of them substitutes for an actual
  installed desktop session.
- Observation: the latest source-tree terminology cleanup is committed as
  `f6e431cc4`, so the previously installed `0.1.0` package cannot be treated as
  current-release evidence until a fresh package is built and identified by
  commit/checksum.
- Observation: `Copy Result` copies the current text-search match span, not the
  search query itself. The current match may happen to equal the query, making
  the distinction invisible. Text-selection mode uses a separate viewer-toolbar
  `Copy selected text` action and the Edit command path; the sidebar `Copy Result`
  button does not change meaning when text-selection mode is active.
  Evidence: `DocumentTextSearchSession.current_copy_text()` and
  `SigningWorkspaceSidebar._build_document_text_controls()`.
- Clarification: search is case-insensitive substring matching. The copied match
  preserves the extracted PDF text, so it can differ from the query's casing or
  extracted representation. A search highlight is not a text selection, however;
  the toolbar `Copy selected text` action remains disabled until the user enters
  text-selection mode and selects text directly.
  Evidence: `QtPdfDocumentTextSearchEngine.search()` lowercases both operands,
  then copies `QPdfDocument`'s selected span; the viewer selection state is
  maintained separately in `document_review_workspace.py`.
- Observation: the disabled signature selector in the unsigned fixture represents
  the absence of embedded signatures in the PDF, not missing certificates or
  presets. Certificate/preset readiness is a separate signing-rail state.
  Evidence: `document_review.build_document_review_summary()` and the selector
  enablement in `SigningWorkspaceSidebar.apply_document_review_workspace_state()`.
- Observation: at the default installed window size, the right rail reserves a
  large vertical status region and places verbose review/search/status groups in
  one scrollable column. The human observer reported that signature/presentation
  controls are effectively hidden behind an unhelpful scrollbar, with excess
  whitespace under the search prompt and oversized horizontal action buttons.
  Evidence: live installed-package observation; the current rail uses a fixed
  320-pixel width, `STATUS_REGION_MINIMUM_HEIGHT = 200`, wrapped labels, and
  vertically stacked full-width buttons.
- Observation: `Choose output...` is semantically accurate to the current
  implementation but unclear to a first-time user because it chooses the output
  path before signing. A clearer candidate is `Choose save path...` or
  `Save signed PDF as...`; changing the timing or label requires a focused UI
  decision and regression coverage rather than an acceptance-only edit.
  Evidence: `SigningActionCoordinator.accept_output_path()` records the path
  before `Confirm and sign`.

## Decision Log

- Decision: use the installed Debian package as the sole final human target.
  Rationale: source-tree audits are valuable diagnostics, but SPEC.md defines
  V1 in terms of a packaged Linux desktop application.
  Date/Author: 2026-08-16 / Codex.
- Decision: classify Qt/AT-SPI warnings by observed behavior, not stderr text.
  Rationale: the same warnings occur in a minimal usable PySide6 control; a
  release failure requires a FoliaSeal-specific missed announcement,
  unreachable control, or incomprehensible state.
  Date/Author: 2026-08-16 / Codex.
- Decision: keep privileged host installation separate from the human matrix.
  Rationale: package usability can be tested in a disposable installed root or
  authorized host session without silently changing the package database.
  Date/Author: 2026-08-16 / Codex.
- Decision: do not run Wayland as part of V1 acceptance.
  Rationale: the V1 Linux target is Cinnamon/X11; Wayland validation is a later
  compatibility tranche.
  Date/Author: 2026-08-16 / Codex.
- Decision: combine packaged workflow, keyboard, Orca, visual, and Help checks
  into one ordered HITL session after AFK package preparation.
  Rationale: the installed package is the actual V1 deliverable, and a single
  session prevents accepting the source tree and then repeating the same user
  workflow against a different artifact.
  Date/Author: 2026-08-23 / Codex.
- Decision: require a fresh package from the current checkout before host
  installation.
  Rationale: the package version may remain unchanged while user-facing
  terminology and other fixes change; commit identity and checksum are needed
  to prove which build was accepted.
  Date/Author: 2026-08-23 / Codex.
- Decision: pause the human matrix at the first document-open review when a
  control's meaning or default layout is materially unclear.
  Rationale: continuing into certificate/signing gates would mix acceptance of
  a confusing surface with later workflow results and could hide a release
  defect behind a successful signing operation.
  Date/Author: 2026-08-23 / Codex.
- Decision: treat search-match copy and arbitrary selected-text copy as one
  user-facing copy concept for the V1 surface unless a later usability test
  demonstrates a strong need for both visible actions.
  Rationale: the backend operations are technically distinct, but two prominent
  copy buttons create a discoverability problem and do not represent two common
  user intents. The focused correction should remove or demote `Copy Result`,
  retain the clear `Copy selected text` affordance, and preserve search-match
  copying in the application layer only if a secondary convenience action is
  still justified.
  Date/Author: 2026-08-23 / Codex.

## Outcomes & Retrospective

The AFK preparation is complete when this plan contains a fresh package audit,
the baseline metadata, the current commit/checksum, and an explicit ordered
HITL handoff. The plan must not be marked fully complete until the combined
installed-package session, required fixture coverage, and final release
reconciliation are recorded. A successful session closes the human release
gate; an observed failure becomes a bounded implementation plan with a new
acceptance test or reproducible observation.

## Context and Orientation

`scripts/build_pyinstaller.sh` and `scripts/build_deb.sh` create the package;
`scripts/deb_package_audit.py` checks its payload and offline resources;
`scripts/live_gui_accessibility_audit.py` supplies source-tree X11 diagnostics;
and the installed wrapper is `/usr/bin/foliaseal` inside the package. The HITL
session must use the packaged executable, not the checkout's Python entry
point. Temporary HOME and XDG roots are required so test data and credentials
cannot affect the user's normal FoliaSeal configuration.

The default HITL target is the user's Mint Cinnamon/X11 host after explicit
authorization to install this exact package. A disposable VM or snapshot with
the same desktop is an equally valid safer target. The host procedure below is
not authorized merely by this plan: stop before `sudo dpkg -i` until the user
confirms the target and accepts the rollback. The private install-root audit is
safe AFK evidence but cannot create a display-backed desktop session.

“HITL” means human-in-the-loop: the human observes speech, focus, legibility,
and workflow comprehension that an automated process cannot judge. “Release
matrix” means the complete set of observable scenarios required before V1 can
be called usable, not merely a test count.

## Plan of Work

First build a fresh `.deb` in one owned temporary directory from the current
checkout and record both `git rev-parse HEAD` and a checksum of the package.
Run the existing offline extraction audit, private package-manager-root audit,
and display-backed audit. Record the package filename, package version, audit
status, Help topics, resource checks, Poppler result, selected display, Qt
platform, and cleanup result. Do not install it into the host package database
during AFK preparation. Do not reuse an older package merely because its
version string is unchanged.

Next capture the environment baseline immediately before the human session.
Run the following from the same X11 session and preserve its output with the
package report:

    .venv/bin/python -c 'import PySide6,sys; from PySide6.QtCore import qVersion; print(sys.version.split()[0]); print(PySide6.__version__); print(qVersion())'
    printf 'DISPLAY=%s QT_QPA_PLATFORM=%s\n' "$DISPLAY" "$QT_QPA_PLATFORM"
    xrandr --query
    gsettings get org.cinnamon.desktop.interface gtk-theme
    gsettings get org.cinnamon.desktop.interface text-scaling-factor
    orca --version
    pgrep -af '^orca([[:space:]]|$)' || true

Record whether Orca was already active, and retain only session-owned process
IDs for cleanup. Run the controlled source-tree audit if a fresh AT-SPI context
record is needed; its `address_resolved`, status properties, probe status,
timeout/return code, and bounded stderr are context, not a pass/fail substitute
for speech.

After the user authorizes the selected host/VM target, install the exact package
identified by the recorded commit and checksum, then launch
`/usr/bin/foliaseal gui` with the disposable fixture and temporary HOME/XDG
roots. Follow one continuous session: normal visual workflow, keyboard-only
workflow, Orca workflow, high-contrast/scaling/minimum-size/monitor checks,
additional edge-case fixtures, and installed Help. Record the ten UI_SPEC
scenarios and the SPEC release-bar workflow. Before the visual-responsiveness
checks, use Mint's accessibility/appearance controls to enable a high-contrast
theme and record the theme transition; restore the previous theme after the
session. The observer may use screenshots or short notes, but must not record
credentials, private keys, or document contents beyond disposable fixtures.

## Concrete Steps

Run from `/home/daekar/FoliaSeal` in the supported Cinnamon/X11 session.

    package_root=$(mktemp -d /tmp/foliaseal-release-matrix-XXXXXX)
    .venv/bin/python -m foliaseal.build.debian_packaging --output-dir "$package_root/dist"
    deb=$(find "$package_root/dist" -name 'foliaseal_*.deb' -type f -print -quit)
    test -n "$deb"
    .venv/bin/python scripts/deb_package_audit.py "$deb" \
      --artifacts-dir "$package_root/offline"
    .venv/bin/python scripts/deb_package_audit.py "$deb" \
      --artifacts-dir "$package_root/install-root" \
      --package-manager-root "$package_root/dpkg-root"
    DISPLAY=:0 QT_QPA_PLATFORM=xcb .venv/bin/python scripts/deb_package_audit.py \
      "$deb" --artifacts-dir "$package_root/evidence" --display-backed
    .venv/bin/python - "$deb" <<'PY'
    import json, os, subprocess, sys
    import PySide6
    from PySide6.QtCore import qVersion
    print(json.dumps({
        "python": sys.version.split()[0],
        "pyside6": PySide6.__version__,
        "qt": qVersion(),
        "display": os.environ.get("DISPLAY"),
        "qt_platform": os.environ.get("QT_QPA_PLATFORM"),
        "orca": subprocess.run(["orca", "--version"], check=False,
                                capture_output=True, text=True).stdout.strip(),
        "package": os.path.basename(sys.argv[1]),
    }, sort_keys=True))
    PY

Do not run `sudo dpkg -i` in this AFK step. When the user authorizes the chosen
host/VM target, install and launch the exact package with:

    sudo dpkg -i "$deb"
    /usr/bin/foliaseal gui

Before installation, record `dpkg-query -W -f='${Status} ${Version}\n' foliaseal`
if a prior package exists. After the session, remove this package with
`sudo dpkg -r foliaseal` if it was installed only for acceptance, and verify the
recorded prior state or snapshot rollback. Clean only session-owned FoliaSeal
processes/windows and preserve any Orca process that was active before the
session; never require that the desktop screen reader be absent at teardown.

## Validation and Acceptance

The AFK preparation passes when the fresh package audit reports the existing
payload/Help/font/icon/Poppler checks, the display-backed startup is `started`
or the exact known `SingleInstanceUnavailable` limitation, the environment
record is captured, and cleanup is verified. Any other package failure stops
before HITL and becomes an implementation defect.

The HITL matrix must record the following observations:

1. **UI_SPEC §19 scenario 1:** Direct launch exposes the stable no-document
   frame, Open PDF, Library, menus, and keyboard reachability.
2. **UI_SPEC §19 scenario 2:** A partial preset visibly requests only missing inputs and never silently
   places a signature.
3. **UI_SPEC §19 scenario 3:** Pointer and keyboard placement can be created, adjusted, cancelled,
   undone, and restored without becoming unreachable.
4. **UI_SPEC §19 scenario 4:** Eligible and ineligible existing signature fields are distinguished through
   explicit commands and explanations.
5. **UI_SPEC §19 scenario 5:** Preview and signed output remain visually equivalent, including text,
   image alpha, font, geometry, frozen time, glyph support, and overflow checks.
6. **UI_SPEC §19 scenario 6:** Source overwrite safety, preserved artifacts, encrypted/restricted PDFs, and
   recovery behavior remain truthful.
7. **UI_SPEC §19 scenario 7:** Protected PDFs remain protected or signing is blocked with an explanation.
8. **UI_SPEC §19 scenario 8:** Orca and keyboard-only operation can create/select a preset and appearance,
   place with Enter/arrows, sign/save, enter a password, and understand every
   state without pointer or color.
9. **UI_SPEC §19 scenario 9:** At minimum size, with high contrast enabled, and after scaling or monitor movement, the canvas remains
   primary, the signing rail remains right, the toolbar does not wrap, and all
   controls remain reachable and legible.
10. **UI_SPEC §19 scenario 10:** In-app Help is searchable, and installed CLI Help topics remain readable
    offline through the documented path.

Also record the SPEC release-bar actions: certificate create/import/manage,
PDF review/search/select/copy, explicit appearance/certificate/placement
selection, pointer or keyboard placement, offline signing, user-chosen output,
reopen, plain-language verification, and a second approval where permitted.

## Idempotence and Recovery

Every generated package, extraction root, fixture, and report belongs under the
single temporary root. If the build or audit fails, retain source changes,
record the exact failure, remove only that root and owned child processes, and
retry. If a human test fails, preserve only safe descriptive evidence, return to
the source tree, and create a focused child plan. Never delete shared AT-SPI
state, kill unrelated windows, or mutate the host package database without
explicit authorization.

## Artifacts and Notes

The final evidence record should contain the package name/version, environment
metadata, automated audit summary, ten scenario results, SPEC release-bar
result, observed defects, and cleanup result. Do not commit `.deb` files,
PyInstaller directories, PDFs, screenshots containing private data,
credentials, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing package builder and `scripts/deb_package_audit.py`; do not add
runtime dependencies or product behavior for this acceptance slice. Use the
existing X11 audit only for machine context. The human session is the authority
for speech, physical readability, and workflow comprehension. A failure must
be represented by a focused source/test change or a documented environment
limitation, never by downgrading the release requirement.

Revision note: 2026-08-16 / Codex: created after a minimal stock PySide6 app
was successfully used with Mint Screen Reader and Orca despite the same Qt
AT-SPI warnings seen in the FoliaSeal probe. This separates non-blocking Qt
diagnostics from user-visible accessibility failures and makes the installed
package the single final HITL target.

Revision note: 2026-08-23 / Codex: revised after the acceptance review to make
the current-commit fresh package and the single combined installed-package,
keyboard, Orca, visual, fixture, and Help session the required order. The
previously installed package remains historical evidence until this exact
checkout is rebuilt and identified by checksum.

Revision note: 2026-08-23 / Codex: recorded the fresh package audits, desktop-
authenticated installation, and bounded visible no-document launch. The human
matrix remains intentionally open; machine-rendered startup is not a substitute
for visual, keyboard, Orca, or physical-DPI judgment.
