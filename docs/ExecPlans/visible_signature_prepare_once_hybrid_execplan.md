# Replace visible-signature layout replanning with one prepare-once boundary

This ExecPlan is a living document and must be maintained in accordance with `PLANS.md` and `.agents/skills/write-execplan/SKILL.md`. It describes one complete implementation slice: introduce the recommended prepare-once layout boundary, migrate every production caller, preserve preview/signing/evidence behavior, remove obsolete compatibility layers and private bridges, reconcile documentation, validate the observable contracts, and commit the result.

## Purpose / Big Picture

Today a visible signature can be planned more than once as it travels through signing, canonical preview, and backend reservation evidence. The planner, boundary, and service facades also expose overlapping APIs, while `phase3_signing_backend.py` retains private fit/layout forwarding helpers for older callers and tests. This makes layout changes risky: a caller can silently get a different plan, fit decision, or rendered geometry depending on which path reached it.

After this slice, a caller obtains one immutable preparation from one application-owned boundary. That preparation contains the neutral layout plan and authoritative fit decisions, and lazily materializes signing or canonical-preview output from that preparation without silently planning again. Users will observe the same signature geometry, fit diagnostics, preview behavior, evidence fields, CLI commands, signed PDFs, and acceptance-matrix results. Developers will have one small seam to test and one explicit place to remove the obsolete wrappers rather than adding another compatibility facade.

## Child ExecPlan Dependencies

- [x] Fresh explorer-light review of the current checkout, relevant architecture debt, callers, contracts, and validation targets completed before planning.
- [x] The prior typed Phase 3 command-pipeline slice is present at commit `2249d98da`; this plan depends on its clean application boundary but does not modify its command contract.
- [x] No child ExecPlans are required. The work is intentionally bounded to one vertical slice so all callers, tests, documentation, and compatibility deletions land together.

## Progress

- [x] (2026-08-01) Reviewed the selected architecture candidate and confirmed the prepare-once hybrid design.
- [x] (2026-08-01) Fresh checkout exploration identified the four production planning paths, the optional-plan re-planning branches, the backend fit bridges, the preview stamp-suppression exception, and the contracts that must remain stable.
- [x] (2026-08-01) Wrote this one-slice ExecPlan before implementation.
- [x] Add the prepare-once request/preparation boundary and migrate the layout service/materializers; keep target construction behind explicit adapters and record the remaining module-split debt.
- [x] Migrate signing backend, canonical preview, reservation evidence, workflow validation, and tests to the new boundary with no optional-plan re-planning path.
- [x] Delete the overlapping planner/boundary facades and optional-plan materialization APIs; retain only behavior-bearing backend fit policy needed by the authoritative gate.
- [x] (2026-08-01) Ran focused, integration, full-suite, Ruff, diff, matrix, and process-cleanup validation; completed initial and high-risk compliance reviews and addressed their correctness findings.
- [x] (2026-08-01) Marked complete in the focused commit created by the write-git-commit worker (`refactor: prepare visible signature layout once`).

## Surprises & Discoveries

- Observation (pre-migration): The former service accepted an optional `layout_plan`; when it was absent, it silently planned again.
  Evidence: the retired `VisibleSignatureLayoutService.pyhanko_style_for_signing()` and `.pyhanko_style_for_canonical_preview()` paths.
- Observation: The backend, preview renderer, and reservation evidence each have a distinct planning/materialization path.
  Evidence: `prepare_phase3_signing_plan()`, `signing_preview_renderer._build_canonical_preview_layout()`, and `build_backend_reservation_evidence()` each construct or obtain plans independently.
- Observation: Canonical preview may intentionally suppress a horizontal stamp and therefore needs an explicit derived preview decision rather than an accidental second plan.
  Evidence: The existing preview path re-plans for stamp-suppressed text-only layout in compact cases.
- Observation: Rendered-ink fallback can accept a compact layout after structural fit checks, so deleting backend fit helpers without moving that decision would change acceptance behavior.
  Evidence: `_layout_fit_issues`, `_visible_signature_fit_issues*`, and rendered-ink helpers participate in the current signing fit gate and are covered by backend/layout tests.
- Observation (resolved): Evidence formerly materialized a signing style only to derive reservation facts.
  Evidence: `build_backend_reservation_evidence()` now obtains one `PreparedSigningPlan`, reads its captured preparation/fit gate, and derives JSON layout facts without materializing a style.
