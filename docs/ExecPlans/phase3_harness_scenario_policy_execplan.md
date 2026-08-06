# Extract the Shared Harness Scenario Policy

## Purpose

Deepen `phase3_harness_workspace.py` by removing the duplicated profile and appearance-override
policy from its live and headless adapters. A pure, Qt-free scenario resolver will turn the normalized
scenario fields into one immutable resolved plan. The adapters will retain only target-specific
effects, viewer refresh, event pumping, rendering, and capture orchestration.

This is a single behavior-preserving architecture slice. `docs/SPEC.md`, public Phase 3 CLI verbs,
DTO names, JSON keys, fixture paths, artifact paths, and current-page placement semantics remain
unchanged. The separate [phase3 nomenclature retirement plan](phase3_nomenclature_retirement_execplan.md)
remains the only place where historical naming contracts may be migrated atomically.

## Architecture selection record

- Candidate: remaining mixed scenario/effect policy in
  `src/foliaseal/presentation/qt/phase3_harness_workspace.py`.
- Candidate Priority: approximately `73.2` for the selected shape at confidence `0.92`; scan
  cluster priority was approximately `69.0` with three independent evidence records.
- Dependency category: local-substitutable/in-process. The resolver is pure domain computation;
  profile catalogs are supplied by the existing local profile-store object and tests use a fake store.
- Selected interface: common-caller optimized `Phase3HarnessScenarioResolver`, returning one immutable
  `Phase3HarnessResolvedScenario`. Shape score approximately `92`; no hybrid was justified because
  the base design already met the hard gates and no alternative addressed a five-point weakness.

```python
@dataclass(frozen=True)
class Phase3HarnessResolvedScenario:
    appearance: SignatureAppearance
    timestamp_required: bool | None
    signature_rect: SignatureRect | None

class Phase3HarnessScenarioResolver:
    def __init__(self, *, profile_store: Any) -> None: ...
    def resolve(
        self,
        *,
        profile_name: str | None,
        appearance_overrides: Mapping[str, Any] | None,
        timestamp_required: bool | None,
        signature_rect: SignatureRect | None,
        fallback: SignatureAppearance,
    ) -> Phase3HarnessResolvedScenario: ...
```

The resolver owns profile lookup, fixture/direct/text/box/visible-field override validation and
composition, including the exact existing `ValueError` messages. It imports only domain models,
the preview-stress fixture profile helper, and typing/dataclass utilities. It does not import Qt,
Pillow, pyHanko, workflows, shell bundles, or artifact/capture code.

## Migration inventory and behavior map

| Behavior | Current path/evidence | Replacement boundary | Status |
|---|---|---|---|
| Named profile fallback | `_base_appearance()` in `phase3_harness_workspace.py`; workspace adapter tests | resolver `resolve(profile_name=..., fallback=...)` | pending |
| Fixture/direct appearance overrides | `_apply_appearance_overrides()` and fixture helper; preview-matrix tests | resolver policy tests | pending |
| Text, box, and visible-field overrides | private helpers in workspace module; scenario fixtures | resolver matrix tests with exact errors | pending |
| Timestamp tri-state and signature rectangle | adapter `apply_scenario()` methods; current-page placement tests | immutable resolved scenario, adapter effects unchanged | pending |
| Headless mutation order | `HeadlessPhase3HarnessWorkspaceAdapter.apply_scenario()` | resolver then existing workflow setters | pending |
| Live mutation/refresh/event order | `QtPhase3HarnessWorkspaceAdapter.apply_scenario()` and Qt workspace tests | resolver then existing panel/session refresh and event pump | pending |
| Capture/render behavior | workspace capture tests and release matrices | unchanged; no capture code moves | preserved |

The existing shallow policy helpers may be deleted only after equivalent resolver boundary tests pass.
The `Phase3HarnessScenarioCommand`, `Phase3HarnessWorkspacePort`, capture service, and all callers
remain in their current modules. No public compatibility alias or generic command dispatcher is added.

## Baseline and predicted improvement

