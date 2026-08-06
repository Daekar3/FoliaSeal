# Autonomous Architecture Improvement Loop for FoliaSeal V1

This ExecPlan is the persistent state for the autonomous architecture-improvement loop. It must
remain self-contained and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. The product contract is frozen in `docs/SPEC.md`; this
loop may improve implementation, tests, documentation, packaging, and agent-facing command
surfaces, but it must not edit `docs/SPEC.md` without explicit user permission.

## Purpose / Big Picture

FoliaSeal must become simpler to change, easier to test through meaningful boundaries, less burdened
by obsolete compatibility and `phase3` debris, faster on normal workflows, and ready for both
production-quality GUI work and safe agent-targeted CLI additions. The loop will repeatedly identify
the strongest remaining architectural opportunity, choose a bounded deep-module refactor, execute it
through a complete DevLoop slice, measure the result, and rescan the live checkout. A successful slice
must improve the architecture rather than merely preserve green tests.

Observable success means that a representative user workflow is still demonstrably correct, a
smaller or clearer boundary owns more of the behavior, callers coordinate less implementation detail,
obsolete paths are retired when no V1 contract requires them, and repeatable tests or headless CLI
evidence prove the behavior without requiring fragile GUI internals.

## Loop Configuration

The fixed rules below come from the architecture-improvement-loop reference and may not be changed
during this run:

- Three independent explorers are required for every scan round.
- A candidate continues only at Candidate Priority 60/100 or higher with confidence at least 0.60.
- Two consecutive independent below-threshold confirmation scans are required before stopping.
- An accepted cycle must achieve Actual Improvement of at least 0.15 and no improvement component may
  regress by more than 0.10.
- A hybrid design must beat its highest-scoring base design by at least five shape-score points.
- At most five refactor cycles may be accepted in this run.
- Two consecutive accepted cycles delivering less than half their predicted improvement stop the loop.
- At most one architecture redesign attempt is allowed for a selected candidate.

Candidate scoring uses the reference formulas for Navigation Friction (NF), Change Amplification
(CA), Seam Risk (SR), Testability Gain (TG), Interface Compression (IC), Conceptual Cohesion (CC),
Migration Risk (MR), Behavioral Uncertainty (BU), agreement, evidence coverage, confidence, and
Candidate Priority. Design scoring uses the fixed Refactor Shape Score dimensions and penalties.

The repository does not currently contain the referenced `scripts/architecture_metrics.py`; arithmetic
will therefore be reproduced with a small ephemeral command or hand calculation, and the exact inputs
and outputs will be recorded here and in each child plan. No separate ledger or state file may be
created.

## Child ExecPlan Dependencies

- [x] The frozen product contract is available in `docs/SPEC.md`.
- [x] The current architecture map is available in `docs/ARCHITECTURE.md`.
- [x] The current checkout baseline is `main` at commit `ca6857ef9` (clean at loop start).
- [x] Child plan `signing_workspace_primary_session_hybrid_execplan.md` records the hybrid interface,
  baseline proxies, behavior map, predicted improvement, and acceptance gates.
- [ ] The selected child DevLoop has completed implementation, validation, compliance review,
  documentation reconciliation, and commit closure.

## Progress

- [x] (2026-08-05) Read the architecture-improvement-loop rules and fixed reference thresholds.
- [x] (2026-08-05) Verified that no existing incomplete parent ExecPlan governs this loop.
- [x] (2026-08-05) Rechecked the frozen product specification, current architecture documentation,
  repository baseline, and availability of the metrics helper.
- [x] (2026-08-05) Created this parent ExecPlan before the first independent scan.
- [x] (2026-08-05) Ran scan round 1 with three independent explorers and recorded all candidate
  evidence and scores.
- [x] (2026-08-05) Selected `signing-workspace-shell-seam` at Candidate Priority 70.93 and recorded
  the problem frame, rejected candidates, and fixed-formula arithmetic.
- [x] (2026-08-05) Generated and independently reviewed minimal, flexible/ports-and-adapters, and
  common-caller designs; selected the constrained hybrid at Refactor Shape Score 95.5.
