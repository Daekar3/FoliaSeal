# Remove Private Harness Reach-Through from Evidence Runner Factories

This living ExecPlan follows `.agents/skills/write-execplan/PLANS.md` and is governed by
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`. It is one complete architecture
slice: provider ownership, factory migration, boundary tests, evidence validation, documentation,
cleanup, and commit all belong to this plan.

## Purpose / Big Picture

FoliaSeal's evidence runner factories currently assemble runner dependencies by reading private
helpers from the 1,780-line `presentation/qt/phase3_harness.py` module. That makes a factory know
composition-root implementation details and makes focused tests import or monkeypatch a large Qt,
Pillow, and PDF harness. After this slice, the factories will consume a small typed provider bundle.
The harness remains the one production composition owner, but the private helper wiring is contained
there rather than spread into `evidence_runner_factories.py`.

The observable behavior is unchanged: the CLI evidence commands still construct lazily, preview and
signed matrices still emit the same scenario counts, JSON summaries, artifact paths, exit codes, and
phase3 DTO names, and interactive capture still follows the same Qt lifecycle. The architectural
improvement is demonstrated by fake-provider factory tests, import-isolation checks, and the existing
offscreen preview/signed evidence matrices.

## Child ExecPlan Dependencies

- [x] The parent scan round 15 found the private evidence-runner provider seam at Priority `68–71`
  with confidence `0.91` and three independent evidence records.
- [x] The parent design round compared minimal, flexible, and common-caller shapes with two
  independent reviews and selected the constrained hybrid recorded there.
- [x] The certificate-model boundary commit `dab5b7e59` is present and the worktree is clean.
- [x] `docs/SPEC.md` is frozen; this plan must not rename phase3 contracts.

## Progress

- [x] (2026-08-06) Created this self-contained child plan after the parent scan/design gates.
- [x] (2026-08-06) Added Qt-free operation-scoped provider records and aggregate in
  `src/foliaseal/presentation/qt/evidence_runner_providers.py`.
- [x] (2026-08-06) Added one lazy production composition builder in `phase3_harness.py` that binds existing
  helpers exactly once and returns the provider aggregate.
- [x] (2026-08-06) Migrated `evidence_runner_factories.py` to consume the aggregate without private helper access;
  preserve no-argument call sites and memoized operation runners.
- [x] (2026-08-06) Added provider/factory/import-isolation tests and updated existing assertions without changing
  runner dependency dataclasses or external output contracts.
- [x] (2026-08-06) Ran focused/full validation, offscreen evidence, process/temp-root cleanup, and
  docs reconciliation; parent ledger update and commit closure remain in progress.

## Surprises & Discoveries

Record every hidden provider, signature mismatch, import-cycle, or artifact/lifecycle difference here
with the command or test that exposed it. Do not solve a discovery by adding a compatibility alias or
by renaming phase3 symbols.

Initial discovery: the factories reach through at least ten private harness names, not only the
workspace builder. The selected boundary therefore groups the current interactive, preview-matrix,
and signed-acceptance dependencies separately so the new aggregate cannot become a generic
`run(kind)` service locator. The phase3 names remain external-contract debt and are intentionally
unchanged in this slice.

Implementation discovery: the production harness builder can bind all three operation records from
the existing helper functions without changing runner dependency dataclasses or eager-import behavior;
the provider module itself imports only the standard library. The first signed-matrix audit attempt
failed before execution because my temporary manifest path omitted the generated `assets/artifacts/`
segment; correcting the path produced the expected matrix and no code change was needed.

## Decision Log

- Decision: use one immutable `EvidenceRunnerProviders` aggregate containing three explicit
  operation-scoped provider records. Rationale: it combines the common-caller design's single
  construction policy with the flexible design's caller/test isolation, while avoiding a generic
  dispatcher and preserving existing runner dependency records. Date/Author: 2026-08-06, Codex.
- Decision: keep private helper references in one lazy builder owned by `phase3_harness.py`; factories
  may import only the public builder inside their build functions. Rationale: the harness is already
  the composition root and this removes the broad reach-through without eagerly loading Qt/Pillow/
  pyHanko. Date/Author: 2026-08-06, Codex.
- Decision: do not rename or alias phase3 symbols, CLI commands, DTOs, JSON keys, fixture names, or
  artifact paths. Rationale: the separate atomic nomenclature plan must inventory and migrate those
  contracts together; piecemeal renaming would create compatibility debris. Date/Author: 2026-08-06,
  Codex.

## Outcomes & Retrospective

The slice completed with 16 focused factory/provider tests, 107 runner/harness tests (one skipped),
1,074 full tests (11 skipped, one pre-existing Pillow warning), passing Ruff, CLI help, import
isolation, and diff checks. Preview parity produced 18/18 rows with zero errors; signed acceptance
produced 10 rows with 7 successful signings and zero scenario errors; fit rejection produced 3 rows
with zero scenario errors. The temporary evidence root was removed and process audit found no
FoliaSeal/Python/Qt process. `docs/SPEC.md` hash stayed `d929e189269f0f057c6a72b43fd2d430965a975be720b55139fdb1d92afe282b`.
Proxy measurement was navigation `0.30`, change amplification `0.70`, seam-risk reduction `0.75`,
boundary-test improvement `0.80`, interface compression `0.75`, and boundary isolation `0.85`, for
weighted Actual Improvement `0.52` versus predicted `0.45`, with no component regression below
`-0.10`. The provider aggregate remained operation-scoped; the next candidate must come from a fresh
three-explorer scan rather than an unplanned phase3 rename.

## Context and Orientation

`src/foliaseal/presentation/qt/evidence_runner_factories.py` owns lazy construction of three public
runner operations: interactive capture, headless preview matrices, and Qt-backed signed-acceptance
matrices. The runner classes in `phase3_preview_matrix_runner.py` and
`phase3_signed_acceptance_matrix_runner.py` already receive frozen dependency records. The
`InteractiveCaptureEngine` in `evidence_interactive_capture.py` likewise receives explicit callable
fields. `phase3_harness.py` contains the concrete Qt/Pillow/pyHanko adapters and private helpers that
currently fill those records.

A provider record is an immutable group of the callables required by one runner. The aggregate is
only a typed container of those three records; it has no lifecycle methods, string-key lookup, generic
dispatcher, or application-facing behavior. `phase3_harness.build_evidence_runner_providers()` is
called only from a factory build function, so importing the factory module remains headless.

## Plan of Work

First create `evidence_runner_providers.py` with Qt-free dataclasses
`InteractiveEvidenceProviders`, `PreviewMatrixEvidenceProviders`, `SignedAcceptanceEvidenceProviders`,
and `EvidenceRunnerProviders`. Their fields must match the current constructor inputs in the three
runner dependency records, including artifact/report policy for interactive capture and projection,
diagnostic, evaluator, render, workspace, and scenario callables for the matrix runners. Use
`collections.abc.Callable` and `Any` only at this presentation composition boundary; keep imports
free of `phase3_harness`, PySide6, Pillow, pyHanko, and runner implementation modules.

Then add `build_evidence_runner_providers()` to `phase3_harness.py`. It should construct the three
records one-for-one from the exact existing imports/functions used by the factories. It may call
`build_interactive_session_runner()` and `build_capture_assembler()` as before, and it must bind
`QtPdfRenderBackend`, `SignaturePresetCatalogStore.default`, projections, reports, and scenario
helpers exactly once. The function itself is reached only after a lazy factory call; do not move
matrix/session lifecycle or alter helper signatures.

Migrate `evidence_runner_factories.py` so each public `build_*_runner` accepts an optional keyword-only
`providers: EvidenceRunnerProviders | None = None` for deterministic tests but keeps the existing
no-argument behavior. When omitted, obtain the aggregate by importing and calling the public harness
builder inside the function. Populate the unchanged `InteractiveCaptureEngine`,
`Phase3PreviewMatrixRunnerDeps`, and `Phase3SignedAcceptanceMatrixRunnerDeps` records from the
operation-specific provider record. Remove every `harness._...` reference from this module. Keep
`_build_matrix_operation` and its one-time runner memoization unchanged.

Add focused tests in `tests/unit/test_evidence_runner_factories.py` or a dedicated provider test:
construct fake operation records, inject the aggregate, and assert each existing runner receives the
exact callable/object identity. Add a subprocess test proving importing both provider and factory
modules loads no PySide6, Pillow, pyHanko, or `phase3_harness`; add a production-builder smoke test
that confirms all required fields are populated only when explicitly requested. Assert the retirement
grep for `harness._` is empty. Preserve and run all existing matrix, CLI, lifecycle, and harness tests.

Update `docs/ARCHITECTURE.md` with the provider module, ownership rule, lazy composition data flow,
testing boundary, and a changelog entry. Update this child and the parent ledger with measurements,
surprises, acceptance evidence, and the selected future seam. Do not edit `docs/SPEC.md`.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    rg -n "harness\\._|build_.*evidence_runner|Phase3PreviewMatrixRunnerDeps|Phase3SignedAcceptanceMatrixRunnerDeps" src tests
    .venv/bin/pytest -q tests/unit/test_evidence_runner_factories.py tests/unit/test_phase3_preview_matrix_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py
    .venv/bin/ruff check src tests scripts
    .venv/bin/pytest -q
    .venv/bin/python -m foliaseal --help
    git diff --check

Run the existing preview-parity and signed-acceptance evidence commands with `QT_QPA_PLATFORM=offscreen`
under an explicit `/tmp/foliaseal-evidence-runner-provider-evidence` root. Record scenario counts,
successful/rejected outcomes, and summary paths. Remove that exact temporary root afterward and audit
for FoliaSeal/Python/Qt processes or dialog windows before committing.

## Validation and Acceptance

The slice is accepted only when all of the following are true: focused and full tests pass; Ruff and
diff checks pass; CLI help and subprocess import isolation pass; provider fake tests prove field
identity and no eager heavy imports; `rg 'harness\\._' src/foliaseal/presentation/qt/evidence_runner_factories.py`
returns no matches; preview and signed matrices report the same scenario counts and output contracts
as baseline; interactive capture still constructs and runs through its existing lifecycle; phase3
CLI/DTO/JSON/artifact names remain unchanged; `docs/SPEC.md` hash is unchanged; temporary roots and
processes are cleaned; and `git status --short` is empty after the intentional commit.

Measure proxies before and after: navigation friction `0.35`, change amplification `0.55`, seam-risk
reduction `0.65`, boundary-test improvement `0.70`, interface compression `0.70`, and boundary
isolation `0.80` are the initial estimates. Compute weighted Actual Improvement with the parent
formula; predicted improvement is `0.45`. Continue fixing or redesigning within this plan if the
threshold is missed; do not accept a green but shallow relocation.

## Idempotence and Recovery

Provider records and the builder are additive until factory tests pass. If a callable signature or
identity differs, compare the old factory wiring and migrate the exact function rather than wrapping
it in a new behavior path. If importing the provider module loads a heavy library, move that import
behind the harness builder. If a hidden caller expects a private factory name, migrate the caller or
record it; do not add a new alias in the factory. If matrix evidence fails, preserve the artifact
logs, update `Surprises & Discoveries`, and continue this plan or use the single allowed redesign.
Never leave GUI processes, dialogs, or temporary evidence roots behind.

## Artifacts and Notes

Allowed generated artifacts are only the explicit temporary evidence root named above and its logs;
they must be removed after validation. The durable artifacts are the provider module, the harness and
factory edits, focused tests, architecture documentation, this child plan, and the parent ledger.
No phase3 rename, compatibility alias, SPEC edit, or unrelated GUI redesign belongs in this slice.

## Interfaces and Dependencies

The final provider module must expose these stable types:

    @dataclass(frozen=True)
    class InteractiveEvidenceProviders: ...

    @dataclass(frozen=True)
    class PreviewMatrixEvidenceProviders: ...

    @dataclass(frozen=True)
    class SignedAcceptanceEvidenceProviders: ...

    @dataclass(frozen=True)
    class EvidenceRunnerProviders:
        interactive: InteractiveEvidenceProviders
        preview: PreviewMatrixEvidenceProviders
        signed: SignedAcceptanceEvidenceProviders

The public harness builder is:

    def build_evidence_runner_providers() -> EvidenceRunnerProviders: ...

The three factory functions retain their existing return types and no-argument behavior, with only a
keyword-only optional provider override for tests. Existing runner dependency records remain the
behavioral contract; this slice does not introduce a second runner implementation or a new CLI API.

Revision note: created 2026-08-06 after scan round 15 and design review; selected the constrained
hybrid to centralize provider policy while keeping operation-specific records and preserving all
phase3 contracts.
