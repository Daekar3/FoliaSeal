# Extract Signing-Draft Contracts from the Mutable Workflow

This living ExecPlan follows `.agents/skills/write-execplan/PLANS.md` and the fixed architecture loop
rules in `.agents/skills/architecture-improvement-loop/REFERENCE.md`. It is the complete next DevLoop
slice selected from Scan Round 23: move immutable validation, placement, and preview contracts out of
the mutable signing workflow, remove the reverse workflow/semantics import workaround, migrate all
callers, prove import isolation, preserve user-visible behavior, and close with documentation,
acceptance evidence, cleanup, and a commit.

## Purpose / Big Picture

Today, modules that merely consume a preview or validation value must import `signing_draft_workflow.py`,
a 671-line mutable state machine that also reads certificates, captures signing time, builds requests,
and coordinates fit validation. This makes the semantics module point back into the workflow while the
workflow uses a method-local semantics import to avoid a cycle. It forces maintainers to understand
workflow mutation when changing a passive value object and makes import-isolation and headless testing
harder.

After this slice, a preview renderer, layout planner, semantics resolver, or Qt view imports the small
neutral `application/signing_draft_contracts.py` module instead. The workflow remains the owner of
mutable draft state and request construction. Preview fields, validation issue codes/messages, placement
validation, signing readiness, serialized values, CLI behavior, and signed/preview output remain
unchanged. A subprocess import test demonstrates that the contracts boundary does not load the
workflow, Qt, Pillow, PyHanko, or the Phase 3 backend, and that the semantics boundary does not load
the workflow, Qt, or the Phase 3 backend. Existing PyHanko loading through `sign_pdf_use_case` is
characterized and left out of scope.

## Child ExecPlan Dependencies

- [x] Parent loop `docs/ExecPlans/architecture_improvement_loop_parent_execplan.md` records Scan Round
  23 and identifies `signing-draft-contract-boundary` as the strongest qualifying candidate.
- [x] The frozen product contract `docs/SPEC.md` and current architecture map `docs/ARCHITECTURE.md`
  are available and remain unchanged by this slice.
- [x] Three independent design reports and two independent reviews compared minimal, flexible, and
  common-caller shapes. Shape C was selected at Refactor Shape Score `91.8` with no penalty.
- [x] Baseline is clean commit `215b37818` (`Record artifact boundary completion ledger`).

## Progress

- [x] (2026-08-06) Recorded the candidate and design-selection evidence in the parent loop.
- [x] (2026-08-06) Completed preimplementation inventory: 16 production files and 9 test files
  import the workflow module; 15 production files and 8 test files actually consume moved contract
  names (the others import only `SigningDraftWorkflow`); the workflow contains six shared contract
  types plus `_issue`; the semantics module imports three of those types and the workflow has a
  method-local semantics import.
- [x] (2026-08-06) Added `signing_draft_contracts.py` with the exact immutable contracts and invariant behavior.
- [x] (2026-08-06) Migrated production, presentation, package-lazy-export, and test imports; removed
  workflow DTO definitions and compatibility aliases after the grep retirement gate passed.
- [x] (2026-08-06) Added contract, import-firewall, class-identity, and cycle-order tests while
  preserving existing workflow/preview/backend/Qt coverage.
- [x] (2026-08-06) Ran focused contract/import-boundary validation (`126 passed`), then corrected
  the workflow alias retirement gap and reran the full suite (`1,108 passed, 1 warning`).
- [x] (2026-08-06) Updated `docs/ARCHITECTURE.md`; offscreen signed acceptance passed `10/7`, preview
  parity `18/18`, and fit rejection `3/3`; exact evidence roots and canonical-preview directories
  were removed and no FoliaSeal/Python/Qt processes remained.
- [ ] Fresh-scan the clean post-commit repository and record the next residual opportunity.

## Surprises & Discoveries

- Observation: The application package lazy export map currently resolves all six contract names and
  `SigningDraftWorkflow` from `signing_draft_workflow.py`.
  Evidence: `src/foliaseal/application/__init__.py` maps the seven names in one tuple; split the DTO
  names to the new module while keeping only `SigningDraftWorkflow` in the workflow module.
