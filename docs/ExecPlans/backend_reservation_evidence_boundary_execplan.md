# Move Backend Reservation Evidence Behind a Core Boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the temporary Qt Phase 3 harness will no longer reconstruct backend reservation evidence by calling private layout and signing helpers itself. Instead, one core application/backend boundary will build the reservation snapshot and reservation error from a `SigningRequest`, and the harness will only serialize and display the returned information. A user will still see the same `backend_reservation_snapshot` and `backend_reservation_error` fields in Phase 3 evidence, but the UI layer will be thinner and easier to discard or replace later.

You can see the change working by running the focused Phase 3 backend and harness tests after implementation. The same evidence fields should still be present, but the direct helper choreography will live outside `src/foliaseal/presentation/qt/phase3_harness.py`.

## Child ExecPlan Dependencies

- [x] (2026-05-24 22:56Z) No child ExecPlans are required for this bounded boundary-extraction slice.

## Progress

- [x] (2026-05-24 22:56Z) Explored the current harness/backend seam and confirmed that `_snapshot_backend_reservation()` and `_backend_reservation_error()` still reconstruct backend state inside the Qt harness.
- [x] (2026-05-24 22:56Z) Wrote this ExecPlan before implementation.
- [x] (2026-05-25 03:23Z) Added `BackendReservationEvidence` and `build_backend_reservation_evidence()` in `src/foliaseal/application/phase3_signing_backend.py`.
- [x] (2026-05-25 03:28Z) Rewired `src/foliaseal/presentation/qt/phase3_harness.py` to consume the backend evidence boundary while preserving `backend_reservation_snapshot` and `backend_reservation_error`.
- [x] (2026-05-25 03:41Z) Moved detailed reservation evidence assertions into `tests/unit/test_phase3_signing_backend.py` and kept `tests/unit/test_phase3_harness.py` focused on delegation and capture wiring.
- [x] (2026-05-25 04:18Z) Fixed the extracted evidence serializer to normalize both enum-backed and string-backed layout-rule values and stabilized the snapshot `error` key.
- [x] (2026-05-25 04:26Z) Ran focused validation, updated `docs/ARCHITECTURE.md`, and brought this ExecPlan to completion state.

## Surprises & Discoveries

