# Reconcile product-support and release status

This ExecPlan is a living document maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK documentation/status slice under
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`.

## Purpose / Big Picture

FoliaSeal’s Help, privacy-safe diagnostics, offscreen accessibility contract, and isolated package
installation smoke are implemented, but the broad release plan still marks many completed children
unchecked and the accessibility child retains an obsolete “not implemented/commit” tail. This slice
will reconcile those records so the release bar clearly separates completed local evidence from the
remaining display-backed and privileged-host gates. It will not claim that a sandboxed offscreen run
is human visual acceptance or that an isolated package root is a privileged host installation.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are the governing contracts.
- [x] `docs/ExecPlans/ui_product_support_and_release_execplan.md` owns cross-surface release status.
- [x] `docs/ExecPlans/ui_accessibility_acceptance_execplan.md`, `ui_support_surfaces_execplan.md`,
  `ui_help_support_execplan.md`, and `ui_package_manager_install_smoke_execplan.md` contain the
  completed local implementation/evidence slices.
- [x] Explorer audit of source, tests, package audit reports, and stale plan markers completed on
  2026-08-16.

## Progress

- [x] (2026-08-16) Confirmed Help commands/resources, privacy-safe diagnostics, Restore defaults,
  real-Qt offscreen accessibility checks, and isolated package-manager install-root smoke are live.
- [x] (2026-08-16) Confirmed remaining release gates are display-backed screen reader/high contrast/
  physical DPI/monitor checks and privileged host package installation.
- [x] Reconcile completed-child dependency markers and obsolete accessibility progress wording.
- [x] Update release outcomes/gates and architecture status without deleting historical evidence.
- [x] Run static validation, clean artifacts, and prepare the reconciliation for commit.

## Surprises & Discoveries

- Observation: the release plan’s dependency list still marks most completed UI children unchecked.
  Evidence: the parent plan marks those same children complete and their plans contain current
  validation evidence.
- Observation: support diagnostics and clipboard-copyable UTF-8 logs satisfy the current privacy-safe
  support surface without adding a risky new clipboard path. Evidence: `support_diagnostics.py`,
  AppFrame diagnostic routing, and the existing UI_SPEC support wording.
- Observation: package extraction and private `dpkg --unpack` prove payload behavior but cannot prove
  privileged host installation. Evidence: the package smoke report and sandbox permissions.

## Decision Log

- Decision: perform status reconciliation rather than add diagnostic clipboard behavior. Rationale:
  the current logs are ordinary UTF-8 files and already copyable through the filesystem; no concrete
  defect was observed, while a clipboard feature would expand the slice without a failing contract.
  Date/Author: 2026-08-16 / Codex.
- Decision: retain the release plan open for display-backed, privileged, and final cross-surface
  acceptance. Rationale: those requirements cannot be proven by offscreen or private-root tests.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The release plan now identifies completed local support/package evidence and only the genuine
external gates as open. Historical progress entries remain audit records. No source, test, package,
persisted format, or product compatibility surface changed.

## Context and Orientation

`help_catalog.py` and the Help viewer/CLI own local packaged Help. `support_diagnostics.py`, AppFrame,
and support dialogs own privacy-safe diagnostics and support commands. The accessibility child owns
deterministic real-Qt/offscreen names, roles, keyboard, and minimum-size evidence. The package audit
script owns extraction and private install-root checks. The parent plan owns final display-backed and
privileged release gates.

## Plan of Work

Mark completed children in the release plan’s dependency list according to the parent and child
evidence. Rewrite the release progress/outcomes to distinguish Help, diagnostics, accessibility
offscreen, and private package installation from display-backed and privileged acceptance. Reconcile
the accessibility child’s stale completion tail and record its actual focused test/evidence result.
Update architecture only where a present-tense ownership or release claim contradicts current code.

## Concrete Steps

From `/home/daekar/FoliaSeal`:

    rg -n "^[-*] \[ \]|not implemented|create.*test|commit|display-backed|privileged|diagnostic|package" docs/ExecPlans/ui_product_support_and_release_execplan.md docs/ExecPlans/ui_accessibility_acceptance_execplan.md
    rg -n "support_diagnostics|HelpCatalog|Restore defaults|accessibility|dpkg --unpack" src tests scripts docs/ARCHITECTURE.md
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    git diff --check

The final status must contain documentation-only changes, no generated package or QA artifacts, and
no FoliaSeal/PySide6/pytest process.

## Validation and Acceptance

Acceptance is truthful release status: completed local support/accessibility/package children are
checked and linked to evidence; display-backed screen-reader/high-contrast/DPI/monitor checks and
privileged host installation remain explicitly open; no full-release claim is made. Static checks and
process/artifact cleanup pass.

## Idempotence and Recovery

This is documentation-only and safe to repeat. Preserve historical evidence and remove only temporary
audit roots created during validation. Never delete package fixtures, user data, or private material.

## Artifacts and Notes

Record the completed child paths, focused/offscreen/package evidence, remaining external gates, and
the commit hash. Do not commit generated `.deb` files, screenshots, logs, keys, or temporary roots.

## Interfaces and Dependencies

No Python interface changes are allowed. The slice depends on current Help, diagnostics, accessibility,
package-audit, parent-plan, and architecture ownership records. After this reconciliation, the next
work requires a display-enabled/privileged environment or a fresh audit identifying a concrete code
defect.

Revision note: 2026-08-16 / Codex
Reconciled support/release dependency markers and accessibility status; local evidence is complete
for Help, diagnostics, offscreen accessibility, and isolated package installation, while
display-backed, privileged-host, and final cross-surface release gates remain open.
