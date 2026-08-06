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
- [x] Child plan `reusable_signing_models_application_boundary_execplan.md` records the persisted-
  schema boundary, canonical application models, repository protocol, phase3 migration handoff,
  baseline proxies, and acceptance gates.
- [x] The selected child DevLoop has completed implementation, validation, compliance review,
  documentation reconciliation, and commit closure in `9ce248fd3`.

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
- [x] Complete the child DevLoop's final validation, compliance review, measurement, documentation,
  and commit closure before accepting the cycle.
- [x] Independently rescan the live checkout after the accepted cycle; scan round 2 selected the
  visible-signature-layout boundary for the next design review.
- [x] Completed scan round 2 with three independent explorers after `9ce248fd3`; the next
  candidate is recorded below and the next child plan is pending design review.
- [x] Completed fresh scan round 6 and design review after cycle 5; persisted-schema boundary was
  selected over compatibility-surface, CLI, and nomenclature-only alternatives.
- [x] Execute `reusable_signing_models_application_boundary_execplan.md` through the complete
  DevLoop, including duplicate schema deletion, import-boundary tests, full suite, release
  matrices, cleanup, and documentation reconciliation.
- [x] Complete the post-cap continuation slice after measuring the reduced schema boundary and
  confirming no frozen contract or acceptance-matrix regression; this is not counted as a sixth
  accepted cycle under the fixed five-cycle loop cap.
- [x] Completed the next post-cap scan with three independent explorers and recorded the
  signature-properties surface as the highest qualifying candidate.
- [x] Completed minimal, flexible, and common-caller design reviews; selected the constrained
  properties-surface hybrid and created its child ExecPlan.
- [x] Execute `signature_properties_surface_hybrid_execplan.md` through the complete DevLoop,
  including the setup port, refinement-dialog extraction, boundary tests, full validation,
  acceptance evidence, cleanup, and documentation reconciliation.
- [x] Complete the post-cap continuation slice's improvement measurement and record the explicit
  `QT_QPA_PLATFORM=offscreen` acceptance invocation required by this headless environment.
- [x] Completed the next fresh three-explorer scan after `4c8570724`; the interactive harness Qt
  lifecycle is the next qualifying seam.
- [x] Completed three independent lifecycle design reviews and created the child ExecPlan for the
  selected constrained lifecycle-port design.
- [x] Completed the post-lifecycle three-explorer scan; duplicate Phase 2 harness lifecycle wiring
  is the next qualifying seam.
- [x] Completed three Phase 2 lifecycle design reviews and created the child ExecPlan reusing the
  existing shared harness lifecycle port.
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

### Cycle 1 — accepted 2026-08-05

- Child: `signing_workspace_primary_session_hybrid_execplan.md`
- Baseline: `ca6857ef9`; implementation/docs commit: `9ce248fd3`
- Shape: constrained `typed-capabilities-plus-primary-session` hybrid, score `95.5`
- Improvement: predicted `0.1925`, actual `0.2125` (`1.10x`), no component regression over `0.10`
- Gates: frozen SPEC unchanged; 1,039 tests passed; Ruff/diff/import isolation passed; preview 8/0;
  signed 8 with 6 successes and 2 matched intentional rejections; no leftover artifacts/processes;
  caller seam grep 4 -> 0; docs and plans reconciled; main clean after commit.
- Status: accepted. The strongest residual opportunity is the tracked
  `phase3_nomenclature_retirement_execplan.md`, pending a fresh scan and contract inventory.

### Scan Round 2 — completed 2026-08-05

Three independent explorers reviewed the post-cycle checkout at `a8c41d954` without sharing
reports. The qualifying candidates were:

- `visible-signature-layout-boundary`: `application/visible_signature_layout.py` (1,959 LOC) still
  co-locates neutral layout contracts with Pillow/PyHanko measurers, stamp probes, appearance
  adapters, layout conversion, and rendered-ink fit/cache helpers. Independent priorities were
  approximately `64.0`, `62.6`, and `64.0` with confidence `0.82`–`0.90`; the median candidate
  remains above the `60` threshold and the architecture document explicitly tracks import-purity
  debt. Existing boundary tests make this locally substitutable.
- `signing-workspace-lifecycle-surface`: shell/composition/compatibility ownership remains broad;
  one explorer scored it about `70.4`, but the evidence was less independent than the layout cluster
  and it is deferred until the new typed bundle has another consumer cycle.
- `phase3-evidence-composition/nomenclature`: the 2,386-line composition root and historical names
  remain broad, but CLI/DTO/artifact contracts make a rename-only slice high-risk and below the
  layout candidate for this round.
- `persisted-schema-boundary`: 1,633 lines and direct application imports remain a candidate, but
  migration risk and lower GUI leverage keep it behind layout extraction.
- Render-cache/performance and CLI inspect/verify were below threshold (approximately `40` and `51`).

Selected next candidate: `visible-signature-layout-boundary`. The required next child must preserve
the neutral `VisibleSignatureLayoutPort`/`VisibleSignaturePreparation` and prepare-once WYSIWYG
semantics while moving third-party materializers and backend-only rendered-ink routines behind a
one-way adapter boundary. It must not reintroduce removed planner facades or optional-plan paths.

Design review selected the constrained A+B shape in
`visible_signature_layout_adapter_boundary_execplan.md`: a minimal neutral-module split plus narrow
injected Pillow/PyHanko materializer ports. Two reviewers rejected a standalone common-caller facade
as a second planning path and agreed that import isolation, one-time measurement, memoized
preview/signing projections, and explicit stamp suppression are hard gates.

### Scan Round 3 — completed after commit `4554c6922`

Three fresh independent explorers reviewed the committed checkout. The qualifying residual
candidate was:

- `phase3-preview-render-capture-boundary`: `presentation/qt/phase3_harness.py` remains a 2,386-line
  composition root that wires private Qt/headless preview rendering, widget geometry, Pillow overlay
  drawing, canonical render comparison, analysis diagnostics, artifact writes, and snapshot payload
  shaping into both live and headless adapters (`_snapshot_preview`,
  `_build_qt_preview_render_capture_payload`, `_capture_headless_preview_render`, and overlay
  helpers). Two explorers independently identified this cluster; the third explorer independently
  verified the main alternative below. Dependency category is local-substitutable presentation
  infrastructure with injected Qt/Pillow/render/analysis ports. Scores `(NF,CA,SR,TG,IC,CC,MR,BU)`
  are `(4.5,4,4,4.5,3.5,4,3,2.5)`, confidence `1.00`, Benefit `4.125`, Penalty `2.8`, and
  Candidate Priority `65.7`.
- `signing-time-snapshot`: preview and final signing independently read the system clock across
  `SigningDraftWorkflow`, `VisibleSignatureSemanticsService`, `SigningActionCoordinator`,
  `SigningRequest`, and `phase3_signing_backend.prepare_phase3_signing_plan()`. It is a credible
  SPEC/WYSIWYG candidate, but one explorer plus orchestrator verification yields lower confidence;
  scores `(3.5,3,3.5,4,3.5,4,2.5,2)` and Candidate Priority `55.5`.
- App-frame/workspace lifecycle plus dialog compatibility scored `56.9` in one independent report
  and remains below threshold for this round.

Selected next candidate: `phase3-preview-render-capture-boundary` at `65.7`. It wins over the
signing-time alternative by the fixed threshold and has the strongest independent evidence. The
next child must leave the signed-matrix lifecycle and external `phase3-signing-*` CLI/JSON/artifact
contracts unchanged while extracting only the preview/render capture analyzer boundary.

### Cycle 3 — accepted 2026-08-05

Child `docs/ExecPlans/phase3_preview_render_capture_boundary_execplan.md` is implemented. The
workspace dependency bundles now consume one typed `PreviewRenderCapturePort`, and both live Qt and
headless snapshot paths make one request/result capture call while retaining separate environment
adapters and the existing artifact mapping. The large environment-specific callback bodies remain
in `phase3_harness.py` by explicit scope decision; a future scan may rank their extraction, but this
cycle is not claiming that file move.

Evidence: focused boundary/harness/workspace tests `96 passed`; full suite `1044 passed` with one
pre-existing Pillow deprecation warning; Ruff and `git diff --check` clean. The preview matrix ran 8
scenarios with 0 error rows. The signed acceptance matrix ran 8 scenarios with 6 successful
signings, 2 matched intentional rejections, zero cryptographic/annotation/preview-output failures,
and `acceptance_expectations_passed=True`. Explicit temporary matrix directories were removed and
the process audit found no FoliaSeal, Qt harness, or pytest processes.