- [x] Execute the implementation portion of `signing_workspace_primary_session_hybrid_execplan.md`
  through `$dev-loop`; typed bundle/session/view callers and boundary tests are present.
- [ ] Complete the child DevLoop's final validation, compliance review, measurement, documentation,
  and commit closure before accepting the cycle.
- [ ] Independently measure the completed slice, update the parent and child plans, and rescan.
- [ ] Stop only after the fixed threshold confirmation rule, cycle cap, or prediction-underperformance
  rule is actually satisfied.

## Scan and Candidate Ledger

### Scan Round 1 — completed 2026-08-05

Baseline commit: `ca6857ef9`; the main worktree was clean. Independent explorers
`arch_scan_one`, `arch_scan_two`, and `arch_scan_three` inspected the same objective without sharing
reports. The following bounded candidates had at least two independent evidence records and passed the
credibility gate:

- `signing-workspace-shell-seam`: `signing_shell.py` (551 lines),
  `signing_workspace_runtime.py` (415 lines), `signing_workspace_orchestrator.py`,
  `signing_workspace_composition.py`, `signing_workspace_action_bridge.py`,
  `signing_workspace_review_bridge.py`, `signing_workspace_shell_surface.py`,
  `signing_workspace_compatibility_surface.py`, and `signing_workspace_port.py`. The app-frame path
  `app_frame.open_pdf_path -> SigningWorkspaceHost.open -> SigningWorkspaceLifecycle ->
  build_qt_signing_shell` currently exposes dynamically patched widget attributes and a compatibility
  surface while the runtime, bridges, and interaction plan coordinate review, placement, refresh,
  and signing. Tests include `test_qt_signing_shell.py`, `test_qt_signing_workspace_runtime.py`,
  shell-surface, host, lifecycle, and workspace-interaction tests. It is local-substitutable: fake Qt
  widgets, in-memory stores, and application workflow fakes can stand in for the GUI adapters.
  Explorer scores were `(5,5,5,5,4,5,4,2)` and `(4.5,4.5,4.5,4.5,4,4.5,4,3)` for
  `(NF,CA,SR,TG,IC,CC,MR,BU)`. Medians are `(4.75,4.75,4.75,4.75,4,4.75,4,2.5)`;
  agreement is `0.912`, evidence coverage is `1.0`, confidence is `0.939`, benefit is `4.638`,
  penalty is `3.4`, and Candidate Priority is `70.93`.

- `visible-signature-layout-boundary`: `application/visible_signature_layout.py` (1,959 lines),
  `application/signing_preview_renderer.py` (1,145 lines), and
  `presentation/qt/signature_preview_layout.py` (1,183 lines) combine policy, geometry, Pillow,
  pyHanko, and Qt concerns. Explorer scores were `(5,4,5,5,4,5,4,3)` and
  `(4.5,4,4,4.5,3.5,4.5,3,2.5)`. Medians `(4.75,4,4.5,4.75,3.75,4.75,3.5,2.75)`;
  confidence `0.921`; Candidate Priority `68.05`.

- `phase3-evidence-composition-root`: `presentation/qt/phase3_harness.py` (2,385 lines), its
  matrix/session/workspace/reporting collaborators, and the application evidence service already
  have a typed boundary, but the composition root still owns many Qt/Pillow/pyHanko builders and
  snapshot projections. Explorer scores were `(5,5,5,4,4,3,4,2)` and
  `(4.5,4,4.5,4,4,4,3.5,2.5)`. Medians `(4.75,4.5,4.75,4,4,3.5,3.75,2.25)`;
  confidence `0.930`; Candidate Priority `64.86`.

- `persisted-schema-boundary`: `infra/config/schemas.py` (1,633 lines) combines app settings,
  certificates, reusable signing objects, and validators; application modules import those infra
  DTOs directly. Explorer scores were `(4,4,4,4,4,5,3,3)` and `(4,4.5,4,4,4,4.5,3.5,2.5)`.
  Medians `(4,4.25,4,4,4,4.75,3.25,2.75)`; confidence `0.965`; Candidate Priority `63.97`.