- Observation: the harness still reconstructs backend reservation state directly instead of consuming a stable core boundary.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` defines `_snapshot_backend_reservation()` and `_backend_reservation_error()` that call `_load_simple_signer`, `_current_signing_time`, `_build_stamp_text`, `_stamp_background_for_path`, `VisibleSignatureLayoutEngine().plan`, `_background_layout_for_stamp`, and `_build_stamp_style`.

- Observation: most of the detailed reservation assertions are still attached to harness-named helpers even though the behavior itself is backend logic.
  Evidence: `tests/unit/test_phase3_harness.py` contains `test_backend_reservation_snapshot_*` coverage for layout-fit numbers, field-derived values, and error details.

- Observation: the first extracted serializer pass assumed pyHanko-like enum objects for all layout-rule fields, but the layout-plan path exposes string-backed `LayoutRuleSpec` values instead.
  Evidence: focused pytest initially failed with `"'str' object has no attribute 'value'"` from `build_backend_reservation_evidence()`, and inspection showed `layout_plan.text_layout.x_align`/`y_align` are strings while scaling is exposed through `scaling`, not `inner_content_scaling`.

## Decision Log

- Decision: keep the Phase 3 evidence payload fields stable in this slice.
  Rationale: the goal is to move behavior out of the UI layer, not to refresh artifact contracts or rename capture fields at the same time.
  Date/Author: 2026-05-24 / Codex

- Decision: use a small backend-owned evidence boundary rather than a harness-specific wrapper.
  Rationale: the user explicitly wants UI and core logic separated, and the harness is temporary. The backend/application layer should own the evidence generation seam so the future GUI can reuse it or replace the harness without reintroducing private helper coupling.
  Date/Author: 2026-05-24 / Codex

- Decision: keep this slice behavior-preserving and avoid a broader evidence-platform abstraction.
  Rationale: the highest-value immediate improvement is removing private-helper reconstruction from the harness. A richer extensible probe can be considered later if another caller actually needs it.
  Date/Author: 2026-05-24 / Codex

## Outcomes & Retrospective

This slice is complete.

Implemented results:

- Added `BackendReservationEvidence` plus `build_backend_reservation_evidence()` in `src/foliaseal/application/phase3_signing_backend.py`.
- Removed harness-local reservation reconstruction helpers from `src/foliaseal/presentation/qt/phase3_harness.py`.
- Kept the Phase 3 capture payload fields stable: `backend_reservation_snapshot` and `backend_reservation_error` are still emitted.
- Moved detailed reservation evidence checks into `tests/unit/test_phase3_signing_backend.py`, while the harness suite now proves thin delegation and capture wiring.
- Updated `docs/ARCHITECTURE.md` so the backend owns reservation evidence assembly and the harness is only a consumer.

Validation evidence:

- `pytest tests/unit/test_phase3_signing_backend.py tests/unit/test_phase3_harness.py` passed with `196 passed`.
- `ruff check src/foliaseal/application/phase3_signing_backend.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_signing_backend.py tests/unit/test_phase3_harness.py` passed.
- `git diff --check` passed.

Retrospective:

- The main implementation correction was not architectural but representational: the extracted builder needed a generic layout-rule snapshot helper because the backend evidence path touches both pyHanko-style layout objects and application-layer `LayoutRuleSpec` objects.
- The slice successfully moved logic in the intended direction: the temporary Qt harness is now thinner, while the core/backend module owns the reusable reservation evidence seam that a future non-harness GUI can consume directly.

## Context and Orientation

`src/foliaseal/presentation/qt/phase3_harness.py` contains the temporary interactive Phase 3 harness, the unattended preview matrix entry points, and several helper functions that capture evidence about preview state, sign requests, reservation layout, and signed output. In this repository, “backend reservation evidence” means a JSON-safe summary of how the backend would lay out and validate a visible signature before writing the signed PDF. That evidence currently includes fields such as:

- `layout_template`
- `stamp_position`
- `stamp_text`
- fit-gate dimensions and pass/fail state
- text and box style summaries
- background and content layout summaries
- an `error` string when evidence generation fails

The problem is that the harness currently builds this evidence itself in:

- `src/foliaseal/presentation/qt/phase3_harness.py::_snapshot_backend_reservation`
- `src/foliaseal/presentation/qt/phase3_harness.py::_backend_reservation_error`

Those functions are not simple serializers. They replay backend-private logic by calling helpers that belong to visible-signature signing and layout behavior:

- `_load_simple_signer`
- `_current_signing_time`
- `_build_stamp_text`
- `_stamp_background_for_path`
- `VisibleSignatureLayoutEngine().plan`
- `_background_layout_for_stamp`
- `_build_stamp_style`

That coupling matters because the harness is UI-layer code and is temporary. The core backend logic should be reusable without the harness, and tests should assert the behavior at that core boundary instead of patching private helpers through the harness.

Relevant files for this slice:

- `src/foliaseal/presentation/qt/phase3_harness.py`
- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_phase3_harness.py`
- `tests/unit/test_phase3_signing_backend.py`
- `docs/ARCHITECTURE.md`

## Plan of Work

First, add a backend-owned evidence API in `src/foliaseal/application/phase3_signing_backend.py`. It must accept a `SigningRequest` or `None` and return a small typed result with two JSON-ready pieces: the reservation snapshot and the reservation error. The implementation may continue using current backend-private helpers internally, but those calls must no longer live in the harness.

Second, update `src/foliaseal/presentation/qt/phase3_harness.py` so `_capture_interactive_state()` and any related capture paths consume the new backend API. The harness must keep writing `backend_reservation_snapshot` and `backend_reservation_error` into captured state exactly as before. The harness should become a consumer and serializer only.

Third, move detailed reservation behavior tests down to `tests/unit/test_phase3_signing_backend.py`. That suite should prove:

