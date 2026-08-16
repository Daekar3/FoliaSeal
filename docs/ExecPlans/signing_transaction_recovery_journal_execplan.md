# Add durable signing-transaction recovery records

This ExecPlan is a living document and must be maintained in accordance with
`/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The current signing flow protects the original PDF during one running process, but it forgets the
temporary signed artifact if the process crashes after writing it. `docs/SPEC.md` and `docs/UI_SPEC.md`
require restart recovery to consider only a secret-free journal and FoliaSeal-owned artifacts, verify
the artifact before offering it, and never delete unrelated temporary files. This slice adds that
durable foundation without claiming a new GUI dialog: a signing request writes a small JSON journal
before the atomic write, records the owned staged path, removes the journal after successful completion,
and leaves a recoverable record when post-write verification fails or the process is interrupted.

The observable outcome is headless and testable. A simulated interrupted transaction can be discovered
after a new process starts, an owned artifact is offered only after injected verification succeeds,
malformed or secret-bearing journals are ignored safely, and resolving or discarding a candidate removes
only the journal and artifact proven to belong to that transaction.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` §4 and `docs/UI_SPEC.md` WF01/WF05/§16 define the secret-free journal,
  verification-before-offer, and safe-cleanup requirements.
- [x] `docs/ExecPlans/ui_signing_transaction_progress_execplan.md` provides the existing
  prepare/write/verify transaction boundary and owned temporary-output cleanup.
- [x] `docs/ExecPlans/ui_verification_recovery_reopen_execplan.md` provides the in-process
  preserved-artifact verification and untrusted-reopen semantics.
- [x] `docs/ExecPlans/signing_transaction_recovery_gui_execplan.md` connects verified candidates to
  explicit Open, Save copy as, Replace, and Discard actions; display-backed HITL remains open.

## Progress

- [x] (2026-08-16) Explorer review identified durable transaction journaling as the clearest
  remaining headless-capable SPEC/UI_SPEC gap; the current lifecycle explicitly defers it.
- [x] (2026-08-16) Confirmed the existing atomic staging boundary in
  `src/foliaseal/application/sign_pdf_use_case.py` and the lazy executor composition seam.
- [x] (2026-08-16) Added the Qt-free journal record, strict decoder, and recovery-candidate contract.
- [x] (2026-08-16) Added the filesystem-backed journal store under the application configuration
  directory with atomic writes and ownership-safe cleanup.
- [x] (2026-08-16) Integrated journal begin/stage/preserve/complete/discard transitions into
  `SignPdfUseCase`; journal failures fail closed as signing failures.
- [x] (2026-08-16) Exposed verified recovery candidates through the signing executor without
  importing Qt, including the lazy production executor.
- [x] (2026-08-16) Added red-to-green tests for interruption, malformed/secret-bearing records, ownership checks,
  verification gating, resolution cleanup, and idempotent restart scans.
- [x] (2026-08-16) Ran focused/full validation and reconciled architecture/parent/child plans;
  no generated journals or staged PDFs were retained. Full validation is `1519 passed, 20 skipped,
  1 warning`; display-backed and privileged gates remain open. The subsequent GUI recovery child
  raises the current full-suite evidence to `1535 passed, 20 skipped, 1 warning`.
- [x] Commit the complete journal plus GUI recovery slice and record revision `3e5a3913f`.

## Surprises & Discoveries

- Observation: `_write_atomically()` already creates a sibling `.tmp` file and the existing
  `finally` block removes it unless a post-write failure deliberately preserves it.
  Evidence: `SignPdfUseCase.execute()` and its `_write_atomically()`/`_replace_staged()` methods.
- Observation: a journal must begin before the first irreversible signing work but may contain only
  paths and a transaction identifier; certificate paths, passphrases, timestamps, and request
  payloads must never be serialized.
  Evidence: `SigningRequest` contains a passphrase and certificate path, while UI_SPEC explicitly
  limits restart detection to secret-free recovery data.
- Observation: path ownership can be proven without trusting arbitrary temporary files: the staged
  path must resolve inside the output directory, use the generated `.<output-name>.*.tmp` shape, and
  match the journal record exactly.
  Evidence: `_write_atomically()` uses `NamedTemporaryFile` with that prefix/suffix in the destination
  parent directory.

## Decision Log