The following were rejected for this round: render-cache integration had only one independent score
record and Priority `53.10`; document-review/viewer interaction, certificate-management dialogs, and
the agent-safe inspect/verify CLI had one or insufficiently overlapping records for a credible
aggregate, or were lower-priority additive/GUI slices. They remain residual candidates for later fresh
scans. No candidate was rejected because tests were green; rejection was based on the fixed evidence
and priority gates.

Selected candidate: `signing-workspace-shell-seam`. It wins by more than two points over the next
candidate, has the highest testability and cohesion scores, directly advances the frozen SPEC's
document-centric GUI workflow, and removes a compatibility seam that currently forces app-frame,
harness, runtime, bridge, and tests to know widget internals. Its dependency category is
local-substitutable, so a stable session/port boundary can be tested with fake Qt widgets and
in-memory application collaborators.

## Design Selection Ledger

The selected candidate is `signing-workspace-shell-seam` (Candidate Priority `70.93`). Three designs
were generated and independently reviewed by `shell_design_review_one` and `shell_design_review_two`.
The flexible design is also the applicable ports-and-adapters design because the seam is
local-substitutable: fake Qt/application collaborators can implement the ports while the production
Qt shell remains an adapter.

- Design A, minimal command gateway: `SigningWorkspacePort.invoke(command)->WorkspaceCommandResult`
  plus `apply_app_settings(settings)->None`, with frozen command variants for current maintenance
  actions. Reviewer component medians were `(3,3.5,3.5,3,2.5,3,3)` and the base score was `62.5`.
  A generic dispatcher/manager penalty, caller command-construction burden, and the risk of leaking
  `CertificateCatalog` through the result union make this invalid for the selected scope. It also
  leaves the primary review/place/preview/sign flow outside the boundary.

- Design B, explicit capability ports: typed settings, actions, catalog, document-text, and reusable-
  object ports grouped in a `WorkspaceCapabilities` bundle; a typed workspace handle and separate
  testing adapter; a one-way compatibility facade with an explicit removal criterion. Reviewer
  component medians were `(4,3.5,4.5,4.5,4,3.5,4)`, yielding BaseShapeScore `81.0`. With cohesive
  protocols, no service-locator penalty, and a recorded retirement criterion it is valid, but by
  itself it still makes primary workflow callers coordinate several capabilities.

- Design C, common-caller session facade: `review`, `place_signature`, `preview`, `submit_sign`,
  `open_signed_output`, and `snapshot` alongside the existing maintenance verbs. Reviewer component
  medians were `(4.5,5,4.5,3.5,3.5,2.5,5)`, yielding BaseShapeScore `83.0`. A shallow-overlap penalty
  and speculative/mismatched sign-result surface reduce its credible score to `63.0`; it would also
  duplicate current runtime, review-bridge, properties-panel, and action-coordinator ownership if
  introduced as a standalone facade.

Selected architecture: constrained hybrid `typed-capabilities-plus-primary-session`. It retains the
existing narrow maintenance port as explicit cohesive capabilities, adds one `SigningWorkspaceSessionPort`
for the already-existing primary workflow sequencing and coherent snapshot, and returns a typed bundle
whose lifecycle view, maintenance capabilities, session port, and testing adapter are distinct. The
compatibility surface remains a one-way Qt-local adapter only until `rg` proves no production or harness
caller reaches its dynamic exports; it receives an explicit retirement milestone, not indefinite
compatibility status. Orchestrator scoring is `(4.5,5,5,5,4.5,4.5,5)` with BaseShapeScore `95.5`, no
fixed penalties, so it exceeds the best valid base by `14.5` points and introduces no hard-gate risk.
It hides runtime/bridge sequencing, eliminates caller `getattr`/widget knowledge, preserves existing
testing boundaries, and directly serves the SPEC's review/place/preview/sign workflow without merging
certificate/profile maintenance into a generic manager.

## Cycle Ledger