- Observation: The semantics/workflow cycle is avoided by a method-local import rather than a true
  domain dependency.
  Evidence: `signing_draft_workflow.py:_resolve_visible_signature_semantics()` imports
  `visible_signature_semantics` locally, while `visible_signature_semantics.py` imports workflow
  contract types. Once contracts are neutral, a module-level workflow-to-semantics import is safe.
- Observation: The broad Phase 3 nomenclature inventory is not part of this slice.
  Evidence: the parent scan found roughly 106 phase3-named paths and 254 files containing the term;
  CLI names, DTOs, JSON keys, fixtures, and artifact paths require a separate atomic contract plan.
- Observation: `visible_signature_semantics` is not fully third-party-free on the baseline because it
  imports concrete appearance types from `sign_pdf_use_case` for runtime `isinstance` checks.
  Evidence: a subprocess import loads PyHanko through that existing dependency. The hard firewall is
  therefore limited to the new contracts module being free of workflow, Qt, Pillow, PyHanko, and the
  Phase 3 backend, while semantics must be free of the workflow, Qt, and Phase 3 backend. Extracting
  backend appearance types is a separate candidate and is forbidden in this slice.
- Observation: the completed contracts extraction preserves the existing PyHanko transitive import
  constraint rather than widening the neutral boundary.
  Evidence: `signing_draft_contracts.py` imports only `PageBox` and domain models; a subprocess import
  remains clean, while importing `visible_signature_semantics.py` still reaches PyHanko through
  `sign_pdf_use_case.py` for runtime appearance-type checks.

## Decision Log

- Decision: Select Shape C, common-caller optimized neutral contracts, as a standalone design.
  Rationale: it gives the 11 shared application consumers one immutable owner, removes the cycle
  workaround, and keeps mutable state and request orchestration in the workflow. Its reviewed score is
  `91.8`, above Shape A `87.5` and Shape B `86.6`; it is not called a hybrid, so the five-point hybrid
  rule does not apply. Date/Author: 2026-08-06, Codex with independent reviewers.
- Decision: Preserve constructor signatures, field order, enum values, tuple ordering, validation
  messages, and package-level names during migration. Rationale: these are UI, test, and persisted
  behavior contracts even though the values are not themselves persisted as a new schema. Date/Author:
  2026-08-06, Codex.
- Decision: Use a temporary identity re-export only while migrating callers, then remove it in this
  same slice. Rationale: it permits staged edits without type identity drift, but the hard retirement
  gate is `rg` showing no first-party imports of moved names from `signing_draft_workflow`; retaining
  the bridge beyond the completed migration would violate the selected architecture. Date/Author:
  2026-08-06, Codex.
- Decision: Do not add a generic extension dictionary, a validation service, a second port, or a Phase
  3 rename. Rationale: those are speculative surfaces or separate contract-governance work; this slice
  owns only immutable contracts and the import-direction correction. Date/Author: 2026-08-06, Codex.

## Outcomes & Retrospective

Implementation evidence recorded 2026-08-06: the focused contract/workflow/semantics/layout/preview/
fit set passed `126`; the complete suite passed `1,108` with one pre-existing Pillow deprecation
warning. Contract isolation and semantics import-order subprocess tests passed; all six package-level
contract identities resolve directly to `signing_draft_contracts`, and the workflow no longer exposes
those six names. `rg` shows only `SigningDraftWorkflow` imports remain from the workflow module. Ruff,
compileall, and diff checks pass; `docs/SPEC.md` is unchanged. Offscreen acceptance remains required
after the final commit and must report signed acceptance `10/7`, preview parity `18/18`, and fit
rejection `3/3`, followed by exact temporary-root and process cleanup.

The conservative before/after measurement is: navigation `0.35` (the six contracts move from the 671-
line workflow to one neutral module), change amplification `0.65` (15 production and 8 test contract
imports migrate to one owner), seam reduction `1.00` (one reverse import plus one local cycle workaround
to zero), boundary-test improvement `0.65` (no direct contract-owner tests to the new invariant,
identity, and firewall suite), interface compression `0.50` (six workflow exports retired), and
boundary isolation `1.00` (all moved-name workflow imports to zero). Weighted Actual Improvement is
`0.67` versus predicted `0.58`; no component regressed below `-0.10`. Independent compliance review
found no unresolved critical or major findings after the workflow alias removal, Qt-prefix firewall
correction, identity assertions, and architecture documentation update.

