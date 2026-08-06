# Unify visible-signature layout policy at one neutral boundary

This ExecPlan is a living document and must remain compliant with
`.agents/skills/write-execplan/PLANS.md`. The architecture-loop parent is
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md` and `docs/SPEC.md` is frozen.

## Purpose / Big Picture

Visible-signature spacing and reservation rules currently exist in the canonical application layout
module and in a second copy inside the signing backend. The Qt evidence harness also imports two of
the backend's private margin helpers. After this slice, signing, preview evidence, and capture
padding will ask one neutral `VisibleSignatureLayoutPolicy` for the same geometry facts. A layout
change will therefore have one implementation and one boundary test instead of separate backend and
harness rules. The user-visible proof is unchanged preview/signing parity and fit rejection, while
source inspection proves that the Qt harness no longer reaches backend-private policy names.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` remains frozen and byte-identical.
- [x] The typed prepare-once layout boundary exists in
  `src/foliaseal/application/visible_signature_layout.py`.
- [x] The previous compatibility-bridge slice is closed at `26d05c6d2`; the worktree is clean.
- [x] Scan Round 54 selected this in-process/local-substitutable candidate at Candidate Priority
  approximately `70.14`, with confidence `0.978125`.
- [x] Design Selection 55 selected the stateless common-caller facade at median shape score
  `90.775`, with no hard-gate penalty.

## Progress

- [x] (2026-08-06) Captured the baseline module sizes, duplicate helper inventory, and focused
  layout/backend/harness test boundaries.
- [x] (2026-08-06) Completed three independent designs and two independent reviews; selected the
  constrained stateless `VisibleSignatureLayoutPolicy` facade.
- [x] (2026-08-06) Completed focused implementation-context review of backend imports, harness
  snapshot padding, lazy application exports, and the exact test migration surface.
- [x] (2026-08-06) Added the neutral policy facade and public reservation type with exact legacy
  arithmetic parity, and exported the neutral types through the lazy application boundary.
- [x] (2026-08-06) Migrated application layout internals, signing backend, and Qt harness to the
  facade; removed duplicate backend helpers and backend-private harness policy imports.
- [x] (2026-08-06) Added direct spacing/border/reservation/fit policy tests and migrated the dead
  backend-width assertions to the public facade; retained the existing import-firewall suite.
- [x] (2026-08-06) Focused and full validation passed; architecture documentation is reconciled.
  Offscreen acceptance passed and generated artifacts/processes were cleaned. Commit `bb9e77b2c`
  and three independent closure audits passed; the literal retirement gate was narrowed to
  backend/harness callers so canonical same-module delegates remain intentional.

## Surprises & Discoveries

- Observation: `visible_signature_layout.py` contains the canonical reservation and fit policy, but
  `phase3_signing_backend.py` repeats base spacing, border inset, effective margin, and optical-shift
  arithmetic.
  Evidence: `visible_signature_layout.py:191-238` and `phase3_signing_backend.py:628-716`.
- Observation: `phase3_harness.py` imports `_effective_layout_edge_margin` and
  `_single_line_vertical_outer_margin` from the backend solely to compute preview-capture padding.
  Evidence: `phase3_harness.py:20-23` and `_preview_padding_for_capture()`.
- Observation: the backend's `_effective_horizontal_text_reservation_width` has no source caller and
  is covered only by direct private-helper tests; it is a dead compatibility-shaped assertion rather
  than a second required policy consumer.
  Evidence: `rg` over `src` and `tests/unit/test_phase3_signing_backend.py:849-866`.
- Observation: rendered-ink measurement/materialization and pyHanko fit adapters are behavior-bearing
  implementation details and must remain in their current owners; moving them into a generic policy
  manager would widen the boundary and introduce infrastructure leakage.
  Evidence: `_single_line_rendered_ink_fits_reservation`, `_BackendHorizontalInkMeasurer`, and the
  layout materializer paths in `visible_signature_layout.py` and `phase3_signing_backend.py`.

## Decision Log

- Decision: Keep the facade in `visible_signature_layout.py` instead of creating a second planner or
  policy service module.
  Rationale: that module already owns the canonical neutral reservation, margin, and fit implementation;
  a same-module facade compresses callers without creating a second source of truth or import cycle.
  Date/Author: 2026-08-06 / Codex and design reviewers.
