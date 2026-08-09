# FoliaSeal V1 SPEC and UI_SPEC Compliance Parent Plan

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It governs the dependency-ordered child plans that
implement the frozen product contract in docs/SPEC.md and docs/UI_SPEC.md.

In this document, AFK means “agent can implement and validate without a pending human product
decision.” A Qt port is a small typed interface between application behavior and Qt widgets. A
compatibility surface is an adapter retained only for old callers. “phase3” is legacy evidence or
harness nomenclature, not a product feature name.

## Purpose / Big Picture

After this parent plan is complete, a non-expert user will be able to launch FoliaSeal as a
document-centric Linux desktop application, review one PDF, create and select reusable signing
objects, place one visible approval signature by pointer or keyboard, preview the exact signed
appearance, sign and save safely, verify locally, and reopen the result for another approval when
permissions allow. Each child is a thin vertical slice with an observable user outcome; no child
is merely a horizontal refactor.

The governing documents are already written and frozen. This plan implements their requirements; it
does not silently revise them. The persistent model remains governed by docs/SCHEMAS.md. Existing
compatibility paths, manual-assembly paths, and product-facing phase3 labels may be removed when a
child migrates their consumers, provided the child records the retirement evidence.

## Child ExecPlan Dependencies

The following children are created in dependency order. A child may begin only when its listed
predecessors are checked off in this parent and in the child plan itself.

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
- [ ] docs/ExecPlans/ui_product_support_and_release_execplan.md

## Progress

- [ ] (2026-08-09) Confirm the frozen SPEC/UI_SPEC baseline and current implementation map.
- [x] (2026-08-09) Created and structurally reviewed all 29 child ExecPlans in dependency order.
- [x] (2026-08-09) Added requirement traceability, exact live paths, executable validation commands,
  schema/SVG ownership, and milestone/evidence requirements before implementation.
- [ ] (2026-08-09) Resolve the live contract blockers identified during review: default GUI signing
  execution, placement-schema alignment, Library/AppSettings restart state, and a real
  single-instance process boundary.
- [ ] Implement, validate, document, and commit each child without mixing unrelated change classes.
- [ ] Run the final live GUI, offline, accessibility, and packaged-install acceptance pass.
- [ ] Reconcile architecture/status documentation and retire obsolete product-facing terminology.

## Surprises & Discoveries

- Observation: the repository contains substantial domain, signing, certificate, viewer, and Qt
  infrastructure, but current UI surfaces do not yet satisfy the new topology and interaction
  contract end to end.
  Evidence: current files include app_frame.py, viewer_widget.py, reusable_signing_models.py,
  certificate-management dialogs, and signing-workspace modules, while UI_SPEC.md still requires
  a modeless three-column Library, fixed signing rail, and keyboard-equivalent workflows.
- Observation: existing phase3-named modules are primarily evidence/harness infrastructure rather
  than the user-facing product path.
  Evidence: phase3-prefixed files occur under application evidence and Qt acceptance tooling.
  Their product-facing labels must not leak into the V1 UI; migrations must preserve evidence meaning
  while removing obsolete nomenclature where safe.

## Decision Log

- Decision: use thin vertical slices instead of the former broad GUI plans.
  Rationale: each slice must produce a demoable behavior and keep implementation, validation, and
  rollback narrow.
  Date/Author: 2026-08-09 / Codex
- Decision: treat SPEC.md as the product authority, SCHEMAS.md as the persistence authority, and
  UI_SPEC.md as the interface authority.
  Rationale: this is the explicit precedence contract and prevents implementation behavior from
  silently redefining product requirements.
  Date/Author: 2026-08-09 / Codex
- Decision: mark implementation slices AFK.
  Rationale: the frozen documents already resolve topology and interaction choices; a later human
  usability review may provide evidence but is not an implementation dependency.
  Date/Author: 2026-08-09 / Codex
- Decision: remove legacy compatibility and product-facing phase3 cruft only after each migration
  proves its concrete callers are gone; retain or rename production evidence/backend imports in a
  separate neutral migration first.
  Rationale: SPEC.md prioritizes V1 clarity, but current fit validation and acceptance tooling still
  import phase3-named modules, so a broad rename would break production behavior and evidence.
  Date/Author: 2026-08-09 / Codex
- Decision: treat the current implementation mismatches recorded in child plans as explicit
  prerequisites, not assumptions hidden inside later GUI work.
  Rationale: the default signing executor, placement schema fields, restart settings, and process
  routing determine whether the UI contract can be exercised end to end.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. Update this section after each major dependency tranche and at final acceptance.

## Context and Orientation

FoliaSeal is a Python/Qt Linux desktop PDF signing application. The CLI entry point is
src/foliaseal/__main__.py. The top-level Qt frame is
src/foliaseal/presentation/qt/app_frame.py. The signing workspace is assembled through
signing_shell.py, signing_workspace_composition.py, and related bridge/sidebar modules. Viewer
behavior is split between application viewer workflows and presentation/qt/viewer_widget.py.
Reusable objects persist through application models and infra/config stores. Certificate creation,
import, secrets, and export live in application and presentation certificate modules. Tests are
under tests/unit.