Commit and post-commit offscreen evidence are appended before closing this plan. The cycle is accepted
only with zero unresolved critical or major review findings, Actual Improvement at least `0.15`, and no
component regression below `-0.10`.

## Context and Orientation

`src/foliaseal/application/signing_draft_workflow.py` is the mutable application state machine. It
stores paths, certificate choices, appearance, placement, cached certificate preview values, and the
preview signing time. It also currently defines six immutable contracts: validation severity, one
validation issue, the validation exception, placement context, preview field, and preview payload. The
private `_issue()` factory remains workflow behavior because it creates validation results during state-
machine checks.

`src/foliaseal/application/visible_signature_semantics.py` resolves certificate-derived fields, stamp
text, metadata, and fit requests. `visible_signature_layout.py`, fit policy, horizontal reservation,
preview rendering, stamp preview construction, setup/coordinator sessions, viewer and workspace
sessions, and Qt preview/shell modules consume the shared contracts. The application package's
`__init__.py` lazily exposes selected names to keep import-time dependencies small.

The selected dependency graph is deliberately acyclic:

    signing_draft_contracts -> coordinate_transform + domain models
    visible_signature_semantics -> signing_draft_contracts + sign_pdf_use_case
    signing_draft_workflow -> signing_draft_contracts + visible_signature_semantics

The new contracts module must not import the workflow, semantics, backend, Qt, Pillow, PyHanko,
certificate readers, or filesystem adapters. Phase 3 naming in existing modules and commands is out of
scope and must remain unchanged.

## Architecture Selection Record

The candidate is local in-process application data with local test substitutes, so no remote port or
external-service mock is needed. Shape A was a data-only extraction with reviewed score `87.5`; Shape B
added an explicit typed additive-evolution policy and a temporary identity bridge, reviewed score
`86.6`; Shape C keeps the same contract module but optimizes the dominant callers by migrating all
consumers and removing the cycle workaround, reviewed score `91.8`. Shape B or C would receive the fixed
`-10` compatibility penalty if the bridge lacked an observable retirement gate; Shape C includes the
gate and removes it before acceptance.

The exact public contracts are:

    class SigningDraftValidationSeverity(str, Enum):
        ERROR = "error"
        WARNING = "warning"

    @dataclass(frozen=True)
    class SigningDraftValidationIssue:
        code: str
        message: str
        field_name: str | None = None
        severity: SigningDraftValidationSeverity = SigningDraftValidationSeverity.ERROR

    class SigningDraftValidationError(ValueError):
        def __init__(self, issues: tuple[SigningDraftValidationIssue, ...]) -> None: ...

    @dataclass(frozen=True)
    class SignaturePlacementContext:
        page_index: int
        page_box: PageBox
        rotation: int = 0

    @dataclass(frozen=True)
    class SigningDraftPreviewField:
        field_key: SignatureFieldKey
        label: str
        text: str
        visible: bool
        source: SignatureFieldSource
        hint: str | None = None

    @dataclass(frozen=True)
    class SigningDraftPreview:
        title: str
        page_index: int | None
        signature_rect: SignatureRect | None
        signer_label_prefix: str | None
        layout_template: SignatureLayoutTemplate | None
        stamp_position: SignatureStampPosition | None
        timezone_display_mode: SignatureTimezoneDisplayMode | None
        show_field_names: bool
        datetime_format: str | None
        text_style: SignatureTextStyle | None
        box_style: SignatureBoxStyle | None
        image_stamp_path: str | None
        fields: tuple[SigningDraftPreviewField, ...]
        detail_text: str
        issues: tuple[SigningDraftValidationIssue, ...]
        can_submit: bool
        stamp_text: str | None = None

`SignaturePlacementContext.__post_init__` must reject boolean or negative page indexes, non-90-degree
rotations, and invalid page boxes with the current exact messages. The validation exception must retain
`.issues` and join issue messages exactly as it does today, including `Invalid draft.` for an empty tuple.