- Observation (post-review): The rendered-ink cache needed page/placement/template and image-stat identity in addition to text/style fields to prevent left/right and stale-file collisions.
  Evidence: The high-risk review identified cross-position cache reuse; the key now includes those identities.
- Observation (post-review): Backend rendered-ink fallback is behavior-bearing acceptance policy rather than a compatibility facade, so the preparation captures its fit gate once and evidence consumes the same decision.
  Evidence: `VisibleSignaturePreparation.fit_gate_passed`/`fit_gate_error` are reused by signing, validation, and evidence.

## Decision Log

- Decision: Use one `VisibleSignatureLayoutPort.prepare(request)` entry point returning a lazy `VisibleSignaturePreparation` with neutral plan, fit issues, and target materialization methods.
  Rationale: This makes the common caller trivial while preserving explicit target ownership and preventing duplicate planning. Lazy materialization avoids eagerly constructing an unused PyHanko object.
  Date/Author: 2026-08-01 / Codex.
- Decision: Keep preview stamp suppression as an explicit preview result/derived plan decision inside the preparation, never as an implicit re-planning fallback.
  Rationale: Preview and signing have different presentation needs, but the difference must be observable and tested so geometry cannot drift silently.
  Date/Author: 2026-08-01 / Codex.
- Decision: Keep neutral planning and fit contracts dependency-light; isolate PyHanko/Pillow construction in injected target materializers.
  Rationale: The application boundary must remain directly testable and importable without GUI or third-party rendering dependencies.
  Date/Author: 2026-08-01 / Codex.
- Decision: Remove legacy compatibility pieces in this same slice after caller migration: overlapping planner/service/boundary facades, optional-plan re-planning, backend `_layout_*`/`_single_line_*` forwarding helpers, `_visible_layout` aliases, and tests whose only purpose is preserving those names.
  Rationale: The user explicitly requested cruft removal and `docs/SPEC.md` prefers replacement over indefinite compatibility layers.
  Date/Author: 2026-08-01 / Codex.
- Decision: Preserve serialized evidence names and CLI behavior; provider or implementation metadata must not enter stable schemas in this slice.
  Rationale: Existing acceptance tooling depends on `backend_reservation_snapshot`, `backend_reservation_error`, fit counters, command labels, and output artifacts.
  Date/Author: 2026-08-01 / Codex.

## Outcomes & Retrospective

Implementation outcome: the final public boundary is `VisibleSignatureLayoutPort.prepare()` with frozen `VisibleSignaturePreparation`; signing and canonical preview materializers consume the captured plan and fit gate, while compact horizontal preview stamp suppression is prepared explicitly and exposed in the preview result. The overlapping planner/boundary facades, old neutral plan request/result classes, and optional-plan materialization paths were removed. Backend evidence now obtains one `PreparedSigningPlan`, consumes its neutral preparation/fit decision, and derives layout facts without signing-style materialization; the rendered-ink cache is identity-safe. Behavior-bearing backend rendered-ink/fit helpers remain implementation policy for the authoritative gate. Architecture and README documentation describe the seam. Validation evidence: focused 239 passed; related integration 118 passed with one existing Pillow deprecation warning; full suite 1,034 passed with the same warning; Ruff and `git diff --check` passed; preview matrix 8 scenarios/0 errors; signed matrix 8 scenarios/6 successful signings/2 matched intentional rejections/0 cryptographic, annotation, comparison, or expectation failures; no FoliaSeal/Phase 3 processes remained after cleanup. The focused commit is finalized on `main`. Deliberate follow-up debt: extract the concrete PyHanko/Pillow adapters from `visible_signature_layout.py` so a truly dependency-light contract module can be imported without third-party modules; the current prepare-once seam already isolates construction behind typed ports and adapters.

## Context and Orientation

FoliaSeal is a Python desktop application that signs PDFs and renders visible-signature previews. A visible-signature layout is the rectangle, text/image arrangement, fit decision, and reservation evidence used to make the signature appear consistently in the preview and in the signed PDF. A materializer turns that neutral decision into a target-specific object such as a PyHanko signing style or a canonical preview layout. “Prepare once” means that the expensive and policy-bearing neutral decision is created once and every target-specific output consumes that decision rather than recomputing it.

