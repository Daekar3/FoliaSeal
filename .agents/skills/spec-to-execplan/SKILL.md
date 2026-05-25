---
name: spec-to-execplan
description: Break a spec into independently-grabbable execplans using tracer-bullet vertical slices. Use when user wants to convert a spec to execplans, create execplans to implement a large feature or features, or break down a feature into work items.
---

# Spec to ExecPlans

Break a spec into independently-grabbable execplans using vertical slices (tracer bullets).

## Process

### 1. Locate SPEC.md

Ask the user for the SPEC.md file path.

If the SPEC.md is not already in your context window, fetch it.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code.

### 3. Draft vertical slices

Break the spec into **tracer bullet** execplans. Each execplan is a thin vertical slice that cuts through ALL integration layers end-to-end, NOT a horizontal slice of one layer.

Slices may be 'HITL' or 'AFK'. HITL slices require human interaction, such as an architectural decision or a design review. AFK slices can be implemented and merged without human interaction. Prefer AFK over HITL where possible.

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
</vertical-slice-rules>

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each slice, show:

- **Title**: short descriptive name
- **Type**: HITL / AFK
- **Blocked by**: which other slices (if any) must complete first
- **User stories covered**: which user stories from the PRD this addresses

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the dependency relationships correct?
- Should any slices be merged or split further?
- Are the correct slices marked as HITL and AFK?

Iterate until the user approves the breakdown.

### 5. Create the ExecPlans

For each approved slice, create an ExecPlan using $write-exec-plan.

Create execplans in dependency order (blockers first) so you can reference real issue numbers in the "Blocked by" field.