## Scope and Migration Inventory

Create `src/foliaseal/application/signing_draft_contracts.py`. Move only the six contract classes and
their required imports. Keep `_issue()`, workflow fields, preview construction, certificate caching,
signing-clock capture, semantics resolution, fit delegation, request conversion, and state invalidation
in `signing_draft_workflow.py`.

Migrate the 15 production import sites that consume moved names, including application and Qt
presentation modules. Keep `SigningDraftWorkflow` imports pointed at the workflow. Migrate the eight test
files that import moved names. Split the package lazy export map so the six DTO/error names load from
`signing_draft_contracts` and `SigningDraftWorkflow` loads from `signing_draft_workflow`.

Allowed generated artifacts are temporary preview/signing evidence under explicitly named `/tmp` roots;
no generated PDF, PNG, JSON, or summary is committed. Forbidden mixed work includes Phase 3 renames,
new CLI commands, schema changes, fit-policy extraction, GUI redesign, certificate behavior changes, and
unrelated compatibility cleanup.

## Behavior Preservation Map

`SDC-1` preserves validation severity string values and enum identity; characterize with contract unit
tests and all existing validation tests. `SDC-2` preserves issue fields, defaults, tuple identity, and
error message formatting; add direct constructor/error tests and retain workflow validation tests.
`SDC-3` preserves placement page/rotation/page-box checks and exact errors; add an invariant matrix.
`SDC-4` preserves preview field order, visibility/source/hint values, optional defaults, and
`can_submit`; add direct DTO tests and retain preview renderer/Qt tests. `SDC-5` preserves class identity
through package-level lazy exports and both import orders; add subprocess tests. `SDC-6` preserves
canonical preview, fit diagnostics, signing output, CLI evidence, and JSON/artifact keys; prove through
the full suite and the offscreen signed acceptance/parity/fit matrices. No existing behavior test may be
deleted unless an equivalent or stronger boundary test is added and its mapping is recorded here.

## Baseline Measurements and Predicted Improvement

Baseline commit is `215b37818`. The representative workflow is draft construction -> semantics
resolution -> neutral layout/preview -> signing validation. The baseline workflow module is 671 lines,
defines six shared contract classes plus `_issue`, and is imported by 16 production files and 9 test
files overall; 15 production and 8 test files consume the moved contracts. The semantics-to-workflow reverse import is one direct cycle edge, and the
workflow contains one method-local semantics import workaround. Boundary tests directly exercising the
contract owner are absent; existing tests reach the classes through the workflow module.

Using the fixed component scale and conservative repeatable proxies, predicted improvements are:
navigation `0.35`, change amplification `0.65`, seam reduction `0.90`, boundary-test improvement
`0.55`, interface compression `0.35`, and boundary isolation `0.95`. With the reference weights this
is predicted Actual Improvement `0.58`. Recompute each component using the same counts after migration;
assign zero rather than inventing a value where a before/after count is not credible.

## Plan of Work

First add the contract module by copying the exact class bodies and imports, then add direct unit tests
for defaults, enum values, error formatting, placement rejection, preview tuples, and optional
`stamp_text`. Do not alter field order or messages. Add the subprocess import firewall before migration
so the dependency rule is executable.

Next update `application/__init__.py` lazy mappings and migrate application imports, then Qt imports,
then tests. During this additive phase, workflow may import and re-export the classes solely to keep any
unmigrated caller type-identical; the bridge is not accepted as a final state. Update
`visible_signature_semantics.py` to import contracts and move its workflow dependency to zero. Replace
the method-local semantics import in the workflow with a normal module-level import only after the
firewall passes; leave backend/fit imports local because that is a separate heavy runtime seam.