The current neutral/application code is concentrated in `src/foliaseal/application/visible_signature_layout.py`. It contains `VisibleSignatureLayoutRequest`, `VisibleSignaturePreparation`, `SignatureLayoutPlan`, fit issues, measurement ports, `VisibleSignatureLayoutPort`, `VisibleSignatureLayoutService`, and PyHanko-facing style adapters. `src/foliaseal/application/phase3_signing_backend.py` owns concrete PyHanko signing plus behavior-bearing fit/layout policy and `PreparedSigningPlan`. `src/foliaseal/presentation/qt/signing_preview_renderer.py` builds canonical preview layouts. `src/foliaseal/application/signing_draft_workflow.py` validates visible-signature fit for UI readiness. Existing evidence consumers require stable reservation keys and fit diagnostics.

The final composition should have one application-owned port and one concrete production composition. The neutral plan may depend on domain value types and injected measurement/fit ports. PyHanko and Pillow may be imported only by target-specific adapters. Tests should use deterministic fake measurers/materializers and retain a small number of PyHanko parity tests at the adapter boundary.

## Plan of Work

First add the new request, preparation, and port types in the layout module or a narrowly named application companion module. `VisibleSignatureLayoutRequest` must contain the current appearance, rectangle, stamp text/background, include-text/stamp/border/background options, horizontal-ink policy, and explicit fit-policy inputs currently spread across `LayoutRequest`, `VisibleSignaturePlanRequest`, and backend helpers. `VisibleSignaturePreparation` must expose the immutable neutral `SignatureLayoutPlan` or `VisibleSignaturePlan`, authoritative `VisibleSignatureFitIssue` values/decision, reservation evidence, and memoized `signing()` and `preview()` materializers. Keep result types opaque at the neutral boundary if they contain PyHanko/Pillow objects. The preview result must carry an explicit `stamp_suppressed` or derived-plan marker when compact preview policy changes the effective layout.

Then make the concrete layout composition implement `VisibleSignatureLayoutPort.prepare()`. Move rendered-ink fallback and fit-gate decisions into the preparation path using explicit injected probes/policies. The normal path must measure and reserve once. A target-specific preview derivation is allowed only when the existing stamp-suppression policy requires it, and that derivation must be represented in the returned preview artifact rather than hidden behind an optional argument. Materializers must consume the supplied plan and must not call the planner.

Migrate every production caller. `prepare_phase3_signing_plan()` should call the port once and store the preparation/neutral plan and fit decision in `PreparedSigningPlan`. The backend stamp builder must consume the prepared signing artifact and must not call a boundary or fit wrapper when a plan is absent; change its request flow so a preparation is mandatory for visible signing. `signing_preview_renderer._build_canonical_preview_layout()` should consume the preparation’s preview artifact. `build_backend_reservation_evidence()` should read reservation evidence and fit facts from the preparation without materializing a signing style solely for diagnostics. `SigningDraftWorkflow` should use the public fit decision or a small application adapter rather than importing backend-private validation helpers.

The migration removed the overlapping `VisibleSignatureLayoutBoundary`/planner facades and optional `layout_plan` materialization parameters. Retain backend `_layout_fit_issues`, `_visible_signature_fit_issues*`, `_ensure_layout_can_fit`, and rendered-ink helpers only where they remain behavior-bearing implementation policy for the authoritative fit gate; do not describe them as compatibility facades. Do not leave a new generic gateway or provider registry without a concrete second provider requirement.

Migrate tests from concrete planner/service/private-helper contracts to boundary behavior. Add tests proving one preparation can produce signing and preview artifacts without a second measurement or planning call; explicit preview stamp suppression produces a derived preview decision; compact rendered-ink fallback preserves current fit acceptance; structural errors still map to the same `SigningDraftValidationIssue` codes/messages; reservation evidence retains existing JSON fields; invisible signing remains unchanged; and the PyHanko materializer receives the exact prepared plan. Delete tests whose only assertion is that removed facades, aliases, or private helper names exist.

Finally update `docs/ARCHITECTURE.md`, `README.md` if they mention the old seam, and relevant ExecPlans. Document the prepare-once boundary, adapter ownership, explicit preview derivation, and removed compatibility pieces. Run the full acceptance audit, remove generated temporary artifacts, verify no FoliaSeal/Phase 3 processes remain, and commit all source/tests/docs/plan changes as one focused slice.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Confirm the clean baseline and inventory all callers before edits:

       git status --short --branch
       rg -n "VisibleSignatureLayout(Boundary|Service|Planner)|pyhanko_style_for_|prepare_preview_style|prepare_signing_style|layout_plan=|_layout_fit_issues|_visible_signature_fit_issues|_ensure_layout_can_fit|_single_line_|_visible_layout" src tests docs/ARCHITECTURE.md

   The baseline must be `main` at `2249d98da` or later with no unrelated changes. Preserve any unexpected user edits and stop only to scope them safely; do not reset or discard them.

