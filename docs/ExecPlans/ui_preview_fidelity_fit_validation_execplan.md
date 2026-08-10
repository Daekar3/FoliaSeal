# Authoritative preview, image/font/time fidelity, and fit validation

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can preview the authoritative signed appearance with frozen time, normalized images, and clear fit/glyph blocking in the real FoliaSeal GUI. It is mapped to SPEC goal 4 and UI_SPEC section 9 and acceptance scenario 5. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_pointer_signature_placement_execplan.md — pointer/keyboard placement,
  snapping, history, and off-page recovery are implemented and reconciled in the parent corpus.
- [x] docs/ExecPlans/ui_appearance_content_layout_execplan.md — managed image semantics,
  staged-file cleanup, and save/reload preview-signing path parity are complete; this child still
  owns authoritative rendered-preview fidelity and glyph/time/readiness evidence.
- [x] docs/ExecPlans/ui_certificate_selection_readiness_execplan.md — typed catalog-backed
  certificate readiness and selected-material projection are implemented and reconciled.

## Progress

- [x] (2026-08-10) Re-audited current behavior and reconciled the placement, Appearance, and
  certificate dependencies against the parent plan; remaining work is the preview-specific
  authoritative parity slice rather than dependency setup.
- [ ] (2026-08-09) Audit current behavior and add a failing focused test.
- [ ] (2026-08-09) Implement the smallest complete model/application/Qt path.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [ ] (2026-08-09) Run focused, regression, and GUI validation; clean processes and artifacts.
- [ ] (2026-08-09) Update this plan and relevant docs, then commit.

## Surprises & Discoveries

- Observation: preview rendering, layout, and fit validation are separate application seams; the
  child must prove parity and page-local recovery rather than treating a rendered bitmap as proof
  of signing readiness.
  Evidence: the live source paths and focused tests listed below are the audit baseline.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible authoritative preview, image/font/time fidelity, and fit validation outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

Not started. Record the demonstrated behavior, evidence, and remaining gaps at completion.

## Context and Orientation

The relevant code is signing_preview_renderer.py; signature_preview_layout.py; preview render adapters; rendered-fit validators; evidence parity helpers. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Make the on-document preview the authoritative representation. Share one render/layout/time snapshot with the signing backend, normalize PNG/JPEG/static GIF imports with EXIF/sRGB/alpha/metadata rules and size limits, and block unsupported glyphs or overflow before submission. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.

## Milestones

Milestone 1 builds deterministic render/layout fixtures and red parity tests. Milestone 2 connects
the preview snapshot, glyph fallback, fit validator, and page-local recovery. Milestone 3 compares
preview with signed output and records the evidence artifact and cleanup.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'render|fit|glyph|time|image' src/foliaseal/application/signing_preview_renderer.py src/foliaseal/presentation/qt/signature_preview_layout.py src/foliaseal/application/visible_signature_fit_validator.py
    .venv/bin/pytest -q tests/unit/test_signing_preview_renderer.py tests/unit/test_signature_preview_layout.py tests/unit/test_visible_signature_fit_validator.py tests/unit/test_visible_signature_rendered_fit_adapters.py
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

Acceptance is behavioral: The preview and signed output use identical content, image alpha, font, geometry, and frozen time; an unsupported glyph, empty appearance, or exact-fit failure blocks signing with field/character guidance. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Required Acceptance Cases

Preview and final output share one render/layout/time snapshot. Unsupported glyphs identify the field
and character; overflow blocks signing without shrinking; empty semantic content is invalid; alpha,
font, geometry, image prominence, and frozen time are equal in preview and signed output.

## Evidence Record

Before completion, record the exact render/layout/fit test command and result, the GUI preview input
sequence and parity observation, owned `docs/ui/appearance-profile-editor-exploratory.svg` agreement,
evidence path, cleanup, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by tests/unit/test_signing_preview_renderer.py,
tests/unit/test_signature_preview_layout.py, tests/unit/test_visible_signature_fit_validator.py,
tests/unit/test_signature_preview_lifecycle.py, and tests/unit/test_visible_signature_rendered_fit_adapters.py.
Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-10 / Codex
Reconciled after the managed-image closeout: placement, Appearance, and certificate-readiness
dependencies are checked against their current implementation evidence. The child remains open
for authoritative preview/signing snapshot parity, unsupported-glyph guidance, frozen-time
mutation coverage, and real readiness/fit-gate integration.