Run focused suites and grep the complete tree for moved-name imports from the workflow. When zero
first-party imports remain, delete the six old definitions and all compatibility re-exports from the
workflow, then rerun identity and import-order tests. Update `docs/ARCHITECTURE.md` to describe the
neutral contract owner and the state-machine boundary, and update both parent and child plan ledgers.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`.

    rg -n "from foliaseal.application.signing_draft_workflow import|import foliaseal.application.signing_draft_workflow" src tests
    .venv/bin/pytest -q tests/unit/test_signing_draft_workflow.py tests/unit/test_visible_signature_semantics.py tests/unit/test_visible_signature_layout.py tests/unit/test_signing_preview_renderer.py tests/unit/test_visible_signature_fit_policy.py
    .venv/bin/ruff check src tests

After migration, run the focused contract/import suites, then `.venv/bin/pytest -q`,
`.venv/bin/python -m compileall -q src`, `git diff --check`, CLI help, and fresh subprocess import
checks. Run the offscreen evidence command with an exact root:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence --artifacts-root /tmp/foliaseal-contract-boundary-evidence --summary-markdown-path /tmp/foliaseal-contract-boundary-evidence-summary.md

Expect signed acceptance `10` scenarios with `7` successful signings, preview parity `18/18`, and fit
rejection `3/3`. Remove that exact root, summary, and any `foliaseal-canonical-preview-*` directories,
then audit for active FoliaSeal/Python/Qt processes before committing.

## Validation and Acceptance

Acceptance requires the full preexisting suite and new contract tests to pass with no added skips,
weakened assertions, or live external services. A subprocess importing contracts must show no
`signing_draft_workflow`, `phase3_signing_backend`, Qt, Pillow, or PyHanko module loaded. A subprocess
importing semantics and layout must show no `signing_draft_workflow`, `phase3_signing_backend`, or Qt
module loaded; existing PyHanko loading through `sign_pdf_use_case` is characterized, not changed.
Importing workflow then semantics and semantics then workflow must
complete in fresh processes with one shared contract class identity. `rg` must show zero first-party
imports of the six moved names from `signing_draft_workflow`; only `SigningDraftWorkflow` may remain
there. Package-level exports must resolve to contract classes, not aliases with a second type.

The current exact validation messages, preview field order/defaults, fit diagnostics, signing output,
CLI names, JSON keys, fixtures, artifact suffixes, and Phase 3 nomenclature are immutable. The full
offscreen matrices must retain their expected counts. Documentation must match final ownership. The
cycle hard gates are Actual Improvement at least `0.15`, no component regression below `-0.10`, zero
unresolved critical or major review findings, and a clean worktree after commit.

## Idempotence and Recovery

The extraction is additive until focused tests and import firewalls pass. If an import cycle appears,
restore only the temporary identity bridge and move the smallest offending import to the contracts
module; never add a contracts-to-workflow import. If class identity differs, compare package lazy
exports and update them to point directly at the contract module before deleting aliases. If a preview
or signed matrix differs, stop removal, compare old/new DTO field values and error strings, repair the
migration, and rerun the exact matrix. Cleanup uses only named temporary roots and the canonical
preview prefix.

## Artifacts and Notes

Persistent artifacts are this child plan, the parent ledger, source/tests/docs, and the final commit.
Generated evidence is temporary and must be removed. The frozen `docs/SPEC.md` hash is
`d929e189269f0f057c6a72b43fd2d430965a975be720b55139fdb1d92afe282b`; no SPEC edit is authorized.

## Interfaces and Dependencies

`signing_draft_contracts.py` may import `dataclasses`, `enum`,
`foliaseal.application.coordinate_transform.PageBox`, and necessary domain value types only. It must
expose the six classes listed in the Architecture Selection Record and no workflow or infrastructure
type. `signing_draft_workflow.py` imports those classes and keeps `SigningDraftWorkflow` and `_issue`.
`visible_signature_semantics.py` imports only contract classes from the new module. The application
package lazy map points each moved name to `signing_draft_contracts`.

The contract module has no I/O and no runtime service dependency, so tests instantiate it directly. The
production workflow continues to use its current certificate preview reader, signing clock,
fit-validator, layout service, and request conversion. This slice deliberately does not move those
behaviors or create a generic validation service.

Revision note: created 2026-08-06 after Scan Round 23 and Design Selection 24; selected Shape C after
two independent reviews, with explicit bridge retirement and cycle-removal gates. Updated after
preimplementation reconnaissance to record that `visible_signature_semantics` already loads PyHanko
through `sign_pdf_use_case`; only the new contracts module is required to be fully third-party-free.