No architecture cycle has been accepted yet. Each cycle record will name its child ExecPlan, baseline
and implementation commits, predicted and actual component improvements, hard-gate results, prediction
accuracy, accepted/corrected/redesigned/abandoned status, and the strongest residual opportunity.

## Surprises & Discoveries

- Observation: the repository has many historical ExecPlans, but no existing parent plan that carries
  the fixed architecture-improvement-loop ledger and stopping rules.
  Evidence: `rg` found completed release/GUI/architecture child plans but no loop parent with Candidate
  Priority, Refactor Shape Score, and cycle records.
- Observation: the metrics helper named by the loop reference is absent from the checkout.
  Evidence: `rg --files | rg 'architecture_metrics.py|architecture.*metrics'` returned no path.
- Observation: the product specification explicitly favors replacement over V1 compatibility layers.
  Evidence: `docs/SPEC.md` says compatibility with previously saved profiles/presets is not a V1
  priority and clarity may replace old workflow or persisted shapes.

## Decision Log

- Decision: create a new loop parent at `docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`.
  Rationale: no incomplete parent plan matched the required autonomous loop state, and the parent is
  the only permitted persistent ledger.
  Date/Author: 2026-08-05 / Codex.
- Decision: preserve `docs/SPEC.md` unchanged.
  Rationale: its governance section freezes the product contract; implementation friction must be
  resolved in code, architecture docs, tests, packaging, or CLI plans unless user permission changes.
  Date/Author: 2026-08-05 / Codex.
- Decision: treat public historical names as removable unless current SPEC, active callers, persisted
  data, or documented release behavior proves they are V1 contracts.
  Rationale: the frozen V1 posture explicitly prefers replacement over compatibility debris.
  Date/Author: 2026-08-05 / Codex.

## Outcomes & Retrospective

The loop has just been initialized. This section will record accepted cycles, measured architectural
improvement, cumulative performance and friction changes, residual opportunities, and the exact
stopping condition. It must not be replaced with a claim of completion before the requirement-by-
requirement audit proves full scope or the fixed confirmation rule proves that remaining candidates
fall below the intervention threshold.

## Context and Orientation

The repository is a Python/PySide6 Linux desktop PDF signing application. `src/foliaseal/application`
contains workflows and application boundaries; `src/foliaseal/domain` contains signing and reusable
object models; `src/foliaseal/infra` contains concrete filesystem, PDF, certificate, timestamp, and
rendering adapters; `src/foliaseal/presentation/qt` contains the GUI shells, document viewer, signing
workspace, harnesses, and app-frame composition. `docs/ARCHITECTURE.md` describes current ownership,
while `docs/SPEC.md` defines user-visible V1 behavior and explicitly permits replacing legacy local
objects and workflows.

The loop must prioritize deep modules: a small stable interface that hides substantial sequencing,
policy, lifecycle, or dependency decisions. A file move, rename-only change, or private helper cleanup
without a stronger behavioral boundary is not an accepted architecture cycle, though such cleanup may
be included when it is necessary to retire a confirmed dead path in a deeper refactor.

## Plan of Work

Each scan round begins by spawning three independent explorer-light agents with the same repository-
level objective. Their reports will be consolidated into bounded candidate clusters and scored with the
fixed formulas. The highest qualifying candidate will then receive at least three radically different
interface designs: minimal, flexible, common-caller optimized, and ports-and-adapters when relevant.
Two independent reviewers plus the orchestrator will score each design. A hybrid may be selected only
after a base design is scored and the hybrid beats it by at least five points without a new hard-gate
risk.

The selected design becomes a self-contained child ExecPlan with behavior-preservation mappings,
baseline measurements, predicted improvement, exact interface signatures, migration/retirement rules,
validation commands, and explicit out-of-scope boundaries. `$dev-loop` then implements the child plan
completely, including tests, compliance review, architecture documentation, acceptance evidence,
cleanup, and commits. The parent is updated after every meaningful milestone.