Cycle 3 measurement: navigation `0.0`, change amplification `0.5`, seam reduction `1.0`,
boundary-test improvement `0.25`, interface compression `0.5`, boundary isolation `0.0`;
`Actual Improvement = 0.35`, predicted `0.30`, prediction accuracy `1.17x`, no component below
`-0.10`. The cycle is accepted. The internal `phase3_*` names remain external-contract debt and
are tracked by the atomic nomenclature-retirement plan rather than renamed piecemeal.

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

Cycle 2 implementation, documentation reconciliation, and commit are complete. The child
plan moved third-party layout materialization out of the neutral core without changing the plan,
preview, signing, CLI, JSON, or artifact contracts. The neutral module now imports without PIL,
PyHanko, Qt, or the signing backend; the adapter edge owns concrete rule/materializer construction.

Implementation evidence so far:

- Child: `docs/ExecPlans/visible_signature_layout_adapter_boundary_execplan.md`.
- New composition edge: `src/foliaseal/application/visible_signature_layout_adapters.py`.
- Neutral core reduced from `1,959` LOC to `1,876` LOC; the adapter edge is `177` LOC. The former
  `_SignatureLayoutReservation` now carries only `LayoutRuleSpec` values.
- Boundary, layout, backend, and preview tests pass; the final full suite is `1042 passed` with one
  pre-existing Pillow deprecation warning. Ruff, `git diff --check`, and subprocess import-isolation
  checks are clean.
- Compliance review identified and resolved adapter/backend import-order risk, duplicated private
  background-layout wrappers, weak neutral appearance typing, backend-vendor result naming, and
  stale direct adapter imports. The two Qt `VisibleSignatureLayoutEngine.plan()` callers are
  documented as geometry-only consumers rather than target materializers.

Release evidence is also green: the preview matrix executed 8 scenarios with 0 error rows; the
signed matrix executed 8 scenarios with 6 successful signings, 2 matched intentional rejections,
zero cryptographic/annotation/preview-output failures, and `acceptance_expectations_passed=True`.
The explicit `/tmp/foliaseal-layout-preview` and `/tmp/foliaseal-layout-signed` directories were
removed and the process audit is clean. The child records the same six-component proxy measurement:
`Actual Improvement = 0.34`, predicted `0.25`, prediction accuracy `1.36x`, with no component below
`-0.10`; all major compliance findings are resolved. Commit `4554c6922` (`refactor: isolate
visible-signature layout adapters`) is on `main`, and Cycle 2 is accepted.

Cycle 3 was committed as `81c613e4e`. Cycle 4 source and plan changes are ready for the intentional
commit. The loop is not globally complete: commit this accepted cycle, then run a fresh
three-explorer rescan and apply the fixed below-threshold confirmation rule before stopping.

### Scan Round 4 — completed after commit `81c613e4e`

Two independent explorers plus an orchestrator-local scan reviewed the clean post-commit checkout.
The preview/widget evidence residual remains qualifying: `phase3_harness.py` is 2,399 lines and
still combines widget geometry, scalar snapshot readers, overlay-coordinate policy, canonical
rendering, and evidence orchestration. Independent priorities were approximately `66.5` and
`65.7`, confidence at least `0.68`; the strongest alternative was backend fit-policy extraction at
approximately `60.2`, while app-frame lifecycle and application-to-infra schema coupling ranked
below threshold or required a broader migration. The scan also confirmed that the public
`phase3-signing-*` CLI/DTO/JSON/artifact names are compatibility-frozen and must not be renamed
piecemeal.

Design reviews compared minimal relocation (`61.0`), flexible ports/adapters (`78.5`), common-caller
unification (`76.0`), and constrained hybrid (`90.1`; independent 23/25 safety score). The selected
Cycle 4 child keeps live/headless lifecycles and the typed capture port unchanged while extracting
only shared preview-widget evidence policy into a presentation-edge module.

### Cycle 4 — accepted 2026-08-05

Child `docs/ExecPlans/preview_widget_evidence_boundary_execplan.md` is implemented. New module
`src/foliaseal/presentation/qt/preview_widget_evidence.py` owns shared duck-typed geometry, text
color, pixmap projection, and overlay-coordinate helpers; `phase3_harness.py` retains only Qt
ancestor mapping, canonical rendering, artifact writers, and orchestration. No public contract or
phase nomenclature was renamed.

Evidence: full suite `1046 passed` with one pre-existing Pillow warning; Ruff and diff checks clean;
preview matrix 8 scenarios/0 error rows; signed matrix 8 scenarios/6 successful signings/2 matched
intentional rejections/zero cryptographic, annotation, or preview-output failures/
`acceptance_expectations_passed=True`. Temporary `/tmp/foliaseal-widget-evidence-*` directories
were removed and the process audit is clean.

Cycle 4 proxy measurement: navigation `0.0`, change amplification `0.5`, seam reduction `0.5`,
boundary-test improvement `0.25`, interface compression `0.5`, boundary isolation `0.5`;
`Actual Improvement = 0.30`, predicted `0.25`, prediction accuracy `1.20x`, no component below
`-0.10`. Commit `8f43bb9a3` (`refactor: isolate preview widget evidence policy`) is on `main`.

### Scan Round 5 — completed after commit `8f43bb9a3`

Two independent explorers and an orchestrator-local scan reviewed the clean checkout. The strongest
remaining candidate is rendered-ink/visible-signature fit-policy ownership in
`application/phase3_signing_backend.py` (1,538 lines): duplicated fit-gate mutation, concrete
measurement wiring, and preview/output fidelity policy remain concentrated there. Independent
priority was approximately `65.1` with confidence `0.90+`. Workspace compatibility exports and
application-to-infra schema coupling are credible debts but broader or lower-confidence; the
unfinished phase nomenclature migration remains a separate atomic plan because public CLI/DTO/JSON/
artifact names are frozen contracts.

Design reviews compared minimal gate relocation (`~78.8`), flexible ports/adapters (`~78.8` after
scope penalty), common-caller backend ownership (`~63`), and constrained hybrid (`~89.5`). The
selected child keeps concrete PyHanko/Pillow measurement in the backend adapter, introduces one
neutral decision/gate helper, and preserves the existing prepare-once object as the sole gate.

### Cycle 5 — accepted 2026-08-05

Child `docs/ExecPlans/visible_signature_fit_policy_boundary_execplan.md` is implemented. The new
`VisibleSignatureFitDecision` and `apply_visible_signature_fit_gate()` policy are used by both
prepared-plan and public validation paths, removing duplicate gate mutation while leaving fit
error codes, reservation evidence, and external contracts unchanged. Focused policy and fit suites
are green. Full suite `1047 passed` with one pre-existing Pillow warning; Ruff and diff checks are
clean. Preview matrix: 8 scenarios/0 error rows. Signed matrix: 8 scenarios/6 successful signings,
2 matched intentional rejections, zero cryptographic/annotation/preview-output failures, and
`acceptance_expectations_passed=True`. Temporary directories and processes are clean.

Cycle 5 measurement: navigation `0.0`, change amplification `0.5`, seam reduction `0.5`,
boundary-test improvement `0.25`, interface compression `0.5`, boundary isolation `0.5`;
`Actual Improvement = 0.30`, predicted `0.25`, prediction accuracy `1.20x`, no component below
`-0.10`. This reaches the fixed five-cycle cap; the loop stops after the intentional commit and
final clean-worktree audit. Remaining backend adapter concentration, workspace compatibility
exports, app-to-infra DTO coupling, and phase nomenclature migration are ranked follow-on plans,
not silently ignored work. Implementation commit `597efea39` and architecture-documentation commit
`f308bbe30` are on `main`.

### Post-cap continuation scan — completed 2026-08-06

Three independent design/scan reports and the orchestrator's repository review were consolidated
after cycle 5. The strongest qualifying seam was `persisted-schema-boundary`: `infra/config/
schemas.py` had 1,633 lines combining app settings, certificates, reusable signing-object models,
validation, and JSON codecs, while five application modules imported reusable DTOs from infra.
Independent candidate dimensions were approximately `(4.5, 4.5, 4, 4.5, 4, 4.5, 3, 3.5)` with
confidence `0.86`--`0.97` and Candidate Priority approximately `64`--`67`, above the fixed `60`
gate. The compatibility-surface candidate was lower and the phase3 rename remained an atomic
external-contract migration rather than a safe rename-only cycle.

Design review compared a minimal schema submodule (83/100), a ports/adapters repository split,
and a flexible application-owned model plus persistence adapter. The selected constrained hybrid
kept `CatalogRepository` as the application protocol, moved canonical reusable models and catalog
policy to `application/reusable_signing_models.py`, and left JSON/path/atomic-write/legacy-reader
behavior in `infra/config/profile_storage.py`. It exceeded the valid minimal shape on ownership and
boundary clarity without extracting certificates or changing public contracts.

