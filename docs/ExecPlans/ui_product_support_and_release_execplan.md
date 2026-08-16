# Product support surfaces and packaged release acceptance

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can use the integrated settings, accessibility, Help, diagnostics, privacy,
packaging, and acceptance surfaces in FoliaSeal. It is mapped to UI_SPEC sections 12–14 and
acceptance scenarios 8–10. The slice is one vertical path through the relevant model, application workflow,
Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_package_manager_install_smoke_execplan.md — isolated `dpkg --unpack`/
  `unshare` install-root smoke gate proves package-manager payload installation and installed-wrapper
  Help/resource/Poppler parity without touching the host package database; privileged host installation
  remains a separate gate.
- [x] docs/ExecPlans/ui_launch_no_document_execplan.md
- [x] docs/ExecPlans/ui_single_instance_open_routing_execplan.md
- [x] docs/ExecPlans/ui_command_model_shortcuts_execplan.md
- [x] docs/ExecPlans/ui_signing_rail_stage_status_execplan.md
- [x] docs/ExecPlans/ui_window_theme_responsive_execplan.md
- [x] docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md
- [x] docs/ExecPlans/ui_pdf_navigation_zoom_pan_execplan.md
- [x] docs/ExecPlans/ui_document_search_selection_execplan.md
- [x] docs/ExecPlans/ui_document_signatures_review_execplan.md
- [x] docs/ExecPlans/ui_safe_links_external_changes_execplan.md
- [x] docs/ExecPlans/ui_signature_library_topology_execplan.md
- [x] docs/ExecPlans/ui_catalog_search_sort_pinning_execplan.md
- [x] docs/ExecPlans/ui_signature_preset_transactions_execplan.md
- [x] docs/ExecPlans/ui_appearance_editor_transaction_execplan.md
- [x] docs/ExecPlans/ui_placement_editor_transaction_execplan.md
- [x] docs/ExecPlans/ui_first_use_preset_setup_execplan.md
- [x] docs/ExecPlans/ui_certificate_import_configuration_execplan.md
- [x] docs/ExecPlans/ui_certificate_create_export_password_execplan.md
- [x] docs/ExecPlans/ui_certificate_selection_readiness_execplan.md
- [x] docs/ExecPlans/ui_pointer_signature_placement_execplan.md
- [x] docs/ExecPlans/ui_keyboard_numeric_placement_execplan.md
- [x] docs/ExecPlans/ui_signature_field_targeting_profiles_execplan.md
- [x] docs/ExecPlans/ui_appearance_content_layout_execplan.md
- [x] docs/ExecPlans/ui_preview_fidelity_fit_validation_execplan.md — authoritative preview/signing
  parity, glyph and exact-fit readiness guidance, frozen-time refresh stability, and deterministic
  public-panel walkthrough are complete; display-backed accessibility/DPI/monitor, privileged host package installation,
  and final human release gates remain open; the compatibility/nomenclature audit found no safe
  additional retirement.
- [x] docs/ExecPlans/ui_readiness_caveats_status_execplan.md
- [x] docs/ExecPlans/ui_sign_confirmation_output_policy_execplan.md
- [x] docs/ExecPlans/ui_atomic_sign_write_safety_execplan.md
- [x] docs/ExecPlans/ui_verification_recovery_reopen_execplan.md
- [x] docs/ExecPlans/ui_help_support_execplan.md — completed first Help milestone for canonical
  packaged Markdown, CLI discovery, modeless viewer/F1, and offline resource parity.
- [x] docs/ExecPlans/ui_support_surfaces_execplan.md — product Help support commands, privacy-safe
  bounded diagnostics, and Settings Restore defaults are implemented; final package/release evidence
  remains here.
- [x] docs/ExecPlans/ui_accessibility_acceptance_execplan.md — focused real-Qt/offscreen keyboard,
  names/roles, menu-mnemonic, support-dialog, Settings, minimum-size, and Unicode-path acceptance
  passes; display-backed screen-reader/high-contrast/DPI and package-install gates remain open.