After implementation, the same measurements are repeated. The cycle is accepted only when all hard
gates pass and Actual Improvement is at least 0.15 without a component regression over 0.10. The loop
then starts a fresh three-explorer scan rather than reusing stale rankings. It stops only at the fixed
cycle cap, prediction-underperformance rule, or after two consecutive independent scans find no
credible candidate at or above Priority 60.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Confirm the baseline and inspect `docs/SPEC.md`, `docs/ARCHITECTURE.md`, active ExecPlans, source,
   tests, packaging metadata, and CLI entry points before every scan.
2. Spawn exactly three independent `explorer-light` scans for the current round. Do not share reports
   or scores between them before each has completed.
3. Record candidate evidence and arithmetic in this parent plan. Reject candidates lacking two
   independent evidence records, confidence 0.60, or a bounded one-slice shape.
4. Spawn design subagents for the selected candidate under the fixed minimal, flexible,
   common-caller, and applicable ports-and-adapters constraints. Obtain two independent design
   reviews, rescore, and write the child plan before implementation.
5. Execute the child plan through `$dev-loop`; do not stop at an intermediate milestone. Keep the child
   and parent plans current, clean up processes and temporary artifacts, and commit intentionally.
6. Repeat the baseline measurements and perform the independent completion audit. If a hard gate or
   improvement threshold fails, continue the same child plan or perform the one allowed redesign.
7. Rescan from fresh explorers and continue until the fixed stopping condition is proven.

## Validation and Acceptance

The loop is not complete merely because tests are green. For every accepted cycle, the evidence must
show: preserved SPEC-visible behavior; a smaller or deeper boundary with less caller coordination;
equivalent or stronger boundary tests before any shallow tests are removed; no forbidden dependency
leaks; retired compatibility/dead paths with no live consumer; measured performance or friction
improvement where claimed; updated architecture and ExecPlans; clean process/artifact state; and a
clean `main` worktree.

At overall completion, the parent must list every accepted cycle and child plan, repeat the same
measurements, identify the best remaining candidate, and show two consecutive independent below-
threshold scans or another fixed stopping rule. If any SPEC requirement is unverified, the loop remains
active.

## Idempotence and Recovery

All scans and measurements are read-only. Child implementation plans must use additive migrations and
boundary tests before removing old paths. Temporary GUI or matrix artifacts must be written under
explicit `/tmp` directories and removed after validation; no broad recursive deletion is permitted.
If an implementation fails, preserve the failure evidence, update the child plan, and continue or use
the one permitted redesign. Never weaken acceptance criteria or restore compatibility code without a
current consumer and a recorded decision.

## Artifacts and Notes

Initial evidence:

    baseline commit: ca6857ef9
    baseline worktree: clean main
    frozen spec: docs/SPEC.md
    architecture map: docs/ARCHITECTURE.md
    metrics helper: absent; arithmetic must be recorded explicitly

The parent and child ExecPlans are the only persistent loop artifacts. Generated screenshots,
matrices, package audits, or temporary logs may be retained only when they are required evidence for a
specific child plan and must be named there.

## Interfaces and Dependencies

The loop itself depends on repository-local evidence rather than a runtime service. Explorers inspect
the checkout independently; design reviewers evaluate concrete signatures and migration paths; `$dev-loop`
owns implementation and validation. Production architecture may use in-process composition,
local-substitutable adapters, ports for owned remote services, or mocks for true external services, as
classified by the fixed reference. The product's existing CLI entry point is
`src/foliaseal/__main__.py`, and future agent-targeted commands must remain explicit, deterministic,
headless where possible, and separate from interactive GUI/manual harnesses.

## Change-Slice Boundary

The parent plan governs architecture refactors, tests, performance/friction measurements, packaging or
CLI changes required by a selected child, and documentation/status updates. Each child must define its
own narrow primary change class. Unrelated feature work, broad visual redesign, arbitrary SPEC edits,
and speculative public APIs are forbidden from being mixed into a child slice.

Revision note: created 2026-08-05 after confirming no existing architecture-loop parent plan and
reading the frozen product specification and fixed loop reference.
