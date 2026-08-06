---
name: architecture-improvement-loop
description: Autonomously and repeatedly improve a codebase's architecture by finding and ranking module-deepening opportunities, selecting the strongest refactoring shape, implementing it through $dev-loop, measuring the result, and continuing until the remaining opportunities fall below a fixed threshold.
---

# Architecture Improvement Loop

Repeatedly deepen shallow, tightly coupled modules until the best credible remaining opportunity is below the stopping threshold. Make the architectural choices autonomously, implement each selected refactor with `$dev-loop`, and use ExecPlans as the only persistent state.

A **deep module** (John Ousterhout, "A Philosophy of Software Design") has a small interface hiding a large implementation. Deep modules are more testable, more AI-navigable, and let you test at the boundary instead of inside.

## Non-negotiable rules

- Do not invoke `$improve-codebase-architecture`; reproduce the required analysis and design work within this skill.
- Do not ask the user to choose a candidate, interface, or hybrid. Use the fixed scoring and tie-breaking rules in [REFERENCE.md](REFERENCE.md).
- Do not create a separate state file, ledger, database, YAML record, or other persistent loop artifact. The parent and child ExecPlans are the persistent state.
- Do not alter the scoring formulas, weights, thresholds, hard gates, or cycle limits during a run.
- Do not accept a refactor merely because tests pass. It must also produce the required measured architectural improvement.
- Do not weaken behavioral evidence, delete tests before equivalent boundary coverage exists, or redefine acceptance to make a refactor pass.
- Do not silently change a selected architecture during implementation. Implementation details may evolve, but a material change to module ownership, public interface, dependency strategy, or approved scope must return to the architecture-selection phase and be recorded in the ExecPlans.

Read [REFERENCE.md](REFERENCE.md) before the first scan. Use `scripts/architecture_metrics.py` for arithmetic when practical; record the relevant inputs and outputs in the ExecPlans rather than preserving separate score files.

## 1. Initialize or resume the parent ExecPlan

Search the repository's normal ExecPlan location for an incomplete parent ExecPlan governing an autonomous architecture-improvement loop.

- If one exists, read it completely and resume from its recorded state.
- If none exists, use `$write-execplan` to create a parent ExecPlan for the overall loop.
- If several plausible incomplete parent plans exist, select the newest plan whose purpose clearly matches this repository and record that decision.

The parent ExecPlan must comply with the repository's `PLANS.md` and contain the additional loop information required by [REFERENCE.md](REFERENCE.md). Keep it current after every scan, selection, implementation result, evaluation, and stopping decision.

## 2. Scan the current codebase independently

For each scan round, spawn three independent `explorer-light` subagents. Give each the same repository-level objective but do not expose the other explorers' findings or scores.

Each explorer must navigate organically and identify friction such as:

- understanding one behavior requires bouncing among many small files;
- an interface is nearly as complex as its implementation;
- callers coordinate a sequence that one module should own;
- pure helpers were extracted for unit testing while integration bugs remain in their orchestration;
- tightly coupled modules create risky seams;
- implementation details or infrastructure types leak into callers;
- meaningful behavior is untested or difficult to test at a stable boundary.

Each candidate must include concrete evidence: repository-relative paths, symbols, callers, call paths, imports, tests, and representative workflows. Each explorer independently scores the candidate dimensions defined in [REFERENCE.md](REFERENCE.md).

Consolidate overlapping reports into bounded candidate clusters. A candidate is credible only when it meets the evidence and support rules in the reference.

## 3. Rank and select the candidate

For every credible candidate:

1. Classify its dependencies using the reference categories.
2. Aggregate explorer scores by median.
3. Calculate agreement, evidence coverage, confidence, and Candidate Priority.
4. Record the evidence, component scores, confidence, and total in the parent ExecPlan.

Select the highest-scoring credible candidate at or above the continuation threshold. Apply the deterministic tie-breakers from the reference when scores are close.

If no candidate qualifies, perform the required fresh confirmation scan. Finish successfully only when the confirmation rule is satisfied.

## 4. Frame the selected problem

Before designing interfaces, write a concise problem-space record into the parent ExecPlan and the forthcoming child ExecPlan. Include:

- the modules and concepts involved;
- the architectural friction and representative workflows;
- the constraints any interface must satisfy;
- the dependency category and available stand-ins or adapters;
- the behavior that must be preserved;
- the expected source of architectural improvement;
- a rough illustrative code sketch that grounds the constraints without predetermining the design.