## Progress

- [x] (2026-08-09) Historical audit identified the need to delegate Help, accessibility, and package
  work into dedicated children; those children are now complete for their local/offscreen scopes.
- [x] (2026-08-10) Reconciled the release corpus by delegating the first Help milestone to
  `ui_help_support_execplan.md`; the broader settings/diagnostics/packaging acceptance remains open.
- [x] (2026-08-10) Help child completed with `72` focused passes and full-suite evidence of
  `1465 passed, 20 skipped, 1 warning`; this plan retains ownership of diagnostics, accessibility,
  installed-package, and final release acceptance.
- [x] (2026-08-10) Accessibility child completed its focused real-Qt/offscreen contract with `64`
  passes, including explicit no-document accessible names and corrected typed View mnemonics;
  display-backed accessibility, privileged host package installation, diagnostics, and final release acceptance remain
  open under this plan.
- [x] (2026-08-10) Packaged-release child completed its bounded audit: focused audit helper tests
  passed (`12 passed`), including offline-environment and complete-font-set assertions; the audit
  script executable bit was restored. A fresh temporary package audit passed (`status=passed`) for wrapper,
  executable, desktop entry/icon, `Depends: poppler-utils`, five-topic offline Help, 18 bundled
  fonts (the complete canonical set), PyInstaller 6 `_internal/foliaseal/resources`, and a true
  `pdftoppm` fixture conversion. Its report recorded `offline_environment.proxy_environment_removed=true`,
  `network_requests_required=false`, and `dependency.help_output_present=true`.
  The GUI probe was classified `limited` with return code `1` and the exact isolated endpoint
  reason `SingleInstanceUnavailable: Unable to claim or reach the FoliaSeal instance endpoint:`;
  temporary extraction/process cleanup succeeded and no generated artifact was committed. The
  display-backed accessibility/GUI and privileged host package installation gates remain open; the
  isolated install-root `dpkg --unpack` gate is complete in the child plan below.
- [x] (2026-08-16) Added and ran the isolated package-manager install-root smoke gate. A fresh `.deb`
  passed both extraction and `dpkg --unpack` audits; the private install report recorded dpkg code `0`,
  five offline Help topics, 18 fonts, successful `pdftoppm` conversion, GUI `limited` only for the
  known isolated endpoint signature, and complete private-root cleanup. This does not claim privileged
  host package installation or display-backed acceptance.
- [x] (2026-08-10) Preview/readiness closure evidence is complete: focused parity/fit/renderer/
  readiness validation is `104 passed`; the full suite is `1482 passed, 20 skipped, 1 warning`;
  Ruff, `pip check`, and `git diff --check` are clean. The deterministic walkthrough covers the
  public placement, unsupported `Common name`/`U+2603`, exact-fit blocking, ready, repeated-refresh
  frozen-time, request-timestamp equality, and cleanup states. This release plan remains open for display-backed
  screen-reader/high-contrast/DPI/monitor, privileged host package installation, diagnostics, and final
  human release acceptance; the later compatibility/nomenclature audit found no safe additional
  retirement, and no full release-compliance claim is made.
- [x] (2026-08-16) Reconciled completed child markers and accessibility status. Help, privacy-safe
  diagnostics, offscreen accessibility, and isolated package-manager installation are complete;
  display-backed accessibility/GUI, privileged host installation, and final release matrix remain
  open external gates.
- [x] (2026-08-16) Re-audited the previously unchecked child set and found no remaining
  dependency-ready model/application/Qt path in the then-published release tranche. Later
  nested-placement and nested-certificate audits identified and completed additional AFK paths;
  remaining gates are now current-document Placement capture, environment-dependent acceptance,
  or deliberate compatibility/nomenclature work.
- [x] (2026-08-16) Added the bounded X11 acceptance evidence: the source-tree GUI now has a real
  Cinnamon/X11 two-process routing smoke and interactive-harness launch/close checkpoint with clean
  owned-process cleanup. This does not substitute for packaged GUI, screen-reader/high-contrast,
  physical-DPI/multi-monitor, privileged-install, or final release-matrix acceptance.
