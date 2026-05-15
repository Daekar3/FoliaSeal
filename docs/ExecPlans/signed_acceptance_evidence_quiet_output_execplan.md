# Signed Acceptance Evidence Quiet Output

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The one-command signed acceptance evidence runner now proves signed-output acceptance, but a successful run emits repeated low-level pyHanko and Qt messages that make the command look unhealthy. After this change, the high-level evidence command should stay readable by suppressing only known benign dummy-TSA and offscreen Qt chatter, while the underlying matrix summaries and failure policy remain unchanged. The raw per-manifest matrix command remains available when full diagnostics are wanted.

This is a CLI usability and evidence hygiene slice. It must not weaken cryptographic validation, acceptance counters, manifest expectations, or signed matrix execution.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/signed_acceptance_evidence_runner_execplan.md` added the one-command evidence runner and validated a green end-to-end local run.
- [x] Compliance review for that runner identified runtime verbosity as a residual usability risk, not a correctness blocker.
- [x] Explorer review confirmed the largest noise source is pyHanko logging from dummy TSA trust validation, with a smaller Qt offscreen plugin message.

## Progress

- [x] (2026-05-14T20:24Z) Started the dev-loop slice for reducing evidence-command runtime chatter.
- [x] (2026-05-14T20:25Z) Spawned an explorer to inspect pyHanko/Qt output origins and safe filtering seams.
- [x] (2026-05-14T20:30Z) Confirmed the smallest safe slice is a command-scoped, exact filter around the evidence runner’s matrix calls.
- [x] (2026-05-14T20:32Z) Created this ExecPlan.
- [x] (2026-05-14T20:37Z) Implemented scoped pyHanko logging and Qt message filters for known benign evidence-run chatter.
- [x] (2026-05-14T20:42Z) Added regression tests proving benign pyHanko chatter is suppressed while nonmatching warnings still surface.
- [x] (2026-05-14T20:43Z) Updated README and architecture docs to explain quiet evidence behavior and raw matrix diagnostics.
- [x] (2026-05-14T20:58Z) Ran focused tests, lint, and the real evidence command successfully.
- [x] (2026-05-14T21:01Z) Committed the first-pass quiet-output slice as `950f915 Quiet signed evidence runtime chatter`.
- [x] (2026-05-14T21:07Z) Compliance review found the layout warning filter was broader than the README described and could hide useful layout diagnostics outside intentional rejection scenarios.
- [x] (2026-05-14T21:14Z) Reran focused tests, lint, and the real evidence command after narrowing layout warning suppression to the fit-rejection matrix.
- [x] (2026-05-14T21:16Z) Committed the follow-up as `05d03b8 Scope signed evidence layout warning filter`.
- [x] (2026-05-14T21:20Z) Final compliance review found no issues with the scoped layout-warning filter, docs, or tests.

## Surprises & Discoveries

- Observation: the repeated dummy TSA validation block is Python logging, not direct `print`.
  Evidence: `pyhanko.sign.validation.generic_cms.handle_certvalidator_errors()` logs messages beginning `Validation error [cert context: ...]` through `logging.getLogger(__name__)`.

- Observation: plain stderr redirection is not enough for the Qt plugin message.
  Evidence: the explorer found the offscreen Qt message originates during Qt bootstrap before the harness returns, and env-only runs still produced `This plugin does not support propagateSizeHints()`.

- Observation: the initial filter removed the large dummy TSA tracebacks and Qt plugin line, but the real fit-rejection matrix still emitted repeated pyHanko layout warnings for intentional validation-rejection scenarios.
  Evidence: the first real run after the initial filter printed repeated `Content box width/height ... post_margin will be ignored` messages before the final PASS summary. Adding an exact `pyhanko.pdf_utils.layout` filter removed those messages on the next real run.

- Observation: layout warnings are real diagnostics and should not be suppressed for success-oriented matrices.
  Evidence: compliance review noted pyHanko emits `post_margin will be ignored` whenever content exceeds a box. The filter is now active only while running `signed_fit_rejection_matrix`, where the corpus intentionally exercises rejection geometry.

## Decision Log

- Decision: filter only the evidence command path, not the raw `phase3-signing-acceptance-matrix` command.
  Rationale: the evidence command is intended as a readable acceptance gate. The raw matrix command should keep full low-level diagnostics for debugging.
  Date/Author: 2026-05-14 / Codex

- Decision: make the pyHanko filter exact to dummy TSA self-signed validation messages.
  Rationale: over-broad timestamp or certificate logging suppression could hide real trust regressions. The summaries still retain the authoritative pass/fail counters.
  Date/Author: 2026-05-14 / Codex

## Outcomes & Retrospective

This plan is complete. The one-command signed acceptance evidence runner now suppresses the known benign dummy-TSA and Qt offscreen chatter on the high-level evidence path while preserving raw diagnostics in the per-manifest matrix command. The follow-up narrowed layout-warning suppression to the intentional fit-rejection matrix, focused tests and lint passed, the real evidence command reported all three matrices as `PASS`, and final compliance review found no remaining issues.

## Context and Orientation

The one-command evidence runner lives in `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py`. It calls `run_phase3_signed_acceptance_matrix()` three times. The harness creates a Qt application and validates signed outputs. In dummy timestamp mode, pyHanko validates a self-signed dummy TSA certificate repeatedly; the summary counters remain correct, but the terminal output is noisy.

## Plan of Work

Add a context manager in `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` that installs an exact logging filter on `pyhanko.sign.validation.generic_cms` and, when PySide6 is importable, a temporary Qt message handler. The logging filter should suppress only records whose message contains both the known dummy TSA subject and the self-signed validation phrase. The Qt handler should suppress only the exact `This plugin does not support propagateSizeHints()` message and delegate other messages to the previous handler if one exists.

Wrap each matrix runner call in that context by default. Leave a `suppress_known_runtime_chatter` argument on `run_signed_acceptance_evidence()` for tests or diagnostics.

Add unit tests to `tests/unit/test_qa_signed_acceptance_evidence.py` that monkeypatch a matrix runner to emit the known pyHanko warning and verify it is filtered, while a nonmatching warning still reaches `caplog`.

Update README and `docs/ARCHITECTURE.md` with a short statement that the one-command evidence runner filters known benign runtime chatter and the per-manifest matrix command remains the raw diagnostic path.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Run focused tests:

    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/unit/test_qa_signed_acceptance_evidence.py tests/unit/test_cli_parser.py tests/unit/test_main_cli.py

Run lint:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py tests/unit/test_qa_signed_acceptance_evidence.py README.md docs/ARCHITECTURE.md

Run the real evidence command if time allows:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence

## Validation and Acceptance

This slice is accepted when the high-level evidence command still passes the same matrix counters, known dummy TSA logging is filtered in the evidence command, nonmatching warnings remain visible to logging, and documentation clearly says raw matrix diagnostics remain available through the per-manifest command.

## Idempotence and Recovery

The change is additive and command-scoped. Rerunning the evidence command overwrites ignored local artifacts only. If the filter hides too much, remove or narrow the filter and rerun the focused tests plus the real evidence command.

## Artifacts and Notes

Focused tests:

    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/unit/test_qa_signed_acceptance_evidence.py tests/unit/test_cli_parser.py tests/unit/test_main_cli.py
    30 passed in 3.04s

Focused lint:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py tests/unit/test_qa_signed_acceptance_evidence.py
    All checks passed!

Real one-command evidence run after filtering:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence
    Phase 3 signed acceptance evidence
    - summary markdown: artifacts/phase3_signed_acceptance_evidence_summary.md
    - signed_acceptance_matrix: PASS (10 scenarios, 7 successful signings)
    - signed_preview_parity_matrix: PASS (18 scenarios, 18 successful signings)
    - signed_fit_rejection_matrix: PASS (3 scenarios, 0 successful signings)

Real one-command evidence run after narrowing layout-warning suppression to fit-rejection only:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence
    Phase 3 signed acceptance evidence
    - summary markdown: artifacts/phase3_signed_acceptance_evidence_summary.md
    - signed_acceptance_matrix: PASS (10 scenarios, 7 successful signings)
    - signed_preview_parity_matrix: PASS (18 scenarios, 18 successful signings)
    - signed_fit_rejection_matrix: PASS (3 scenarios, 0 successful signings)

## Interfaces and Dependencies

The filter code should stay in `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` because it is evidence-command policy, not core signing behavior. It depends on Python `logging`; PySide6 QtCore should be imported lazily and treated as optional so unit tests that do not load Qt remain lightweight.

Revision note: Created 2026-05-14 by Codex to make the one-command signed acceptance evidence proof readable without weakening validation.

Revision note: Updated 2026-05-14 by Codex after implementing scoped quieting for known dummy-TSA, Qt offscreen, and pyHanko layout chatter and validating the real evidence command.

Revision note: Updated 2026-05-14 by Codex after compliance review to scope layout-warning suppression to the intentional fit-rejection matrix and clarify the docs.

Revision note: Updated 2026-05-14 by Codex after final compliance review to close the completed follow-up progress item.

Revision note: Updated 2026-05-14 by Codex after resuming the interrupted dev-loop to close the completed outcomes status.