- Decision: Expose `SignatureLayoutReservation` as the neutral reservation type and remove the leading
  underscore rather than retaining a runtime alias.
  Rationale: backend annotations currently leak `_SignatureLayoutReservation`; private names are not
  frozen V1 contracts and the retirement grep can prove all callers migrated in this slice.
  Date/Author: 2026-08-06 / Codex.
- Decision: The facade exposes only neutral geometry operations: `spacing`, `border_safe_inset`,
  `effective_edge_margin`, `margins`, `reservation`, `ensure_fit`, and
  `horizontal_text_reservation_width`. Rendered-ink measurement, Qt, Pillow, pyHanko, and artifact
  operations remain outside it.
  Rationale: this is the smallest common boundary that removes the documented duplicate policy while
  preserving ownership of environment-specific behavior.
  Date/Author: 2026-08-06 / Codex and design reviewers.
- Decision: Do not rename any `phase3` module, command, DTO, JSON key, fixture, or artifact here.
  Rationale: `phase3_nomenclature_retirement_execplan.md` is a separate atomic contract migration;
  mixing it with geometry changes would make parity failures ambiguous.
  Date/Author: 2026-08-06 / Codex.

## Outcomes & Retrospective

Baseline commit `26d05c6d2` had 1,899 lines in the canonical layout module, 1,225 lines in the
signing backend, and 1,832 lines in the Qt harness. After implementation, the modules measure 2,009,
1,118, and 1,832 lines respectively: the neutral facade adds typed surface area while deleting the
backend duplicate cluster. The backend-private policy import count is zero, and the only remaining
spacing helper definitions are one-line delegates inside the canonical owner. Direct policy coverage
adds four spacing cases plus border/reservation/fit tests, and the Qt harness now has a live/snapshot
capture-padding parity matrix. Focused coverage is `270 passed, 1 warning`; the full suite is
`1,153 passed, 1 warning`; Ruff, compileall, CLI help, import isolation, diff checks, and
SPEC immutability pass. Offscreen signed acceptance is `10` scenarios/`7` successful signings,
preview parity `18/18`, and fit rejection `3/3`; generated artifacts and processes were cleaned.
Measured Actual Improvement is conservatively `.70` (ownership `.85`, navigation `.70`, change
amplification `.75`, seam-risk `.75`, testability `.80`, interface compression `.75`, cohesion `.80`,
isolation `.85`), above the `.15` threshold with no component regression above `.10`. Commit
`bb9e77b2c` is the completed implementation commit. Three closure audits confirmed clean state,
SPEC immutability, neutral import isolation, backend/harness ownership, and validation parity; the
only correction was narrowing the source gate below to exclude intentional canonical-owner delegates.

## Context and Orientation

`visible_signature_layout.py` is the application-layer prepare-once boundary. Its
`_layout_reservation_for_template()` builds neutral `LayoutRuleSpec` margins and area dimensions;
`VisibleSignatureLayoutEngine.plan()` and `VisibleSignatureLayoutService.prepare()` use those
results before target-specific materialization. Before this slice,
`phase3_signing_backend.py` repeated margin/optical helpers and imported private reservation/fit
functions, while `phase3_harness.py` reached those backend-private helpers for widget capture
evidence. The committed implementation routes both callers through the neutral facade.

The selected facade is stateless and Qt/Pillow/pyHanko-free. It delegates to the canonical functions
inside the same module, so it does not own rendering or signing. The backend will use it for neutral
reservation and fit calls while retaining rendered-ink orchestration. The harness will use it for
capture padding. Existing `LayoutMargins`, `LayoutRuleSpec`, `SignatureLayoutPlan`, CLI commands,
JSON fields, artifact paths, current-page behavior, and phase3 nomenclature remain unchanged.

## Plan of Work

First rename `_SignatureLayoutReservation` to public `SignatureLayoutReservation` in the canonical
module and all internal annotations, then add `LayoutSpacing` and `VisibleSignatureLayoutPolicy`.
The facade's static/class methods must preserve the current integer rounding, clamps, border-safe
inset, vertical optical shift, horizontal text-width, reservation, and fit-error behavior exactly.
`reservation()` delegates to the canonical reservation builder and `ensure_fit()` delegates to the
existing canonical fit gate; neither method may import or instantiate a backend, Qt widget, renderer,
or service locator. Export the neutral type/facade through the existing lazy application exports only
if current import conventions require it.