### Post-cap continuation slice 1 — accepted 2026-08-06

Child `docs/ExecPlans/reusable_signing_models_application_boundary_execplan.md` is implemented.
`infra/config/schemas.py` fell from `1,633` to `712` lines: the duplicate reusable model block,
appearance/placement codecs, and infrastructure re-exports were deleted. Application reusable
callers now import only the canonical model module; the coordinator accepts the `CatalogRepository`
protocol, and a shared domain `ConfigValidationError` keeps application and infrastructure
validation behavior coherent without an application-to-infra import.

Evidence: focused reusable-model/storage/coordinator/draft suites passed; the full suite passed
`1048` tests with one pre-existing warning; Ruff and `git diff --check` passed; application model
subprocess import isolation passed; CLI help/parser checks passed. The preview matrix executed `8`
scenarios with `0` errors. The signed matrix executed `8` scenarios with `6` successful signings,
`2` matched intentional rejections, `0` cryptographic failures, `0` annotation mismatches, `0`
preview-output comparison failures, and `acceptance_expectations_passed=true`. Explicit temporary
directories were removed and the process audit was clean.

Continuation-slice proxy measurement: navigation `0.5`, change amplification `0.5`, seam reduction `0.5`,
boundary-test improvement `0.5`, interface compression `0.5`, boundary isolation `0.75`;
`Actual Improvement = 0.54`, predicted `0.25`, prediction accuracy `2.16x`, with no component below
`-0.10`. The phase3 nomenclature plan now contains the live inventory (32 source files, 30 test/
fixture files, 3 scripts, README, and 162 documentation files) and replacement mapping; no public
phase3 contract was renamed piecemeal. The implementation commit closes the continuation slice; it
does not alter the original loop's five-cycle cap.

### Post-cap continuation scan 2 — completed 2026-08-06

Three independent explorers reviewed the clean post-schema-boundary checkout. The qualifying
candidate was the `SignaturePropertiesPanel` surface (`src/foliaseal/presentation/qt/
signing_workspace_properties_panel.py`, 1,163 lines): its constructor and handlers still combine
certificate/preset selection, contextual refinement persistence, preview lifecycle/layout handoff,
Qt control rendering, and application-session orchestration. `SigningWorkspaceComposition` passes
many concrete panel callbacks into the action/interaction/shell bridges, and
`SigningWorkspaceActionBridge._confirm_signing_request()` still reaches the panel's private
`_setup_session`.

The primary explorer scored `(4.5,4,4,4,3.5,4.5,3,2.5)` for
`(NF,CA,SR,TG,IC,CC,MR,BU)`; the orchestrator independently verified the same call paths and scored
`(4,4,4.5,4.5,3.5,4.5,3,2.5)`. Medians are `(4.25,4,4.25,4.25,3.5,4.5,3,2.5)`, confidence
`0.92`, Benefit `4.1375`, Penalty `2.8`, and Candidate Priority approximately `64.3`. The
candidate is local-substitutable through fake Qt bindings, an in-memory setup session, and existing
coordinator tests.

Other credible or verified alternatives were below the fixed gate or less bounded: application /
infra certificate DTO coupling (`~59.7`), the broad phase3 evidence composition root (`~55`), the
signing-shell lifecycle surface (`~56`), render-cache integration (`~50`), and a new agent-safe
sign/verify CLI (`~58`). The phase3 nomenclature migration remains a coordinated external-contract
plan and is not used to inflate this candidate's score.

### Post-cap continuation design selection 2 — completed 2026-08-06

Three designs were reviewed independently:

- Minimal dialog extraction: move the ~170-line `open_refinement_dialog()` workflow to a Qt-local
  `SignatureRefinementDialog` with `RefinementDialogResult`; BaseShapeScore `78`. It sharply
  reduces panel orchestration and preserves the existing modal behavior, but does not remove the
  composition/action bridge's concrete-panel and private-session coupling.
- Flexible application session port: expose a variation-neutral `SigningPropertiesSessionPort`
  returning `SignaturePropertiesViewState` / typed transitions and hide coordinator/workflow/store
  details behind an injected adapter. BaseShapeScore `84`; risk is a broad capability interface
  that duplicates the already-existing `SigningSetupSession`.
- Common-caller setup port: add a `SigningWorkspaceSetupPort` for the dominant shell/action/
  interaction callers, replacing private `_setup_session` access and concrete-panel callback
  wiring. BaseShapeScore `82`; risk is a read/command/dialog surface that could grow into a generic
  manager.

Selected constrained hybrid: combine the minimal dialog extraction with only the common-caller
setup port elements that remove the verified private-panel leak. The hybrid keeps all domain
decisions in `SigningSetupSession`/`DefaultSignaturePropertiesCoordinator`, keeps Qt dialog/error/
preview policy at the presentation edge, and exposes no widget, coordinator, workflow, store, or
private-session objects. Rescored dimensions `(4.5,4.5,4.5,4,4.5,4,5)` produce BaseShapeScore
`87.5`, exceeding the highest base by `5.5` points with no hard-gate risk. The exact interface,
retirement rule, and behavior map are recorded in
`docs/ExecPlans/signature_properties_surface_hybrid_execplan.md`.

### Post-cap continuation slice 2 — accepted 2026-08-06

Child `docs/ExecPlans/signature_properties_surface_hybrid_execplan.md` is implemented. The
1,163-line `SignaturePropertiesPanel` fell to 1,008 lines as the modal refinement workflow moved to
`signing_workspace_refinement_dialog.py` (247 lines) and shell callers moved behind
`SigningWorkspaceSetupPort`/`PanelSigningWorkspaceSetupAdapter` (88 lines). The action bridge no
longer reaches `_setup_session`; the only remaining active-dialog bridge is explicitly temporary
for existing acceptance tests and has a retirement criterion in the child plan.

Focused setup/shell/coordinator coverage passed `158` tests; the full suite passed `1,049` tests with
one pre-existing warning. Ruff, `git diff --check`, CLI help/parser checks, and application-boundary
imports passed. Offscreen release evidence passed signed acceptance (`10` scenarios, `7` successful
signings, `3` matched intentional rejections), signed preview parity (`18/18` successful), and
signed fit rejection (`3/3` matched), with zero cryptographic, annotation, or preview-comparison
failures and `acceptance_expectations_passed=true`. Explicit preview/signed `/tmp` directories were
removed and the process audit was clean. The initial non-offscreen invocation failed before matrix
execution because `xcb` could not connect to display `:0`; the supported offscreen rerun passed.

Continuation-slice proxy measurement: navigation `0.25`, change amplification `0.25`, seam-risk
reduction `0.25`, boundary-test improvement `0.50`, interface compression `0.25`, cohesion `0.25`,
and behavioral-uncertainty reduction `0.25`; `Actual Improvement = 0.25`, predicted `0.25`, with no
component regression below `-0.10`. This accepts the post-cap continuation slice without reopening
the fixed five-cycle cap. The coordinated `phase3_nomenclature_retirement_execplan.md` remains the
next contract-sensitive cleanup plan; its public CLI/DTO/JSON/artifact names stay frozen until an
atomic migration is approved.

### Post-cap continuation scan 3 — completed after `4c8570724`

Three independent explorers reviewed the clean checkout. The highest valid bounded candidate is the
interactive evidence harness lifecycle in
`src/foliaseal/presentation/qt/phase3_harness_session_runner.py` (291 lines). Its `run()` method
still creates/reuses `QApplication`, constructs and sizes `QMainWindow`, builds the central toolbar /
body layouts, calls `setCentralWidget`, shows/executes the event loop, and closes the window across
several failure paths while also coordinating shell callbacks, capture assembly, and signing state.
The existing `phase3_signed_acceptance_lifecycle.py` demonstrates a local fakeable lifecycle seam,
and `tests/unit/test_phase3_harness_session_runner.py` already asserts title, size, mount, show, and
cleanup behavior.

The lifecycle-focused explorer scored `(4.5,4,4.5,4.5,4,4,3,2.5)` for
`(NF,CA,SR,TG,IC,CC,MR,BU)`, confidence `0.88`, and Candidate Priority approximately `67`. The
other independent scans ranked the broad evidence composition root at approximately `64.87` and
the rendered-fit/layout suggestion as already completed or below-gate after rechecking the live
checkout. Render-cache integration scored approximately `55` because its tested `RenderCachePolicy`
has no production caller and lacks measured invalidation semantics. The `phase3` nomenclature
migration remains a broad external-contract change and is not inflated into this lifecycle slice.