Baseline commit: `a1dec0e27`, clean `main`. The workspace module is 520 lines and contains both
adapters plus approximately 170 lines of scenario parsing/policy helpers. Both adapters duplicate
profile fallback and override composition before applying different workflow/testing effects.

Predicted component improvements (0–0.5 proxy scale): navigation friction `0.25`, change amplification
`0.50`, seam-risk reduction `0.50`, boundary-test improvement `0.50`, interface compression `0.50`,
cohesion `0.50`, behavioral-uncertainty reduction `0.25`; predicted Actual Improvement `0.25`.
The proxy counts compare policy call sites, duplicated helper ownership, and the number of adapter
effects that must be coordinated to test one scenario.

## Acceptance contract

- `docs/SPEC.md` remains byte-for-byte unchanged.
- Resolver module has no Qt/Pillow/pyHanko/workflow imports and imports in isolation.
- Exact validation errors, profile semantics, enum conversion, fixture profiles, timestamp tri-state,
  current-page rectangle semantics, and adapter effect ordering remain unchanged.
- `rg` shows policy helpers only in the resolver; adapters contain only resolver invocation and target
  effects. No direct profile/override parsing remains in either adapter.
- Focused resolver/workspace/matrix tests, full pytest, Ruff, diff/import isolation, CLI checks, and
  offscreen acceptance matrices pass with unchanged counts and expectations.
- Explicit temporary acceptance roots and generated repo artifacts are removed; no FoliaSeal/Python
  process or open Qt dialog remains.
- Actual Improvement is at least `0.15`, with no component regression below `-0.10`.

## Implementation steps

1. Add the resolver module and immutable result; copy policy behavior without changing messages or
   `replace()` ordering.
2. Add resolver matrix/import-isolation tests and adapter parity/effect-order tests.
3. Migrate both adapters, remove the old private policy helpers/imports, and verify the retirement grep.
4. Update architecture docs, this plan, and the parent ledger.
5. Run focused/full validation, acceptance, cleanup, and process audits; commit on `main`.
6. Start a fresh three-explorer scan after the commit.

## Out of scope

Do not rename phase3 modules/types/CLI commands, move event pumping or render/capture effects into the
resolver, redesign matrix runners, change signing policy, or alter evidence JSON/artifact contracts.

## Completion record

- [x] (2026-08-06) Added the Qt-free `Phase3HarnessScenarioResolver` and immutable
  `Phase3HarnessResolvedScenario`; both workspace adapters now resolve policy once and retain only
  target-specific workflow/testing effects, refresh, event pumping, rendering, and capture.
- [x] (2026-08-06) Migrated the four former private policy tests into resolver-boundary coverage;
  focused policy/workspace/harness/scenario validation passed `98` tests with one skipped test and
  one pre-existing Pillow warning.
- [x] (2026-08-06) Full validation passed: `1,049 passed, 11 skipped, 1 warning`; Ruff, diff checks,
  application and resolver import isolation, and CLI help checks passed.
- [x] (2026-08-06) Offscreen acceptance passed signed acceptance (`10` scenarios, `7` successful
  signings, `3` matched intentional rejections), signed preview parity (`18/18` successful), and
  signed fit rejection (`3/3` matched). The explicit `/tmp/foliaseal-scenario-policy-acceptance`
  root was removed and the FoliaSeal/Python process audit was clean.
- [x] (2026-08-06) Policy retirement grep shows the old profile/override helpers only in the new
  resolver; adapters retain only resolved target effects and event/render sequencing. Proxy measures
  are navigation friction `0.25`, change amplification `0.50`, seam-risk reduction `0.50`, boundary
  testability `0.50`, interface compression `0.50`, cohesion `0.50`, and behavioral-uncertainty
  reduction `0.25`; `Actual Improvement = 0.43` versus predicted `0.25`, with no component
  regression below `-0.10`.
- [x] (2026-08-06) Architecture documentation and parent-ledger reconciliation are complete; commit
  closure remains the final step for this child.