Next make the canonical layout engine call the facade internally, leaving any private functions as
one-line internal delegates only while the migration is in progress. This proves that the facade is
not a second implementation. Update `phase3_signing_backend.py` to import the facade and public
reservation type, delete its duplicate spacing/border/effective-margin/optical helpers, and replace
the private reservation/fit calls with `VisibleSignatureLayoutPolicy.reservation()` and
`.ensure_fit()`. Migrate the test-only horizontal-width assertions to
`.horizontal_text_reservation_width()` and delete the dead backend helper.

Update `phase3_harness.py` to import the facade rather than `phase3_signing_backend` for policy. Make
`_preview_padding_for_capture()` call the facade's effective margin/margins operation for both
single-line vertical and other stamped positions, preserving the existing fallback of six points
when there is no usable signature rectangle or stamp position. Add a focused parity assertion that
snapshot-driven and live-preview padding produce the same value for each position/border case.

Add direct policy matrix tests for top/bottom/left/right positions, representative heights, border
off/on widths, stamp/no-stamp, horizontal templates, reservation fields, optical shift, and exact fit
error text. Retain existing layout-plan, rendered-ink, preview-parity, and fit-rejection tests as
behavior tests; migrate only tests that import deleted private backend helpers, and record the mapping
in this plan. Add an import-firewall test proving the policy can load without Qt, Pillow, or pyHanko,
and a source grep/AST assertion that the Phase 3 harness no longer imports backend-private policy.

Finally update `docs/ARCHITECTURE.md`, this child plan, and the parent with the new ownership and
measured results. Run the complete validation and offscreen acceptance commands, delete generated
summary/matrix output, verify no process/dialog remains, commit the source/tests/docs together, and
run three fresh explorers against the committed tree.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Capture baseline and focused tests:

       git status --short --branch
       rg -n "_base_layout_spacing|_effective_layout_edge_margin|_single_line_vertical_outer_margin|_single_line_no_stamp_vertical_optical_shift|_border_safe_inset|_effective_horizontal_text_reservation_width|phase3_signing_backend import" src tests
       .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_phase3_signing_backend.py tests/unit/test_phase3_harness.py

   The baseline is clean at `26d05c6d2`; the grep must show the duplicate policy and backend-private
   harness import before edits.

2. Implement the facade and canonical delegation. Run the policy/layout tests. The expected result is
   exact equality of existing reservation snapshots, margin values, and fit error messages.

3. Migrate backend and harness callers, delete duplicate helpers, and run the focused backend/harness
   suites. The expected source gate is zero `phase3_harness.py` imports from `phase3_signing_backend`
   for layout policy and zero duplicate policy definitions in the backend.

4. Run comprehensive validation:

       .venv/bin/pytest -q
       .venv/bin/ruff check src tests
       .venv/bin/python -m compileall -q src tests
       .venv/bin/python -m foliaseal --help
       .venv/bin/python -c "from foliaseal.application.visible_signature_layout import VisibleSignatureLayoutPolicy; print('neutral layout policy import: PASS')"
       git diff --check
       git diff --exit-code -- docs/SPEC.md

   Expect the full suite to remain green with only the existing Pillow warning.

5. Run unchanged offscreen evidence:

       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence

   Expect signed acceptance `10` scenarios with `7` successful signings, preview parity `18/18`, and
   fit rejection `3/3`. Remove `artifacts/phase3_signed_acceptance_evidence_summary.md` and
   `artifacts/signed_acceptance_evidence/` after recording the result.

6. Verify retirement and ownership gates:

       rg -n "phase3_signing_backend import.*(_base_layout_spacing|_effective_layout_edge_margin|_single_line_vertical_outer_margin|_single_line_no_stamp_vertical_optical_shift|_border_safe_inset)|^def (_base_layout_spacing|_effective_layout_edge_margin|_single_line_vertical_outer_margin|_single_line_no_stamp_vertical_optical_shift|_border_safe_inset|_effective_horizontal_text_reservation_width)" src/foliaseal/application/phase3_signing_backend.py src/foliaseal/presentation/qt/phase3_harness.py tests

   The command must return no backend/harness/test matches. Same-module canonical delegates in
   `visible_signature_layout.py` are intentional and are not part of this retirement gate.
   Confirm no FoliaSeal/Python/Qt process remains and the worktree is clean after commit.

