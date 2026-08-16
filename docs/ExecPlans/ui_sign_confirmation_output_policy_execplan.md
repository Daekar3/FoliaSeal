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
- [x] docs/ExecPlans/ui_readiness_caveats_status_execplan.md — typed readiness projection and
  document-source safety inputs are implemented; the parent ledger remains separately reconciled.

## Progress

- [x] (2026-08-10) Audited the live action bridge, coordinator, draft workflow, output-path policy,
  and staged signing use case. The current confirmation omits exact page/field, frozen time, and
  caveats; same-source output is always rejected; and the new verified sibling staging path has no
  typed authorization for deliberate source replacement.
- [x] (2026-08-10) Add failing focused tests for the typed final summary, collision-safe suggestions,
  Cancel-lossless source-overwrite authorization, and staged same-source replacement; the tests were
  red before implementation and green after the slice.
- [x] (2026-08-10) Implement the smallest complete model/application/Qt path.
- [x] (2026-08-10) Retain the `_paths_conflict` static wrapper because an existing test seam monkeypatches
  it; the wrapper delegates to the new neutral `paths_refer_to_same_file()` policy and is now an
  explicitly documented compatibility boundary rather than dead product surface. No acceptance product
  terminology was introduced or removed in this slice.
- [x] (2026-08-10) Run focused, regression, and GUI validation; clean processes and artifacts:
  current focused confirmation/bridge/shell command is `136 passed`; the current full suite is
  `1440 passed, 20 skipped, 1 warning`; Ruff and diff checks clean; the
  bounded offscreen launch exits at `SingleInstanceUnavailable`, leaves no matching processes, and
  removes its temporary configuration root.
- [x] (2026-08-10) Update this plan and relevant docs and obtain independent compliance review. The
  review led to consequence-labeled buttons, explicit setup synchronization coverage, and removal
  of the broad exception-swallowing fallback. Real display-backed dialog acceptance remains
  environment-blocked at the isolated single-instance endpoint; exact existing-field identity is
  deferred to `ui_signature_field_targeting_profiles_execplan.md`.
- [x] (2026-08-10) Commit the completed slice as `def5ce0f5` and record the next
  dependency-ordered blocker.

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
- Decision: represent deliberate source replacement as an explicit, non-persisted authorization on
  the in-memory signing draft and public `SigningRequest`; ordinary equal input/output paths remain
  rejected by the use case.
  Rationale: the UI must ask a Cancel-default question, while the verified sibling staging/replace
  algorithm can safely support the authorized case without weakening headless callers or persisted
  schemas.
  Date/Author: 2026-08-10 / Codex
- Decision: build the final confirmation text from one typed, Qt-free summary over the existing
  `SigningDraftPreview` and frozen workflow signing time, with page/field and warning-caveat lines.
  Rationale: the preview already owns authoritative visible-signature semantics and warning issues;
  a small application contract prevents Qt from re-deriving signing facts or taking another clock
  reading.
  Date/Author: 2026-08-10 / Codex
- Decision: synchronize visible setup controls before taking the confirmation preview, then present
  consequence-labeled `Sign and save` / `Cancel` buttons with Cancel as the default; retain a Yes/No
  fallback only for legacy test and harness message-box doubles.
  Rationale: the confirmation must describe the same authored draft that the coordinator submits,
  while real users need an unambiguous irreversible-action control and an escape-safe default.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The slice now provides a typed final confirmation summary, collision-safe default output naming,
Cancel-lossless output selection, explicit source-overwrite authorization, consequence-labeled
confirmation controls, and verified staged same-source replacement. The summary is derived from
the synchronized draft, frozen preview time, and warning issues; the authorization is session-local
and resets when the output path changes. Implementation and compliance-review gates are complete;
the remaining work is the closeout commit and future display-backed acceptance once the environment
can claim the single-instance endpoint.

## Context and Orientation

The relevant code is signing_workspace_action_bridge.py; signing_action_coordinator.py; output_path_policy.py; signing sidebar/modal surfaces. FoliaSeal is a Python/Qt Linux PDF signing application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “acceptance” names identify legacy
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

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'confirm|output|Save As|Sign and save' src/foliaseal/presentation/qt/signing_workspace_action_bridge.py src/foliaseal/application/output_path_policy.py src/foliaseal/presentation/qt/signing_action_coordinator.py
    .venv/bin/pytest -q tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_output_path_policy.py tests/unit/test_qt_signing_workspace_action_bridge.py tests/unit/test_qt_signing_shell.py
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
walkthrough. The current bounded launch may stop at the isolated single-instance endpoint; record
that exact limitation rather than treating it as a signing-flow success. Record Save/Sign/Replace inputs, observed wording, evidence path, and cleanup result;
the bounded timeout is only a lifecycle check. Package evidence belongs only to the final release plan.

## Validation and Acceptance

Acceptance is behavioral: A ready user must confirm before signing; the dialog shows the active
objects, exact destination, page/field, frozen time, and caveats; first Save opens a standard save
dialog; cancelling changes neither draft nor output; source replacement uses a distinct
Cancel-default warning; and signed bytes are verified before any replacement. Focused tests and the
full suite must pass; the final acceptance record must distinguish headless evidence from real Qt
interaction and must include cleanup evidence.

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

Record the contributing UI_SPEC scenario ID(s) (WF04 §11) and either the owning SVG path or an explicit
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
exercised by tests/unit/test_qt_signing_action_coordinator.py tests/unit/test_output_path_policy.py tests/unit/test_qt_signing_workspace_action_bridge.py tests/unit/test_qt_signing_shell.py. New help/diagnostic surfaces must not expose secrets, PDF contents, selected
text, Reason, Location, or private keys.

Revision note: 2026-08-10 / Codex
Implemented and reviewed the confirmation/output-policy vertical slice after the live audit and
red/green tests; updated the acceptance contract, compatibility note, and evidence requirements.
Current focused evidence is `136 passed`; full regression and cleanup are recorded; display-backed
acceptance is explicitly environment-blocked. Documentation closeout is committed as
`def5ce0f5`; the next dependency-ordered blocker is display-backed acceptance when a usable
single-instance GUI environment is available.