### Post-cap continuation design selection 3 — completed after `4c8570724`

Three independent designs were reviewed:

- Minimal lifecycle port: add `Phase3HarnessLifecyclePort` with opaque toolbar/body targets and
  `start/mount/show/exec/close`; BaseShapeScore `85`. This is tightly bounded but leaves the runner
  dependent on lifecycle-specific bindings and does not provide a reusable context/cleanup shape.
- Flexible ports/adapters context: add `QtHarnessSurface`, separate application/window ports, and a
  context-managed `Phase3HarnessQtLifecycle.session(...)`; BaseShapeScore `84.5`. It maximizes
  substitution but risks a generic Qt service and broadens the surface with separate port objects.
- Common-caller lifecycle design: generalize the existing fakeable harness lifecycle pattern to a
  `HarnessQtLifecyclePort` with typed window specification, mount/show/exec/process-events/close,
  while leaving toolbar/capture/signing orchestration in the runner; BaseShapeScore `88`.

Selected constrained hybrid: use the common-caller lifecycle port with the flexible context-managed
cleanup/session implementation, but scope it to the interactive evidence harness and do not merge it
with the app-frame `SigningWorkspaceLifecycle` or migrate Phase 2 in this slice. Rescored dimensions
`(4.75,4.75,4.75,4.75,4.5,4.5,4.5)` produce BaseShapeScore `93.5`, exceeding the strongest base by
`5.5` points with no hard-gate risk. The child plan preserves all CLI/JSON/artifact contracts and
records the exact retirement grep for direct Qt lifecycle calls in the runner.

### Post-cap continuation slice 3 — accepted 2026-08-06

Child `docs/ExecPlans/phase3_harness_qt_lifecycle_hybrid_execplan.md` is implemented. The
interactive session runner now consumes `HarnessQtLifecyclePort`; `QtHarnessLifecycle` owns
QApplication reuse/creation, QMainWindow setup, central/toolbar/body layout construction, mount,
show/exec, and idempotent close. The runner retains callback, signing, workspace, capture, and
result orchestration, and no direct QApplication/QMainWindow/setCentralWidget/local-close calls
remain in it. The runner source fell from `291` to `284` lines while the new lifecycle adapter is
`105` lines and its boundary tests are `111` lines; this is an ownership/depth improvement rather
than a file move alone.

Focused lifecycle/session/harness coverage passed `108` tests; the full suite passed `1,051` tests
with one pre-existing warning. Ruff, diff checks, application import isolation, and CLI help/parser
checks passed. Offscreen acceptance evidence passed signed acceptance (`10` scenarios, `7` successful
signings, `3` matched intentional rejections), signed preview parity (`18/18` successful), and
signed fit rejection (`3/3` matched), with zero cryptographic, annotation, or preview-comparison
failures and `acceptance_expectations_passed=true`. Explicit `/tmp` matrix directories were removed
and the process audit was clean.

Continuation-slice proxy measurement: navigation friction `0.25`, change amplification `0.50`,
seam-risk reduction `0.50`, boundary-test improvement `0.50`, interface compression `0.50`,
cohesion `0.50`, and behavioral-uncertainty reduction `0.25`; `Actual Improvement = 0.43`, predicted
`0.25`, with no component regression below `-0.10`. This accepts the slice without altering the
fixed five-cycle cap. The `phase3` nomenclature plan remains the next contract-sensitive cleanup
candidate; public commands/DTOs/JSON/artifact names remain frozen until its atomic migration.

### Post-cap continuation scan 4 — completed after `c246d9b02`

Three independent explorers reviewed the clean lifecycle-boundary checkout. The highest qualifying
candidate is duplicate Qt lifecycle wiring in `src/foliaseal/presentation/qt/phase2_harness.py`
(447 lines): it independently creates/reuses QApplication/QMainWindow, sizes the window to 1280x900,
constructs the central/toolbar layout, mounts via `setCentralWidget`, shows/executes the event loop,
and never guarantees close on report or setup failures. The shared, tested
`phase3_harness_qt_lifecycle.py` seam now provides exactly the fakeable lifecycle contract needed by
both harnesses.

The lifecycle scan scored `(4,4.5,4,4.5,4.5,4.5,2.5,2.5)` for
`(NF,CA,SR,TG,IC,CC,MR,BU)`, confidence `0.90`, and Candidate Priority approximately `69.34`.
The compatibility-surface retirement alternative scored about `66` but remains more test-coupled;
the signing-backend adapter boundary scored about `63.3`; render-cache integration and a new agent
CLI remained below gate. The existing shared lifecycle makes this candidate local-substitutable and
keeps Phase 2 behavior/CLI/artifact contracts bounded.

### Post-cap continuation design selection 4 — completed after `c246d9b02`

Three designs were independently reviewed:

- Minimal direct migration to `HarnessQtLifecyclePort` scored `90.5`; it removes duplicate lifecycle
  calls while keeping Phase 2 orchestration in place.
- Flexible dependency-injected Phase 2 runner extraction scored `84.5`; it improves unit seams but
  adds a broad request/dependency bundle and is unnecessary for this bounded ownership fix.
- Common-caller shared-lifecycle migration scored `92`; it reuses the existing port unchanged,
  preserves Phase 2-specific vertical content/control ordering, and keeps lifecycle policy identical
  across Phase 2 and Phase 3.

Selected design: the common-caller shared-lifecycle migration. It is a single base design (not a
hybrid), so no hybrid bonus gate applies. The child plan keeps the Phase 2 public wrapper, capture
JSON/checklist/evidence command, CLI names, artifact paths, and dimensions unchanged while removing
all direct Qt lifecycle calls and guaranteeing idempotent cleanup.

### Post-cap continuation slice 4 — accepted 2026-08-06

Child `docs/ExecPlans/phase2_harness_shared_lifecycle_execplan.md` is implemented and closed. The
Phase 2 viewer harness now reuses `HarnessQtLifecyclePort` and the shared `HarnessQtBindings` instead
of maintaining a second QApplication/QMainWindow binding and lifecycle implementation. It retains
the viewer workflow, toolbar callbacks, metrics, selection/error capture, checklist rendering,
evidence-command generation, public defaults, and 1280x900 window contract. One content QWidget/VBox
preserves the established viewer → metrics → instructions → status order, while controls remain on
the shared toolbar. Setup, event-loop, report, and artifact failures all close the lifecycle exactly
once; the local direct lifecycle calls and duplicate binding dataclass are retired.

Focused Phase 2/shared lifecycle/session coverage passed `14` tests; the full suite passed `1,054`
tests with one pre-existing warning. Ruff, diff checks, application import isolation, and CLI
help/parser checks passed. Offscreen acceptance passed signed acceptance (`10` scenarios, `7`
successful signings, `3` matched intentional rejections), signed preview parity (`18/18` successful),
and signed fit rejection (`3/3` matched), with zero cryptographic, annotation, preview-comparison, or
expectation failures. The explicit `/tmp/foliaseal-phase2-acceptance` root and generated repository
acceptance artifacts were removed; no FoliaSeal/Python process or dialog remained.

Continuation-slice proxy measurement: navigation friction `0.25`, change amplification `0.50`,
seam-risk reduction `0.50`, boundary-test improvement `0.50`, interface compression `0.50`,
cohesion `0.50`, and behavioral-uncertainty reduction `0.25`; `Actual Improvement = 0.43`, predicted
`0.25`, with no component regression below `-0.10`. This accepts the slice without changing the fixed
five-cycle cap. The next scan must be fresh; coordinated `phase3` nomenclature retirement remains the
leading contract-sensitive candidate, but public commands/DTOs/JSON/artifact names stay frozen until
its atomic migration is executed.

### Post-cap continuation scan 5 — completed after `5e396932a`

Three independent explorers reviewed the clean post-Phase-2 checkout. The highest qualifying bounded
candidate is the residual mixed responsibility in
`src/foliaseal/presentation/qt/phase3_harness_workspace.py` (540 lines): it combines normalized
scenario/capture DTOs, live-shell and headless adapters, appearance/placement mutation, preview
capture, backend reservation/sign-time diagnostics, and Qt event pumping. The live adapter still
reaches through the testing panel and mount-target process-events path in both `apply_scenario()` and
`capture_snapshot()`, while callback/materializer dependency records carry broad policy bundles.