- [x] (2026-08-16) Added the completed source-tree semantic parent workflow evidence: the canonical
  X11 runner passed 19 checkpoints through asynchronous signing, reopen, and a second locally
  verified signature. This closes the source-tree X11 workflow gate; human accessibility, packaged
  GUI, privileged host installation, and final release gates remain open. Wayland is deferred until
  Mint treats it as a first-class supported session.
- [x] (2026-08-16) Completed the bounded compatibility-retirement audit. Removed only the
  consumerless `LayoutRequest` and private fit-validation aliases; AppFrame dialog/test seams and
  Acceptance evidence contracts remain because current consumers still exercise them.
- [x] (2026-08-16) Reconciled the active-plan corpus through
  `release_readiness_reconciliation_execplan.md`; stale completion markers were corrected, while
  display-backed accessibility, physical DPI/monitor, packaged GUI, privileged installation, and
  final human release acceptance remain open.
- [x] (2026-08-16) Added and passed the bounded source-tree Cinnamon/X11 accessibility audit via
  `scripts/live_gui_accessibility_audit.py`. The audit activated only its uniquely titled window,
  verified direct Help QAction wiring, delivered native F1 through XTest, opened the modeless Help
  viewer, captured menu/control metadata plus two-monitor/theme/scaling/Orca context, and cleaned
  its owned windows and temporary stores. This closes native X11 keyboard/Help evidence only;
  human assistive-technology speech, high contrast, physical-DPI interpretation, packaged GUI,
  privileged installation, final release acceptance, and Wayland remain open/deferred.
- [x] (2026-08-16) Completed the packaged-X11 release child
  `packaged_x11_gui_acceptance_execplan.md`. A fresh Debian package reached the
  real `xcb` startup boundary with `gui_startup.status=started`; the corrected
  PyInstaller payload contains the two runtime SVG icons, 18 fonts, offline
  Help, Poppler support, and clean owned-process/root teardown. This does not
  close human accessibility, privileged host installation, final release
  matrix, or Wayland.
- [x] (2026-08-16) Completed the source-tree X11 visual/geometry evidence child
  `x11_visual_layout_audit_execplan.md`. The exact Qt-owned client capture was
  inspected at 1100x700 with the no-document message, menu row, and full-width
  Open/Library controls visible on a 1920x1080 primary screen (DPR 1.0, 96 DPI);
  native F1 and teardown remained green. The first desktop-helper capture was
  discarded as contaminated by the underlying editor. Human assistive
  technology, contrast, physical-DPI/monitor interpretation, privileged host
  installation, final release acceptance, and Wayland remain open/deferred.
- [x] (2026-08-16) Implemented the partial-preset missing-input guidance child. The typed
  readiness projection and signing rail now distinguish a missing per-document certificate from
  missing placement, preserve certificate-blocking error precedence, and prove certificate-first
  progression without automatic placement or signing. Certificate/placement creation flows and
  all display-backed, privileged, and final-release gates remain open.
- [x] (2026-08-16) Implemented nested blank-page Placement creation from the suspended Preset
  editor. The existing transactional editor returns a saved stable id, the Preset selector attaches
  it without applying the Preset to the active document, and focused/offscreen plus active-draft
  invariance tests are green. Nested Certificate creation/import remains AFK follow-up work, as
  does current-document capture; display-backed, privileged, and final-release gates remain open.
- [x] (2026-08-16) Implemented nested Certificate Create/Import from the suspended Preset. The
  existing modal certificate lifecycle dialogs return a stable configuration, the provider-backed
  selector refreshes and attaches it only on explicit Preset Save, and focused/offscreen plus
  active-draft invariance tests are green.