The product story is open -> review -> select preset/certificate -> place -> preview/readiness ->
sign/save -> verify/reopen. The UI contract additionally requires one open PDF, a stable right rail,
a modeless Signature Library, keyboard-accessible equivalents, plain-language status, safe atomic
output, and offline operation. The anti-goals in both governing documents remain out of scope.

## Requirement Traceability and Evidence Ownership

The final child must rerun this evidence map. Each row names the owning children and the observable
proof that must be recorded; headless tests do not substitute for GUI or package evidence.

| Requirement | Owning children | Evidence |
|---|---|---|
| SPEC primary story: open/review | launch, lifecycle, navigation, search children | No-document launch, validated open, page and text walkthrough |
| SPEC primary story: reusable setup | Library through first-use children | CRUD/nested transaction tests and first-use GUI walkthrough |
| SPEC primary story: certificate | certificate import through readiness children | Import/create/export/delete/password/readiness tests and GUI evidence |
| SPEC primary story: placement | placement children | Pointer, keyboard, field, profile, and on-page placement evidence |
| SPEC primary story: preview/readiness | appearance through readiness children | Render parity, frozen-time, fit/glyph, and state evidence |
| SPEC primary story: sign/save/verify/reopen | confirmation through verification children | Atomic output, verification, recovery, reopen/add-approval evidence |
| UI_SPEC scenarios 1–4 | foundation/review/placement children | Keyboard launch, partial preset, placement undo, field targeting |
| UI_SPEC scenarios 5–7 | appearance/signing children | Preview parity, source overwrite, restriction and verification checks |
| UI_SPEC scenarios 8–10 | product support/release child | Accessibility, minimum-size/DPI, offline Help, and package evidence |
| Normative SVG topology/state artifacts | rail, Library, appearance, placement, confirmation children | Review every file under docs/ui/ and record agreement |
| Global V1 anti-goals | product support/release child | Negative audit for tabs, printing, page editing, restoration, cloud/plugins, ordinary forms, trust/timestamp controls, arbitrary fields, and multiple pending signatures |

Schema ownership is explicit: `src/foliaseal/infra/config/schemas.py` and matching codecs,
`src/foliaseal/application/reusable_signing_models.py`, certificate models, and AppSettings are
owned by the relevant Library, placement, certificate, and product-support children. Any migration
must include a before/after serialized fixture and a backwards-read or deliberate rejection test.
The placement child owns the `top_pt` versus live `bottom_pt` decision and `page_number`/`source_page`
mapping; no other child may persist placement fields before that decision is recorded.

Normative UI artifacts are individually owned: `docs/ui/main-workspace-no-document-exploratory.svg`
and `docs/ui/main-workspace-document-open-exploratory.svg` by launch/lifecycle;
`docs/ui/sign-and-save-states-exploratory.svg` by rail, readiness, and confirmation;
`docs/ui/signature-library-presets-exploratory.svg` by Library; and
`docs/ui/appearance-profile-editor-exploratory.svg` plus
`docs/ui/placement-profile-editor-exploratory.svg` by appearance and placement. The repository has
no separate signing-rail SVG; rail ownership must cite the relevant state file and UI_SPEC text.
Each owner records the file path and observed agreement in its Evidence Record.

The ten scenario rows are also cross-linked to their contributing children: scenario 1 owns launch,
open/lifecycle, navigation, and search; scenario 2 owns rail, first-use, preset transactions, and
certificate readiness; scenario 3 owns pointer, keyboard, and placement editor; scenario 4 owns
field targeting, placement, and document review; scenario 5 owns appearance, preview, review,
readiness, confirmation, and verification; scenario 6 owns confirmation, atomic write, and
lifecycle; scenario 7 owns atomic write and verification; scenario 8 owns command model, keyboard
placement, Library/editor accessibility, and product support; scenario 9 owns window/theme and
product support; scenario 10 owns product support/release. Each row must cite one focused test,
one GUI evidence artifact, and its owning SVG or explicit “no SVG” decision.

The final acceptance record must also cover password-protected PDF prompts and password clearing on
Close/replacement/success/Exit; certification and ordinary-signature preflight; final verification
of every existing signature; page-local render recovery; exact source-overwrite warnings;
retained-but-unconfigured certificates; claimed signing time versus trusted timestamp; network-
disabled operation with no telemetry/uploads/accounts; screen-reader names/roles/tab order;
high-contrast/scaling/Unicode; Markdown/CLI Help parity with no JavaScript or remote assets; and
PyInstaller/.deb launcher plus poppler-utils verification.

## Change Slice

Primary change class: behavior change, with documentation/status reconciliation and final package
acceptance only where a child explicitly owns those outputs. Allowed artifacts are the named source
and test changes, bounded ignored local evidence, and truthful updates to architecture, README, or
ExecPlans. Do not mix speculative V2 features, broad PDF editing, printing, cloud/trust
administration, unrelated architecture scans, or evidence rebaselines into this parent.

## Plan of Work

