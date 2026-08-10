# Typed safe-link and source-change safety contracts

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK prerequisite child of
`docs/ExecPlans/ui_safe_links_external_changes_execplan.md` and the parent
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`.

## Purpose / Big Picture

FoliaSeal must never let a PDF link launch an unsafe destination or silently replace a document
whose source changed while a signing draft is active. The full Qt behavior is not yet possible
because the current viewer renders only raster pages and has no link or reload seam. This slice
creates the pure, typed application contracts that make those later GUI integrations deterministic:
one classifier returns allow/confirm/block for destinations, and one source-change model returns
unchanged, reload-or-ignore, or locate-or-close. A human can observe the result by running the new
unit tests; no GUI claim is made until the render and workspace seams exist.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are frozen governing contracts.
- [x] `docs/ExecPlans/ui_pdf_navigation_zoom_pan_execplan.md` is implemented and reconciled.
- [ ] `docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md` remains open for the eventual
  draft-preserving reload operation.
- [ ] `docs/ExecPlans/ui_safe_links_external_changes_execplan.md` remains open for render hit
  testing, banners, and Qt wiring.

## Progress

- [x] (2026-08-10) Audited the safe-links parent plan, UI_SPEC section 16, raster render boundary,
  viewer widget, and workspace lifecycle; confirmed that the requested full GUI slice has two
  architectural prerequisites rather than an isolated missing callback.
- [x] (2026-08-10) Added the first red focused test for internal destinations, then iterated
  vertically through external confirmation, blocked schemes, and source-change cases; the focused
  matrix now reports 14 passing tests.
- [x] (2026-08-10) Implemented the typed application contracts with no Qt or renderer coupling.
- [x] (2026-08-10) The initial contract baseline ran 14 focused tests and 1332 full-suite tests
  (20 skipped, 1 warning), plus Ruff and diff validation; the bounded GUI launch reached the known
  isolated single-instance endpoint limitation and left no FoliaSeal/python process or temporary
  audit root.
- [x] (2026-08-10) Reconciled this plan, the safe-links parent, and the compliance parent; the
  initial contract slice was committed in `0c9b20564`, while hardening remains tracked separately.

## Surprises & Discoveries

- Observation: the current `PdfRenderBackend` exposes page rasters and geometry but no PDF link
  rectangles or destinations, so link activation cannot be implemented safely in the widget alone.
  Evidence: `src/foliaseal/infra/render/base.py` and `src/foliaseal/infra/render/qt_backend.py` have
  no link projection API.
- Observation: opening a new path replaces the entire workspace and would discard the signing draft;
  a source reload must be a separate typed operation. Evidence: `app_frame.py` and
  `app_frame_workspace_open.py` compose a new `WorkspaceHandle` for each open path.

## Decision Log

- Decision: implement pure destination and source-change contracts before touching Qt or the PDF
  renderer. Rationale: the safety policy must be testable independently and prevents an unsafe
  partially-wired click path. Date/Author: 2026-08-10 / Codex.
- Decision: classify `http`, `https`, and `mailto` as confirmation-required; allow only internal
  page destinations; block file, executable, JavaScript, embedded-launch, and unknown schemes.
  Rationale: this is the explicit UI_SPEC section 16 policy. Date/Author: 2026-08-10 / Codex.
- Decision: represent source changes as condition-only decisions (`unchanged`, `changed`, `missing`,
  or `unknown`) with actions (`none`, `reload_or_ignore`, `locate_or_close`, or
  `review_required`). Rationale: a later banner can render these values without inventing a reload
  operation or auto-reloading, and unavailable identity must never be treated as equality.
  Date/Author: 2026-08-10 / Codex.

## Outcomes & Retrospective

The pure `document_safety` module now makes the UI_SPEC section 16 policy executable without Qt or
I/O. Internal page destinations are allowed only with a valid page index; HTTP, HTTPS, and mailto
require confirmation; file, executable, JavaScript, embedded-launch, unknown, empty, and invalid
destinations are blocked. Source fingerprints project to unchanged/no action, changed/reload-or-
ignore, missing/locate-or-close, or unknown/review-required when either identity is unavailable.
The contracts never launch, open, read, reload, or mutate a workspace. The remaining GUI work is
explicitly handed to the renderer and lifecycle children.

## Context and Orientation

`docs/UI_SPEC.md` section 16 says Pan mode may follow internal links with Back/Forward history;
`http`, `https`, and `mailto` require confirmation; file, executable, JavaScript, arbitrary-scheme,
and embedded-launch actions are blocked; Select and Place clicks never activate links. The same
section says an external source change never auto-reloads: a changed source offers Reload or Ignore,
and a missing source offers Locate or Close. The current viewer is raster-only, so this child does
not pretend to implement hit testing. The source path is the document opened in
`src/foliaseal/application/viewer_workflow.py`; the future Qt banner belongs at the app-frame or
workspace boundary, not inside the PDF raster widget.

## Change Slice

Primary change class: behavior contract plus focused tests. Allowed files are the new application
module, its focused unit tests, this child plan, and the minimum parent-plan status update. Do not
mix renderer extraction, Qt widgets, source-reload mutation, packaging, or unrelated documentation.

## Plan of Work

Create `src/foliaseal/application/document_safety.py` with immutable enums and result dataclasses.
`classify_link_destination(raw_destination: str | None, *, internal_page_index: int | None = None)`
must return an internal-page result only when a valid page index is supplied and the destination is
not an external scheme. It must normalize the scheme case-insensitively, trim whitespace, reject
empty/unknown destinations as blocked, and never resolve or open a path. External results must carry
the display destination but no executable callback. Add `SourceChangeStatus` and
`SourceChangeDecision`, plus `source_change_decision(*, exists: bool, observed_fingerprint: tuple[object,
...] | None, current_fingerprint: tuple[object, ...] | None)`; unchanged returns no action, changed
returns `reload_or_ignore`, missing returns `locate_or_close`, and an existing source with either
fingerprint unavailable returns `review_required`. Keep the fingerprint opaque: this slice does not
read files or monitor mtime.

Add `tests/unit/test_document_safety.py` covering every scheme and case, whitespace/case
normalization, missing/invalid internal page indexes, unchanged/changed/missing/unknown source decisions,
and the invariant that no classifier result exposes a launcher or performs I/O. Export the module
through `src/foliaseal/application/__init__.py` only if the repository's lazy export convention
requires it; otherwise import the module directly to avoid unnecessary public surface.

Update `docs/ExecPlans/ui_safe_links_external_changes_execplan.md` with this prerequisite and its
remaining renderer/workspace work, and add this child to the compliance parent as an open child.

## Milestones

Milestone 1 is a red test matrix proving the policy is absent. Milestone 2 adds the pure classifier
and source-change projection and turns the matrix green. Milestone 3 runs the full repository
validation and records the exact handoff: renderer link extraction, Pan-only hit testing, typed
draft-preserving reload, and a condition-only Qt banner are still required.

## Concrete Steps

Run every command from `/home/daekar/FoliaSeal` using the repository virtual environment:

    .venv/bin/pytest -q tests/unit/test_document_safety.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Expected focused output is `N passed`; the full suite must remain green. Run the bounded lifecycle
check with an isolated temporary configuration root as in the parent plan. If it exits with
`SingleInstanceUnavailable`, record that known environment limitation, verify no FoliaSeal/python
process remains, remove the temporary root, and continue; do not treat that transport limitation as
evidence that the safety contracts failed.

## Validation and Acceptance

Acceptance is observable through tests: every UI_SPEC section 16 destination class maps to exactly
one safe decision; internal page links are inert without a page index; external destinations require
confirmation; unsafe and unknown destinations are blocked; unchanged/changed/missing/unknown source
states map to no action/reload-or-ignore/locate-or-close/review-required without automatic reload.
No test may launch a
process, open a URL, read a PDF, or mutate a workspace. The later GUI plan cannot be marked complete
from this contract evidence alone.

## Evidence Record

Evidence for the initial contract covers UI_SPEC section 16 and WF01/WF05. The current hardened
evidence is recorded in `ui_safe_links_contract_hardening_execplan.md`: 24 focused tests and 1342
full-suite tests (20 skipped, 1 warning); Ruff and `git diff --check` pass. No SVG is owned by this application-only
contract slice. The bounded GUI command exits with the known isolated `SingleInstanceUnavailable`
endpoint limitation; `AUDIT_ROOT_CLEAN=1` and no process output prove cleanup. The red first test
was the missing-module import, followed by vertical red-to-green additions for each policy class.

## Idempotence and Recovery

The module is pure and safe to rerun. If a test or implementation fails, update Progress with the
last green matrix, leave no generated files, and retry from the same source tree. Do not add a
compatibility wrapper or silently fall back to a URL opener.

## Artifacts and Notes

No generated artifacts are required. Record test output and the bounded cleanup result in this plan;
never commit PDFs, URLs, credentials, or machine-local paths.

## Interfaces and Dependencies

The new module must depend only on Python standard-library types. It must not import Qt, pyHanko,
the raster renderer, `subprocess`, `webbrowser`, or filesystem APIs. The future renderer child will
adapt PDF link annotations into the classifier input; the future workspace child will adapt file
fingerprints into `source_change_decision` and preserve the active `SigningDraftWorkflow`.

Revision note: 2026-08-10 / Codex. Created after explorer review found the original safe-links
ExecPlan was architecturally premature; split the policy contracts from renderer and workspace
integration so each step is independently testable and cannot claim unsafe behavior.

Compliance note: 2026-08-10 / Codex. The post-implementation review found unknown fingerprints,
mode gating, malformed internal destinations, and architecture ownership gaps; those corrections
are tracked in `ui_safe_links_contract_hardening_execplan.md`.
