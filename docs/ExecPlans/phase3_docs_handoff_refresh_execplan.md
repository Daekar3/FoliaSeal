# Phase 3 Documentation Refresh and Handoff Prep

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, a new contributor or agent should be able to open the repository, read the canonical docs, and understand three things quickly: what Phase 3 already does reliably, what still blocks true FR-3B acceptance, and which files/commands define the current working path. The immediate user value is smoother handoff and less re-discovery work when Phase 3 continues in a new chat.

The proof is documentary rather than executable: the core docs and one dedicated handoff artifact should all tell the same story about the current Phase 3 state, remaining blockers, and next work.

## Progress

- [x] (2026-04-03 23:28Z) Audited the current canonical docs (`README.md`, `docs/SPEC.md`, `docs/ExecPlans/phase3_parallel_plan.md`) plus the acceptance artifacts and the new acceptance-governance ExecPlan.
- [x] (2026-04-03 23:39Z) Updated the canonical docs so they describe the current Phase 3 state and remaining blockers more honestly.
- [x] (2026-04-03 23:39Z) Added a dedicated Phase 3 handoff document for the next finishing wave.
- [x] (2026-04-03 23:43Z) Verified that the docs agree on what is working, what is blocked, and how to continue.

## Surprises & Discoveries

- Observation: the acceptance docs are now stronger about gate classification, but they are still not the best “start here” guide for a new agent.
  Evidence: `artifacts/phase3_fr3b_acceptance_checklist.md` is focused on run execution and pass/fail recording, not on engineering handoff.

- Observation: `README.md` and `docs/ExecPlans/phase3_parallel_plan.md` already contain much of the right material, but the most current blocker set still lives mostly in chat history and recent harness observations.
  Evidence: the docs acknowledge preview/output parity issues broadly, but they do not yet call out the current narrow blockers like horizontal stamp packing and GIF transparency.

- Observation: one important contradiction had survived in `docs/ExecPlans/phase3_parallel_plan.md`: it still implied there was no real user-facing concept of appearance in the GUI, even though the shell already has named appearance profiles and focused appearance controls.
  Evidence: the old `Not yet achieved` list included “a real end-user concept of "appearance" in the GUI”.

## Decision Log

- Decision: add one explicit handoff artifact instead of trying to overload the acceptance worksheet with engineering state.
  Rationale: the worksheet is for gate review; a handoff note is a better place for “what to work on next” and “where to start in code”.
  Date/Author: 2026-04-03 / Codex

- Decision: keep the handoff scoped to Linux-only current Phase 3 work.
  Rationale: `Agents.md` explicitly forbids speculative cross-platform expansion in current scope.
  Date/Author: 2026-04-03 / Codex

## Outcomes & Retrospective

The docs are now much closer to a usable handoff set. The canonical files now agree that the remaining Phase 3 work is concentrated in visible-signature fidelity, horizontal packing, GIF transparency, timestamping, and final FR-3B acceptance rather than broad missing infrastructure. The new tactical handoff note in `artifacts/phase3_handoff_2026-04-03.md` gives the next agent a direct start point.

The consistency sweep is complete. The core docs and the new handoff note now agree on the narrow
remaining Phase 3 blockers and on the role of the acceptance/gate machinery.

## Context and Orientation

The canonical product requirements live in `docs/SPEC.md`. The canonical object-model vocabulary lives in `docs/SCHEMAS.md`. The current Phase 3 execution and ownership context lives in `docs/ExecPlans/phase3_parallel_plan.md`. The short repo entry point is `README.md`. The manual QA/gating workflow is described in `artifacts/phase3_fr3b_acceptance_checklist.md` and `artifacts/phase3_fr3b_acceptance_results.md`.

What is currently missing is a concise engineering handoff document that says: “here is what already works, here is what remains broken, here is how to rerun the current evidence flow, and here are the code modules you should inspect first.” That is what this refresh adds.

## Plan of Work

First, tighten `README.md` so it states the current Phase 3 status more concretely, especially the new evidence contract, the acceptance boundary, and the real remaining visible-signature issues. Second, update `docs/ExecPlans/phase3_parallel_plan.md` so its “Current Status” and remaining-work framing reflect the latest wins and blockers instead of only broad categories. Third, update `docs/SPEC.md` and `docs/SCHEMAS.md` where needed so the durable product and object-model docs stay aligned with the handoff framing. Finally, add a dedicated handoff file under `artifacts/` that a new agent can use as a jump-in brief.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

After editing, verify the docs agree on the core terms:

    rg -n "engineering_run|gate_candidate|release_gate_passed|Phase 4A|Phase 3 is not yet accepted|remaining blockers" \
      README.md docs/SPEC.md docs/ExecPlans/phase3_parallel_plan.md artifacts/phase3_fr3b_acceptance_checklist.md artifacts/phase3_handoff_2026-04-03.md

## Validation and Acceptance

The refresh is successful when:

- `README.md` tells a new reader what Phase 3 can do now, what is still blocked, and how the harness/gate works.
- `docs/ExecPlans/phase3_parallel_plan.md` describes the current Phase 3 state honestly enough that a new agent can pick up the next finishing wave.
- `docs/SPEC.md` and `docs/SCHEMAS.md` continue to hold the durable product/object-model truth without contradicting the more tactical docs.
- `artifacts/phase3_handoff_2026-04-03.md` exists and gives a clean starting brief for the next agent.

## Idempotence and Recovery

This work is documentation-only. Re-running the refresh means editing the same Markdown files again with updated truth. No destructive recovery step is needed.

## Artifacts and Notes

The main deliverable is the new handoff note in `artifacts/phase3_handoff_2026-04-03.md`, supported by aligned updates to the canonical docs.

## Interfaces and Dependencies

No new runtime dependency is needed. The only “interfaces” in scope are documentation contracts:

- `README.md` remains the concise repo entry point.
- `docs/SPEC.md` remains the canonical product source.
- `docs/SCHEMAS.md` remains the canonical product-facing object-model source.
- `docs/ExecPlans/phase3_parallel_plan.md` remains the current Phase 3 coordination document.
- `artifacts/phase3_handoff_2026-04-03.md` becomes the tactical handoff note for the next Phase 3 finishing wave.

Revision note: created on 2026-04-03 to prepare the repository docs for a Phase 3 handoff into a new chat/agent context.
