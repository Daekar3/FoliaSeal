# Architecture Improvement Loop Reference

This reference defines the fixed analysis, scoring, acceptance, and stopping rules for `$architecture-improvement-loop`. Do not change these rules during a run.

## Default configuration

- Independent explorers per scan: **3**
- Candidate continuation threshold: **60 / 100**
- Candidate credibility confidence: **0.60**
- Confirmation scans required below threshold: **2 consecutive independent scans**
- Minimum Actual Improvement for an accepted cycle: **0.15**
- Maximum allowed regression in any improvement component: **0.10**
- Hybrid must exceed its base design by: **5 points**
- Maximum accepted refactor cycles: **5**
- Prediction-underperformance stop: **2 consecutive accepted cycles below 50% of predicted improvement**
- Architecture redesign attempts per candidate: **1**

The cycle cap is a safety boundary. Reaching it is not evidence that the repository has no further worthwhile opportunities.

## Dependency categories

Classify every candidate before designing its interface.

## Dependency Categories

When assessing a candidate for deepening, classify its dependencies:

### 1. In-process

Pure computation, in-memory state, no I/O. Always deepenable — just merge the modules and test directly.

### 2. Local-substitutable

Dependencies that have local test stand-ins (e.g., PGLite for Postgres, in-memory filesystem). Deepenable if the test substitute exists. The deepened module is tested with the local stand-in running in the test suite.

### 3. Remote but owned (Ports & Adapters)

Your own services across a network boundary (microservices, internal APIs). Define a port (interface) at the module boundary. The deep module owns the logic; the transport is injected. Tests use an in-memory adapter. Production uses the real HTTP/gRPC/queue adapter.

Recommendation shape: "Define a shared interface (port), implement an HTTP adapter for production and an in-memory adapter for testing, so the logic can be tested as one deep module even though it's deployed across a network boundary."

### 4. True external (Mock)

Third-party services (Stripe, Twilio, etc.) you don't control. Mock at the boundary. The deepened module takes the external dependency as an injected port, and tests provide a mock implementation.

## Testing Strategy

The core principle: **replace, don't layer.**

- Old unit tests on shallow modules are waste once boundary tests exist — delete them
- Write new tests at the deepened module's interface boundary
- Tests assert on observable outcomes through the public interface, not internal state
- Tests should survive internal refactors — they describe behavior, not implementation

## Scan evidence requirements

A candidate report must identify:

- a bounded cluster of modules or concepts;
- at least one representative workflow;
- exact repository-relative files and symbols involved;
- production callers or call paths;
- the seams or sequencing currently owned by callers;
- existing tests and their level of coupling;
- the dependency category;
- the expected boundary through which behavior could be tested.

A candidate is credible when:

- at least two independent explorers identify substantially the same cluster; or one explorer identifies it and the orchestrator independently verifies the complete evidence;
- at least two score records are available;
- confidence is at least 0.60;
- the cluster is bounded enough for one child ExecPlan or a clearly defined parent/child refactor plan;
- the expected improvement is architectural, not merely naming, formatting, file movement, or local cleanup.

## Candidate scoring

Score each dimension from **0 to 5**. Use integers or half-points. Every score must cite concrete repository evidence in the parent ExecPlan.

### Benefit dimensions

- **Navigation friction (NF):** How many files, indirections, and concepts must be followed to understand representative behavior.
- **Change amplification (CA):** How broadly a concept-level change spreads across modules, callers, and tests.
- **Seam risk (SR):** How many coordination boundaries must behave correctly and how likely defects are to occur between them.
- **Testability gain (TG):** How much a stable deep boundary would improve meaningful behavioral testing.
- **Interface compression (IC):** How much public surface and caller knowledge could be replaced by a smaller contract.
- **Conceptual cohesion (CC):** How strongly the modules co-own one concept, invariant, lifecycle, or workflow.

### Penalty dimensions

- **Migration risk (MR):** Breakage potential, breadth of migration, deployment complications, and rollback difficulty.
- **Behavioral uncertainty (BU):** How poorly current behavior is understood or protected by observable tests.

### Aggregation and confidence

For each candidate, aggregate each dimension with the median of the independent scores.

For each dimension, calculate:

    dimension_range = (maximum explorer score - minimum explorer score) / 5