The strongest scan scored `(4.5,4.5,4.5,4.5,4.0,4.5,3.0,2.5)` for
`(NF,CA,SR,TG,IC,CC,MR,BU)`, confidence `0.88`, and Candidate Priority approximately `66`. The
remaining `phase3_harness.py` preview/evidence composition root scored about `64.87`; the signing
backend seam about `63`; compatibility-surface retirement about `61`; and phase3 nomenclature
retirement about `45` because CLI/DTO/JSON/artifact contracts are explicitly frozen. The shared
workspace seam is therefore the next design target; all public phase3 names and serialized contracts
remain frozen pending an atomic nomenclature migration plan.

### Post-cap continuation design selection 5 — completed after `5e396932a`

Three independent designs were reviewed for the shared workspace seam:

- Pure snapshot builder: move `Phase3HarnessWorkspaceSnapshot` and `as_mapping()` to a Qt-free
  builder module, leaving both adapters' reads/effects in place; shape score approximately `90`.
- Flexible scenario resolver: extract profile/appearance/timestamp/rectangle mutation into a pure
  `ScenarioMutation` resolver reused by live and headless adapters; shape score approximately `90.5`,
  but profile-reader/API and import-cycle risk make it a broader behavioral migration.
- Common-caller capture service: accept one typed input record from each adapter and centralize only
  stable snapshot construction/mapping, leaving workflow/render/event-pump/sign-time effects in the
  existing boundary; shape score approximately `90`, Candidate Priority approximately `72` at
  confidence `0.90`.

Selected design: the common-caller `Phase3HarnessWorkspaceCaptureService`. It is a single base design,
not a hybrid, so no hybrid bonus gate applies. Child
`docs/ExecPlans/phase3_harness_workspace_capture_service_execplan.md` records the exact interface,
contract-preservation map, retirement grep, and acceptance gates. The coordinated phase3 nomenclature
plan remains separate; no public names, DTOs, JSON keys, or artifact paths are renamed here.

### Post-cap continuation slice 5 — accepted 2026-08-06

Child `docs/ExecPlans/phase3_harness_workspace_capture_service_execplan.md` is implemented and
closed. New Qt-free `Phase3HarnessWorkspaceCaptureInput` and
`Phase3HarnessWorkspaceCaptureService` own the pure construction and stable `as_mapping()` projection
of `Phase3HarnessWorkspaceSnapshot`. Both live and headless workspace adapters now delegate that
field-transfer policy; they retain request/workflow reads, scenario mutation, render adapters, Qt
event pumping, sign-time diagnostics, and all existing `Phase3HarnessWorkspacePort` callers. The
snapshot class remains import-compatible from the workspace module, and no public phase3 name or
serialized evidence contract changed.

Focused workspace/harness/session/scenario/capture coverage passed `105` tests with one skipped test;
the full suite passed `1,047` tests with `11` skipped and one pre-existing warning. Ruff, diff checks,
application and capture-service import isolation, and CLI help checks passed. Offscreen acceptance
passed signed acceptance (`10` scenarios, `7` successful signings, `3` matched intentional
rejections), signed preview parity (`18/18` successful), and signed fit rejection (`3/3` matched),
with no cryptographic, annotation, preview-comparison, or expectation failures. The explicit
`/tmp/foliaseal-workspace-capture-acceptance` root was removed and the process audit was clean.

Continuation-slice proxy measurement: navigation friction `0.25`, change amplification `0.50`,
seam-risk reduction `0.50`, boundary-test improvement `0.50`, interface compression `0.50`,
cohesion `0.50`, and behavioral-uncertainty reduction `0.25`; `Actual Improvement = 0.43`, predicted
`0.25`, with no component regression below `-0.10`. This accepts the slice without changing the fixed
five-cycle cap. The next fresh scan must reassess the residual workspace scenario policy, the
composition-root preview helpers, the signing backend, compatibility-surface debris, and the atomic
phase3 nomenclature plan; external names remain frozen until that migration is explicitly executed.

### Post-cap continuation scan 6 — completed after `c6b0d1efa`

Three independent explorers reviewed the clean workspace-capture checkout. The strongest consensus
candidate is the remaining mixed scenario/effect policy in
`src/foliaseal/presentation/qt/phase3_harness_workspace.py` (520 lines): both live and headless
adapters still coordinate profile/appearance override parsing, workflow or panel mutation, preview
state reads, rendering, Qt event pumping, backend reservation/sign-time diagnostics, and capture
delegation behind one workspace port. The new capture service removed only snapshot assembly; the
remaining policy/effect bundle is the next deeper boundary.

The consensus scenario/effect candidate scored `(4.5,4.5,4.5,4.5,4.0,4.5,3.0,2.5)`, confidence
`0.88`, and Candidate Priority approximately `69.0`. The narrower event-pump seam scored about
`67.54`, the preview-capture composition extraction about `67.6`, the signing backend below `57`,
compatibility-surface retirement about `53`, and atomic phase3 nomenclature about `28` because the
current inventory is roughly `4,480` active references and external CLI/DTO/JSON/fixture/artifact
contracts are explicitly frozen. The next design round should target scenario/effect policy or prove
that event pumping is the safer tracer bullet; the nomenclature plan remains deferred and must not be
renamed piecemeal.

### Post-cap continuation design selection 6 — completed after `a1dec0e27`

Three independent designs were reviewed for the remaining scenario/effect policy:

- Minimal policy boundary: `Phase3HarnessScenarioPolicy.build(...)` returns one immutable
  `Phase3HarnessScenarioPlan`, keeping the command and adapters in the existing workspace module;
  shape score approximately `92`.
- Flexible resolver boundary: `ScenarioResolver.resolve(...)` accepts a profile-reader protocol and
  fallback appearance, returning a `ResolvedScenario` with an optional refresh flag; shape score
  approximately `88` because the extra extension surface risks a generic resolver/manager.
- Common-caller optimized resolver: `Phase3HarnessScenarioResolver.resolve(...)` returns one
  immutable `Phase3HarnessResolvedScenario`; adapters apply the resolved effects in their existing
  target-specific order while the resolver owns all profile/appearance override policy; shape score
  approximately `92`, Candidate Priority approximately `73.2` at confidence `0.92`.

Selected design: the common-caller optimized pure scenario resolver. It is a single base design, not a
hybrid, so no hybrid bonus gate applies. The resolver has one behavior-bearing entry point, imports no
Qt/Pillow/pyHanko/workflow code, and leaves event pumping, rendering, capture, and adapter effects in
the existing workspace module. The child plan preserves `Phase3HarnessScenarioCommand`, current-page
placement semantics, exact validation errors, CLI/JSON/artifact contracts, and the separate atomic
phase3 nomenclature migration boundary.

### Post-cap continuation slice 6 — accepted 2026-08-06

Child `docs/ExecPlans/phase3_harness_scenario_policy_execplan.md` is implemented and closed. The new
Qt-free `Phase3HarnessScenarioResolver` owns named-profile lookup and fixture/direct/text/box/
visible-field override composition, returning one immutable `Phase3HarnessResolvedScenario`. The
headless and live workspace adapters now resolve policy once and retain only target-specific
workflow/testing mutations, refresh, Qt event pumping, rendering, and capture. The old duplicated
policy helpers were removed from `phase3_harness_workspace.py`; their former tests were migrated to
resolver-boundary coverage before deletion. Existing scenario command, current-page placement,
CLI/DTO/JSON/artifact, and phase3 external naming contracts remain unchanged.

Focused policy/workspace/harness/scenario coverage passed `98` tests with one skipped test; the full
suite passed `1,049` tests with `11` skipped and one pre-existing warning. Ruff, diff checks,
application/resolver import isolation, and CLI help checks passed. Offscreen acceptance passed signed
acceptance (`10` scenarios, `7` successful signings, `3` matched intentional rejections), signed
preview parity (`18/18` successful), and signed fit rejection (`3/3` matched), with no cryptographic,
annotation, preview-comparison, or expectation failures. The explicit `/tmp/foliaseal-scenario-policy-
acceptance` root was removed and the process audit was clean.

Continuation-slice proxy measurement: navigation friction `0.25`, change amplification `0.50`,
seam-risk reduction `0.50`, boundary-test improvement `0.50`, interface compression `0.50`,
cohesion `0.50`, and behavioral-uncertainty reduction `0.25`; `Actual Improvement = 0.43`, predicted
`0.25`, with no component regression below `-0.10`. This accepts the slice without changing the fixed
five-cycle cap. The next scan must reassess the remaining event-pump and preview-capture seams; the
atomic phase3 nomenclature plan remains deferred because external CLI/DTO/JSON/fixture/artifact
contracts are still frozen.

### Post-cap continuation scan 7 — completed after `5c89e171d`

