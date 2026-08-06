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
2. Move PyHanko/Pillow concrete adapters and rule conversion into
   `application/visible_signature_layout_adapters.py` with lazy backend composition. Ensure
   importing the neutral layout module does not load those packages, Qt, or `phase3_signing_backend`.
3. Route signing and rendered preview artifact callers through the existing preparation object.
   Geometry-only Qt helpers (`signature_preview_layout.py` and the harness snapshot geometry
   helper) may continue to call `VisibleSignatureLayoutEngine.plan()` because they consume only
   neutral `SignatureLayoutPlan` geometry and do not materialize a signing/preview artifact; record
   that exception rather than introducing a second target-materialization path.
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

## Implementation findings and compliance resolution

- The neutral reservation now stores `LayoutRuleSpec`/`LayoutMargins` values only; PyHanko
  `SimpleBoxLayoutRule` objects are materialized by `visible_signature_layout_adapters.py`.
- `VisibleSignatureAppearancePort` and `SignatureAppearanceMaterializer` preserve structural typing
  at the neutral boundary without importing the backend appearance implementation.
- Concrete names moved to `visible_signature_layout_adapters.py`; package-level lazy exports remain,
  while direct imports from the old concrete module path are intentionally retired as dead
  compatibility surface. No current production caller used that path.
- The old private background-layout wrapper was replaced by the neutral
  `_background_layout_spec_for_stamp()` and concrete `materialize_background_layout()` adapter;
  backend callers import the latter lazily to keep the dependency direction one-way.
- `PyHankoVisibleSignatureStyle` was renamed to the neutral `SigningVisibleSignatureStyle` so the
  core contract does not carry a backend/vendor name.
- The two Qt geometry-only helpers remain on `VisibleSignatureLayoutEngine.plan()` by design; they
  consume neutral geometry and do not perform target materialization or duplicate fit policy.
- Additional subprocess coverage verifies neutral import isolation and both adapter/backend import
  orders.

## Validation and measured outcome

- Focused layout/backend/boundary tests: `175 passed`.
- Full suite after the final code pass: `1042 passed` with one pre-existing Pillow deprecation
  warning.
- Ruff and `git diff --check` pass.
- Neutral import isolation: importing `foliaseal.application.visible_signature_layout` loads no
  PIL, pyHanko, Qt, or `phase3_signing_backend` modules.
- Baseline layout core: `1,959` LOC, 56 functions, 27 classes. Final neutral core: `1,876` LOC;
  concrete adapter module: `177` LOC. The boundary moved third-party rule/materializer knowledge
  out of the neutral module while preserving the existing plan and prepare-once behavior.
- Architecture-loop proxy measurement (same six-component rubric): navigation `0.00` (the same
  four production workflow modules remain involved), change amplification `0.00` (caller count is
  unchanged), seam reduction `1.00` (three forbidden concrete imports from the neutral module to
  zero), boundary-test improvement `0.20` (the existing boundary inventory remains covered and now
  adds neutral import and both import-order checks), interface compression `0.00` (the package-level
  adapter names remain the same), and boundary isolation `1.00` (neutral PIL/PyHanko/Qt/backend
  import set reduced from three categories to zero). This yields `Actual Improvement = 0.34`.
  The pre-implementation prediction was `0.25`, so prediction accuracy is `1.36x`; no component
  regressed below `-0.10`.
- Focused/full tests, Ruff, diff-check, and import-isolation evidence are recorded above. The release
  preview matrix executed 8 scenarios with 0 error rows. The signed acceptance matrix executed 8
  scenarios with 6 successful signings, 2 matched intentional rejections, zero
  cryptographic/annotation/preview-output failures, and `acceptance_expectations_passed=True`.
  Explicit `/tmp/foliaseal-layout-preview` and `/tmp/foliaseal-layout-signed` directories were
  removed and the process audit is clean. The worktree is intentionally still uncommitted, and the
  post-implementation architecture rescan is pending the commit.

## Status

- [x] Candidate and design reviews recorded on 2026-08-05.
- [x] Implementation and boundary migration.
- [x] Full test/Ruff/diff/import-isolation validation and docs reconciliation.
- [x] Release preview and signed matrices, post-measurement, and docs reconciliation.
- [x] Commit `4554c6922` (`refactor: isolate visible-signature layout adapters`).
- [ ] Post-commit architecture rescan.