Then calculate:

    agreement = 1 - mean(dimension_range across all eight dimensions)

Evidence coverage is the fraction from 0 to 1 of the eight dimensions supported by at least two independent concrete evidence observations.

    confidence = clamp(0.70 * agreement + 0.30 * evidence_coverage, 0, 1)

### Candidate Priority formula

    Benefit =
        0.20 * NF
      + 0.15 * CA
      + 0.15 * SR
      + 0.20 * TG
      + 0.15 * IC
      + 0.15 * CC

    Penalty =
        0.60 * MR
      + 0.40 * BU

    CandidatePriority = clamp(
        100 * (
            0.75 * Benefit
          + 0.25 * Benefit * confidence
          - 0.30 * Penalty
        ) / 5,
        0,
        100
    )

Use `scripts/architecture_metrics.py candidate` to perform the arithmetic when practical.

### Candidate tie-breakers

When candidates are within **2 points**, select in this order:

1. higher Testability Gain;
2. lower Behavioral Uncertainty;
3. lower Migration Risk;
4. smaller independently deliverable change slice;
5. fewer true-external dependencies;
6. lexicographically smaller stable candidate identifier.

## Refactoring-shape generation

Generate at least three radically different interfaces:

1. minimal public surface;
2. flexible but encapsulated extension model;
3. dominant-caller optimized interface;
4. ports-and-adapters design when dependency boundaries warrant it.

Each design record must contain:

- signatures and types;
- caller usage example;
- responsibilities and invariants owned by the module;
- implementation details hidden;
- dependency strategy;
- boundary-testing strategy;
- migration sequence;
- compatibility and retirement plan;
- trade-offs and likely failure modes.

## Refactor Shape Score

Have two independent reviewers and the orchestrator score each dimension from **0 to 5**. Aggregate by median.

- **Interface depth (25%):** Small contract hiding substantial decisions, sequencing, and invariants.
- **Caller simplicity (15%):** Callers express intent without coordinating internals.
- **Behavioral testability (20%):** Important behavior can be verified through a stable public boundary.
- **Dependency isolation (15%):** Infrastructure and transport details remain behind ports or internal adapters.
- **Ownership clarity (10%):** The module has one coherent responsibility and clear invariant ownership.
- **Migration feasibility (10%):** The design can be introduced, verified, and retired safely.
- **Requirement compatibility (5%):** The design preserves known behavior and repository constraints.

    BaseShapeScore = 20 * (
        0.25 * InterfaceDepth
      + 0.15 * CallerSimplicity
      + 0.20 * BehavioralTestability
      + 0.15 * DependencyIsolation
      + 0.10 * OwnershipClarity
      + 0.10 * MigrationFeasibility
      + 0.05 * RequirementCompatibility
    )

Apply evidence-backed penalties:

- service locator or hidden global dependency registry: **-20**
- generic manager that combines unrelated responsibilities: **-15**
- callers still coordinate the critical internal workflow: **-15**
- infrastructure, transport, or persistence types leak through the public interface: **-15**
- compatibility layer has no explicit retirement criterion: **-10**
- supposed deepening merely collects code into a large shallow file: **-15**
- speculative public entry points not required by known callers: **-5 each, maximum -15**

    RefactorShapeScore = clamp(BaseShapeScore - penalties, 0, 100)

A design that violates a hard behavioral, dependency, or repository requirement is invalid regardless of score.

Use `scripts/architecture_metrics.py shape` to perform the arithmetic when practical.

### Hybrid rule

A hybrid may be considered only after scoring the original designs.

1. Choose the highest-scoring valid design as the base.
2. Identify one or more specific scored weaknesses in the base.
3. Borrow only the elements from another design that directly address those weaknesses.
4. Produce complete signatures, ownership, dependency, testing, and migration details for the hybrid.
5. Rescore it as a new design.
6. Select it only when it exceeds the base by at least **5 points** and introduces no new hard-gate risk.

Do not use “hybrid” as permission to combine every desirable feature or to avoid choosing a coherent ownership model.

## Parent ExecPlan requirements

The parent ExecPlan is the sole persistent state for the overall loop. In addition to all `PLANS.md` requirements, it must maintain these sections or equivalent clearly labeled material.

### Loop Configuration