- Decision: keep the journal contract Qt-free and place the JSON store under the existing XDG
  FoliaSeal configuration directory.
  Rationale: startup scanning and headless signing must share one durable contract, while Qt should
  only consume typed candidates later. The existing `AppSettingsStore.default()` already resolves
  the platform configuration root.
  Date/Author: 2026-08-16 / Codex.
- Decision: use one JSON file per transaction and replace it atomically.
  Rationale: a crash cannot leave a partially rewritten multi-record catalog, and per-transaction
  files make cleanup and restart idempotent.
  Date/Author: 2026-08-16 / Codex.
- Decision: verify candidates through an injected boolean verifier before exposing them; malformed,
  secret-bearing, missing, outside-owned, or failed-verification records are not candidates and are
  never used to delete arbitrary files.
  Rationale: the governing documents forbid implying an unverified artifact is safe and forbid
  deleting unrelated temporary files.
  Date/Author: 2026-08-16 / Codex.
- Decision: preserve the existing synchronous and asynchronous signing behavior; journal failures
  fail the signing operation rather than silently proceeding without crash recovery.
  Rationale: an unjournaled transaction would violate the safety contract, and callers already map
  unexpected execution errors to a stable failed result.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The durable journal is a secret-free, one-record-per-transaction JSON store under the application
configuration directory. `SignPdfUseCase` begins the record before signing, records the sibling
staged path and SHA-256 digest immediately after the atomic write, marks post-write verification
failures as preserved, marks final replacement as committing, and removes the record only after
successful completion. Ordinary pre-final failures discard the record and owned staged path.

