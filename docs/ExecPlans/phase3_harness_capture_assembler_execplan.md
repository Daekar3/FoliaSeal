# Extract Phase 3 Harness Capture Assembler

> **Archived completed plan (2026-08-16).** Retained for provenance; current
> work belongs to the durable acceptance/evidence owners. Do not execute as an
> active implementation queue.

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the interactive Phase 3 harness will still behave the same from a caller's perspective, but `src/foliaseal/presentation/qt/phase3_harness.py` will stop owning both Qt session collection and the evidence-shaping logic that turns raw session state into signed-run bundles and the final capture payload. The user-visible proof stays the same: `foliaseal phase3-signing-harness` still emits the same JSON and checklist artifacts, and the focused harness tests still pass, but contributors can test the capture assembler at a narrower boundary without monkeypatching as many module-private helpers.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_evidence_service_program_execplan.md` is complete and already established the reporting boundary, the session-runner boundary, and the caller-facing evidence service.
- [x] (2026-08-16) No child ExecPlans were required; the completed slice is archived after implementation, validation, documentation, and commit `537a8dc9c`.

## Progress

- [x] (2026-06-05 23:05Z) Re-read the completed Phase 3 evidence-service program plans and the current harness/service architecture to identify the narrowest remaining internal seam.
- [x] (2026-06-05 23:10Z) Audited the live harness/session/reporting/service code and confirmed that signed-run bundling plus final capture-payload assembly are still co-owned by `phase3_harness.py`.
- [x] (2026-06-05 23:34Z) Extracted `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py` and rewired the interactive harness path to delegate signed-run bundling and final payload assembly through a dedicated assembler.
- [x] (2026-06-05 23:39Z) Added focused assembler tests in `tests/unit/test_phase3_harness_capture_assembler.py` and updated the raw session-runner harness test to pass a fake assembler instead of patching the old module-private seam.
- [x] (2026-06-05 23:46Z) Ran focused validation, reconciled `docs/ARCHITECTURE.md`, and closed the slice to final state.

## Surprises & Discoveries

- Observation (superseded 2026-08-01): the service boundary originally left `_build_signed_run_bundle()` and `_build_phase3_harness_capture_payload()` as harness seams. The signed-PDF evidence extraction removed the unused forwarding wrapper; capture payload shaping remains owned by the assembler.
  Evidence: `run_phase3_signing_harness()` still calls `_run_phase3_harness_session()` and then immediately calls `_build_phase3_harness_capture_payload()` in the same module.

- Observation: the current tests already point at the next seam because they patch session collection separately from payload finalization.
  Evidence: `tests/unit/test_phase3_harness.py::test_run_phase3_signing_harness_orchestrates_session_and_reporting` monkeypatches `_run_phase3_harness_session()` and asserts on the payload later passed into `finalize_phase3_harness_report()`.

- Observation: threading the assembler through `_run_phase3_harness_session()` is enough to move the signed-run seam without changing the public harness entry point or the reporting boundary.
  Evidence: `run_phase3_signing_harness()` now builds one assembler instance, passes it into `_run_phase3_harness_session()`, and reuses it for final payload assembly before calling `finalize_phase3_harness_report()`.

## Decision Log

- Decision: make the first follow-on slice an internal capture-assembler extraction instead of a broader Qt-session port rewrite.
  Rationale: the public service verbs and CLI routing are already explicit. The highest remaining leverage is to stop the interactive harness module from co-owning raw session collection and evidence shaping in one file. This moves the seam materially without widening into matrix execution or new public APIs.
  Date/Author: 2026-06-05 / Codex

- Decision: keep the new assembler in `src/foliaseal/presentation/qt/` for this slice.
  Rationale: the assembler still depends on preview/output snapshot helpers that live in the Qt harness layer, so forcing it into the application package now would widen the slice into a larger dependency migration. The goal here is a deepened internal boundary, not a package move.
  Date/Author: 2026-06-05 / Codex

## Outcomes & Retrospective

This slice is complete. `phase3_harness.py` still owns the interactive Qt session and the public Phase 3 harness entry points, but signed-run bundle assembly and final capture-payload shaping now live in `phase3_harness_capture_assembler.py`. The public service verbs, CLI dispatch, JSON field names, and report finalization path stayed unchanged.

## Context and Orientation

The current Phase 3 evidence stack has three important boundaries already in place. `src/foliaseal/application/phase3_evidence_service.py` owns the caller-facing verbs used by the CLI and the signed-acceptance evidence wrapper. `src/foliaseal/presentation/qt/phase3_harness_reporting.py` owns final report writing for one interactive harness capture. `src/foliaseal/presentation/qt/phase3_harness.py` still owns the remaining internal harness seam: it launches the interactive Qt shell, captures manual/final/signed-run states, builds signed-run evidence bundles, builds the final capture payload, runs preview matrices, and contains many preview-analysis helpers.

