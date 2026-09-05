# Eliminate duplicate preset-selection work and bound preview refreshes

This ExecPlan is a living document and must be maintained under
`/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

One user choice in the Signature preset combo should apply once. This slice
removes duplicate Qt signal delivery and proves that the resulting preview and
certificate resolution do not run twice. The observable result is a responsive
signing rail: selecting a disposable saved preset updates its fields and
preview once, without a CPU/RSS spike or repeated password prompt.

## Child ExecPlan Dependencies

- [x] The parent plan records the 2026-09-04 installed resource spike, QtPdf
  coredump, and duplicate-signal lead.
- [x] No dependency on the deeper PDF lifecycle child is required to implement
  the single-delivery correction, but its load-count evidence consumes this
  child’s instrumentation results.

## Progress

- [x] (2026-09-04) Located both signal connections at
  `signing_workspace_properties_panel.py:1064-1071` and the handler at
  `:1154-1183`.
- [x] Added a focused test that models one real Qt combo change and fails on two
  handler/coordinator invocations.
- [x] Kept `currentTextChanged` as the sole preset-selection signal, removed
  the duplicate index path, and added an explicit reentrancy guard.
- [x] Added exact preview/session/coordinator/password counts and a separate
  viewer-refresh invariant.
- [x] Focused tests and the full suite pass; the corrected `0.1.0` package is
  installed and its GUI launched on Cinnamon/X11 for the pending HITL rerun.
- [ ] Confirm the installed preset/certificate workflow remains responsive and
  crash-free after the duplicate-delivery correction.

## Surprises & Discoveries

- Observation: the repository fake combo emits `currentTextChanged` followed by
  `currentIndexChanged` for one `setCurrentText()`/`setCurrentIndex()` change.
  Evidence: the Qt test doubles used by `tests/unit/test_qt_signing_shell.py`.
- Observation: `_suspend_updates` suppresses signals while state is rendered,
  but it is cleared before the second original signal is delivered; it cannot
  prevent this duplicate callback.
- Observation: a canonical preview may perform full, text-only, and stamp-only
  rendering, with additional work for horizontal image-stamp measurement.

## Decision Log

- Decision: retain `currentTextChanged` as the sole preset-selection signal.
  Rationale: the handler consumes the display name, and this signal directly
  expresses the user-visible value change; a second index signal adds no
  capability and doubles work.
  Date/Author: 2026-09-04 / Codex.
- Decision: do not add a time-based debounce as the primary fix.
  Rationale: deterministic single delivery is easier to test and avoids making
  keyboard selection feel delayed or hiding legitimate changes.
  Date/Author: 2026-09-04 / Codex.

## Outcomes & Retrospective

At completion, tests must demonstrate exactly one preset handler invocation,
one session/coordinator application, one password-prompt path, and one
canonical preview lifecycle refresh for one combo change. Viewer refresh count
must remain unchanged by a preset selection. The slice must state whether PDF
load counts also fell as expected and whether any remaining spike belongs to the
separate lifecycle child.

Implementation evidence (2026-09-04): `eed5c93da` removes the duplicate signal
connection and the focused shell test observes exactly one handler, session,
coordinator, canonical preview refresh, and certificate password prompt, with
no viewer refresh. Full-suite validation is `1616 passed, 20 skipped, 1
warning`; installed placement/edit acceptance remains the only open gate.

## Context and Orientation

`SignaturePropertiesPanel._build_signature_preset_controls()` creates the
combo. `_on_signature_preset_selected()` translates the placeholder to an
empty selection, calls `SigningSetupSession.select_signature_preset()`, applies
the returned state, and notifies the shell. `_apply_coordinator_state()` uses
`_suspend_updates` while it repopulates controls and calls
`_update_preview_controls()`.

The application layer resolves a certificate-bearing preset and can prompt for
its password before applying appearance and placement. The test suite already
has Qt fakes and coordinator/session tests; extend those seams rather than
driving a real desktop in unit tests.

## Plan of Work

Add a focused Qt-panel test using the existing bindings fake or a minimal real
`QComboBox` that emits both signals. Instrument the panel’s setup session,
coordinator, and preview lifecycle with counters. Select one named preset and
assert one call at each boundary. First run the test against the current code
to capture the red behavior (two calls), then change the construction to
connect only `currentTextChanged` and rerun it green.

Add a certificate-bearing preset test to ensure session-level password
resolution and coordinator application each occur once; also cover canceled
and invalid-password paths returning a stable state. Add canonical
preview-refresh and viewer-refresh assertions so the fix cannot regress into
duplicate rendering under a different fake signal order. Keep placeholder
selection behavior and programmatic `_apply_coordinator_state()` refreshes
covered.

## Concrete Steps

From `/home/daekar/FoliaSeal`, inspect the current test names before editing:

    rg -n "SignaturePropertiesPanel|signature_preset|currentTextChanged|currentIndexChanged" tests/unit tests/integration src/foliaseal/presentation/qt/signing_workspace_properties_panel.py

Run the focused tests before and after the change:

    .venv/bin/python -m pytest tests/unit/test_qt_signing_shell.py tests/unit/test_signing_setup_session.py -q
    .venv/bin/python -m pytest -q

The expected post-change result is one new regression test passing, the focused
suite passing, and no change to unrelated command or library behavior.

## Validation and Acceptance

The slice is accepted when a real or faithful Qt combo change invokes the
preset handler once; a certificate-bearing preset resolves material once; one
preview refresh is observed; existing unit/integration tests pass; and Ruff,
compile, and diff checks remain clean. The installed package must still be
retested by the parent after the lifecycle child is complete.

## Idempotence and Recovery

Keep counters in tests or temporary diagnostics only. Do not leave logging or
extra signal connections in release code. If the real Qt test cannot run in the
current display environment, use the repository fake plus an isolated minimal
Qt test and record that limitation; do not claim the native crash is fixed until
the installed reproduction is repeated.

## Artifacts and Notes

Commit only source/tests and the living-plan updates for this behavior slice.
Do not commit package files, PDFs, certificate material, coredumps, or temporary
profiling output.

## Interfaces and Dependencies

Preserve `_on_signature_preset_selected()`, `SigningSetupSession.select_signature_preset()`,
`DefaultSignaturePropertiesCoordinator.apply_signature_preset()`, and
`QtCanonicalPreviewLifecycle.refresh()` signatures. The only intended UI wiring
change is one deterministic signal-to-handler connection; do not add a time
debounce or alter the viewer refresh contract in this child.

Revision note: 2026-09-04 / Codex — explorer review clarified that acceptance
must count session/password calls and canonical preview refreshes separately
from viewer refreshes, and must preserve placeholder/programmatic update
coverage.

Revision note: 2026-09-04 / Codex — implementation removed duplicate signal
delivery, added the reentrancy guard, and recorded exact boundary counts.
