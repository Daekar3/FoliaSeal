# Bounded appearance content and layout controls

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can configure and preview bounded signing-meaningful Appearance content, image, typography, color, and time controls in the real FoliaSeal GUI. It is mapped to SPEC Appearance semantics and UI_SPEC section 9. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [ ] docs/ExecPlans/ui_appearance_editor_transaction_execplan.md
- [ ] docs/ExecPlans/ui_certificate_selection_readiness_execplan.md

## Progress

- [ ] (2026-08-09) Audit current behavior and add a failing focused test.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; clean processes and artifacts.
- [ ] (2026-08-09) Update this plan and relevant docs, then commit.

## Surprises & Discoveries

- Observation: appearance content is assembled from reusable models, layout, and font registry
  seams; this child must preserve field-order and Unicode behavior through preview and signing.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible bounded appearance content and layout controls outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. Record the demonstrated behavior, evidence, and remaining gaps at completion.

## Context and Orientation

The relevant code is reusable_signing_models.py; domain appearance models; visible_signature_setup_form.py; signature layout/fit modules. FoliaSeal is a Python/Qt Linux PDF signing application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “phase3” names identify legacy
evidence/harness infrastructure and must not be introduced into ordinary product UI or new primary
contracts; production backend/evidence imports may be renamed only after a neutral migration proves
the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named modules, focused tests,
bounded ignored local evidence, and minimum truthful documentation. Do not mix unrelated evidence
rebaselines, V2 features, or packaging work.

## Plan of Work

Implement the bounded field set and visibility/order controls, Compact versus Stacked text, independent image position and prominence, image-only semantics, standardized signing statement, bounded time formats, solid colors, border/background rules, and exact bundled font choices. Reject arbitrary decorative fields and silently shrinking text. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.
Any persisted appearance-field change requires a before/after serialized fixture and backward-read
or deliberate rejection test; otherwise prove existing appearance fixtures remain readable.

## Milestones

Milestone 1 audits the named models, layout functions, and existing focused tests and adds a red
test for the user-visible appearance outcome. Milestone 2 wires the smallest complete model,
application, and Qt path, keeping saved state separate from the active draft. Milestone 3 runs the
focused suite, records the required GUI observation for this slice, removes only proven cruft, and
updates this plan with cleanup and handoff evidence.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

    rg -n -e 'Appearance|image|font|color|datetime|field_order' src/foliaseal/application/reusable_signing_models.py src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/signature_font_registry.py
    .venv/bin/pytest -q tests/unit/test_signature_appearance_models.py tests/unit/test_visible_signature_layout.py tests/unit/test_signature_font_registry.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the stated user-visible behavior plus a mandatory Qt-test or display-backed
walkthrough. Record the exact input sequence, widget state, expected observation, evidence path, and
cleanup result; the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance is behavioral: The Appearance editor exposes only signing-meaningful fields and bounded controls; empty/no-content appearances are invalid; saved output can resolve certificate identity and session Reason/Location without placeholders. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Required Acceptance Cases

Image imports accept only content-validated PNG, JPEG, and static GIF; reject animated/vector content,
25 MP or 20 MB inputs, normalize accepted images to managed PNG with EXIF orientation/sRGB/alpha and
metadata stripping, and require explicit confirmation for optimization. Fonts are exact bundled
families with no silent fallback; colors, image prominence, border rules, and bounded time formats
match UI_SPEC.md.

## Evidence Record

Before completion, record the SPEC/UI_SPEC requirement and owned `docs/ui/appearance-profile-editor-exploratory.svg`,
the exact focused command and result, the GUI input sequence and observed field/layout state, the
evidence file path under `artifacts/ui-audits/`, cleanup/process results, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by tests/unit/test_signature_appearance_models.py tests/unit/test_visible_signature_layout.py tests/unit/test_signature_font_registry.py. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
