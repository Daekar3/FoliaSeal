# Give partial presets explicit per-document setup guidance

This ExecPlan is a living document and must be maintained in accordance with
`/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

Selecting a saved Signature Preset must make the next required per-document
input obvious when the preset intentionally omits a Certificate Configuration
or Placement Profile. The current shell applies the partial preset correctly,
but the signing rail can fall back to generic `Setup required` or `Place a
visible signature` wording. This slice makes the readiness projection and
signing rail name the missing input and its consequence-labeled next action,
without creating a certificate, placing a signature, or changing the draft
implicitly.

The user-visible result is a truthful staged workflow: after selecting a
partial preset, the rail says which document-specific value is missing; once a
certificate is supplied, it advances to placement; once placement is supplied,
it advances through the existing preview/readiness path. Preset selection still
never signs or places automatically.

## Governing requirements and dependencies

- `docs/SPEC.md` §§2, 5, and Release Bar require explicit per-document optional
  certificate/placement selection and a complete non-expert signing workflow.
- `docs/UI_SPEC.md` WF02/WF03 and §11 require partial presets to request only
  missing inputs, preserve explicit selection semantics, and expose clear next
  actions.
- `docs/ExecPlans/ui_first_use_preset_setup_execplan.md` records this exact
  remaining gap after the first-use Library path was completed.
- `docs/ExecPlans/ui_readiness_caveats_status_execplan.md` owns the broader
  readiness vocabulary; this child only improves partial-preset specificity.

## Scope and non-goals

In scope:

- typed readiness facts for a selected preset's missing certificate and/or
  placement;
- plain-language rail detail for the missing per-document input;
- focused application, coordinator, panel, and offscreen walkthrough tests;
- status/architecture documentation and cleanup.

Out of scope:

- certificate creation/import UI from the first-use path;
- placement-profile creation or automatic placement;
- changes to schemas, signing cryptography, output policy, or preset
  persistence;
- screen-reader, physical-DPI, privileged-package, final-release, or Wayland
  acceptance. Wayland remains deferred for Mint 22.3.

## Progress

- [x] (2026-08-16) Fresh source/spec audit identified the gap: partial-preset
  selection currently applies safely but does not distinguish missing
  Certificate versus Placement guidance in the typed readiness path.
- [x] (2026-08-16) Added typed missing-input facts and deterministic readiness messages while
  preserving the existing stage/action ordering.
- [x] (2026-08-16) Reconciled the Qt panel/coordinator rendering and proved explicit
  certificate-then-placement progression without automatic mutation.
- [x] (2026-08-16) Ran focused and full validation, independent compliance review,
  documentation update, commit, and owned-process/artifact cleanup.
- [x] (2026-08-16) Corrected certificate-blocking precedence after review: an expired,
  invalid, or otherwise blocking certificate retains its specific blocking detail, while
  the no-certificate-selected status may expose partial-preset guidance.

## Surprises & Discoveries

- The coordinator already emits a certificate-only partial-preset notice, but
  it is prepended to generic validation text and is not represented as a typed
  readiness fact. Placement omission is handled only by the generic placement
  stage.
- A selected preset may intentionally omit either reusable input while the
  current document can still have an explicitly selected certificate or an
  existing placement. Guidance must describe the effective missing value, not
  merely the preset's stored null reference.
- The existing readiness action vocabulary already distinguishes
  `COMPLETE_SETUP` and `PLACE_SIGNATURE`; this slice should enrich their detail
  and preserve the existing action state rather than inventing an auto-action.

## Decision Log

- Decision: represent missing certificate and placement as typed readiness
  inputs derived at the coordinator boundary, while retaining the existing
  `SigningReadinessStage` and `SigningReadinessAction` values.
  Rationale: the stage/action contract already drives the signing rail; adding
  specific facts avoids a second competing state machine.
  Date/Author: 2026-08-16 / Codex.
- Decision: use explicit instructional text and existing selectors/form modes
  rather than automatically selecting a certificate or placing a rectangle.
  Rationale: UI_SPEC forbids preset selection from implying signing or
  placement, and users must remain the author of per-document values.
  Date/Author: 2026-08-16 / Codex.
- Decision: preserve the existing certificate-first ordering when both inputs
  are missing, then expose placement guidance after certificate selection.
  Rationale: signing cannot proceed without certificate readiness, and this
  sequence matches the staged workflow and current readiness projection.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

Implemented in the focused commit `feat: clarify partial preset setup guidance`.
`SigningReadinessMissingInput.CERTIFICATE` and `.PLACEMENT` now identify the
selected preset's missing per-document value. The rail says “Choose a certificate
for this preset” before certificate selection and “Place the signature for this
preset” after certificate readiness; selection does not create a certificate,
place a rectangle, or sign. A `NO_CERTIFICATE_SELECTED` readiness status is treated
as the expected partial-preset omission, while blocking certificate statuses retain
their original specific error detail.

Focused readiness/coordinator/Qt/walkthrough validation is `164 passed`; the full
suite is `1548 passed, 20 skipped, 1 warning`. Ruff, compileall, and
`git diff --check` are clean. Independent compliance review found and this slice
fixed certificate-blocking precedence; no architectural boundary violation or
implicit mutation remained. Remaining release gates are certificate/placement
creation flows, human display-backed accessibility/monitor fit, privileged host
installation, final release acceptance, and deferred Wayland support on Mint 22.3.

## Context and Orientation

`src/foliaseal/application/signing_readiness.py` owns the pure stage/action
projection. `signature_properties_coordinator.py` owns effective selected
preset/certificate/placement facts. The Qt properties panel creates the
certificate selector, preset selector, placement form, and public readiness
port; `signing_action_coordinator.py` projects readiness into the right-rail
status text. Existing workflow methods already preserve current placement when
a preset omits placement and never auto-place a signature.

## Plan of Work

1. Add a small typed readiness vocabulary for missing effective inputs (or
   equivalent boolean facts with an explicit enum) and pass it from the
   coordinator/panel into `SigningReadinessInputs`.
2. Update `project_signing_readiness()` so a selected partial preset produces
   precise certificate guidance first, then precise placement guidance after
   certificate readiness is satisfied. Keep generic readiness behavior for
   manually assembled drafts and blocking certificate errors.
3. Ensure the panel's existing controls remain reachable and the rendered
   helper/status text names the selected preset and missing input without
   exposing secrets or changing selection. If a focus helper is added, it must
   only focus the existing selector/form; it must not apply a value.
4. Add red-to-green tests for pure readiness, coordinator effective facts,
   partial-preset selection with unchanged placement, certificate progression,
   and an offscreen panel/rail walkthrough. Assert no signing request or
   placement rectangle is created by selecting the preset.
5. Update this plan, the first-use plan, the parent/release status, and
   `docs/ARCHITECTURE.md` only where present-tense ownership or remaining-gap
   wording changes. Run focused/full validation, independent compliance review,
   commit the bounded slice, and clean every owned process/root.

## Milestones

Milestone 1 is a typed red test for certificate/placement-specific readiness.
Milestone 2 is the green application/coordinator projection with unchanged
workflow semantics. Milestone 3 is the offscreen rail walkthrough and complete
validation/documentation/commit closeout.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/python -m pytest -q tests/unit/test_signing_readiness.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py tests/integration/test_preview_readiness_walkthrough.py
    .venv/bin/python -m ruff check src tests
    .venv/bin/python -m compileall -q src tests
    .venv/bin/python -m pytest -q
    git diff --check

Use only `QT_QPA_PLATFORM=offscreen` or the supported Cinnamon/X11 session for
bounded GUI checks. If a temporary configuration or artifact root is needed,
create an exact `/tmp/foliaseal-*` root, remove it in `finally`/teardown, and
verify no FoliaSeal, PySide6, pytest, or helper process remains. Do not run
Wayland.

## Validation and Acceptance

Acceptance requires:

- selecting a preset without a certificate yields explicit certificate
  guidance and remains unsigned/unplaced;
- after a certificate is selected, a preset without placement yields explicit
  placement guidance;
- an existing document placement remains unchanged when a preset omits it;
- a preset that includes each input retains the current behavior;
- blocking certificate errors still take precedence over missing-placement
  guidance;
- focused tests, full pytest, Ruff, compileall, and diff checks pass;
- governing docs and plans distinguish this AFK completion from remaining
  display-backed, privileged, final-release, and deferred Wayland gates.

## Idempotence and Recovery

The projection and tests are deterministic and safe to rerun. If a Qt test
fails, close only windows/processes created by the test, remove only its exact
temporary root, and record the failure before retrying. Never delete user
configuration, PDFs, credentials, or unrelated processes.

## Artifacts and Notes

No generated artifact belongs in the commit. Record only concise test output,
typed state/message observations, and the exact cleanup result. No SVG is
needed: this slice changes readiness copy and state projection, not topology.

## Interfaces and Dependencies

The public setup/readiness ports remain stable unless a narrowly typed missing-
input fact is required. The application layer must not import Qt; the panel may
adapt existing Qt selectors/forms through its current public setup boundary.
Persisted schemas, CLI commands, certificate material, signing requests, and
Wayland behavior must remain unchanged.

Revision note: 2026-08-16 / Codex — created from a fresh SPEC/UI_SPEC audit after
the first-use preset flow and release evidence closeouts identified explicit
missing per-document input guidance as the next AFK product slice.
