# QtPdf link-inspection prerequisite

This ExecPlan is a living document maintained under `.agents/skills/write-execplan/PLANS.md`. It
is an AFK prerequisite child of
`docs/ExecPlans/ui_safe_links_external_changes_execplan.md` and the UI compliance parent.

## Purpose / Big Picture

Expose one neutral, read-only page-link DTO from the installed QtPdf renderer so the safe-links
child can perform Pan-only hit testing through the existing `document_safety.py` policy. This slice
does not activate URLs, open destinations, reload documents, or mutate a signing draft.

## Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are governing contracts.
- [x] `docs/ExecPlans/ui_safe_links_source_safety_contracts_execplan.md` supplies the pure
  allow/confirm/block policy.
- [x] `docs/ExecPlans/ui_readiness_caveats_status_execplan.md` supplies source-safety readiness
  gating without claiming link activation.
- [ ] `docs/ExecPlans/ui_safe_links_external_changes_execplan.md` still owns hit testing, history,
  confirmation UI, and changed-source banner behavior.

## Progress

- [x] (2026-08-10) Audited the QtPdf installation and confirmed `QPdfLinkModel` exposes link,
  rectangle, URL, target-page, location, and zoom roles.
- [x] (2026-08-10) Added neutral `DocumentLink`/`DocumentLinkInspector` contracts and a QtPdf
  adapter that normalizes top-left Qt coordinates into PDF bottom-left rectangles.
- [x] (2026-08-10) Added generated-PDF integration coverage for internal, HTTPS, mailto, and file
  destinations, plus DTO multi-rectangle preservation and policy classification.
- [x] (2026-08-10) Completed focused validation (`3 passed`) and full regression (`1401 passed,
  20 skipped, 1 warning`); Ruff, `pip check`, and diff checks are clean. The bounded offscreen GUI
  audit exits at the known isolated `SingleInstanceUnavailable` endpoint, leaves no FoliaSeal
  process, and removes its owned temporary root.
- [x] (2026-08-10) Updated existing Qt binding fixtures for the expanded private adapter seam and
  committed the complete prerequisite as `feat(pdf): add QtPdf link inspection boundary`.

## Decision Log

- Decision: keep link inspection as a separate optional protocol instead of expanding the generic
  `PdfRenderBackend` contract.
  Rationale: null/fake/raster backends do not need link support, and safe activation must remain a
  separate policy-driven presentation concern.
  Date/Author: 2026-08-10 / Codex
- Decision: normalize QtPdf's top-left rectangles at the infrastructure boundary.
  Rationale: application and domain geometry already use PDF bottom-left coordinates; converting
  once prevents duplicated or inconsistent hit-test arithmetic in future Qt callers.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The QtPdf adapter now returns safe, neutral page-link facts and leaves all destination activation
and workspace mutation to later children. Focused validation is `3 passed`; full regression is
`1401 passed, 20 skipped, 1 warning`. The bounded offscreen GUI audit reaches the known isolated
`SingleInstanceUnavailable` endpoint with no leftover process or temporary root.

## Validation and Acceptance

`tests/integration/test_qt_pdf_link_inspection.py` must prove generated internal, HTTPS, mailto,
and file links are extracted with correct rectangles and then classified by the pure safety policy.
Ruff, the full suite, `pip check`, and diff checks must pass. The bounded GUI lifecycle audit must
remove its owned temporary root and leave no FoliaSeal process; it is not proof of link activation.
The current fixture intentionally proves the unrotated, zero-origin page boundary; the future
Pan-only hit-testing child must add non-zero page-box and rotated-page evidence before claiming
production interaction coverage.

## Interfaces and Dependencies

`src/foliaseal/application/document_links.py` remains Qt-free. `QtPdfRenderBackend.inspect_links()`
is a concrete optional capability and may be adapted by the future safe-links viewer bridge. No
URL launcher, subprocess, reload operation, history mutation, or product-facing acceptance terminology
may be introduced by this child.

Revision note: 2026-08-10 / Codex. Created after the safe-links review found that QtPdf link
annotation extraction was the strongest independently testable prerequisite.
