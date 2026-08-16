# Atomic signing, overwrite safety, passwords, and restriction checks

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can sign and save safely with password prompts, restriction checks, and explicit source replacement in the real FoliaSeal GUI. It is mapped to SPEC Output Behavior and UI_SPEC WF04/WF05/section 16. The
slice is one vertical path through the relevant model, application workflow,
Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [ ] docs/ExecPlans/ui_sign_confirmation_output_policy_execplan.md — the existing action bridge
  already prompts before a ready request and confirms an existing destination, but the full
  confirmation-summary and source-overwrite policy remains open.

## Progress

- [x] (2026-08-10) Audited the live composition. `foliaseal gui` passes no executor, so
  `SigningActionCoordinator.submit()` builds a request and returns without signing; the existing
  `SignPdfUseCase` writes the destination before verification. Added red acceptance coverage for
  lazy default-executor construction and verification-before-replacement.
- [x] (2026-08-10) Implemented the default production executor and staged output transaction.
- [x] (2026-08-10) Reviewed compatibility/acceptance cruft; retained the historical backend only behind the
  neutral lazy executor until its separate migration consumers are gone.
- [x] (2026-08-10) Ran focused, regression, and GUI lifecycle validation; cleaned processes and
  temporary roots. Focused command reports `72 passed`; full suite reports `1272 passed, 20 skipped,
  1 warning`; Ruff and `git diff --check` are clean. The bounded launch reports the known
  `SingleInstanceUnavailable` socket limitation with `launch_rc=1`, then cleanup succeeds.
- [x] (2026-08-10) Updated this plan, `docs/ARCHITECTURE.md`, and the parent plan; committed the
  bounded increment. Explicit source overwrite, richer frozen-time confirmation, asynchronous
  progress/recovery, and package acceptance remain incomplete.

## Surprises & Discoveries

- Observation: the current CLI/GUI composition can construct a coordinator with
  `sign_executor=None`; this child must wire the default executor before claiming atomic output
  behavior.
  Evidence: src/foliaseal/presentation/qt/signing_action_coordinator.py:52-107 and the live source
  paths listed below.
- Observation: the existing action bridge already supplies a confirmation and output-overwrite
  prompt, so default executor wiring can be delivered independently of the later richer summary
  dialog. The executor must still reject same-path writes until the explicit source-overwrite policy
  child changes that contract.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible atomic signing, overwrite safety, passwords, and restriction checks outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: introduce a neutral lazy executor adapter whose production factory imports the historical
  backend only on first sign, and stage/verify output before replacement while retaining the existing
  same-input/output rejection.
  Rationale: the GUI becomes usable without loading heavy signing dependencies at frame construction;
  verification failures cannot replace an existing destination, and the separate source-overwrite
  policy remains explicit rather than being silently broadened.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The default GUI composition now supplies `LazySigningRequestExecutor`, so a ready request no longer
silently returns without execution. `SignPdfUseCase` writes to a sibling `.tmp`, verifies that path,
and atomically replaces the requested destination only after verification; all failure paths remove
the temporary file and preserve an existing destination. The plan remains open for explicit
same-source overwrite, richer frozen-time confirmation contents, asynchronous progress/recovery,
and installed-package acceptance.

## Context and Orientation

The relevant code is sign_pdf_use_case.py; signing_completion.py; output_path_policy.py; pdf_compatibility.py; signing action bridge. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

First wire a production default SigningRequest executor for the foliaseal gui path; currently the
CLI can construct a coordinator with sign_executor=None and return only a request. Then implement
the non-cancellable prepare/write/verify transaction: write and verify a sibling temporary output,
including every existing signature, before any destination replacement; retain a byte-for-byte
snapshot of an existing destination until replacement succeeds. Password retry must happen before writing, sibling
temporary output must be used for explicit source overwrite, and atomic replacement occurs only after verified success,
standard Replace confirmation, encryption/restriction preservation checks, and safe recovery artifact
ownership. Use typed application contracts and public Qt ports, not private child-widget reach-through.
Keep persistent objects and secrets within the schemas/storage rules. Retire obsolete compatibility
paths only after proving their consumers migrated, and record every retirement in the Decision Log.

## Milestones

Milestone 1 wires and tests the default GUI signing executor. Milestone 2 stages output, verifies
the sibling file, and only then replaces the destination while preserving drafts on failure.
Milestone 3 exercises password, restriction, overwrite, and recovery cases, records byte-preserving
evidence, and performs cleanup.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'overwrite|temporary|verify|password|restriction' src/foliaseal/application/sign_pdf_use_case.py src/foliaseal/application/signing_completion.py src/foliaseal/application/output_path_policy.py src/foliaseal/application/pdf_compatibility.py
    .venv/bin/pytest -q tests/unit/test_sign_pdf_use_case.py tests/unit/test_signing_executor.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py
    # 72 passed
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest|build_deb|build_pyinstaller' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the staged-output byte comparison, password/restriction results, and mandatory
Qt/integration observation of confirmation and recovery; the bounded timeout is only a lifecycle
check. Record temporary-file and process cleanup explicitly; package evidence belongs only to the
final release plan.

## Validation and Acceptance

Acceptance is behavioral: A source overwrite never changes the original before signing and verification succeed; an existing destination requires explicit confirmation; password or restriction failures preserve the draft and original source. Focused tests and the full suite must pass; the
final acceptance record must distinguish headless evidence from real Qt interaction and must include
cleanup evidence.

## Required Acceptance Cases

A password prompt precedes writing and wrong passwords retry without consuming the draft. Source
replacement writes and verifies a sibling temporary file and replaces the source only afterward;
if verification fails, the original source or pre-existing destination remains byte-for-byte
unchanged. Existing
encryption and restrictions are preserved or signing is blocked; final verification evaluates every
signature; pre-final failures remove only owned temporary output and post-write failures preserve the
artifact with recovery actions.

## Evidence Record

Current evidence for the bounded increment: the new lazy-executor and staged-output tests were red
before implementation and the focused command now reports `72 passed`; the complete suite reports
`1272 passed, 20 skipped, 1 warning` in 47.96 seconds; Ruff and `git diff --check` pass. The
verification-failure test proves an existing destination remains byte-for-byte unchanged and no
`.output.pdf.*.tmp` remains. The fake Qt frame test proves the default executor is present without
injecting a harness executor. The bounded GUI launch exits `1` with the known isolated
`SingleInstanceUnavailable` socket limitation, then its temporary root is removed and no matching
FoliaSeal/PySide6/pytest process remains. No SVG was added because this increment adds no new
topology. Full password/source-overwrite/recovery evidence remains required before this plan closes.

Before final completion, record the exact password/overwrite/recovery test command and result, the
GUI input sequence and observed confirmation/error state, the evidence path, byte-preservation and
cleanup results, and compatibility grep proof.

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
exercised by tests/unit/test_sign_pdf_use_case.py tests/unit/test_signing_completion.py tests/unit/test_output_path_policy.py tests/unit/test_pdf_compatibility.py. New help/diagnostic surfaces must not expose secrets, PDF contents, selected
text, Reason, Location, or private keys.

Revision note: 2026-08-09 / Codex
Created as the final dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.

Revision note: 2026-08-10 / Codex
Completed the default GUI executor and verification-before-replacement increment. The plan stays
open for explicit source overwrite, richer confirmation, asynchronous recovery, and release/package
acceptance.
