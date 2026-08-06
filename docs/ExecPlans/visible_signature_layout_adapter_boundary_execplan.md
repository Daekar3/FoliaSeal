# Extract the Visible-Signature Layout Adapter Boundary

This child ExecPlan follows the accepted signing-workspace cycle and the round-2 architecture scan.
It is a single bounded slice for the visible-signature layout seam. Maintain it under
`.agents/skills/write-execplan/PLANS.md` and the parent loop plan.

## Purpose

Make the visible-signature layout core import-pure and easier to test by separating neutral geometry,
fit policy, and the existing prepare-once contract from Pillow/PyHanko materializers. Preserve the
single `VisibleSignatureLayoutPort.prepare()` boundary, immutable `VisibleSignaturePreparation`,
memoized `signing()`/`preview()` projections, explicit preview stamp suppression, and all current
diagnostics, CLI/JSON fields, and rendered-output behavior.

## Architecture Selection Record

Candidate: `visible-signature-layout-boundary`, round-2 priorities approximately `64.0`, `62.6`,
and `64.0`, confidence `0.82`–`0.90`. Evidence: `application/visible_signature_layout.py` is 1,959
LOC and co-locates neutral contracts with `PyHankoTextMeasurer`, `PillowStampImageProbe`,
`PyHankoSignatureAppearanceAdapter`, PyHanko layout-rule conversion, and rendered-ink fit helpers;
`docs/ARCHITECTURE.md` explicitly tracks import-purity debt. Existing boundary tests cover the
prepare-once semantics and are the acceptance guard.

Designs reviewed independently by two explorers:

- A minimal split: low migration risk but leaves third-party rule materialization and caller-visible
  adapter construction; useful only as a bridge. Scores `(NF,CA,SR,TG,IC,CC)=(3.5,3.5,3,4,2.5,4)`.
- B injected ports/adapters: move materializers behind narrow `TextMeasurer`, `StampImageProbe`,
  `HorizontalInkMeasurer`, and target-materializer factories; strongest purity/testability. Scores
  `(4,4,2.5,4.5,3.5,3.5)`, with migration/cycle penalties recorded.
- C common-caller facade: rejected because it hides rather than extracts dependencies, risks a second
  planning path, and conflicts with the no-optional-plan/no-compatibility-facade architecture rule.

Selected shape: constrained A+B. Keep `VisibleSignaturePreparation` as the only common caller
boundary; introduce only the narrow adapter/materializer ports required to make the neutral module
import-pure. Do not add a second facade, planner, optional-plan API, or duplicate fit policy.

## Baseline and hard gates

- `visible_signature_layout.py`: 1,959 LOC, 56 functions, 27 classes.
- Neutral import currently eagerly loads Pillow/PyHanko layout types; boundary tests must prove the
  neutral module imports without PIL, pyHanko, Qt, or `phase3_signing_backend`.
- Preserve one text measurement, captured fit issues/gate, memoized projections, explicit
  `stamp_suppressed`, diagnostics/messages, and rendered-ink fallback behavior.
- `docs/SPEC.md` remains unchanged; no persisted schema, CLI command, JSON/artifact, signing-policy,
  or GUI behavior changes.

## Plan of Work

1. Add neutral rule/measurement/materializer protocols and opaque result DTOs without third-party
   imports. Keep current public port and preparation signatures stable.
2. Move PyHanko/Pillow concrete adapters and rule conversion into a presentation/infra adapter
   module with lazy composition. Ensure importing the neutral layout module does not load those
   packages or `phase3_signing_backend`.
3. Route existing preview renderer, signing backend, harness, and Qt preview callers through the
   existing preparation object. Delete duplicate direct adapter construction only after equivalent
   boundary tests pass.
4. Keep rendered-ink fit orchestration in its current owner for this slice; extract it only behind
   an injected port if a second concrete consumer is proven. Never rerun fit policy during signing.
5. Add/strengthen tests for import isolation, adapter equivalence, one-time measurement, memoization,
   preview suppression, fit diagnostics, and preview/signing parity. Run full suite and release
   matrices, clean temp artifacts/processes, update architecture docs and this plan, then commit.

## Acceptance and recovery

Acceptance requires all hard gates above, full tests/Ruff/diff checks, unchanged release counts and
artifact contracts, no new facade/planner, and a clean main worktree. If import cycles or adapter
equivalence fail, keep the old adapter at the composition edge and narrow the port; do not weaken
import-purity tests or duplicate preparation.

## Status

- [x] Candidate and design reviews recorded on 2026-08-05.
- [ ] Implementation and boundary migration.
- [ ] Full validation, docs reconciliation, post-measurement, and commit.