- [x] (2026-08-16) Implemented nested current-document Placement capture from the suspended
  Preset. Typed page context/current rectangle conversion reuses the transactional editor, only
  the saved stable id is attached, and the retained no-document Library reports an explicit error
  rather than disabling the action. Focused validation is `123 passed`; external display/package/
  final-release gates remain open and Wayland is deferred for Mint 22.3.
- [x] (2026-08-16) Reconciled active signing/review publication markers with
  current implementation commits and focused evidence. No new AFK product
  implementation gap was found; the remaining unchecked release items are
  human/display, privileged-host, or final-release gates.
- [x] (2026-08-16) Exercised the optional X11 AT-SPI evidence boundary. The
  host probe safely reported `unavailable` because the session bus lacks
  `org.a11y.atspi.Registry`; the source-tree native-X11 and cleanup evidence
  remained green. No screen-reader speech or visual acceptance claim was made.
- [x] (2026-08-16) Repeated the supported source-tree X11 audit at Qt scale 2.
  DPR `2.0`, the `1100x700` logical frame, two-screen context, native F1, and
  owned cleanup passed; direct inspection found no clipping in the primary
  menu, empty-state, Open, or Library surfaces. This closes high-DPI geometry
  evidence only. The desktop exposed `960x540` available logical geometry
  against the `1100x700` minimum, so whole-window monitor fit/restoration,
  physical readability, human accessibility, privileged packaging, and final
  release acceptance remain open.
- [x] (2026-08-16) Re-ran the bounded source-tree X11 accessibility audit with
  `DISPLAY=:0 ... scripts/live_gui_accessibility_audit.py --capture-screenshot
  --probe-atspi`. It reached a real two-monitor Cinnamon/X11 frame; metadata
  capture and owned cleanup passed. Native F1 Help delivery failed with
  `AssertionError: native X11 F1 did not open the Help viewer`; the captured
  report was `/tmp/foliaseal-x11-accessibility-audit-current/audit.json`, with
  `cleanup.passed=true`, no owned process or root remaining, and the exact
  owned artifact root scheduled for removal during closeout. This is observed
  environment-dependent friction with cause not isolated, not a completed
  acceptance gate; prior
  native-X11, geometry, and AT-SPI boundary evidence remains intact, while
  human accessibility, privileged packaging, final release acceptance, and
  Wayland remain open/deferred.
- [x] (2026-08-16) Completed a fresh compatibility and nomenclature consumer audit. No `phase3`
  references remain in `src/`, `scripts/`, or `tests/`; the remaining `Acceptance*` CLI/DTO/JSON/
  artifact names are active developer/release contracts, `build_qt_signing_shell` remains consumed
  by focused tests as an adapter, and `PdfCompatibility` remains production signing policy. No
  additional compatibility or acceptance cruft met a safe retirement condition, so no source
  deletion was made.
- [x] (2026-08-16) Re-ran the bounded Cinnamon/X11 accessibility audit after the prior native-F1
  friction. The same source-tree frame, two-monitor metadata, direct Help action, native XTest F1,
  modeless Help viewer, and owned-resource teardown all passed on the follow-up run. The earlier
  failure is therefore retained as intermittent desktop focus/input friction rather than treated
  as an AppFrame defect; product code and Qt shortcut wiring remain unchanged. The temporary
  report root was removed during closeout and no FoliaSeal-owned processes or windows remained.
- [x] (2026-08-16) Repeated the supported X11 audit with Orca present (`46.1`) and inspected the
  exact Qt-owned screenshot. One native-F1 attempt opened Help; the two-monitor frame reported
  `1100x700`, primary `1920x1080`, DPR `1.0`, and logical DPI `96`, with no clipping in the menu,
  empty-state message, Open, or Library controls. AT-SPI remained unavailable because the session
  bus lacks `org.a11y.atspi.Registry`; this strengthens machine/X11 evidence only and does not
  close human speech/contrast, physical-DPI interpretation, privileged installation, final release,
  or deferred Wayland gates. The exact report/screenshot root and owned processes were cleaned.