## Validation and Acceptance

Acceptance requires one canonical arithmetic implementation, with `VisibleSignatureLayoutPolicy`
serving signing-backend and Qt-harness callers through neutral typed inputs/results. Existing layout
plan/reservation snapshots, current-page placement, preview parity, signed output, fit rejection,
CLI/JSON/artifact contracts, and error text must remain unchanged. The harness may not import backend
private layout helpers; the backend may not define a second spacing/margin/optical policy. The policy
module must import without Qt/Pillow/pyHanko. Focused parity tests, full pytest, Ruff, compileall,
CLI/import checks, SPEC diff, offscreen acceptance, artifact cleanup, and process audit must pass.
Measured Actual Improvement must be at least `.15` with no component regression beyond `.10`.

## Idempotence and Recovery

Add the facade and parity tests before deleting backend helpers. If a parity test fails, preserve the
old helper temporarily as a one-line delegate to the canonical facade, record the exact mismatch here,
and fix the canonical arithmetic rather than restoring a second implementation. Do not rename phase3
contracts, alter persisted JSON, delete profile data, or change render/materialization ownership. All
artifact cleanup targets are generated acceptance outputs only and may be recreated by rerunning the
offscreen command.

## Artifacts and Notes

Allowed generated artifacts are the transient signed-acceptance summary and matrix output directory;
remove both before commit. The primary source/test/docs changes are one architectural change slice;
unrelated GUI redesign, CLI additions, nomenclature renames, and broad formatting are forbidden.
Record the measured grep, focused/full test counts, offscreen counts, SPEC diff, process audit, and
commit ID in the Outcomes section.

## Interfaces and Dependencies

In `src/foliaseal/application/visible_signature_layout.py`, define the neutral public boundary:

    @dataclass(frozen=True)
    class LayoutSpacing:
        edge_margin_pt: int
        separator_width_pt: int

    class VisibleSignatureLayoutPolicy:
        @staticmethod
        def spacing(*, stamp_position: SignatureStampPosition, box_height_pt: int) -> LayoutSpacing: ...
        @staticmethod
        def border_safe_inset(*, box_style: SignatureBoxStyle | None) -> int: ...
        @classmethod
        def effective_edge_margin(cls, *, stamp_position: SignatureStampPosition,
                                  box_height_pt: int,
                                  box_style: SignatureBoxStyle | None) -> int: ...
        @classmethod
        def margins(cls, *, stamp_position: SignatureStampPosition,
                    box_height_pt: int,
                    box_style: SignatureBoxStyle | None) -> LayoutMargins: ...
        @classmethod
        def reservation(cls, layout_template: SignatureLayoutTemplate, *,
                        stamp_position: SignatureStampPosition,
                        signature_rect: SignatureRect,
                        text_box_width_pt: int,
                        text_box_height_pt: int,
                        box_style: SignatureBoxStyle | None = None,
                        has_visible_stamp_image: bool = True,
                        stamp_aspect_ratio: float | None = None) -> SignatureLayoutReservation: ...
        @staticmethod
        def ensure_fit(reservation: SignatureLayoutReservation, *,
                       has_visible_stamp_image: bool = False) -> None: ...
        @staticmethod
        def horizontal_text_reservation_width(*, layout_template: SignatureLayoutTemplate,
                                              stamp_position: SignatureStampPosition,
                                              text_box_width_pt: int) -> int: ...

The facade must remain pure and stateless. Its implementation may call private helpers inside the
same module, but no caller outside that module may import those private names. Rendered-ink fit
helpers, PyHanko adapters, Qt capture, and artifact writers remain outside this interface.

## Change Log

- 2026-08-06: Created from Scan Round 54 and Design Selection 55. Selected the common-caller
  stateless facade to unify duplicate visible-signature geometry while preserving the separate phase3
  nomenclature migration and all frozen evidence contracts.
- 2026-08-06: Implemented the facade, backend/harness migration, public lazy exports, focused policy
  tests, and architecture documentation. Full/offscreen validation passed; commit and post-commit
  closure scan are the remaining gates. The dedicated
  `docs/ExecPlans/phase3_nomenclature_retirement_execplan.md` remains the follow-on atomic rename
  plan and is intentionally not mixed into this geometry slice.
