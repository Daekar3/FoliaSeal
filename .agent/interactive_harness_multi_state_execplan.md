# Interactive Harness Multi-State Capture

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`. The goal is to let one interactive Phase 3 harness session preserve several configuration snapshots without reintroducing a separate validation model or a second batch-runner concept.

## Purpose / Big Picture

After this change, someone using `foliaseal phase3-signing-harness` can inspect several appearance states in a single GUI run and keep all of them in one capture artifact. They should be able to step through `single_line/top`, `single_line/bottom`, `single_line/left`, and `single_line/right`, click a harness control to preserve each state, and then review those saved states later in the same summary JSON that the harness already writes.

The user-visible outcome is straightforward. The interactive harness keeps its existing final capture, but it also exposes an explicit “Capture State” action that records the current preview, validation status, backend reservation snapshot, and preview artifact paths. One run can therefore preserve a sequence of named states instead of forcing the user to relaunch the harness for each comparison.

## Progress

- [x] (2026-04-05 23:47Z) Re-read `.agent/PLANS.md`, inspected the current interactive harness path, and confirmed the existing GUI run writes exactly one final capture after `app.exec()` returns.
- [x] (2026-04-05 23:50Z) Wrote this ExecPlan and fixed the scope around a minimal slice: explicit manual state capture in the interactive harness, not automatic capture on every control change.
- [x] (2026-04-05 23:59Z) Implemented manual multi-state capture storage in `src/foliaseal/presentation/qt/phase3_harness.py`, including the `Capture State` toolbar action, the additive `captured_states` payload, and concise terminal summary output.
- [x] (2026-04-06 00:02Z) Added tests for the new history payload and helper functions in `tests/unit/test_phase3_harness.py`.
- [x] (2026-04-06 00:04Z) Updated `README.md` and `phase3_parallel_plan.md` so the new interactive harness behavior is discoverable.
- [x] (2026-04-06 00:05Z) Ran focused validation and updated this plan with the final behavior and the discovered constraints.

## Surprises & Discoveries

- Observation: the existing interactive harness already has a rich single-state snapshot helper set, while the batch matrix runner already captures repeated states. The missing piece is not capture logic itself, but a user-driven way to preserve several states during one live GUI session.
  Evidence: `run_phase3_signing_harness()` captures one `preview_snapshot` plus backend/request snapshots after `app.exec()`, while `_execute_preview_matrix_scenario()` repeats that pattern for many scenarios.

- Observation: the current harness output shape is stable enough that the safest change is additive. Top-level fields should continue to describe the final state, while a new history field can carry intermediate captures.
  Evidence: `Phase3HarnessCapture` is serialized generically by `_jsonable_capture()`, so adding a new dataclass field is low-risk if the existing top-level fields remain intact.

## Decision Log

- Decision: implement explicit capture-on-demand instead of automatic capture on every control change.
  Rationale: the user asked to examine more than one configuration state per run, not to log every transient keystroke. An explicit harness action keeps the JSON reviewable, deterministic, and easy to use during manual testing.
  Date/Author: 2026-04-05 / Codex

- Decision: keep the current top-level capture fields as the final state and add a new `captured_states` history field.
  Rationale: this preserves backward compatibility for checklist generation, evidence validation, and existing tools that read the current summary shape, while still making multi-state review possible.
  Date/Author: 2026-04-05 / Codex

- Decision: do not change the preview matrix runner in this slice.
  Rationale: the matrix runner already handles many scenarios per run. This slice is specifically about the interactive harness, and mixing the two would violate the existing architectural choice to keep manual acceptance and unattended sweeps distinct.
  Date/Author: 2026-04-05 / Codex

## Outcomes & Retrospective

This slice succeeded.

What changed:

- `Phase3HarnessCapture` now has an additive `captured_states` field.
- `run_phase3_signing_harness()` now exposes a `Capture State` toolbar button and a small count label.
- Each manual capture stores the current preview snapshot, preview text, validation text, sign-request snapshot, backend reservation snapshot, and backend reservation error.
- The top-level capture remains a final-state summary exactly as before, and `captured_states` adds history instead of replacing that summary.
- The final state is always appended into `captured_states` as a `final` entry, even if the operator never clicks `Capture State`.
- When `--summary-json-path` is supplied, the harness now prints a compact summary that includes the number of captured states instead of dumping the full JSON payload to the terminal.
- `README.md` and `phase3_parallel_plan.md` now describe the new one-run multi-state review workflow.

What did not change:

- The preview matrix runner remains untouched.
- The existing top-level evidence fields in the harness summary JSON remain intact.
- Checklist generation and evidence validation still use the top-level final-state fields.

Verification results:

- `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py .agent/interactive_harness_multi_state_execplan.md`
- `.venv/bin/pytest -q tests/unit/test_phase3_harness.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_preview_renderer.py`

Observed outcome:

- focused suite: `82 passed`

Retrospective:

- The safest way to make one run preserve many states was additive history, not replacing the final-state contract.
- An explicit manual capture action keeps the JSON useful; automatic capture on every control change would have created noisy artifacts and made comparisons harder.
- Reusing the existing snapshot helpers kept the implementation small and reduced the risk of creating yet another serialization path.

## Context and Orientation

`src/foliaseal/presentation/qt/phase3_harness.py` contains both the interactive harness and the unattended preview matrix runner. The interactive entry point is `run_phase3_signing_harness()`. That function launches the Qt shell, waits for the GUI session to end, and then builds a single `Phase3HarnessCapture` containing the final preview, backend reservation snapshot, request snapshot, and optional signed-output evidence.

`Phase3HarnessCapture` is the dataclass that becomes the JSON file when `--summary-json-path` is provided. The helper `_jsonable_capture()` serializes dataclasses recursively, so additive dataclass fields become JSON automatically.

`tests/unit/test_phase3_harness.py` already exercises the JSON serializer, checklist rendering, preview snapshot logic, and the matrix-runner helpers. It does not currently cover multi-state interactive capture because that feature does not exist yet.

The user’s goal is not a second matrix runner. The user wants one live harness session to preserve several manually chosen configuration states. This means the harness should keep the final state as it does today, but also expose a way to append the current state to a history list while the window is still open.

## Plan of Work

First, extend `Phase3HarnessCapture` in `src/foliaseal/presentation/qt/phase3_harness.py` with a new `captured_states` field. Each item should be a plain dictionary containing the current preview snapshot, preview text, validation text, sign request snapshot, backend reservation snapshot, backend reservation error, and metadata identifying the sequence and capture kind. The top-level fields must continue to reflect the final state after the window closes.

Second, factor the existing post-`app.exec()` snapshot logic into a small helper in `src/foliaseal/presentation/qt/phase3_harness.py`. That helper should accept the shell, the current request, the artifacts directory, and a state label/kind, then produce one history entry. Reusing one helper prevents the harness from growing two slightly different snapshot builders.

Third, add a new toolbar control inside `run_phase3_signing_harness()`. The control should be labeled `Capture State`. When clicked, it should snapshot the current draft state immediately and append it to an in-memory history list. If `artifacts_dir` is set, the capture should also write a preview PNG for that state using a deterministic basename such as `interactive_state_01`, `interactive_state_02`, and so on. A small status label in the toolbar should show how many states have been captured so far.

Fourth, after the GUI session ends, build the normal final capture as before, then set `captured_states` to the tuple of manual captures plus a final state entry tagged as `final`. This guarantees that every run still has a definitive final state in the history even if the operator never clicked `Capture State`.

Fifth, keep terminal output concise. If `--summary-json-path` is present, print the summary path and the number of captured states rather than dumping the JSON. The full detail remains in the written file.

Finally, add tests in `tests/unit/test_phase3_harness.py` for the additive schema and any new helper functions. The tests should prove that multiple state entries serialize correctly and that the top-level final-state behavior remains intact.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Inspect the current interactive harness capture path before editing:

    sed -n '420,700p' src/foliaseal/presentation/qt/phase3_harness.py
    sed -n '760,980p' tests/unit/test_phase3_harness.py

Implement the additive schema and helper path in:

    src/foliaseal/presentation/qt/phase3_harness.py

Add or update tests in:

    tests/unit/test_phase3_harness.py

Run focused validation:

    .venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py
    .venv/bin/pytest -q tests/unit/test_phase3_harness.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_preview_renderer.py

Expected success looks like:

    All checks passed!
    ...
    <targeted tests passed>

## Validation and Acceptance

This change is acceptable only if all of the following are true:

- One interactive harness run can preserve more than one chosen state without relaunching the GUI.
- The harness summary JSON still includes the existing top-level final-state fields.
- The new `captured_states` history is present and serializes deterministically.
- The preview matrix runner remains unchanged.
- Focused tests pass.

Manual acceptance after implementation is:

    .venv/bin/python -m foliaseal phase3-signing-harness \
      --pdf-path "/path/to/test.pdf" \
      --certificate-path "/path/to/test.p12" \
      --passphrase "secret" \
      --summary-json-path artifacts/phase3_harness_capture.json \
      --checklist-results-path artifacts/phase3_fr3b_acceptance_results.md \
      --artifacts-dir artifacts/phase3_preview_debug

Then, inside the GUI:

1. Draw a rectangle.
2. Configure one state and click `Capture State`.
3. Change the configuration and click `Capture State` again.
4. Close the harness.

Afterward, inspect `artifacts/phase3_harness_capture.json` and confirm that:

- the top-level fields describe the final state,
- `captured_states` includes both manual captures plus a final entry,
- and each captured state includes preview text, validation text, and preview render metadata.

## Idempotence and Recovery

This slice is safe to rerun. Repeated harness runs overwrite the requested summary JSON path just as they do today. If a toolbar capture implementation proves noisy, revert only the button and history-list wiring while leaving the refactored single-state helper in place; that helper remains a safe simplification even on its own.

## Artifacts and Notes

Important schema decision:

- existing top-level capture fields remain the authoritative final-state snapshot
- new `captured_states` is additive history for multi-state review

This keeps existing evidence consumers stable while making one-run comparisons possible.

## Interfaces and Dependencies

In `src/foliaseal/presentation/qt/phase3_harness.py`, define an additive helper with a stable shape. The exact name can be chosen during implementation, but by the end of the slice there must be one function that accepts the current shell state and returns a dictionary suitable for one `captured_states` entry. That dictionary must include:

- a numeric `capture_index`
- a string `capture_kind` such as `manual` or `final`
- a string `capture_label`
- `preview_snapshot`
- `preview_text`
- `validation_text`
- `sign_request_snapshot`
- `backend_reservation_snapshot`
- `backend_reservation_error`

The implementation must continue to use the existing snapshot helpers such as `_snapshot_preview()`, `_snapshot_signing_request()`, `_snapshot_backend_reservation()`, `_backend_reservation_error()`, and `_capture_preview_render()` rather than inventing a separate serialization path.

Revision note: created this plan on 2026-04-05 to support multi-state interactive harness review in a single run, prompted by manual acceptance work on several `single_line` positions. Updated on 2026-04-06 after implementation to record the additive `captured_states` design, the new toolbar action, and the focused verification results.