- [x] (2026-08-16) Re-ran the automated release gates from a fresh build: full suite `1574 passed,
  20 skipped, 1 warning`, Ruff/compile checks clean, PyInstaller bundle successful, and fresh
  Debian extraction plus private `dpkg --unpack` smoke passed with five offline Help topics,
  eighteen fonts, two runtime icons, Poppler conversion, and complete private-root cleanup. The
  isolated packaged GUI probe remains explicitly `limited` by the known `SingleInstanceUnavailable`
  endpoint boundary; this does not claim display-backed packaged acceptance or privileged host
  installation.
- [x] (2026-08-16) Hardened the source-tree X11 native-input audit boundary after the intermittent
  F1 friction. The audit now records X11 focus IDs and retries native F1 at most three times; a
  live run exercised two attempts (first delivery miss, second Help open), recorded
  `opened=true`, and cleaned its owned window/process/temp root. This improves evidence diagnostics
  only; the bounded slice is committed as `7e63dba38`, its focused X11 group is `6 passed`, and
  the current full suite remains green (`1584 passed, 20 skipped, 1 warning`). Product shortcut
  wiring, human AT-SPI speech, and final release gates remain unchanged.
- [x] (2026-08-16) The full validation run left 104 FoliaSeal-owned
  `foliaseal-canonical-preview-*` temporary image roots from direct preview-render consumers;
  all were verified idle, removed as exact owned cleanup targets, and recorded as cleanup
  friction for future preview-lifecycle hardening. No unrelated `/tmp` entries were removed.
- [x] (2026-08-16) Completed the canonical-preview cleanup child: focused preview/evidence/parity
  validation passed (`67 passed`), the full suite passed (`1584 passed, 20 skipped, 1 warning`),
  and the final exact-prefix canonical-preview root check was empty. Exception-safe adapter
  cleanup, test-scoped direct-renderer cleanup, and explicit renderer-failure/adapter
  success-and-exception ownership tests are complete; display-backed accessibility, privileged
  host installation, final release acceptance, and Mint 22.3 Wayland deferral remain unchanged.
- [x] (2026-08-16) Revalidated the current clean checkout after the X11 evidence slice: the full
  suite passed (`1585 passed, 20 skipped, 1 warning`), Ruff, bytecode compilation, `pip check`,
  and `git diff --check` all passed, and no FoliaSeal-owned processes or `/tmp/foliaseal-*` roots
  remained. This closes the AFK regression check only; it does not promote the display-backed,
  human, privileged-host, or deferred Wayland gates to complete.
- [x] (2026-08-16) Re-ran the fresh Debian package audit in the supported Cinnamon/X11 session.
  The report passed with `display_backed=true`, `qt_platform=xcb`, `gui_startup.status=started`,
  five offline Help topics, 18 fonts, two runtime icons, Poppler fixture conversion, and clean
  extraction/process teardown. This refreshes packaged-X11 startup evidence only; it does not
  close human accessibility, privileged host installation, final release acceptance, or deferred
  Mint 22.3 Wayland.
- [ ] (remaining release gate) Close the remaining release-matrix acceptance work. The
  focused/regression rerun and source-tree Cinnamon/X11/native-F1 evidence are complete; the
  remaining external gates are display-backed screen-reader/high-contrast and physical-DPI/monitor
  interpretation, human GUI acceptance, and privileged host package installation. Keep the
  packaged GUI probe explicitly limited by its isolated `SingleInstanceUnavailable` boundary,
  retain the Mint 22.3 Wayland deferral, and clean processes and artifacts after each attempt.
- [ ] (remaining release gate) Update this plan and relevant docs, then commit the final release
  corpus after the remaining children close.

## Surprises & Discoveries

- Observation: the release bar combines settings, accessibility, offline Help, diagnostics, and
  installed packaging; this child is the only plan allowed to own their final integration evidence.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible product support surfaces and packaged release acceptance outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: keep Settings, accessibility, Help/diagnostics, and packaging as separate milestones
  inside this final integration child rather than mixing their implementation details into signing
  children.
  Rationale: each is independently testable, but the release bar requires one installed-package
  acceptance pass that proves they work together.
  Date/Author: 2026-08-09 / Codex