2. Add the typed prepare-once boundary and deterministic fake materializers. Run the new boundary tests immediately after each logical migration. The concrete layout module still co-locates PyHanko/Pillow adapters; record that import-purity extraction as follow-up debt rather than claiming a false guard.

3. Migrate backend, preview, evidence, and workflow callers. Use focused tests while each caller changes. Make a visible-signing preparation mandatory so no caller can reach a fallback branch that silently replans.

4. Delete the obsolete compatibility facades and private bridges only after `rg` proves no production or test references remain. Use `apply_patch` for edits and keep the deletion in this same slice; do not replace deleted names with aliases.

5. Run focused validation:

       .venv/bin/python -m pytest -q \
         tests/unit/test_visible_signature_layout.py \
         tests/unit/test_visible_signature_layout_boundary.py \
         tests/unit/test_phase3_signing_backend.py \
         tests/unit/test_signing_preview_renderer.py \
         tests/unit/test_signing_draft_workflow.py

   Expect all selected tests to pass. Add or rename the new boundary test module if the repository’s existing test layout differs, and record the exact observed count in this plan.

6. Run the related integration and complete suite:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_qa_signed_acceptance_evidence.py tests/unit/test_main_cli.py
       .venv/bin/python -m pytest -q
       .venv/bin/ruff check src tests
       git diff --check

7. Run structural guards:

       rg -n "VisibleSignatureLayout(Boundary|Service|Planner)|pyhanko_style_for_|prepare_preview_style|prepare_signing_style|layout_plan=|_layout_fit_issues|_visible_signature_fit_issues|_ensure_layout_can_fit|_single_line_|_visible_layout" src tests

   The final search must return no deleted compatibility seam or optional-plan re-planning branch in live source/tests. Historical documentation references must be explicitly marked retired, not presented as active APIs.

8. Exercise observable behavior with the tracked Phase 3 release-fidelity fixture. Run the existing offscreen preview and signed acceptance matrix commands against `artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf`, `signed_acceptance_identity.p12`, passphrase `secret`, and `tests/fixtures/phase3/release_fidelity_manifest.json`. Confirm 8 preview scenarios with zero errors, 8 signed scenarios with 6 successful signings and 2 matched intentional rejections, zero critical counters, stable summary paths, and unchanged evidence keys.

9. Audit cleanup:

       pgrep -af '[p]ython.*foliaseal|[p]ython.*phase3' || true
       find /tmp -maxdepth 1 -type d -name 'foliaseal-visible-layout-*' -print

   Remove only the temporary directories created by this plan, close any GUI windows opened by the audit, and rerun the process check. If no display is available for `wmctrl`, record that fact and rely on offscreen process cleanup.

10. Update this plan’s `Progress`, `Surprises & Discoveries`, `Decision Log`, `Outcomes & Retrospective`, `Artifacts and Notes`, and validation counts. Then review the complete diff and use the `write-git-commit` skill to create one focused commit containing the implementation, tests, documentation, retired-plan updates, and this completed ExecPlan.

## Validation and Acceptance

The slice is accepted only when a normal visible-signing caller can prepare once and obtain signing output without re-planning, and canonical preview consumes the same preparation or an explicit, tested preview-derived plan for stamp suppression. No live source or test code may depend on the deleted planner/service/boundary facades, optional-plan re-planning, backend private fit/layout bridges, or compatibility aliases.

All existing visible-signature behavior must remain observable: the same rectangles, text/image inclusion rules, fit issue codes/messages, compact rendered-ink fallback, preview stamp suppression, reservation evidence keys, signed output verification, invisible-signature path, CLI output, and Phase 3 matrix counters. The neutral application module must import without PySide6, PyHanko, Pillow, or cryptography. Focused tests, related integration tests, full pytest, Ruff, diff checks, and the release-fidelity preview/signed matrix commands must pass. The final process audit must show no FoliaSeal/Phase 3 Python process or leftover temporary GUI/audit artifact.