- successful snapshot shape and key fields
- layout-fit failure details and numbers
- signer-field-derived evidence values
- error text for bad requests or missing certificate material

The harness suite should keep only thin tests that prove delegation, JSON safety, and evidence wiring into the capture payload and markdown summary.

Finally, update `docs/ARCHITECTURE.md` so it reflects that backend reservation evidence is generated by a core backend boundary and merely consumed by the temporary harness.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Inspect the current seam:

    rg -n "_snapshot_backend_reservation|_backend_reservation_error|_build_stamp_text|_background_layout_for_stamp|_build_stamp_style|_current_signing_time" src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signing_backend.py

Edit these files:

    src/foliaseal/application/phase3_signing_backend.py
    src/foliaseal/presentation/qt/phase3_harness.py
    tests/unit/test_phase3_signing_backend.py
    tests/unit/test_phase3_harness.py
    docs/ARCHITECTURE.md
    docs/ExecPlans/backend_reservation_evidence_boundary_execplan.md

Run focused validation:

    pytest tests/unit/test_phase3_signing_backend.py tests/unit/test_phase3_harness.py
    ruff check src/foliaseal/application/phase3_signing_backend.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_signing_backend.py tests/unit/test_phase3_harness.py
    git diff --check

Expected successful outcomes:

- backend tests own the detailed reservation evidence behavior
- harness tests still prove captured evidence fields are wired correctly
- `backend_reservation_snapshot` and `backend_reservation_error` remain present in harness captures

## Validation and Acceptance

This slice is accepted when all of the following are true:

- the Qt harness no longer directly assembles backend reservation evidence from private backend helpers
- the backend/application layer exposes one small evidence API for this reservation snapshot/error behavior
- the Phase 3 harness still emits the same reservation evidence fields
- focused backend and harness tests pass
- `docs/ARCHITECTURE.md` accurately describes the new ownership split

Behavioral proof comes from running:

    pytest tests/unit/test_phase3_signing_backend.py tests/unit/test_phase3_harness.py

and seeing those suites pass with the detailed reservation evidence checks attached to the backend suite rather than the harness suite.

## Idempotence and Recovery

This slice is safe to retry because it is behavior-preserving and does not require schema migration. If the backend evidence API lands but the harness integration fails, keep the backend API in place and restore only the old harness call path long enough to regain green tests. Do not change the evidence payload field names as a recovery shortcut. Do not mix preview-layout behavior changes or signing-output behavior changes into this slice.

## Artifacts and Notes

Pre-change seam evidence:

    src/foliaseal/presentation/qt/phase3_harness.py::_snapshot_backend_reservation
    src/foliaseal/presentation/qt/phase3_harness.py::_backend_reservation_error

Both currently know too much about backend reservation assembly. At the end of this slice, those responsibilities should live behind one backend-owned API.

## Interfaces and Dependencies

Define one backend-owned typed result in `src/foliaseal/application/phase3_signing_backend.py` with a stable small interface. The intended end-state of this slice is:

    @dataclass(frozen=True)
    class BackendReservationEvidence:
        snapshot: dict[str, Any] | None
        error: str | None

    def build_backend_reservation_evidence(
        request: SigningRequest | None,
    ) -> BackendReservationEvidence | None:
        ...

This slice uses the `Local-substitutable` dependency category. The new function stays inside the local backend/application code and may depend internally on existing signing, style, and layout helpers. The harness must not call those helpers directly after the migration.

The harness is allowed to own:

- capture payload assembly
- JSON serialization
- markdown rendering
- Qt event wiring

The harness must stop owning:

- request-to-backend-appearance normalization
- signer loading for reservation evidence
- stamp-text construction for reservation evidence
- layout-fit reconstruction for reservation evidence
- backend-style probing for reservation errors

Revision note: Created on 2026-05-24 by Codex after the architecture exploration identified the remaining backend-reservation reconstruction inside the temporary Qt Phase 3 harness as the next high-leverage deepening slice.