- Decision: permit a behavior-plus-release change class only in this child.
  Rationale: the Debian launcher and installed-path smoke test are explicit SPEC.md product
  requirements; earlier children remain behavior-only.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

The local support/release implementation and evidence are complete for their available environments:
packaged Help, privacy-safe diagnostics, Restore defaults, real-Qt/offscreen accessibility, package
payload parity, private install-root `dpkg --unpack`, source-tree native-X11 keyboard/Help
evidence, and packaged-X11 startup all have owning children and current evidence. This plan remains open only for
display-backed screen-reader/high-contrast/physical-DPI/monitor and human GUI acceptance,
privileged host package installation, and final cross-surface release execution. The compatibility
and nomenclature audit found no safe additional retirement; active Acceptance evidence contracts
remain intentionally stable. The isolated package audit’s GUI result is explicitly limited
by `SingleInstanceUnavailable`; no full-release claim is made. Wayland is deferred for Mint 22.3.

## Context and Orientation

The relevant code is app settings/storage; Qt accessibility and help surfaces; src/foliaseal/__main__.py; build/pyinstaller_support.py; build/debian_packaging.py; README/docs. FoliaSeal is a Python/Qt Linux PDF signing application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “acceptance” names identify legacy
evidence/harness infrastructure and must not be introduced into ordinary product UI or new primary
contracts; production backend/evidence imports may be renamed only after a neutral migration proves
the old name is no longer required.

## Change Slice

Primary change class: behavior change plus the final release/acceptance documentation required by
this slice. Allowed changes are the named modules, focused tests, bounded ignored local evidence,
packaging files, and truthful documentation. Do not add V2 features or broad unrelated refactors.

## Plan of Work

Complete this final integration slice in four explicit milestones: integrate the Settings/geometry
contract owned by `ui_window_theme_responsive_execplan.md` (this plan does not own its schema or
storage);
accessibility and input-independent behavior; local Markdown Help/diagnostics/privacy; then
PyInstaller/.deb packaging and the complete acceptance matrix. Each milestone owns its tests and
evidence, while this plan owns only the final cross-milestone wiring and negative anti-goal audit.
Remove stale product-facing acceptance labels only after the neutral backend/evidence migration has
proved the old label is no longer part of a production import or public command. Use typed
application contracts and public Qt ports, not private child-widget reach-through.
Keep persistent objects and secrets within the schemas/storage rules. Retire obsolete compatibility
paths only after proving their consumers migrated, and record every retirement in the Decision Log.

The mixed behavior/release change class is intentional here because the packaged launcher and
installed-path acceptance are themselves V1 product requirements, not optional CI decoration. The
earlier behavior children must not add package files or package smoke evidence.

## Milestones

Milestone 1 owns accessibility/input-independent behavior and acceptance of the typed Settings/
geometry persistence implemented by `ui_window_theme_responsive_execplan.md`; it does not redefine
those keys or storage.
Milestone 2 owns local Markdown Help, diagnostics, privacy, and parity tests. Milestone 3 builds and
extracts the Debian package, runs the installed wrapper and `pdftoppm` checks, then records the full
offline/accessibility/UI-scenario matrix and cleanup.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'help|settings|theme|packag|diagnostic|privacy' src/foliaseal/infra/config/app_settings_storage.py src/foliaseal/presentation/qt/app_frame.py src/foliaseal/__main__.py src/foliaseal/build
    .venv/bin/pytest -q tests/unit/test_app_settings_storage.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_certificate_manager.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check
    .venv/bin/python -m foliaseal --help
    .venv/bin/pytest -q tests/unit/test_app_settings_storage.py tests/unit/test_qt_app_frame.py
    bash scripts/build_pyinstaller.sh
    package_root=$(mktemp -d /tmp/foliaseal-package-audit-XXXXXX)
    .venv/bin/python -m foliaseal.build.debian_packaging --output-dir "$package_root/dist"
    deb=$(find "$package_root/dist" -name 'foliaseal_*.deb' -type f -print -quit)
    test -n "$deb"
    dpkg-deb --extract "$deb" "$package_root/root"
    test -x "$package_root/root/usr/bin/foliaseal"
    command -v pdftoppm
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen "$package_root/root/usr/bin/foliaseal" --help
    rm -rf "$package_root"

