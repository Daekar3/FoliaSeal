# Expose verified signing-transaction recovery in the GUI

This ExecPlan is a living document maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK child of
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md` and follows
`docs/ExecPlans/signing_transaction_recovery_journal_execplan.md`.

## Purpose / Big Picture

The previous recovery slice added a secret-free journal and a Qt-free executor API, but a restarted
application does not yet offer the verified candidate to a person. This slice connects one verified
candidate to a small AppFrame recovery surface with explicit Open, Save copy as, Replace, and Discard
actions. It must never offer an unverified candidate, delete an unrelated file, or replace a destination
without the existing consequence-confirmation policy.

The observable outcome is a restartable, headless-testable flow: AppFrame asks the executor for verified
candidates at startup, presents the candidate's source/output names and a warning that it came from an
interrupted signing transaction, and routes the selected action through a typed application boundary.
Open uses the existing untrusted recovery workspace. Save copy as writes a new destination without
touching the journal-owned artifact. Replace moves the owned staged artifact to its recorded output
only after explicit confirmation. Discard removes only the candidate proven owned by the journal.
Cancel or dialog dismissal leaves the candidate and its journal intact for the next launch.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` WF01/WF05/§16 define verification-before-offer and
  Open/Save copy as/Replace/Discard safety.
- [x] `docs/ExecPlans/signing_transaction_recovery_journal_execplan.md` supplies the immutable
  candidate, ownership predicate, digest-backed committing state, and Qt-free journal protocol.
- [x] `docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md` supplies dirty-draft confirmation,
  candidate workspace preparation, and the existing untrusted recovery open path.
- [ ] Display-backed HITL acceptance remains an external gate; this slice proves behavior through
  fake bindings and real offscreen Qt tests without claiming a live display run.

## Progress

- [x] (2026-08-16) Audited the current executor/AppFrame seams and confirmed that recovery candidates
  are verified headlessly but not surfaced at startup.
- [x] (2026-08-16) Added the Qt-free `FileSigningTransactionRecoveryResolver` for Open, Save copy as,
  Replace, and Discard, including ownership checks, sibling-atomic copy, and typed results.
- [x] (2026-08-16) Exposed verified candidate discovery and resolution through the executor without
  leaking journal/filesystem policy into AppFrame; resolution revalidates the staged digest.
- [x] (2026-08-16) Added the AppFrame recovery prompt with explicit consequence verbs, safe dismissal,
  replace confirmation, and copy-overwrite confirmation. Startup offers run after both no-document
  and initial-PDF launch paths.
- [x] (2026-08-16) Added focused/offscreen coverage for verified-only discovery, cancellation,
  copy, replace, discard ownership, cleanup, and launch integration.
- [x] (2026-08-16) Reconciled architecture, parent/recovery plans, ran validation, and cleaned
  generated resources. Committed as `3e5a3913f`.

## Change Slice

Allowed changes are the new Qt-free resolver, executor protocol methods, AppFrame recovery prompt,
focused tests, and minimum architecture/ExecPlan updates. Do not mix general draft autosave, new
signing UI layout, package changes, or display-only acceptance claims into this commit.

## Plan of Work

First, define a resolver protocol that accepts a `SigningRecoveryCandidate` and performs one typed
action. The resolver must use the journal's ownership-safe discard operation, copy an artifact with
an atomic sibling temporary path, and replace only the candidate's recorded output. It must return a
typed result or error rather than exposing journal/filesystem details to Qt.

Next, extend the executor boundary with `verified_recovery_candidates()` and resolution methods. The
lazy executor delegates to the concrete backend, while tests can inject a temporary journal and fake
resolver. Candidate discovery remains verification-gated and exceptions remain candidate-local.

Finally, have `FoliaSealAppFrame` query candidates after its no-document shell is mounted. If one or
more candidates exist, show one consequence-labeled prompt for the first candidate; later candidates
remain journaled for subsequent launches. Open routes to `open_recovery_pdf_path()` and keeps the
artifact untrusted. Save copy as uses the existing `QFileDialog` and leaves the candidate available.
Replace asks for explicit confirmation and only then resolves the candidate. Discard uses an explicit
destructive button. Dismissal is the safe default and does not mutate anything.

## Validation and Acceptance

Focused tests prove that failed verification produces no prompt, dismissal preserves the journal,
copy leaves the candidate and unrelated files intact, replace requires confirmation and consumes only
the owned candidate, and discard cannot remove a neighboring temporary file. Real offscreen Qt tests
observe prompt/action routing with deterministic fake bindings. The focused recovery command (journal,
recovery, and resolver tests) passes 31 tests; the focused AppFrame/launch command passes 64 tests. The
current validation commands are:

    .venv/bin/pytest -q tests/unit/test_signing_transaction_recovery.py tests/unit/test_signing_transaction_journal.py tests/unit/test_signing_transaction_recovery_resolver.py
    .venv/bin/pytest -q tests/unit/test_qt_app_frame_recovery.py tests/integration/test_gui_recovery_surface.py tests/integration/test_gui_launch_no_document.py
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    .venv/bin/pytest -q
    git diff --check

The full suite passes `1535 passed, 20 skipped, 1 warning`; Ruff, compileall, and `git diff --check`
are clean. The display-backed GUI audit remains separately recorded as environment-limited if
`DISPLAY=:0` is unreachable. No FoliaSeal, PySide6, pytest, or temporary audit process may remain
after validation.

## Idempotence and Recovery

All resolver tests use fresh temporary roots. Copy and replace use sibling atomic writes. Repeating
Discard or resolving a candidate after a prior resolution is harmless and never broadens deletion to a
directory or glob. If the slice is interrupted, leave the candidate journal and staged artifact
untouched, update Progress, and clean only test-owned roots.

## Outcomes & Retrospective

This slice is complete for the headless/offscreen recovery surface. The parent remains open for
display-backed HITL acceptance, privileged host/package gates, and any additional workflow gaps
discovered by compliance review; this child does not claim those release gates.

Focused recovery and AppFrame/launch validation are recorded above (31 and 64 passed respectively),
and the full suite is `1535 passed, 20 skipped, 1 warning`. The production path now revalidates the
candidate digest at resolution, and the explicit Replace and copy-overwrite confirmations remain
separate from candidate discovery.

Revision note: 2026-08-16 / Codex. Completed and committed as `3e5a3913f`. Created after the durable journal slice exposed the remaining
UI_SPEC WF01 restart-recovery surface gap.
