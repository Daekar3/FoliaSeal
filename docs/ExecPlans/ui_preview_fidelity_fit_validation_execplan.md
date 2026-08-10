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
- [x] (2026-08-10) Audited the current preview and signing seams. The workflow already freezes a
  signing time and the backend already prepares one immutable layout plan, but preview validation
  lacks font-codepoint coverage and the Qt readiness surface does not identify the offending field
  and character. The next implementation seam is the shared semantics service, followed by the
  real setup/readiness projection and parity tests.
- [x] (2026-08-10) Added red tests for unsupported glyphs, field/character guidance, and frozen
  preview time reaching the final request; the pre-change collection failed at import because the
  new glyph contract did not exist.
- [x] (2026-08-10) Implemented the shared semantics path: inspect the exact
  bundled font cmap, emit a blocking glyph issue without system fallback, keep the resolved
  semantics and frozen time shared by preview/signing, and surface the issue through readiness.
- [x] (2026-08-10) Added materialized preview/backend layout-plan parity coverage for a glyph-safe
  appearance and a glyph-blocked workflow/request case.
- [ ] (2026-08-10) Complete authoritative rendered-preview parity evidence, including exact-fit
  blocking, managed-image alpha, and one offscreen GUI walkthrough.
- [ ] (2026-08-09) Retire migrated compatibility or phase3 product cruft whose consumers are gone.
- [ ] (2026-08-10) Validation is complete for focused tests (`139 passed`), full regression
  (`1390 passed, 20 skipped, 1 warning`), Ruff, `pip check`, and owned temporary cleanup; the real
  launch still stops at `SingleInstanceUnavailable` before window creation, so display-backed or
  test-adapter GUI evidence remains.
- [ ] (2026-08-10) Update this plan and relevant docs, then commit.

## Surprises & Discoveries

- Observation: preview rendering, layout, and fit validation are separate application seams; the
  child must prove parity and page-local recovery rather than treating a rendered bitmap as proof
  of signing readiness.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: `SigningDraftWorkflow.preview()` freezes `_preview_signing_time`, and
  `build_signing_request()` already carries that value when the draft fingerprint is unchanged;
  the missing trust gate is character coverage, not a second timestamp implementation.
  Evidence: `src/foliaseal/application/signing_draft_workflow.py` and
  `tests/unit/test_signing_draft_workflow.py::test_preview_signing_time_is_invalidated_by_draft_mutation`.
- Observation: the bundled font files expose a finite cmap and Pillow/Qt can otherwise silently
  substitute a missing glyph. A deterministic cmap check is therefore required before fit/render
  validation.
  Evidence: `fontTools.ttLib.TTFont(...).getBestCmap()` reports no snowman/emoji coverage in the
  bundled Noto faces while DejaVu Sans Mono covers the snowman.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible authoritative preview, image/font/time fidelity, and fit validation outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: perform glyph coverage in the application semantics service using the exact resolved
  bundled face, and report the first unsupported printable character with its field name.
  Rationale: both the Qt preview and final backend already consume the semantics contract; a
  single validator prevents target-specific fallback and keeps the readiness gate authoritative.
  Date/Author: 2026-08-10 / Codex
- Decision: retain the existing frozen-time fingerprint mechanism and add parity assertions rather
  than introducing a second preview snapshot object in this slice.
  Rationale: the current workflow already passes the frozen time into `SigningRequest`; duplicating
  that state would increase drift risk without improving the user-visible contract.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The implementation is not yet complete. The plan currently has a verified dependency baseline and
an identified glyph/readiness gap; record the focused red/green evidence and any remaining UI
polish gaps after implementation.

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

Make the on-document preview the authoritative representation. Share the workflow's resolved
semantics, frozen signing time, managed image path, and canonical layout policy with the signing
backend; normalize PNG/JPEG/static GIF imports with EXIF/sRGB/alpha/metadata rules and size limits;
and block unsupported glyphs or overflow before submission. Add or preserve typed application and
public Qt-port boundaries rather than reaching through private widgets. Keep schema and terminology
aligned with the frozen documents. When a legacy path is replaced, prove its callers are migrated
before deleting it.

## Milestones

Milestone 1 adds deterministic glyph and frozen-time red tests. Milestone 2 connects the shared
semantics validation to the Qt readiness/sign gate and preserves canonical layout/image parity.
Milestone 3 compares preview with signed output and records the evidence artifact and cleanup.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'render|fit|glyph|time|image' src/foliaseal/application/signing_preview_renderer.py src/foliaseal/presentation/qt/signature_preview_layout.py src/foliaseal/application/visible_signature_fit_validator.py src/foliaseal/application/signature_font_registry.py
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

Current evidence: the pre-change glyph contract test failed during collection because
`unsupported_glyphs` was absent; the focused semantics/coordinator/workflow/renderer set now passes
`139 passed`, and the full suite passes `1390 passed, 20 skipped, 1 warning`. `pip check` reports no
broken requirements after making FontTools an explicit runtime dependency. The materialized parity
test is `tests/unit/test_signing_preview_renderer.py::test_materialized_preview_and_signing_share_layout_and_block_unsupported_glyph`.
The bounded real-launch audit uses an isolated `/tmp/foliaseal-preview-audit-*` root and currently
returns `SingleInstanceUnavailable` before Qt window creation in this headless environment; the
owned root is removed and no FoliaSeal process remains. A display-backed or test-adapter walkthrough
is still required before this child can close.

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
Reconciled after the managed-image closeout and glyph/frozen-time implementation. Placement,
Appearance, and certificate-readiness dependencies are checked against current evidence; exact
bundled-font cmap validation now reaches preview/readiness/request construction. The child remains
open for rendered preview/signing artifact parity, managed-alpha evidence, exact-fit/readiness
walkthrough, and the bounded GUI limitation described above.
