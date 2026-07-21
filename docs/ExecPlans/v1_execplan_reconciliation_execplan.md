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
- [x] (2026-07-20) Explorer review verified the close candidates and identified two remaining direct acceptance gaps: `gui_signing_flow_guidance_execplan.md` needs its specified sign-and-reopen walkthrough, and `gui_preset_first_shell_reduction_execplan.md` needs an assertion that the default shell omits the inline editor.
- [x] (2026-07-20) Ran a fresh isolated audit at `/tmp/foliaseal-reconciliation-audit`; it passed all twelve checkpoints.
- [x] (2026-07-20) Updated only evidence-backed GUI parent/child records, preserving the historical nine-checkpoint audit as distinct evidence and leaving the staged-flow and preset-first direct acceptances open.
- [x] (2026-07-20) Classified historical unchecked commit/publication markers as archival where their own latest commit proves the behavior landed; did not alter genuine behavior/evidence follow-ups.
- [x] (2026-07-20) Ran documentation checks and an independent compliance review; it found no remaining overclaim, omission, source/architecture conflict, or new ExecPlan need.
- [x] (2026-07-20) Created the dedicated documentation/status commit `4903fba82` (`docs: reconcile V1 release plan status`) and verified its six-plan scope and clean worktree.

## Surprises & Discoveries

- Observation: the GUI MVP parent still says certificate clarity, staged guidance, and end-to-end acceptance are pending even though their children and the current audit are complete.
  Evidence: `gui_mvp_recovery_parent_execplan.md` has unchecked Progress entries while `gui_certificate_and_preset_clarity_execplan.md` and `gui_signing_flow_guidance_execplan.md` record completed evidence.
- Observation: `.tmp/handoff.md` names placement-profile saving as immediate work although its child plan records the 2026-07-19 live walkthrough as complete.
  Evidence: `gui_save_placement_profile_from_refinement_execplan.md` Progress.
- Observation: the old signing/verification parent records a historical nine-checkpoint audit, while the newer certificate/preset UX audit records twelve checkpoints.
  Evidence: `gui_signing_setup_and_verification_recovery_parent_execplan.md` and commit `7d940ab3f` describe different audits and must not be collapsed into a false single historical claim.
- Observation: many unchecked historical “commit” entries are publication residue, not active product work.
  Evidence: the latest commits for `app_frame_certificate_dialog_boundary_execplan.md`, the Phase 3 harness boundary plans, `signed_output_overwrite_confirmation_execplan.md`, signing-setup boundary plans, and per-signature guidance plans are behavior-oriented commits that already contain the named slices.
- Observation: implementation landing and a broader integration audit do not substitute for a child plan's explicitly scoped direct acceptance.
  Evidence: `gui_signing_flow_guidance_execplan.md` records only a display-backed startup smoke and leaves its full sign-and-reopen click-through unperformed; the reusable-object audit proves save/compose/reselect and profile-library visibility, not every management operation.

## Decision Log

- Decision: correct only contradictions that can be verified from the current checkout and committed plans.
  Rationale: historical plans remain useful evidence; rewriting their technical history merely to remove every unchecked box would destroy provenance.
  Date/Author: 2026-07-20 / Codex

## Outcomes & Retrospective

The reconciliation pass closed stale GUI workflow markers, classified archival commit/publication residue without rewriting history, and preserved the historical audit distinction. Documentation checks and an independent compliance review passed, and the six-plan status update landed in `4903fba82`.

The archival classification is intentionally recorded here rather than mass-editing historical plans. Their unchecked commit/publication markers are archival when their latest commits directly name the delivered behavior: `66d64cdd5` (certificate dialog boundary), `3cc7e559b`, `a10ddce66`, `7602aa623`, `0ab01f604`, `5cfdd4de9`, `214f48361`, `612a11a7b`, and `0361563b9` (Phase 3 harness boundaries), `0f04864eb` (overwrite confirmation), `ff3b37f88`, `2af2722df`, `7b2126eda`, `ed616e3ca`, and `18e35ef2c` (signing-setup boundaries), `9430ffe94` and `08d6ae202` (workspace contracts), and `8cddd7546`, `5d05e71b5`, and `4cb84e52a` (per-signature review/guidance). Genuine remaining work stays open: the direct staged-flow sign-and-reopen walkthrough, the direct preset-first shell assertion, the named backend/fidelity behavior follow-ups, and the new V1 parent’s multi-signature, packaging, and fidelity children.

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

Revision note: 2026-07-20 / Codex
Compliance review retained the parent reconciliation dependency until this child commits, retained staged-flow direct acceptance as open, and narrowed reusable-object audit claims to the interactions actually evidenced.

Revision note: 2026-07-20 / Codex
Completed by documentation/status commit `4903fba82`; the remaining staged-flow and preset-first acceptances are deliberately outside this completed reconciliation slice.
