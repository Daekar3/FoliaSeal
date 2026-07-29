# Close the remaining FoliaSeal V1 release bar

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this parent plan is complete, FoliaSeal has current, reproducible proof for every still-unproven V1 release-bar claim: its plan inventory tells the truth, a user can add a second approval signature when the PDF permits it, a Linux desktop package can be installed with its renderer dependency, and preview/output fidelity is measured against a maintained representative corpus. A release reviewer can run the named evidence commands rather than infer compliance from old plans.

## Child ExecPlan Dependencies

- [x] `v1_execplan_reconciliation_execplan.md` completed in `4903fba82`; it reconciled status from fresh evidence while preserving the remaining direct GUI acceptances as real work.
- [x] `v1_multi_signature_acceptance_execplan.md` completed in `2b36c49c4` with its final plan closeout in `794976d8c`; the release-bar “add another approval signature” behavior is now evidenced.
- [ ] `v1_linux_desktop_distribution_execplan.md` must complete before claiming packaged Linux desktop distribution.
- [ ] `v1_visible_signature_fidelity_rebaseline_execplan.md` must complete before claiming durable WYSIWYG evidence beyond the historical or compact-only matrices.
- [x] The direct default-shell acceptance in `gui_preset_first_shell_reduction_execplan.md` completed on 2026-07-28 with a 14-checkpoint audit and retained screenshot review. The staged-flow acceptance completed on 2026-07-20; both pre-existing GUI acceptance slices remain outside this parent’s four child slices.

## Progress

- [x] (2026-07-20) Audited `docs/SPEC.md`, current GUI/recovery plans, `docs/ARCHITECTURE.md`, and the current PyInstaller path.
- [x] (2026-07-20) Created four child plans with one primary change class each.
- [x] (2026-07-20) Executed the reconciliation child: its fresh twelve-checkpoint audit, evidence review, compliance review, and dedicated documentation/status commit `4903fba82` are complete.
- [x] (2026-07-28) Executed and closed the multi-signature child: dynamic unused `SignatureN` allocation, actual-PDF two-signature review coverage, isolated 19-checkpoint audit, compliance review, documentation updates, and commit `2b36c49c4` all passed.
- [ ] Execute the Linux distribution child and retain its package acceptance evidence.
- [ ] Execute the fidelity child and publish the bounded release conclusion.
- [ ] Perform a final release-bar review, reconcile `README.md` and `docs/ARCHITECTURE.md`, and commit the parent-plan closeout.

## Surprises & Discoveries

- Observation: the original display-backed GUI audit proved one complete signing journey, but not a second signing journey over an already signed output.
  Evidence: its pre-extension checkpoint set stopped after certificate, preset, sign, reopen, and verification; the multi-signature child added the second-signing path.
- Observation: the multi-signature audit now covers two separated placements, two signed outputs, and two locally verified review items while preserving the first output.
  Evidence: `/tmp/foliaseal-live-gui-multi-signature-audit/audit.json` reports `status: passed`, `output_signature_count: 2`, and 19 checkpoints.
- Observation: PyInstaller bundles font assets, but the live viewer now relies on the operating-system `pdftoppm` executable.
  Evidence: `src/foliaseal/infra/render/poppler_backend.py` is the interactive viewer pixel source and `docs/ARCHITECTURE.md` says broader desktop distribution remains open.

## Decision Log

- Decision: use four children rather than a single release sweep.
  Rationale: status cleanup, multi-signature behavior, OS packaging, and rendering evidence have different risks and should remain independently reviewable.
  Date/Author: 2026-07-20 / Codex
- Decision: make Debian-family `.deb` packaging the first supported distribution mode.
  Rationale: it can declare `poppler-utils` as a system dependency, which a bare PyInstaller one-dir folder cannot reliably do.
  Date/Author: 2026-07-20 / Codex

## Outcomes & Retrospective

At creation, the one-signature product journey is demonstrated, but the release bar is not yet fully proven. Record each completed child’s observable evidence here and state any remaining limitation plainly.

## Context and Orientation

`docs/SPEC.md` is the frozen V1 contract. Its release bar requires certificate management, document review, reusable signing objects, offline signing and verification, a user-selected output path, reopening and verification, an additional approval signature when allowed, and a packaged Linux desktop application. The prior GUI recovery plans completed the first-signature journey. This parent closes the remaining proof and distribution gaps without reopening completed product work.

## Plan of Work

Run reconciliation first because it makes the status graph trustworthy. Multi-signature, packaging, and fidelity may then proceed independently because they touch different boundaries. Keep their commits narrow: documentation/status update, behavior change, packaging change, and evidence refresh respectively. After every child, update this parent’s Progress and dependencies with the exact command, artifact path, and result. Do not claim all V1 work complete if a child only passes unit tests; each child has a user-observable acceptance requirement.

## Concrete Steps

From `/home/daekar/FoliaSeal`, execute the children in order and run after each one:

    git status --short
    git log -1 --oneline

Expected result: the relevant child plan records its evidence and the worktree is clean after its deliberate commit.

## Validation and Acceptance

Acceptance requires all four child plans to be complete. The multi-signature child supplies the permitted and restricted behavior evidence; the fidelity child supplies the supported-layout evidence; and the packaging child supplies a package-owned end-to-end audit that creates/selects a certificate, signs, reopens, and verifies without importing the checkout or `.venv`. A final package smoke test complements those child artifacts but does not replace them. The final review must map each bullet in `docs/SPEC.md` under “Release Bar” to current behavior and an artifact or test.

## Idempotence and Recovery

Each child uses isolated `/tmp` audit directories or versioned package/evidence output directories. Never overwrite retained evidence without recording why. If one child exposes a product bug, stop its release claim, add the defect to that child’s plan, fix it there, and rerun only that child’s acceptance.

## Artifacts and Notes

The parent acceptance record should name the final package file, package inspection output, multi-signature audit JSON, and fidelity-summary JSON. Generated binary packages and screenshots may remain outside Git when repository policy requires it, but their generation command and checksums must be recorded.

## Interfaces and Dependencies

The children use `scripts/live_gui_parent_audit.py`, `src/foliaseal/application/sign_pdf_use_case.py`, `src/foliaseal/application/document_review.py`, `scripts/build_pyinstaller.sh`, `foliaseal.spec`, and the Phase 3 matrix CLI exposed by `src/foliaseal/__main__.py`. No child may weaken DocMDP permission checks, local-verification honesty, or the existing certificate/profile persistence contracts.

Revision note: 2026-07-20 / Codex
Created the parent from the live release-bar audit. It deliberately separates completed first-signature GUI recovery from still-unproven multi-signature, package, and representative-fidelity acceptance.