Three independent explorers reviewed the clean scenario-policy checkout. Two bounded candidates clear
the continuation threshold: the remaining live/headless event-pump dependency in
`phase3_harness_workspace.py`, and the larger preview-capture composition cluster in
`phase3_harness.py`. The event-pump candidate is the smaller, lower-uncertainty tracer bullet: the
workspace still dynamically discovers `QApplication` and repeats `processEvents()` after live scenario
mutation and before live preview capture, while the headless path has no explicit stand-in. The
preview-capture candidate remains important but mixes Qt geometry, Pillow artifacts, and evidence
policy across a 2,255-line composition root.

Event-pump explorer scores were `(3.5,3.5,4,4.5,4,4,1.5,1.5)`, confidence `0.90`, and Candidate
Priority approximately `67.54`. Preview-capture scores were `(4.5,4.5,4.5,4.5,4,4,3,2.5)`,
confidence `0.88`, and Priority approximately `67.6`. The scores are within two points; deterministic
tie-breakers select event pumping because it has lower Behavioral Uncertainty and Migration Risk and
is independently deliverable in one narrow slice. Signing backend (~63), compatibility surface (~61),
and phase3 nomenclature (~45) remain lower or contract-blocked. Public phase3 CLI/DTO/JSON/fixture/
artifact contracts remain frozen; no nomenclature rename is authorized in this slice.

### Post-cap continuation design selection 7 — completed after `5c89e171d`

Three independent designs were reviewed for the event-pump seam:

- Minimal one-method port with Qt and no-op adapters scored approximately `90.5`; it removes direct
  `QApplication` discovery while preserving the existing call sites.
- Flexible `EventPump` protocol/factory scored approximately `84`; it supports alternate application
  getters but adds extension surface not required by current callers.
- Common-caller optimized `HarnessEventPumpPort.process_events()` injected into the live workspace
  dependency bundle, with a Qt adapter bound to the current application and a headless no-op, scored
  approximately `93` at Candidate Priority ~70 and confidence ~0.93.

Selected design: the common-caller event-pump port. It is a single base design, not a hybrid, so no
hybrid bonus gate applies. The port has one method, owns no refresh/render/lifecycle policy, and keeps
the exact sequences `apply scenario → refresh viewer → pump` and `refresh preview → pump → capture`.
The workspace port, DTOs, CLI, JSON, artifacts, and phase3 nomenclature contracts remain unchanged.

### Post-cap continuation slice 7 — accepted 2026-08-06

Child `docs/ExecPlans/phase3_harness_event_pump_execplan.md` is implemented and closed. The new
`HarnessEventPumpPort` isolates event processing behind `QtHarnessEventPump` and
`NoOpHarnessEventPump`; `phase3_harness_workspace.py` no longer imports or discovers Qt directly.
Both live and headless adapters use the one-method boundary, preserving the exact existing sequences:
scenario effects → viewer refresh → pump, and preview refresh → pump → render/capture. Workspace port,
DTO, CLI, JSON, artifact, and phase3 naming contracts remain unchanged.

Focused event-pump/workspace coverage passed `22` tests; the full suite passed `1,054` tests with `11`
skipped and one pre-existing warning. Ruff, diff checks, application/event-pump import isolation,
and CLI help checks passed. Offscreen acceptance passed signed acceptance (`10` scenarios, `7`
successful signings, `3` matched intentional rejections), signed preview parity (`18/18` successful),
and signed fit rejection (`3/3` matched), with no cryptographic, annotation, preview-comparison, or
expectation failures. The explicit `/tmp/foliaseal-event-pump-acceptance` root was removed and the
process audit was clean.

Continuation-slice proxy measurement: navigation friction `0.20`, change amplification `0.35`,
seam-risk reduction `0.40`, boundary-test improvement `0.45`, interface compression `0.30`,
cohesion `0.40`, and behavioral-uncertainty reduction `0.20`; `Actual Improvement = 0.31`, predicted
`0.23`, with no component regression below `-0.10`. This accepts the slice without changing the fixed
five-cycle cap. The next scan must reassess the preview-capture composition cluster and signing-backend
boundary; phase3 nomenclature remains deferred until its external contracts can migrate atomically.

### Post-cap continuation scan 8 — completed after `075007eaa`

Three independent explorers reviewed the clean event-pump checkout. The strongest remaining bounded
cluster is preview-capture/render projection in `src/foliaseal/presentation/qt/phase3_harness.py`
(2,255 lines): the composition root still owns Qt/Pillow render payload construction, widget geometry
and PNG/text/stamp overlays, temporary-directory cleanup, and artifact policy used by workspace and
interactive/matrix callers. The workspace lifecycle, capture service, scenario policy, and event-pump
seams are now extracted, leaving this composition cluster as the next deepening opportunity.

Preview-capture explorer scores were `(4.5,4.5,4.5,4.5,4,4,3,2.5)`, confidence `0.88`, and
Candidate Priority approximately `67.6`; the broader composition-root score was `(4.75,4.5,4.5,4.5,
4,3.5,3.5,2.5)`, confidence `0.86`, Priority approximately `64.87`. Tie-breaking favors the
focused preview-capture cluster because it has higher testability and a bounded existing
`PreviewRenderCapturePort` seam. Signing backend (~63), compatibility surface (~61), render cache
(~55), and phase3 nomenclature (~45) remain lower or contract-blocked. Public phase3 CLI/DTO/JSON/
fixture/artifact contracts remain frozen; no nomenclature rename is authorized in this slice.

### Post-cap continuation design selection 8 — completed after `075007eaa`

Three independent designs were reviewed for the preview-capture cluster:

- Minimal payload builder: extract `_build_qt_preview_render_capture_payload` behind one typed builder
  request while retaining the existing render-capture port; shape score approximately `85`.
- Flexible provider bundle: introduce rasterizer/widget-probe/artifact-sink providers and typed
  observations behind separate Qt/headless adapters; shape score approximately `85.5`, but its
  provider surface risks over-abstraction and a large migration.
- Common-caller optimized render-evidence adapters: keep `PreviewRenderCapturePort` unchanged and
  move Qt/headless render execution, artifact mapping, canonical temp cleanup, and capture projection
  into focused adapters with capped, cohesive dependency bundles; shape score approximately `91`,
  Candidate Priority approximately `71.5` at confidence `0.90`.

Selected design: common-caller optimized Qt/headless render-evidence adapters. It is a single base
design, not a hybrid, so no hybrid bonus gate applies. Existing workspace/matrix callers continue to
use `PreviewRenderCapturePort`; `phase3_harness.py` becomes composition wiring, while artifact paths,
error fields, cleanup, CLI/JSON contracts, and historical phase3 names remain unchanged.

### Post-cap continuation slice 8 — accepted 2026-08-06

Child `docs/ExecPlans/phase3_preview_capture_adapters_execplan.md` is implemented and closed. The
new `preview_render_evidence_adapters.py` owns Qt/headless canonical-preview rendering, artifact
mapping, analysis projection, debug-overlay coordination, and cleanup behind one explicit dependency
bundle. `phase3_harness.py` retains only composition wrappers that bind current collaborators, and
the existing `PreviewRenderCapturePort`, workspace DTOs, CLI/JSON/artifact contracts, and historical
phase3 names remain unchanged. The old inline capture-projection bodies were removed rather than
left as compatibility aliases.

Focused adapter/workspace/harness coverage passed `92` tests with one skipped; the full suite passed
`1,057` tests with `11` skipped and one pre-existing warning. Ruff, diff checks, import isolation,
and CLI help checks passed. Offscreen acceptance passed signed acceptance (`10` scenarios, `7`
successful signings, `3` matched intentional rejections), signed preview parity (`18/18`), and
signed fit rejection (`3/3`), with the explicit `/tmp/foliaseal-preview-capture-acceptance` root
removed and no FoliaSeal/Python application process left behind.

Continuation-slice proxy measurement: navigation friction `0.35`, change amplification `0.40`,
seam-risk reduction `0.40`, boundary-test improvement `0.40`, interface compression `0.30`,
cohesion `0.45`, and behavioral-uncertainty reduction `0.30`; `Actual Improvement = 0.37`, matching
the predicted `0.37`, with no component regression below `-0.10`. This accepts the slice without
changing the fixed five-cycle cap. The next loop action is a fresh three-explorer scan; phase3
nomenclature retirement remains a separate atomic plan because public CLI/DTO/JSON/fixture/artifact
contracts are still frozen.

### Post-cap continuation scan 9 — completed after `87fa47f6a`

Three independent explorers reviewed the clean post-preview-capture checkout. The strongest SPEC-risk
candidate is the single-line signer-label/title-band reservation gap in
`src/foliaseal/application/phase3_signing_backend.py`: the preview has a dedicated signer-label row,
but dense real-field sets can still budget the label inside the body and report
`visible_signature_layout_unavailable`, risking a WYSIWYG mismatch. Independent SPEC-focused scoring
gave this candidate Priority approximately `78` at confidence `0.96`; the other scans corroborated
the signing-backend policy/adaptor concentration as a high-impact bounded seam (approximately
`63–70` depending on whether the wider extraction is scored).

