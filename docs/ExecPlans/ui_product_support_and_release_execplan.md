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
- [ ] docs/ExecPlans/ui_launch_no_document_execplan.md
- [ ] docs/ExecPlans/ui_single_instance_open_routing_execplan.md
- [ ] docs/ExecPlans/ui_command_model_shortcuts_execplan.md
- [ ] docs/ExecPlans/ui_signing_rail_stage_status_execplan.md
- [ ] docs/ExecPlans/ui_window_theme_responsive_execplan.md
- [ ] docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md
- [ ] docs/ExecPlans/ui_pdf_navigation_zoom_pan_execplan.md
- [ ] docs/ExecPlans/ui_document_search_selection_execplan.md
- [ ] docs/ExecPlans/ui_document_signatures_review_execplan.md
- [ ] docs/ExecPlans/ui_safe_links_external_changes_execplan.md
- [ ] docs/ExecPlans/ui_signature_library_topology_execplan.md
- [ ] docs/ExecPlans/ui_catalog_search_sort_pinning_execplan.md
- [ ] docs/ExecPlans/ui_signature_preset_transactions_execplan.md
- [ ] docs/ExecPlans/ui_appearance_editor_transaction_execplan.md
- [ ] docs/ExecPlans/ui_placement_editor_transaction_execplan.md
- [ ] docs/ExecPlans/ui_first_use_preset_setup_execplan.md
- [ ] docs/ExecPlans/ui_certificate_import_configuration_execplan.md
- [ ] docs/ExecPlans/ui_certificate_create_export_password_execplan.md
- [ ] docs/ExecPlans/ui_certificate_selection_readiness_execplan.md
- [ ] docs/ExecPlans/ui_pointer_signature_placement_execplan.md
- [ ] docs/ExecPlans/ui_keyboard_numeric_placement_execplan.md
- [ ] docs/ExecPlans/ui_signature_field_targeting_profiles_execplan.md
- [ ] docs/ExecPlans/ui_appearance_content_layout_execplan.md
- [ ] docs/ExecPlans/ui_preview_fidelity_fit_validation_execplan.md
- [ ] docs/ExecPlans/ui_readiness_caveats_status_execplan.md
- [ ] docs/ExecPlans/ui_sign_confirmation_output_policy_execplan.md
- [ ] docs/ExecPlans/ui_atomic_sign_write_safety_execplan.md
- [ ] docs/ExecPlans/ui_verification_recovery_reopen_execplan.md
- [x] docs/ExecPlans/ui_help_support_execplan.md — completed first Help milestone for canonical
  packaged Markdown, CLI discovery, modeless viewer/F1, and offline resource parity.
- [x] docs/ExecPlans/ui_support_surfaces_execplan.md — product Help support commands, privacy-safe
  bounded diagnostics, and Settings Restore defaults are implemented; final package/release evidence
  remains here.
- [x] docs/ExecPlans/ui_accessibility_acceptance_execplan.md — focused real-Qt/offscreen keyboard,
  names/roles, menu-mnemonic, support-dialog, Settings, minimum-size, and Unicode-path acceptance
  passes; display-backed screen-reader/high-contrast/DPI and package-install gates remain open.

## Progress

- [ ] (2026-08-09) Audit current behavior and add a failing focused test.
- [x] (2026-08-10) Reconciled the release corpus by delegating the first Help milestone to
  `ui_help_support_execplan.md`; the broader settings/diagnostics/packaging acceptance remains open.
- [x] (2026-08-10) Help child completed with `72` focused passes and full-suite evidence of
  `1465 passed, 20 skipped, 1 warning`; this plan retains ownership of diagnostics, accessibility,
  installed-package, and final release acceptance.
- [x] (2026-08-10) Accessibility child completed its focused real-Qt/offscreen contract with `60`
  passes, including explicit no-document accessible names and corrected typed View mnemonics;
  display-backed accessibility, installed-package, diagnostics, and final release acceptance remain
  open under this plan.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; clean processes and artifacts.
- [ ] (2026-08-09) Update this plan and relevant docs, then commit.

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

Not started. Record demonstrated behavior, evidence, and remaining gaps at completion.

## Context and Orientation

The relevant code is app settings/storage; Qt accessibility and help surfaces; src/foliaseal/__main__.py; build/pyinstaller_support.py; build/debian_packaging.py; README/docs. FoliaSeal is a Python/Qt Linux PDF signing application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “phase3” names identify legacy
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
Remove stale product-facing phase3 labels only after the neutral backend/evidence migration has
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

Acceptance is behavioral: The packaged app starts from its desktop launcher, opens a PDF, completes the primary story offline, exposes help through the documented CLI and in-app viewer, remains usable at minimum sizes and with keyboard/accessibility paths, and leaves no stale phase3 product terminology or unsafe logs. Focused tests and the full suite must pass; the
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
