# Stamp Position Preview Centering Follow-Up

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

Users can now choose a `Stamp Position` of Top, Bottom, Left, or Right, but the current preview
paths still have two gaps after the first follow-up:

- the shell preview wraps `single_line` text against the full rectangle instead of the stamp-
  constrained text area for horizontal layouts
- the deterministic preview renderer still emits a blank title row when the signer label prefix is
  intentionally empty

The immediate goal of this second follow-up is to make the shell preview and the deterministic
preview renderer more honest for `Stamp Position` without reopening the whole feature. After this
change, horizontal `single_line` previews should wrap against a reduced width when an image stamp is
present, and blank prefixes should be truly space-free in both the Qt preview and the deterministic
preview snapshot used by tests and downstream tooling.

## Progress

- [x] (2026-03-31 00:00Z) Reviewed current `Stamp Position` implementation and identified the
  missing vertical-centering contract in the Qt preview.
- [x] (2026-03-31 00:10Z) Implemented explicit centered alignment for the horizontal preview row in
  `src/foliaseal/presentation/qt/signing_shell.py`.
- [x] (2026-03-31 00:12Z) Added regression tests for shell centering behavior and backend `LEFT`
  coverage.
- [x] (2026-03-31 00:14Z) Ran focused tests and lint; all targeted checks passed.
- [x] (2026-03-31 00:25Z) Review gate reported two remaining gaps: horizontal `single_line`
  wrapping still ignored stamp-reserved width, and the deterministic preview renderer still emitted
  an empty title row for blank prefixes.
- [x] (2026-03-31 00:27Z) Implemented shell and deterministic-preview follow-up fixes plus
  harness-facing regression coverage.
- [x] (2026-03-31 00:31Z) Ran the focused shell/preview/harness test slice and lint; all checks
  passed.

## Surprises & Discoveries

- Observation: the current review issue is narrower than the whole feature; the main gap is preview
  geometry, not model or backend wiring.
  Evidence: `Hypatia`'s review reported no major model/backend inconsistency, only missing
  left/right centering semantics and test coverage.
- Observation: the harness-facing `preview_text()` path and the deterministic preview renderer can
  drift independently from the visible Qt widget tree if they do not branch on the same layout
  constraints.
  Evidence: `Epicurus` flagged horizontal `single_line` fit overstatement and a blank title row in
  `render_signing_preview()` even after the visual centering fix landed.

## Decision Log

- Decision: keep this follow-up narrow and avoid reopening the broader `Stamp Position` feature.
  Rationale: the feature already passes local verification broadly; the review found one shell
  behavior gap and one coverage gap, so the safest fix is a targeted patch.
  Date/Author: 2026-03-31 / Codex
- Decision: extend this same ExecPlan instead of creating another one-off document.
  Rationale: the new review feedback is still part of the same `Stamp Position` acceptance thread,
  and keeping it here preserves the implementation history in one place.
  Date/Author: 2026-03-31 / Codex

## Outcomes & Retrospective

- The first follow-up closed the explicit `Left` / `Right` centering gap and added direct backend
  `LEFT` coverage.
- The remaining work is now concentrated on making the non-visual preview paths honest enough for
  harness capture and deterministic parity checks.
- This second follow-up corrected the harness-facing `preview_text()` path for horizontal
  `single_line`, made horizontal wrapping reserve stamp width when an image is present, and removed
  the blank title row from `render_signing_preview()` when the signer label prefix is empty.

## Context and Orientation

The current `Stamp Position` feature is implemented across the domain model, signing request path,
backend layout, shell UI, and harness. The review found that the backend is close enough, but the
Qt preview in `src/foliaseal/presentation/qt/signing_shell.py` only swaps the order of widgets for
`Left` / `Right`; it does not explicitly center the text block beside the stamp. The shell tests in
`tests/unit/test_qt_signing_shell.py` currently prove ordering, but not the centering contract.

The backend layout code lives in `src/foliaseal/application/phase3_signing_backend.py`. The
review also noted that the `LEFT` backend branch is not covered directly enough in
`tests/unit/test_phase3_signing_backend.py`, even though the code path exists.

## Plan of Work

Update the preview layout helper in `src/foliaseal/presentation/qt/signing_shell.py` so horizontal
stamp/text layouts can attach explicit alignment when adding widgets to the preview row. Keep the
existing vertical layouts (`Top` / `Bottom`) unchanged. Add or reuse a small helper rather than
duplicating logic inline.

Then tighten the harness-facing shell helpers in `src/foliaseal/presentation/qt/signing_shell.py`
so `single_line` previews account for horizontal stamp occupancy and `preview_text()` returns the
active detail text even when `single_line` is rendered through the horizontal container. Finally,
update `src/foliaseal/application/signing_preview_renderer.py` so blank prefixes do not serialize an
empty title line.

## Concrete Steps

From the repository root `/home/daekar/SignPDF/Scratch`:

1. Edit `src/foliaseal/presentation/qt/signing_shell.py` to make horizontal `single_line` preview
   wrapping and `preview_text()` reflect the active stamp position.
2. Edit `src/foliaseal/application/signing_preview_renderer.py` to omit blank title rows.
3. Expand `tests/unit/test_qt_signing_shell.py`, `tests/unit/test_signing_preview_renderer.py`, and
   `tests/unit/test_phase3_harness.py` with regression coverage for these paths.
4. Run:

       ./.venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_harness.py
       ./.venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/application/signing_preview_renderer.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_harness.py

## Validation and Acceptance

Acceptance is reached for this follow-up when all are true:

- `Left` and `Right` preview layouts still place widgets in the correct order and use centered
  alignment.
- The shell `preview_text()` path returns the active horizontal detail text for `single_line`
  horizontal stamp positions.
- Horizontal `single_line` wrapping in the shell preview reflects a reduced text area when a stamp
  image is present.
- `render_signing_preview()` omits a blank title line when the signer label prefix is empty.
- Focused tests pass and lint is clean.

## Idempotence and Recovery

These edits are additive and safe to repeat. If a test assertion proves too strict for the fake Qt
bindings, tighten the helper implementation rather than weakening the user-visible centering
contract.

## Artifacts and Notes

- The main review findings for this follow-up now come from two review gates:
  - `Hypatia`: missing explicit centering for left/right preview rows
  - `Epicurus`: horizontal `single_line` fit overstatement and blank title line in the deterministic
    preview renderer
- Focused verification from the first follow-up:
- Focused verification from the second follow-up:

      ./.venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_harness.py
      41 passed in 0.40s

      ./.venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/application/signing_preview_renderer.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_harness.py
      All checks passed!

- Focused verification from the first follow-up:

      ./.venv/bin/python -m pytest -q tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py
      48 passed in 1.24s

      ./.venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py
      All checks passed!

## Interfaces and Dependencies

No new dependencies are needed. The relevant interfaces are:

- `SignatureStampPosition` in `src/foliaseal/domain/models.py`
- preview controls in `src/foliaseal/presentation/qt/signing_shell.py`
- backend layout helpers in `src/foliaseal/application/phase3_signing_backend.py`

Update note: created this focused ExecPlan on 2026-03-31 to track the narrow post-review fix for
`Stamp Position` preview centering and missing `LEFT` coverage.

Update note: revised on 2026-03-31 after implementation to record the completed centering fix,
targeted tests, and verification results.