The relevant terms in this slice are simple. A "session runner" is the code that creates the Qt window and returns raw state such as captured preview states, sign requests, errors, and interaction counts. A "capture assembler" is the code that takes that raw state and turns it into stable JSON-ready dictionaries for signed runs and the final `Phase3HarnessCapture`. This repository already has a session-runner boundary in `Phase3HarnessSessionResult`; the missing deep module is the capture assembler that consumes it.

The key files for this slice are `src/foliaseal/presentation/qt/phase3_harness.py`, `src/foliaseal/presentation/qt/phase3_harness_reporting.py`, and `tests/unit/test_phase3_harness.py`. `docs/ARCHITECTURE.md` also describes the current Phase 3 ownership split and must be updated if the new helper changes that ownership description.

## Plan of Work

Create a new helper module under `src/foliaseal/presentation/qt/` dedicated to capture assembly. That module should own the functions that transform sign-time state into one signed-run bundle and transform `Phase3HarnessSessionResult` into the final capture payload dictionary. Keep the existing JSON field names and artifact semantics exactly the same.

Update `src/foliaseal/presentation/qt/phase3_harness.py` so the interactive session path still owns Qt execution and raw capture-state collection, but delegates signed-run bundling and final payload assembly to the new helper module. Keep `run_phase3_signing_harness()`, `_run_phase3_harness_session()`, `run_phase3_preview_matrix()`, and `run_phase3_signed_acceptance_matrix()` callable with the same signatures.

Move or add focused tests that prove the new boundary directly. The existing signed-run bundle freezing test is the clearest candidate to move to the new module. Add one focused payload-assembly test if the new boundary would otherwise only be covered indirectly through the orchestration test.

Finally, update `docs/ARCHITECTURE.md` so the Phase 3 harness description names the new helper and makes clear that `phase3_harness.py` no longer owns capture assembly inline.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Inspect the current harness/session/reporting split:

    sed -n '536,920p' src/foliaseal/presentation/qt/phase3_harness.py
    sed -n '1,220p' src/foliaseal/presentation/qt/phase3_harness_reporting.py
    sed -n '1712,2065p' tests/unit/test_phase3_harness.py

Implement the capture-assembler helper and rewire the harness module. Then run the focused validation:

    .venv/bin/python -m pytest tests/unit/test_phase3_harness_capture_assembler.py tests/unit/test_phase3_harness.py -k 'build_signed_run_bundle or run_phase3_harness_session_returns_raw_session_state or run_phase3_signing_harness_orchestrates_session_and_reporting'
    .venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_capture_assembler.py
    git diff --check

Architecture ownership changed, so update the docs and rerun the focused checks:

    .venv/bin/python -m pytest tests/unit/test_phase3_harness_capture_assembler.py tests/unit/test_phase3_harness.py -k 'build_signed_run_bundle or run_phase3_harness_session_returns_raw_session_state or run_phase3_signing_harness_orchestrates_session_and_reporting'
    git diff --check

## Validation and Acceptance

Acceptance is behavioral. The public Phase 3 harness entry points must still produce the same payload shape and reporting flow, and the focused tests must prove that the new helper owns signed-run bundle freezing and final capture-payload assembly. The slice is complete when:

- `run_phase3_signing_harness()` still passes the same payload shape into `finalize_phase3_harness_report()`;
- the signed-run bundle freezing proof continues to pass at the new boundary;
- the new payload-assembly test proves the assembler can shape the final payload from raw session state without the interactive harness loop;
- the raw session-runner test still proves `_run_phase3_harness_session()` returns raw state rather than final capture payloads;
- `ruff check` and `git diff --check` are clean.

## Idempotence and Recovery

This slice is additive and safe to retry. If a refactor step breaks imports, restore the prior call sites in `phase3_harness.py` and re-run the focused tests before attempting a narrower extraction. Do not change artifact schema keys or CLI/service request types in this slice; that would widen the work beyond safe recovery for a single loop.

## Artifacts and Notes

The primary allowed change class for the implementation commit is behavior change in the internal architecture only. Documentation/status updates may follow if required by the compliance review. Do not mix unrelated matrix-runner changes, CLI-surface changes, or signing-shell refactors into this slice.

## Interfaces and Dependencies

At the end of this slice, the repository should contain a small helper module, tentatively `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py`, that exposes explicit assembler functions for:

- building one signed-run bundle from sign-time state plus the signing result;
- building the final harness capture payload from `Phase3HarnessSessionResult`.

`src/foliaseal/presentation/qt/phase3_harness.py` should remain the only caller of those helpers in production code for now. The helper may continue to depend on existing preview/output snapshot functions that live in the same Qt package. `src/foliaseal/presentation/qt/phase3_harness_reporting.py` remains the reporting boundary and must not absorb this assembler responsibility.

Revision note: created on 2026-06-05 after the completed Phase 3 evidence-service program left capture assembly as the narrowest remaining internal harness seam.

Revision note: updated on 2026-06-05 after implementation to record the extracted `Phase3HarnessCaptureAssembler`, the focused assembler tests, the validation evidence, and the architecture reconciliation.