## 5. Generate radically different refactoring shapes

Spawn at least three design subagents in parallel. Give each the same technical brief but a different constraint:

1. **Minimal interface:** aim for one to three public entry points.
2. **Flexible interface:** support legitimate variation and extension without leaking implementation details.
3. **Common-caller optimized:** make the dominant use case trivial and safe.
4. **Ports and adapters:** add when the dependency category makes it applicable.

Each design must provide:

- exact interface signatures;
- a caller usage example;
- module responsibilities and invariants;
- what complexity becomes hidden;
- dependency strategy;
- testing strategy at the new boundary;
- migration approach;
- trade-offs and failure modes.

Have two independent reviewers score each design, and add the orchestrator's own score. Aggregate each dimension by median and calculate the Refactor Shape Score using the reference.

Select the highest valid design. A hybrid is permitted only under the reference's constrained hybrid procedure and must beat the base design by the required margin after rescoring.

Record all designs, scores, penalties, rejected alternatives, and the final rationale in the parent ExecPlan.

## 6. Create the child ExecPlan

Use `$write-execplan` to create a child ExecPlan for the selected refactor. It must comply fully with `PLANS.md` and include all additional architecture-selection, baseline, behavior-preservation, acceptance, prediction, and evaluation material required by [REFERENCE.md](REFERENCE.md).

The child ExecPlan must be self-contained. It must identify the chosen interface or hybrid precisely enough that implementation cannot quietly substitute another architecture.

Capture the pre-refactor baseline and predicted improvement before implementation begins. Record the measurements and evidence in the child and summarize them in the parent.

## 7. Implement through `$dev-loop`

Invoke `$dev-loop` to implement the selected solution or hybrid. Identify the child ExecPlan and the selected architecture explicitly in the task given to `$dev-loop`.

Allow `$dev-loop` to manage implementation, testing, child implementation plans when needed, compliance review, documentation, and commits. Continue to maintain the architecture parent and child ExecPlans as the work reveals discoveries and decisions.

When replacing shallow tests:

1. identify the observable behavior each old test protects;
2. add an equivalent or stronger boundary test;
3. demonstrate that the boundary test passes;
4. record the replacement mapping in the child ExecPlan;
5. only then delete the shallow test.

## 8. Evaluate the completed refactor

After `$dev-loop` reports completion, run an independent evaluation against the child ExecPlan.

1. Verify every hard gate in [REFERENCE.md](REFERENCE.md).
2. Repeat the same measurements used for the baseline.
3. Calculate Actual Improvement and prediction accuracy.
4. Check that no component regressed beyond the allowed limit.
5. Determine whether complexity was hidden behind the selected boundary rather than merely relocated or collected into a large shallow module.
6. Record commands, outputs, measurements, findings, and calculations in the child ExecPlan.
7. Summarize the accepted or rejected result in the parent ExecPlan.

If the failure is an incomplete implementation, provide the findings to `$dev-loop` and continue the same child ExecPlan.

If the selected architecture is infeasible or materially wrong, record the evidence, return to interface selection, rescore the remaining valid designs, and permit at most one architecture redesign attempt for that candidate. If no valid shape remains, mark the candidate currently infeasible and rescan the repository. Do not count an unsuccessful attempt as an accepted cycle.

Accept the cycle only when all hard gates pass and the minimum actual-improvement requirement is met.

## 9. Rescan and continue

After an accepted cycle:

- update the parent ExecPlan's Progress, Decision Log, Surprises & Discoveries, and Outcomes & Retrospective;
- record the child ExecPlan and resulting commit;
- record predicted improvement, actual improvement, and prediction accuracy;
- scan the changed repository again from fresh contexts;
- rank the current residual opportunities rather than reusing stale rankings.

Continue until a stopping condition in the reference is met.

## 10. Finish

On successful completion, update the parent ExecPlan with:

- all accepted cycles and child ExecPlans;
- cumulative outcomes;
- the two confirming residual scans;
- the best remaining candidate and its score;
- the exact stopping condition satisfied;
- remaining architectural concerns that fell below the intervention threshold.

On blocked completion, record the exact blocker, supporting evidence, attempted resolutions, current repository state, and the decision required from a human.

Report the final outcome to the user with a concise summary of accepted refactors, measured improvement, remaining residual opportunity, and the governing parent ExecPlan path.