After Milestone 2 adds the local Help command, run these exact post-change parity checks from
/home/daekar/FoliaSeal. The new test file must be created in that milestone and must fail before
the Help implementation exists:

    .venv/bin/python -m foliaseal help --list
    .venv/bin/python -m foliaseal help signing-basics --format markdown
    .venv/bin/python -m foliaseal help signing-basics --path
    .venv/bin/pytest -q tests/unit/test_cli_help.py
    rg -n -e 'https?://|<script|javascript:' src/foliaseal docs tests

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest|build_deb|build_pyinstaller' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the installed-package, offline, accessibility, and Help observations plus
their exact procedures and evidence paths; the bounded timeout is only a lifecycle check. Record
package/temp-root and process cleanup explicitly.

## Validation and Acceptance

Acceptance is behavioral: The packaged app starts from its desktop launcher, opens a PDF, completes the primary story offline, exposes help through the documented CLI and in-app viewer, remains usable at minimum sizes and with keyboard/accessibility paths, and leaves no stale acceptance product terminology or unsafe logs. Focused tests and the full suite must pass; the
final acceptance record must distinguish headless evidence from real Qt interaction and must include
cleanup evidence.

## Required Acceptance Cases

Run with network access disabled and prove no telemetry, upload, or account is required. Verify screen
reader names/roles, spatial tab order, non-color status, high contrast, scaling, Unicode, and minimum
window sizes. Help must be identical through in-app search and foliaseal help --list/help --format
markdown/help --path, use local Markdown with no JavaScript or remote assets, and expose no secrets.
Build and install the PyInstaller-backed Debian package, verify its desktop launcher and poppler-utils,
then run the global anti-goal audit and all ten UI_SPEC scenarios.

## Evidence Record

Before completion, record the exact Settings/accessibility/Help/package commands and results, the
offline and accessibility procedure with observed output, extracted-package launcher evidence,
evidence paths, cleanup, anti-goal audit, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

## Idempotence and Recovery

Use temporary configuration, sibling output, and disposable package-install roots. If a build or GUI
audit fails, retain source data, update Progress, clean owned processes/artifacts, and retry from
the recorded state. Never delete unrelated temporary files or private material.

## Artifacts and Notes

Record exact package name/path, launch command, help output, accessibility observations, and concise
acceptance evidence. Do not commit generated packages, private keys, passwords, or machine-local
absolute paths unless the repository explicitly requires a fixture.

## Interfaces and Dependencies

Use AppSettings, the public Qt frame/workspace ports, packaged Markdown help, the CLI parser in
src/foliaseal/__main__.py, and build helpers under src/foliaseal/build/. The final behavior must be
exercised by tests/unit/test_app_settings_storage.py, the named Qt frame and certificate-management
tests plus tests/unit/test_cli_help.py, tests/integration/test_accessibility_acceptance.py,
tests/unit/test_pyinstaller_support.py, tests/unit/test_debian_packaging.py, and the full
installed-package smoke suite.
New help/diagnostic surfaces must not expose secrets, PDF contents, selected
text, Reason, Location, or private keys.

Revision note: 2026-08-09 / Codex
Created as the final dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
Revision note: 2026-08-16 / Codex
Reconciled completed Help, diagnostics, offscreen accessibility, isolated package-install,
partial-preset guidance, nested blank-page Placement, nested Certificate, and nested current-
document Placement capture child markers. Display-backed, privileged-host, final cross-surface
acceptance, and deferred Mint 22.3 Wayland remain open external gates.