The application and lazy executor expose `verified_recovery_candidates()` without importing Qt.
Candidate discovery is fail-closed: exact-field decoding rejects malformed or secret-bearing
records, ownership requires the recorded sibling shape (or the recorded output plus matching digest
in the committing crash window), and an injected verifier must positively validate the artifact.
Malformed records, verifier exceptions, missing files, and unrelated neighboring files are ignored
without cleanup. A post-replace crash in the `committing` state recovers the final output by digest.
The follow-on GUI child now supplies the Qt-free `FileSigningTransactionRecoveryResolver` and the
AppFrame Open, Save copy as, Replace, and Discard surface; resolution revalidates the candidate
digest before acting. The journal foundation's focused/full evidence was `1519 passed, 20 skipped,
1 warning`; the combined current suite is `1535 passed, 20 skipped, 1 warning`. Display-backed and
privileged-host acceptance remain open.

## Context and Orientation

`SignPdfUseCase` in `src/foliaseal/application/sign_pdf_use_case.py` writes signed bytes to a sibling
temporary file, verifies that file, then replaces the requested destination. A process crash between
those operations can leave a signed temporary file with no durable explanation. The lazy production
executor is `src/foliaseal/application/signing_executor.py`; the concrete backend is assembled in
`src/foliaseal/application/signing_backend.py`. Existing in-process preserved-artifact recovery lives
in `src/foliaseal/presentation/qt/signing_action_coordinator.py` and must remain unchanged.

The new application contract should live in
`src/foliaseal/application/signing_transaction_recovery.py`. It defines immutable records and a
protocol but does not import Qt, PySide6, pyHanko, or the filesystem. The JSON implementation belongs
in `src/foliaseal/infra/config/signing_transaction_journal.py`, alongside other configuration stores.
The journal directory is a child of the same XDG configuration directory used by
`AppSettingsStore.default()`.

## Change Slice

Primary change class: behavior change with focused tests and the minimum architecture/ExecPlan status
updates. Allowed generated artifacts are pytest-managed temporary directories only. Do not mix GUI
dialog layout, display-backed acceptance, certificate/password persistence, broad package changes, or
global evidence/nomenclature migrations into this commit.

## Plan of Work

First, define a `SigningTransactionRecord` with an exact JSON shape containing only version, transaction
ID, input path, output path, staged path (nullable), state, and creation time. Its decoder must reject
unknown fields, non-absolute paths, invalid states, malformed timestamps, and any key containing
secret-like names such as `passphrase`, `password`, `private_key`, or `certificate_bytes`.

Next, define `SigningTransactionJournal` operations for `begin`, `mark_staged`, `mark_preserved`,
`complete`, `discard`, and `verified_candidates`. The filesystem implementation writes records with a
temporary sibling and atomic replacement, uses one file per transaction, and only removes an artifact
after the record proves the path is an owned sibling of the recorded output. Candidate verification is
an injected callable receiving the staged path and returning `True` only for a complete local
verification.

Then integrate the journal into `SignPdfUseCase` as an optional dependency. The concrete production
executor supplies the XDG-backed store; tests can inject an in-memory or temporary store. Begin before
the first signing work, mark the staged path immediately after `_write_atomically()`, mark preserved
on every post-write verification failure, complete after `_replace_staged()`, and discard on ordinary
pre-final failure. The `finally` cleanup must continue removing an owned staged path when no preserved
state was recorded.

Finally, expose `verified_candidates()` on the concrete and lazy executor boundaries so a future app
frame recovery surface can ask for verified candidates without reaching into the journal files. Do not
open, copy, replace, or discard a candidate from this slice; those actions require explicit UI policy
and a follow-up display/test plan.

## Milestones

### Milestone 1: pure recovery contract

The application record, strict decoder, ownership predicate, candidate DTO, and journal protocol exist
with unit tests for exact fields, secret rejection, path confinement, and idempotent state transitions.

### Milestone 2: durable store and signing integration

The filesystem store writes atomic per-transaction JSON, the signing use case updates it at each
transaction boundary, and an injected verifier discovers only owned verified artifacts after a simulated
restart. Existing signing outputs and synchronous/asynchronous tests remain green.

### Milestone 3: validation and handoff

Run focused and full tests, Ruff, compileall, diff checks, active terminology scans, and process/artifact
cleanup. Reconcile `docs/ARCHITECTURE.md`, the parent compliance plan, the transaction-progress plan,
and this plan. Commit the slice and record the explicit follow-up for GUI recovery actions.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/python -m pytest -q tests/unit/test_signing_transaction_recovery.py tests/unit/test_signing_transaction_journal.py
    .venv/bin/python -m pytest -q tests/unit/test_sign_pdf_use_case.py tests/unit/test_signing_executor.py
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    .venv/bin/python -m pytest -q
    git diff --check

The focused tests must demonstrate that a record created in one store instance is discovered by a new
store instance, that a malformed or secret-bearing record is ignored without deleting its neighboring
files, and that only a verifier returning `True` yields a candidate. The full suite must remain green.

## Validation and Acceptance

Acceptance is behavioral and headless: after writing a record and staged artifact in a temporary XDG
configuration root, a fresh journal instance finds no candidate until the injected verifier succeeds;
it then returns exactly one candidate with the recorded input/output paths. Resolving or discarding that
candidate removes only the journal and proven owned staged artifact. A journal containing a passphrase,
private-key field, path outside the output directory, or missing artifact never produces a candidate and
never causes unrelated files to be deleted. A successful normal signing leaves no journal file. A crash
simulation that stops after `mark_staged` leaves the record available for the next process, and a
crash after replacement that leaves `committing` recovers the final output only when its digest
matches. Journal write failures fail closed instead of proceeding without durable recovery state.

## Idempotence and Recovery

All tests use fresh `tmp_path`/XDG roots. Store writes use atomic replacement and tolerate repeated
completion/discard calls. Cleanup resolves and validates the exact recorded path before unlinking; it
never glob-deletes a directory. If implementation fails, remove only pytest temporary roots and leave
the source checkout unchanged apart from the named plan/code/test files.

## Artifacts and Notes

Do not commit JSON journals, staged PDFs, certificates, passwords, generated PDFs, or logs. The only
durable artifacts are the application/infra modules, focused tests, this plan, and reconciled docs.

## Interfaces and Dependencies

The application protocol must be independent of Qt and cryptographic libraries. The infra store may
use only the Python standard library (`json`, `os`, `pathlib`, `uuid`, and `datetime`). The executor
boundary adds a `verified_candidates()` method returning immutable candidate records; it must preserve
existing `execute()` and `verify_preserved_artifact()` behavior. The verifier adapter used by production
must map the existing `VerificationSummary` to `True` only when signatures are present and
cryptographically valid, with no unexpected certification or timestamp failure.

Revision note: 2026-08-16 / Codex. GUI recovery follow-up committed as `3e5a3913f`; the durable
foundation and its explicit GUI actions are complete for headless/offscreen behavior. Created after a fresh governing-document audit identified durable
signing-transaction recovery as the next headless-capable SPEC/UI_SPEC compliance gap.