Record the fixed thresholds, formulas version, cycle limit, and confirmation requirement. State that they cannot be changed during the run.

### Scan and Candidate Ledger

For every scan round, record:

- date and current commit;
- explorer identities or labels;
- all consolidated credible candidates;
- evidence summary and dependency category;
- median component scores;
- agreement, evidence coverage, confidence, and Candidate Priority;
- rejected candidates and reasons;
- selected candidate and tie-breaker rationale;
- below-threshold confirmation scans.

### Design Selection Ledger

For each selected candidate, record:

- problem framing and illustrative constraint sketch;
- all generated designs;
- reviewer component scores and penalties;
- shape totals;
- rejected alternatives and reasons;
- hybrid construction and rescore, if any;
- final selected design and exact rationale.

### Cycle Ledger

For every attempted cycle, record:

- child ExecPlan path;
- baseline commit and implementation commit;
- predicted component improvements and predicted total;
- hard-gate result;
- actual component improvements and Actual Improvement;
- prediction accuracy;
- accepted, corrected, redesigned, abandoned, or blocked status;
- residual opportunity after an accepted cycle.

## Child ExecPlan requirements

Each child ExecPlan must include the following in addition to all `PLANS.md` requirements.

### Architecture Selection Record

- selected candidate and Candidate Priority;
- selected interface or hybrid and Refactor Shape Score;
- exact signatures and usage examples;
- module responsibilities, invariants, hidden details, and forbidden leaks;
- dependency category and concrete production/test dependency strategy;
- rejected alternatives relevant to implementation decisions;
- architecture decisions that implementation may not silently change.

### Scope and Migration Inventory

- production callers to migrate;
- modules or concepts to consolidate;
- old public entry points to retire;
- adapters to introduce or retain;
- generated artifacts allowed to change;
- explicit out-of-scope areas;
- compatibility layers and exact retirement criteria.

### Behavior Preservation Map

Assign stable identifiers to required observable behaviors. For each behavior record:

- current entry path;
- existing test or characterization evidence;
- replacement boundary test to create;
- end-to-end or manual evidence where applicable;
- status during implementation.

No existing shallow test may be deleted or weakened until its behavior is covered by an equivalent or stronger passing boundary test. Record each old-test-to-boundary-test replacement.

### Baseline Measurements and Predicted Improvement

Measure and record the six improvement components below before implementation. Explain exactly how each proxy was counted so it can be repeated after implementation. Estimate the predicted component improvement using the same scale and formula used for actual results.

### Refactor Acceptance Contract

Record:

- exact validation commands and expected outputs;
- all hard gates;
- minimum Actual Improvement;
- maximum component regression;
- approved public surface;
- forbidden imports, bypasses, or dependency directions;
- required callers, modules, tests, and cleanup outcomes;
- immutable behavioral requirements.

### Post-implementation Evaluation

Record repeated measurements, helper-script output, hard-gate evidence, review findings, Actual Improvement, prediction accuracy, and the accept/reject decision.

## Hard acceptance gates

Every applicable gate must pass:

- the full preexisting behavioral suite passes;
- new boundary tests pass;
- build, static analysis, lint, and repository-required validation pass;
- no new skipped, disabled, quarantined, expected-failure, or materially weakened tests appear;
- every behavior in the preservation map remains covered;
- the approved public interface exists and no unauthorized public entry points were introduced;
- all inventoried production callers are migrated;
- no production caller bypasses the new boundary through deprecated internals;
- dependency direction and the selected dependency category are respected;
- tests do not require live true-external services;
- no new dependency cycle is introduced;
- required legacy modules, entry points, and temporary compatibility paths are retired;
- documentation reflects the implemented architecture;
- independent review reports zero unresolved critical or major findings.

A passing test suite cannot override a failed architecture gate.

## Actual Improvement measurements

Use the same counting method before and after implementation. Record representative workflows and raw evidence in the child ExecPlan.

### 1. Navigation reduction — weight 20%

Proxy: files or distinct implementation units that must be followed to understand representative workflows.

    NavigationReduction = (before - after) / max(before, 1)

### 2. Change-amplification reduction — weight 15%

Proxy: average production modules and caller sites that would need coordinated edits for a fixed set of representative concept-level changes.

    ChangeAmplificationReduction = (before - after) / max(before, 1)