## Idempotence and Recovery

The migration is safe to repeat because each caller can be moved to the new port before obsolete code is deleted. If a test exposes a missing behavior, restore the smallest behavior-bearing implementation behind the new preparation boundary; do not restore a compatibility alias or optional-plan fallback. If preview stamp suppression needs a derived plan, encode that result explicitly and add a regression test before continuing. Generated matrix artifacts belong in temporary directories or existing ignored artifact paths; inspect them, then remove only the directories created by this plan. Never delete user documents, certificates, catalogs, or broad workspace paths.

## Artifacts and Notes

Record concise evidence here as implementation proceeds. The completed plan should include:

       focused layout/backend/preview/workflow tests: <observed count> passed
       full suite: <observed count> passed, <warnings>
       preview matrix: 8 scenarios, 0 errors
       signed acceptance matrix: 8 scenarios, 6 successful signings, 2 intentional rejections, 0 critical counters
       import-purity guard: concrete adapter module still loads PyHanko/Pillow; extraction is recorded as follow-up debt
       compatibility guard: no deleted planner/boundary facade, optional-plan materializer, or `_visible_layout` alias remains; retained fit helpers are behavior-bearing policy

Do not paste complete JSON or large diffs into this plan. Record summary paths, counters, test totals, commit hash, and any display/process-audit limitation.

## Interfaces and Dependencies

In `src/foliaseal/application/visible_signature_layout.py` or a narrowly named application companion, define the prepare-once boundary with concrete application-owned types:

    class VisibleSignatureLayoutPort(Protocol):
        def prepare(self, request: VisibleSignatureLayoutRequest) -> VisibleSignaturePreparation: ...

    @dataclass(frozen=True)
    class VisibleSignatureLayoutRequest:
        appearance: SignatureAppearance
        signature_rect: SignatureRect
        stamp_text: str
        stamp_background: object | None = None
        options: VisibleSignatureLayoutOptions = field(default_factory=VisibleSignatureLayoutOptions)

    @dataclass(frozen=True)
    class VisibleSignaturePreparation:
        plan: SignatureLayoutPlan
        fit_issues: tuple[VisibleSignatureFitIssue, ...]
        reservation_snapshot: Mapping[str, object]
        # These methods are lazy and memoized; they never call the planner.
        def signing(self) -> SigningLayoutArtifact: ...
        def preview(self) -> PreviewLayoutArtifact: ...

`SigningLayoutArtifact` and `PreviewLayoutArtifact` may carry opaque target-specific style/layout objects, but their public metadata must include the consumed plan fingerprint, fit issues, reservation evidence, and any explicit `stamp_suppressed` or derived-preview marker. The neutral request and result types must not import PyHanko, Pillow, Qt, or filesystem adapters.

Inject the current text measurer, image probe, horizontal ink measurer, rendered-fit probe/policy, and target materializers. The production composition may use PyHanko/Pillow adapters; tests must provide deterministic fakes. `PreparedSigningPlan` should retain the preparation or its neutral plan and fit decision so downstream signing cannot reconstruct it. `build_backend_reservation_evidence()` should accept those neutral facts rather than materializing a style solely for evidence.

At the end of the slice, the old `VisibleSignatureLayoutBoundary`, `VisibleSignatureLayoutService.production()`, `VisibleSignaturePlanner.production()`, optional `layout_plan` materialization arguments, backend private fit/layout forwarding helpers, and `_visible_layout` aliases must either be removed or be demonstrably behavior-bearing code behind the new boundary. The preferred outcome is deletion after migration. No generic gateway or speculative provider registry is allowed.

## Change-Slice Boundary

This is one structural behavior-preserving refactor with intentional compatibility cleanup. Allowed changes are the application layout/backend seam, directly affected preview/workflow/Qt adapter wiring, focused and integration tests, README/architecture/ExecPlan status, and ignored/temporary evidence outputs used for validation. Forbidden changes include unrelated signing-workspace redesign, certificate/profile schema work, new renderer providers, CLI command redesign, or broad GUI styling changes. The only intended API removal is undocumented legacy compatibility surface proven unused by production callers after migration.

Plan revision note: created 2026-08-01 after a fresh explorer review and three independent interface designs. Chose the common-caller `prepare()` shape combined with plan-first target materialization because it prevents silent re-planning while keeping the normal signing/preview path one call, and explicitly included legacy compatibility removal per the user’s instruction.