Other credible candidates were evidence-runner factory dependence on private `phase3_harness.py`
helpers (~68–72), residual harness snapshot-formatting projection (~65), narrow refinement-dialog
compatibility cleanup (~60), and the atomic phase3 nomenclature migration (~69 but contract-blocked).
The scenario-policy, preview-capture, workspace, event-pump, and capture-service seams are already
extracted. Public phase3 CLI/DTO/JSON/fixture/artifact contracts remain frozen, and the nomenclature
plan stays deferred until a versioned atomic migration is authorized.

The next design round must focus on one title-band/visible-ink reservation boundary, preserve
`PreparedSigningPlan`/`BackendReservationEvidence` and intentional fit-rejection semantics, and keep
the change to one complete implementation slice. No new child plan is selected until the independent
design review records the minimal, flexible, and common-caller shapes.

### Post-cap continuation design and slice 9 — accepted 2026-08-06

Three independent design reviews confirmed that the active production paths already pass the full
semantics-composed `stamp_text` into the shared layout engine. The minimal design only factored a
helper (shape ~80); the flexible per-band reservation port scored ~90 but would introduce a second
geometry model without a current artifact proving it necessary; the common-caller design scored ~90
and centralizes the existing backend preparation/fit-gate choreography. The common-caller design was
selected without a hybrid because it had no unresolved weakness requiring the `+5` gate.

Child `docs/ExecPlans/backend_layout_preparation_boundary_execplan.md` is implemented and closed.
`phase3_signing_backend.py` now owns one typed `_BackendLayoutPreparation` result and
`_prepare_backend_layout()` helper used by both `prepare_phase3_signing_plan()` and
`validate_visible_signature_fit()`. This removes the duplicated service/ink/fallback/fit-gate path,
keeps `prepare_phase3_signing_plan()` as the only semantics/title composition source, and preserves
`PreparedSigningPlan`, `BackendReservationEvidence`, stable fit errors, CLI/JSON/artifact contracts,
and phase3 nomenclature.

Focused backend/layout coverage passed `136` tests; the full suite passed `1,058` tests with `11`
skipped and one pre-existing warning. Ruff, diff checks, import isolation, CLI help, and offscreen
acceptance passed (`10/7/3`, `18/18`, and `3/3`). Proxy measurement was navigation friction `0.25`,
change amplification `0.40`, seam-risk reduction `0.40`, boundary-test improvement `0.40`, interface
compression `0.35`, cohesion `0.40`, and behavioral-uncertainty reduction `0.35`; `Actual Improvement
= 0.36` versus predicted `0.34`, with no component regression below `-0.10`. A fresh three-explorer
scan is required after commit; a true title-band DTO remains deferred unless new live artifacts prove
aggregate metrics cannot represent the GUI contract.

### Post-cap continuation scan 10 — completed after `c62b5d1c4`

Three independent explorers reviewed the clean backend-layout checkout. The strongest bounded
architecture candidate is the duplicated preview-evidence finalization in
`src/foliaseal/presentation/qt/preview_render_evidence_adapters.py` (668 lines). The Qt and headless
capture paths independently repeat analysis-result extraction, diagnostic grouping, appearance
snapshot fallback, debug-overlay projection, and the JSON-ready mapping. Both paths receive the same
22-callable dependency bundle, so a rendering or evidence-contract change currently requires two
parallel edits and parity reasoning. Independent priorities were approximately `74`, `75`, and
`68` with confidence at least `0.86`; the consolidated candidate is above the fixed continuation
threshold and is locally substitutable through existing fake dependencies and headless capture
tests.

The broader signing backend adapter concentration scored approximately `78` in one scan but is
larger and mixes vendor materialization, fit policy, and evidence serialization; the signing-time
snapshot/WYSIWYG candidate scored approximately `72–78` but requires an additive public request
contract decision. Private evidence-runner factory access scored approximately `68–72`. The
phase3 nomenclature migration remains a coordinated external-contract plan and is not a safe
rename-only slice: public CLI, DTO, JSON, fixture, and artifact labels remain frozen until an
atomic migration is explicitly executed.

Selected next candidate: `preview-render-evidence-finalization-boundary`. The design round must
compare a minimal shared assembler, a flexible typed observation/assembler port, and a common-caller
optimized shape, then select a one-slice design (including a constrained hybrid only if it beats its
best base by the required five points). The child must preserve every render-capture mapping key,
artifact suffix, diagnostic/error value, cleanup behavior, and existing `phase3` external name.

### Post-cap continuation design selection 10 — completed 2026-08-06

Three independent designs were reviewed for the duplicate preview-evidence policy:

- Minimal finalizer: a frozen normalized geometry/context record plus one finalization function,
  retaining analysis-request construction in each adapter. Shape score approximately `86`.
- Flexible projection/ports: a Qt-free frame, narrow artifact-writer/analysis protocols, and a
  shared assembler. Shape score approximately `77` after provider-surface and migration penalties.
- Common-caller service: a target-observation port and service owning rendering, analysis, artifacts,
  and cleanup. Shape score approximately `89–90`, but it would move canonical rendering and cleanup
  into a new generic service and enlarge the one-slice behavior change.

Selected constrained A+B hybrid: retain the existing environment adapters for acquisition and
cleanup, add one frozen `PreviewEvidenceFrame`, and centralize request construction plus diagnostic,
appearance, overlay, and JSON mapping policy in `preview_render_evidence_projection.py`. The
rescored shape is `91.5`, 5.5 points above the minimal base, with no new hard-gate risk. This keeps
the `PreviewRenderCapturePort`, workspace callers, CLI/JSON/artifact contracts, and phase3 names
unchanged while providing a Qt-free boundary test seam.

### Post-cap continuation slice 10 — accepted 2026-08-06

Child `docs/ExecPlans/preview_render_evidence_finalization_boundary_execplan.md` is implemented.
The two large Qt/headless finalization bodies now share `PreviewEvidenceFrame`,
`build_preview_analysis_request()`, and `assemble_preview_evidence()`. Qt/headless adapters retain
only widget/canonical acquisition, target-specific geometry, and the cleanup of snapshots they
created; no second renderer or lifecycle service was introduced. The stale preview-capture plan and
architecture map now describe the actual ownership, and the atomic phase3 nomenclature plan records
the new durable projection module without attempting a piecemeal rename.

Evidence: focused adapter/harness/workspace tests `94 passed`, `1 skipped`; full suite `1,060 passed`,
`11 skipped`, one pre-existing Pillow warning; Ruff, diff checks, application/projection import
isolation, and CLI help passed. Offscreen signed acceptance evidence passed `10` scenarios with `7`
successful signings and `3` matched intentional rejections, signed preview parity `18/18`, and fit
rejection `3/3`, with zero cryptographic, annotation, preview-comparison, or expectation failures.
The explicit evidence roots were removed and the process audit was clean.

Proxy measurement: navigation `0.50`, change amplification `0.50`, seam reduction `0.50`,
boundary-test improvement `1.00`, interface compression `0.50`, and boundary isolation `1.00`; the
weighted `Actual Improvement = 0.63` versus predicted `0.40` (`1.56x`), with no component regression
below `-0.10`. Commit `3370748b7` is on `main`; the accepted slice is closed and a fresh
three-explorer scan is required before selecting the next candidate.

### Post-cap continuation scan 11 — completed after `4c834e9bc`

Three independent explorers reviewed the clean preview-finalization checkout. The highest bounded
and SPEC-relevant candidate is strict preview-to-signing-time handoff. `SigningDraftWorkflow.preview()`
resolves visible semantics through an injectable signing clock, but `build_signing_request()` does
not retain that timestamp and `prepare_phase3_signing_plan()` later calls `_current_signing_time()`
again. A clock rollover can therefore change timestamp text between the canonical preview and final
output, contrary to the frozen preview/output-fidelity principle in `docs/SPEC.md:107-118` and the
explicit debt note in `docs/ARCHITECTURE.md:1318`.

The timestamp candidate scored approximately `(NF,CA,SR,TG,IC,CC,MR,BU) = (4,4.5,4,4.5,4,4.5,2.5,2)`,
confidence `0.95`, and Candidate Priority `75`. It is local-substitutable through the existing
`SigningClock` and `_FixedSigningClock`; direct headless `SigningRequest` callers can retain current-
time defaults. Alternatives were the signing-shell composition root (~70), private scalar snapshot
projection (~66–68), evidence-runner private factory access (~65–69), and test-only dialog bridge
cleanup (~63–66). Phase3 nomenclature remains an atomic external-contract migration and is not
inflated into this behavior-sensitive slice.