### 3. Seam reduction — weight 15%

Proxy: internal cross-module coordination points, sequencing calls, or shared-state seams inside the candidate cluster.

    SeamReduction = (before - after) / max(before, 1)

### 4. Boundary-test improvement — weight 20%

Proxy: fraction from 0 to 1 of the behavior-preservation inventory exercised through the selected public boundary.

    BoundaryTestImprovement = after_fraction - before_fraction

### 5. Interface compression — weight 15%

Proxy: public entry points or public concepts callers must understand for the candidate's representative workflows.

    InterfaceCompression = (before - after) / max(before, 1)

### 6. Boundary-isolation improvement — weight 15%

Proxy: production bypasses, forbidden imports, or callers that directly use candidate internals.

    BoundaryIsolationImprovement = (before - after) / max(before, 1)

Clamp each component to the range **-1 to 1**.

    ActualImprovement =
        0.20 * NavigationReduction
      + 0.15 * ChangeAmplificationReduction
      + 0.15 * SeamReduction
      + 0.20 * BoundaryTestImprovement
      + 0.15 * InterfaceCompression
      + 0.15 * BoundaryIsolationImprovement

An accepted cycle requires:

- every hard gate passes;
- `ActualImprovement >= 0.15`;
- no component is less than `-0.10`.

If a proxy cannot be measured credibly, assign that component **0**, document why, and do not substitute an invented value.

Use `scripts/architecture_metrics.py improvement` to calculate the components and total when practical.

## Predicted improvement and calibration

Before implementation, estimate the expected value of the same six components and calculate Predicted Improvement with the same weights.

    PredictionAccuracy = ActualImprovement / PredictedImprovement

When Predicted Improvement is zero or negative, the candidate must not be selected.

Stop for human review when two consecutive accepted cycles achieve less than **50%** of their predicted improvement. Record this as a calibration failure rather than silently lowering the threshold or changing the rubric.

## Critical and major review findings

A **critical** finding means the implementation violates the selected ownership boundary, public interface, dependency direction, required behavior, or safety of the migration.

A **major** finding means the selected architecture is substantially present but caller migration, encapsulation, testing, cleanup, compatibility retirement, or documentation is materially incomplete.

A **minor** finding concerns naming, local clarity, or incidental implementation detail without compromising the selected architecture or acceptance contract.

Accepted cycles require zero unresolved critical and major findings.

## Continue and stop decisions

### Continue

Begin another cycle when the highest credible Candidate Priority is **60 or greater** and no safety stop has triggered.

### Successful completion

When a scan finds no credible candidate at or above 60, run a second scan using fresh explorer contexts that are not shown the prior scan's rankings. Complete successfully only when both consecutive scans remain below 60 and no hard architectural violation is known.

### Safety stops

Stop and report precisely when:

- five refactor cycles have been accepted;
- two consecutive accepted cycles achieve less than half their predicted improvement;
- behavior preservation cannot be demonstrated;
- required validation cannot run reliably;
- no feasible refactoring shape can satisfy the hard requirements;
- an architecture redesign attempt has already failed for the current candidate;
- proceeding requires a product, compatibility, security, or ownership decision not established by repository evidence.

### Failed or infeasible candidates

A failed implementation does not automatically invalidate the candidate.

- If implementation is incomplete, return the findings to `$dev-loop`.
- If the architecture shape is infeasible, permit one return to design selection and choose the next valid rescored shape.
- If no valid shape remains, mark the candidate currently infeasible with evidence and rescan.
- Do not count an unsuccessful attempt as an accepted cycle.
- Do not repeatedly select an infeasible candidate unless new repository evidence materially changes its feasibility.

## Helper script usage

The helper uses only Python's standard library and writes JSON to stdout.

Candidate scoring:

    python path/to/architecture-improvement-loop/scripts/architecture_metrics.py candidate candidate-input.json

Shape scoring:

    python path/to/architecture-improvement-loop/scripts/architecture_metrics.py shape shape-input.json

Improvement scoring:

    python path/to/architecture-improvement-loop/scripts/architecture_metrics.py improvement improvement-input.json

Temporary input files may be used during a run, but they are not persistent loop state. Copy the relevant input values and output into the governing ExecPlan, then delete temporary score files when practical.
