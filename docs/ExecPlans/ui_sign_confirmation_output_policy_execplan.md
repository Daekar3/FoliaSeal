# Sign confirmation and output-path policy

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can confirm the signing objects and destination before signing in the real FoliaSeal GUI. It is mapped to SPEC output behavior and UI_SPEC WF04 section 11. The
slice is one vertical path through the relevant model, application workflow,
Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [ ] docs/ExecPlans/ui_readiness_caveats_status_execplan.md

## Progress

- [ ] (2026-08-09) Audit current behavior and add a failing focused test.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; clean processes and artifacts.
- [ ] (2026-08-09) Update this plan and relevant docs, then commit.

## Surprises & Discoveries

- Observation: confirmation currently spans the action bridge and output-path policy; this child
  must make source overwrite, destination replacement, and protected-input prompts explicit.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible sign confirmation and output-path policy outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. Record demonstrated behavior, evidence, and remaining gaps at completion.

## Context and Orientation

The relevant code is signing_workspace_action_bridge.py; signing_action_coordinator.py; output_path_policy.py; signing sidebar/modal surfaces. FoliaSeal is a Python/Qt Linux PDF signing application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “phase3” names identify legacy
evidence/harness infrastructure and must not be introduced into ordinary product UI or new primary
contracts; production backend/evidence imports may be renamed only after a neutral migration proves
the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named modules, focused tests, bounded
ignored local evidence, and the minimum truthful status documentation. Package construction and
installed-package evidence belong only to ui_product_support_and_release_execplan.md.

## Plan of Work

Add an unmistakable final confirmation that keeps the on-page preview primary and summarizes preset, certificate, output path, page/field, frozen time, caveats, and irreversible effect. Implement first-Save-as, Save As, default output directory, collision-safe <stem>-signed.pdf suggestion, and Cancel-lossless behavior. Use typed application contracts and public Qt ports, not private child-widget reach-through.
Keep persistent objects and secrets within the schemas/storage rules. Retire obsolete compatibility
paths only after proving their consumers migrated, and record every retirement in the Decision Log.

## Milestones

Milestone 1 adds Save/Sign confirmation and output-path policy tests. Milestone 2 wires first-save,
repeat-save, overwrite, and protected-input prompts through the action bridge. Milestone 3 proves
the user-visible confirmation text and records evidence without package-scope changes.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

    rg -n -e 'confirm|output|Save As|Sign and save' src/foliaseal/presentation/qt/signing_workspace_action_bridge.py src/foliaseal/application/output_path_policy.py src/foliaseal/presentation/qt/signing_action_coordinator.py
    .venv/bin/pytest -q tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_output_path_policy.py tests/unit/test_qt_signing_shell.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest|build_deb|build_pyinstaller' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the stated user-visible behavior plus a mandatory Qt-test or display-backed
walkthrough. Record Save/Sign/Replace inputs, observed wording, evidence path, and cleanup result;
the bounded timeout is only a lifecycle check. Package evidence belongs only to the final release plan.

## Validation and Acceptance

Acceptance is behavioral: A ready user must confirm before signing; the dialog shows the active objects and exact destination; first Save opens a standard save dialog; cancelling changes neither draft nor output. Focused tests and the full suite must pass; the
final acceptance record must distinguish headless evidence from real Qt interaction and must include
cleanup evidence.

## Required Acceptance Cases

First Save uses a save dialog; later Save reuses the confirmed path for the same unsigned draft; Save
As always chooses a path. The default output directory is home unless settings changed it. The app
suggests a collision-safe stem-signed name, never silently renames after confirmation, and uses an
explicit Cancel-default source-overwrite warning.

## Evidence Record

Before completion, record agreement with `docs/ui/sign-and-save-states-exploratory.svg`, the exact
confirmation/output-policy test command and result, the GUI
Save/Sign/Replace sequence and observed wording, owned sign-and-save SVG agreement, evidence path,
cleanup, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.

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
exercised by tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_output_path_policy.py tests/unit/test_qt_signing_shell.py. New help/diagnostic surfaces must not expose secrets, PDF contents, selected
text, Reason, Location, or private keys.

Revision note: 2026-08-09 / Codex
Created as the final dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
