# Reconcile stale V1 ExecPlan and handoff status

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this documentation-only slice, a maintainer can identify real remaining V1 work from `docs/ExecPlans/` without being sent back to already completed GUI recovery tasks. The product does not change; the observable result is a consistent dependency graph and current evidence references.

## Child ExecPlan Dependencies

- [x] The 2026-07-19 GUI audit and commit `7d940ab3f` exist.
- [x] This child has no further child ExecPlans.

## Progress

- [x] (2026-07-20) Identified stale status in the GUI MVP parent, staged-guidance child, reusable-object parent, appearance-save child, preset-first child, signing/verification parent, and `.tmp/handoff.md`.
- [ ] Verify each claimed completion against its commit, tests, or audit JSON before changing a checkbox.
- [ ] Update the listed plans and handoff with current status and audit checkpoint counts.
- [ ] Classify historical unchecked “commit” markers as archival rather than active work where a later commit proves completion.
- [ ] Run documentation checks, review the diff for overclaims, and commit this documentation/status slice.

## Surprises & Discoveries

- Observation: the GUI MVP parent still says certificate clarity, staged guidance, and end-to-end acceptance are pending even though their children and the current audit are complete.
  Evidence: `gui_mvp_recovery_parent_execplan.md` has unchecked Progress entries while `gui_certificate_and_preset_clarity_execplan.md` and `gui_signing_flow_guidance_execplan.md` record completed evidence.
- Observation: `.tmp/handoff.md` names placement-profile saving as immediate work although its child plan records the 2026-07-19 live walkthrough as complete.
  Evidence: `gui_save_placement_profile_from_refinement_execplan.md` Progress.
- Observation: the old signing/verification parent records a historical nine-checkpoint audit, while the newer certificate/preset UX audit records twelve checkpoints.
  Evidence: `gui_signing_setup_and_verification_recovery_parent_execplan.md` and commit `7d940ab3f` describe different audits and must not be collapsed into a false single historical claim.

## Decision Log

- Decision: correct only contradictions that can be verified from the current checkout and committed plans.
  Rationale: historical plans remain useful evidence; rewriting their technical history merely to remove every unchecked box would destroy provenance.
  Date/Author: 2026-07-20 / Codex

## Outcomes & Retrospective

At creation, documentation drift is a release-governance risk. On completion, record exactly which plans were reconciled and which unchecked entries remain true work.

## Context and Orientation

An ExecPlan is a living implementation record. A checked Progress item means evidence supports completion; an unchecked item must name real remaining work. `scripts/live_gui_parent_audit.py` now writes twelve checkpoints in the current UX run, while older parent evidence truthfully records its nine-checkpoint historical run. The authoritative plans to reconcile are `gui_mvp_recovery_parent_execplan.md`, `gui_signing_flow_guidance_execplan.md`, `gui_reusable_signing_objects_execplan.md`, `gui_save_appearance_profile_from_refinement_execplan.md`, `gui_preset_first_shell_reduction_execplan.md`, and `gui_signing_setup_and_verification_recovery_parent_execplan.md`.

## Plan of Work

First read every target plan’s Progress, Outcomes, and revision notes, plus the referenced commits. Rerun the current audit into a uniquely named `/tmp` directory before using its JSON; do not rely on an old ephemeral path. Update the MVP, staged-guidance, and reusable-object records to show completed child work. Preserve the historical nine-checkpoint wording where it describes that earlier run, then add a distinct reference to the newer twelve-checkpoint audit rather than rewriting history. Update the appearance child because the current audit exercises its visible save. Do not close the preset-first manual-validation item unless a fresh screenshot/assertion specifically proves the default shell omits the inline editor. `git check-ignore` must decide whether `.tmp/handoff.md` is local-only; if ignored, update it locally but keep the durable status in tracked `docs/ExecPlans/`. For every changed unchecked entry, add a short classification of completed, genuine remaining work, or archival-only.

## Concrete Steps

From `/home/daekar/FoliaSeal`:

    git log --oneline -- docs/ExecPlans
    rg -n '^\s*- \[ \]' docs/ExecPlans
    DISPLAY=:0 timeout 180s .venv/bin/python scripts/live_gui_parent_audit.py --artifacts-dir /tmp/foliaseal-reconciliation-audit
    .venv/bin/python -c 'import json; a=json.load(open("/tmp/foliaseal-reconciliation-audit/audit.json")); print(a["status"], len(a["checkpoints"]))'
    git check-ignore -v .tmp/handoff.md || true
    git diff --check

Expected result: every edited unchecked item has direct evidence, the audit prints `passed 12`, and no unrelated plan is changed.

## Validation and Acceptance

A new contributor reading the parent plans must see the next real release work as multi-signature, packaging, and fidelity rebaseline—not completed certificate/profile or staged-flow work. A reviewer must be able to trace every newly checked item to a commit or current artifact.

## Idempotence and Recovery

This is documentation/status work only. If an artifact is absent, leave the item open and record the missing evidence rather than guessing. Do not delete historical plans or generated evidence.

## Artifacts and Notes

Include a concise revision note in every edited plan. The commit may include only tracked documentation/status files; if `.tmp/handoff.md` is ignored, do not stage it and record its durable replacement in a tracked plan. Do not mix source changes.

## Interfaces and Dependencies

Use Git history, `docs/SPEC.md`, and current plan evidence as the only truth sources. The plan may reference `scripts/live_gui_parent_audit.py` but must not alter its behavior.

Revision note: 2026-07-20 / Codex
Created as the documentation/status child of `v1_release_compliance_parent_execplan.md`.
