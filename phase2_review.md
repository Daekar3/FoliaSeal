# Phase 2 Kickoff Review

Date reviewed: 2026-03-27 (UTC)
Reviewer: Codex agent

## Guidance reviewed
- Functional requirements FR-9, FR-12, FR-13, FR-15, FR-16, FR-17 from the implementation plan.
- Architecture guidance for `presentation.qt`, `application`, and `infra` module responsibilities.
- Delivery milestone expectations for Phase 2 (viewer + coordinate correctness platform).

## Key implementation implications for Phase 2
1. Introduce a renderer abstraction in `infra` so the UI is insulated from backend-specific APIs.
2. Centralize coordinate math in `application` utilities rather than widget event handlers.
3. Validate signature rectangle bounds against the effective page box before signing.
4. Start with a fallback/unavailable backend diagnostic path so UI can degrade gracefully.
5. Build transform tests first to lock deterministic behavior before wiring a concrete Qt renderer.

## Phase 2 work started in this changeset
- Added `infra.render` contracts and a null fallback backend with actionable diagnostics.
- Added deterministic viewer↔PDF coordinate transforms with rotation support (0/90/180/270), zoom, pan, and page box offsets.
- Added rectangle normalization + bounds validation utility for pre-sign checks.
- Added unit tests that cover transform round-trips and invalid input guards.

## Suggested next implementation steps
1. Add a concrete Qt-based render adapter behind `PdfRenderBackend`.
2. Build a lightweight render cache policy object and unit tests.
3. Wire the transform helpers into a simple interactive preview widget prototype.
4. Capture baseline first-render / navigation timing metrics for Phase 2 exit criteria.

## Error review findings (2026-03-27 follow-up)
- **Gap found:** coordinate transforms did not reject invalid page boxes (zero/negative width or height), which could silently produce nonsensical placements.
- **Fix applied:** added explicit `PageBox` validation across conversion and bounds-check functions, with regression tests.
- **Gap found:** no cache policy primitive existed yet for rendered page buffers.
- **Fix applied:** added an in-memory LRU cache policy object (`RenderCachePolicy`) plus unit tests for hit, eviction, and invalidation behavior.