Execute children in dependency order. Each child starts with a live code/spec audit, adds or
replaces the smallest complete path through model/application/Qt wiring/tests, and names the exact
consumer, grep proof, and deletion condition before removing a compatibility path. A child may add focused acceptance
fixtures or ignored local evidence artifacts, but must not mix unrelated evidence refreshes,
packaging changes, or broad refactors.

After each child, run focused tests, ruff on touched files, the relevant offscreen or display-backed
GUI check, and the full regression suite when the slice changes shared Qt/application behavior.
Record exact observations in the child plan, update docs/ARCHITECTURE.md or README.md only when
their current statements become inaccurate, clean processes/dialogs/temp artifacts, and commit the
narrow change. Check the corresponding child box here only after its acceptance criteria are met.

The product-support/release child owns a separate neutralization audit for the phase3 backend and
evidence import graph. It must inventory every production and test consumer, add neutral names with
temporary adapters, run import-isolation and acceptance tests, and record the deletion proof before
any UI child removes a phase3-named module or command. UI children may remove only product-facing
labels after that audit; they may not rename the backend opportunistically.

## Milestones

Milestone 1 is the contract gate: confirm the frozen SPEC/UI_SPEC/SCHEMAS requirements, resolve
the placement serialization decision, and make every child’s focused red test and exact live paths
available. Milestone 2 is the dependency-ordered vertical implementation: foundation and document
flow first, reusable objects and certificates next, then placement, preview, signing, and recovery;
each completed child must leave focused tests and a recorded GUI observation. Milestone 3 is the
release gate: run the two-process routing check, offline/accessibility/help matrix, extracted
package launcher check, all ten UI scenarios, anti-goal audit, and cleanup before checking every
parent box.

## Concrete Steps

All commands run from /home/daekar/FoliaSeal.

    git status --short
    sed -n '1,360p' docs/SPEC.md
    sed -n '1,530p' docs/UI_SPEC.md
    rg -n "phase3|compat|manual assembly|Signature Library|Sign and save" src tests docs

For each child, follow its exact commands. The common validation baseline is:

    .venv/bin/pytest -q
    .venv/bin/ruff check src tests
    git diff --check

    audit_root=$(mktemp -d /tmp/foliaseal-ui-audit-XXXXXX)
    trap 'pkill -TERM -f "foliaseal|FoliaSeal" 2>/dev/null || true; rm -rf "$audit_root"' EXIT
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf
    ! ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg '
    test ! -e "$audit_root"

The common command is only a lifecycle/cleanup smoke check. Each child that claims a visual or
interactive result must add a bounded display-backed or Qt-test walkthrough that records widget
state, input sequence, expected observation, and an evidence file under ignored `artifacts/`; an
offscreen timeout alone is never accepted as proof of a GUI behavior. Never leave FoliaSeal
processes, dialogs, or generated artifacts behind.

## Validation and Acceptance

The parent succeeds only when all children are checked and a novice can complete the primary
SPEC.md story in the packaged application without developer explanation. Acceptance must cover the
ten observable UI_SPEC scenarios, the SPEC.md release bar, keyboard and accessibility paths, offline
verification, safe source overwrite, restriction preservation, and installed Debian-family startup.
Passing unit tests alone is insufficient; record live GUI observations and cleanup evidence.

## Evidence Record

At the final gate, record one row per child and per UI_SPEC scenario: governing requirement, exact
test command/result, GUI input sequence and observed state, evidence path, package/offline result
where applicable, cleanup/process result, and compatibility/schema/SVG grep proof.

## Idempotence and Recovery

Children must use temporary sibling outputs and isolated temporary config roots for destructive or
stateful tests. If a child stops part-way, update its Progress section with done and remaining work,
restore or preserve unrelated user changes, terminate test/GUI processes, and remove only its own
generated artifacts. Do not use broad recursive deletion. Re-running a completed child must be a
no-op at the behavior boundary and must not reintroduce retired compatibility code.

## Artifacts and Notes

Allowed child artifacts are focused tests, bounded local GUI screenshots or JSON evidence under
ignored artifacts/, and documentation/status updates required to keep the repository truthful.
Forbidden mixed changes include unrelated architecture scans, speculative V2 features, broad PDF
editing, printing, cloud/trust administration, or new user-facing phase3 terminology.

## Interfaces and Dependencies

Stable boundaries are the domain models and infra stores in docs/SCHEMAS.md, the application
workflows under src/foliaseal/application/, and the public Qt workspace/frame ports under
src/foliaseal/presentation/qt/. New UI behavior must be expressed through typed application or
presentation contracts rather than test-only widget reach-through. Existing compatibility adapters
are transitional; each child must name its concrete consumer, grep proof, and deletion condition.
Acceptance tooling may remain
headless or interactive, but it must be labeled as developer/acceptance tooling rather than normal
user workflow.

Revision note: 2026-08-09 / Codex
Created after approval of the 29-slice SPEC/UI_SPEC breakdown.
Updated after the second review wave to add schema/SVG ownership, executable package/process
evidence, milestone gates, and explicit GUI-observation requirements.