Selected next candidate: `preview_signing_time_snapshot_handoff`. The next design round must compare
minimal additive request propagation, a flexible prepared-signing context port, and a common-caller
workflow session shape, then choose a one-slice design that preserves direct-call defaults, explicit
preview invalidation after draft edits, timezone semantics, and all serialized contracts.

### Post-cap continuation design selection 11 — completed 2026-08-06

Three independent designs were reviewed for the timestamp handoff:

- Minimal additive propagation: add an optional timezone-aware `signing_time` to the in-memory
  `SigningRequest`, carry it through `SigningBackendRequest`, and let the draft workflow cache and
  invalidate it. Shape score approximately `91`.
- Flexible prepared-submission context: keep `SigningRequest` unchanged and introduce
  `SigningTimeSnapshot`/`PreparedSigningSubmission` plus a new use-case execution path. Shape score
  approximately `82` because the second submission surface expands the Qt migration.
- Common-caller workflow session: expose one prepared submission from the dominant signing action
  path while preserving a legacy execute wrapper. Shape score approximately `91`, but it duplicates
  the minimal path's context without improving direct headless callers.

Selected minimal additive design. It reuses the existing `SigningClock` and private `_FixedSigningClock`,
fixes the existing double semantics resolution in `SigningDraftWorkflow.preview()`, invalidates the
cached timestamp on every draft mutation, and carries the optional value through the backend only.
The external CLI/JSON/profile contracts remain unchanged; direct requests with `signing_time=None`
retain current-clock behavior. No hybrid is justified because the two high-scoring designs solve the
same dominant handoff and the flexible context adds no independent weakness fix.

### Post-cap continuation slice 11 — accepted 2026-08-06

Child `docs/ExecPlans/preview_signing_time_snapshot_handoff_execplan.md` is implemented. The draft
workflow now resolves visible semantics once per preview, stores a timezone-aware timestamp with a
typed current-input fingerprint, invalidates that cache on placement/appearance/preset/certificate
mutations, and copies a matching timestamp into the in-memory `SigningRequest`. The backend carries
it through `SigningBackendRequest` and uses the existing fixed-clock adapter; direct requests with
`None` retain current-clock behavior. The UI preview DTO, persisted schemas, CLI/JSON/artifact
contracts, invisible-signature path, and phase3 nomenclature remain unchanged.

Evidence: focused workflow/backend/semantics tests `135 passed`; full suite `1,062 passed`, `11
skipped`, one pre-existing warning; Ruff, diff checks, CLI/import checks, and offscreen evidence
passed signed acceptance `10/7/3`, preview parity `18/18`, and fit rejection `3/3`, with zero
cryptographic, annotation, preview-comparison, or expectation failures. Temporary evidence roots
were removed and the process audit was clean. A first full-suite pass exposed two UI preview-equality
regressions from adding the timestamp to the preview DTO; removing that UI field preserved the
established snapshot contract, and the corrected suite passed.

Proxy measurement: navigation `0.25`, change amplification `0.40`, seam reduction `0.50`,
boundary-test improvement `0.75`, interface compression `0.25`, and boundary isolation `0.50`; the
weighted `Actual Improvement = 0.45` versus predicted `0.35` (`1.29x`), with no component regression
below `-0.10`. Implementation commit `0391d9eb7` (`fix: preserve preview signing time`) is on
`main`; the child is accepted and a fresh three-explorer scan is required before selecting the next
candidate.

### Post-cap continuation scan 12 — completed after `5a9ff5840`

Three independent explorers reviewed the clean timestamp-handoff checkout. The strongest bounded
presentation seam is the top-level signing-shell composition/lifecycle concentration in
`src/foliaseal/presentation/qt/signing_shell.py:180-426`: construction wires roughly twenty
collaborators, `_install_composition()` re-exposes a large graph, and more than thirty methods
forward runtime, shell-surface, compatibility, and action behavior. Existing fake-Qt shell and
app-frame tests make it locally substitutable while preserving the frozen Open→Review→Choose→Place→
Preview→Sign workflow.

Independent shell scoring was approximately `(NF,CA,SR,TG,IC,CC,MR,BU) = (4.5,4.25,4,4.5,4,4.25,2.5,2)`
with confidence `0.85` and Candidate Priority near `70`. The application-to-infra DTO boundary ranked
approximately `64–67`, the scalar harness projection `65–67`, private factory access `67`, and
test-only compatibility bridges below `60`. Phase3 nomenclature remains atomic-contract blocked.

Selected next candidate: `signing_shell_composition_boundary`. The design round must compare a
minimal shell controller port, a flexible composition graph record, and a common-caller lifecycle
session shape, preserving callback ordering, widget teardown, app-frame open behavior, and all shell
surface/test contracts in one slice.

### Post-cap continuation design selection 12 — completed 2026-08-06

Three independent design reviews compared the selected shell seam. The minimal concrete controller
scored approximately `89` with confidence `0.91`: it owns composition construction, collaborator
publication, one-time bootstrap, and close delegation while preserving the widget's public/private
attribute contract. A flexible graph-record/port design scored approximately `79` but widened the
interface surface without another consumer. A common-caller lifecycle-session design scored roughly
`74` (Priority below the gate) because `SigningWorkspaceHost` already owns atomic compose→mount→
publish→dispose ordering. No hybrid exceeded the minimal design by five points, so the minimal
controller was selected. The separate `phase3_nomenclature_retirement_execplan.md` remains the
single atomic plan for removing historical labels, compatibility aliases, and stale nomenclature;
this child performs no piecemeal rename.

### Post-cap continuation slice 12 — accepted 2026-08-06

Child `docs/ExecPlans/signing_shell_composition_boundary_execplan.md` is implemented. New
`SigningWorkspaceShellController` owns construction of the existing composition record, exact
collaborator publication (including `interaction_bridge`), idempotent orchestrator bootstrap, and
close delegation. `SigningWorkspaceWidget` retains its Qt container setup, callbacks, public methods,
and established attribute names; the duplicated `_install_composition()` body is removed. Focused
controller/shell/app-frame tests passed `110`; Ruff passed; full suite passed `1,064` with `11` skipped
and one pre-existing warning. CLI help/import checks and `git diff --check` passed. Offscreen evidence
passed signed acceptance `10` scenarios with `7` successful signings, preview parity `18/18`, and fit
rejection `3/3`; the explicit temporary root was removed and process audit was clean.

Proxy measurement: navigation `0.25`, change amplification `0.50`, seam reduction `0.75`, boundary
test improvement `0.75`, interface compression `0.50`, and boundary isolation `0.75`; weighted
`Actual Improvement = 0.50` versus predicted `0.40`, with no component regression below `-0.10`.
Implementation/docs are ready for an intentional commit, after which the loop must run a fresh
three-explorer scan. The phase3 retirement plan remains outstanding and must be executed atomically,
not treated as complete by this shell slice.

### Post-cap continuation scan 13 — completed after `98adf8827`

Three independent explorers reviewed the clean post-shell checkout. All agree the signing-shell
composition/lifecycle candidate is closed by `SigningWorkspaceShellController`. The strongest
consensus-backed next seam is application-to-infra certificate/configuration model ownership:
`SigningDraftWorkflow`, `SignaturePropertiesCoordinator`, and `SigningMaterialResolver` still import
infra configuration DTOs/adapters, with the debt recorded in `docs/ARCHITECTURE.md:208,1269,1328`.
The bounded first family is `CertificateConfiguration` plus certificate-catalog resolution while
preserving `infra/config/schemas.py` JSON and storage APIs. One explorer scored it Priority `64–67`
with confidence `0.93`; a second independent architecture record is required before selection under
the evidence gate.

The historical `phase3` cluster remains explicitly planned but risk-disputed. One explorer scored an
internal-only atomic rename (preserving CLI/DTO/JSON/fixture/artifact contracts) near `72`, while two
independent reviews scored the full migration approximately `40–60` after external-contract and
compatibility risk. The current average does not establish a qualifying consensus candidate. The
retirement plan remains unchecked for implementation and must not be executed piecemeal or by adding
aliases. A remaining `phase3_harness.py` scalar projection extraction also lacks a second consumer.

No next candidate is selected from this scan; run the next exact three-explorer scan to confirm the
certificate/configuration boundary or produce a second below-threshold result. The architecture loop
remains active and the phase3 nomenclature plan remains an outstanding atomic work item.

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
