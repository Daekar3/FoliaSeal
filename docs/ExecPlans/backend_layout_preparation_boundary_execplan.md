# Centralize Backend Layout Preparation

## Purpose

Make backend signing-plan construction and draft-fit validation consume one canonical layout/fit
preparation boundary. Both paths currently repeat the same `VisibleSignatureLayoutService.prepare()` →
`_layout_fit_issues()` → fit-gate choreography, which allows a future caller to pass incomplete title
or detail text and silently diverge from the canonical signing plan. This slice removes that duplicate
coordination while preserving the existing aggregate `stamp_text` contract, stable fit issue codes and
messages, prepared-plan identity, evidence snapshots, CLI/JSON output, and all historical phase3 names.

The current evidence does not justify a second title-band geometry model: production planning, preview,
and validation already receive the semantics-composed full `stamp_text`. The durable move is therefore
to enforce one preparation path and add parity tests around signer-label-bearing multiline text. Any
future title-band DTO can build on this seam without reintroducing duplicate geometry.

## Architecture selection record

- Candidate: backend layout/fit coordination and signer-label parity in
  `src/foliaseal/application/phase3_signing_backend.py`, selected from post-cap scan 9 at Priority
  approximately `78` for the SPEC-risk cluster and corroborated by the broader backend seam scans.
- Common-caller optimized design selected, shape score approximately `90`: one private typed helper in
  the backend owns layout preparation and fit gating; `prepare_phase3_signing_plan()` remains the sole
  semantics/title source and `validate_visible_signature_fit()` becomes a thin caller.
- Minimal alternative (shape ~80): duplicate only a tiny helper without explicit parity coverage;
  rejected because it does not protect the caller contract.
- Flexible alternative (shape ~90): introduce a neutral `SignatureTextBands` and per-band reservation
  port; rejected for this slice because current production paths already pass canonical full text and
  a second geometry model would increase migration risk. It remains a future option if live evidence
  proves aggregate text metrics cannot represent the GUI title/detail contract.
- No hybrid is justified: the selected base design has no weakness requiring a five-point hybrid bonus.

## Boundary and interface

```python
def _prepare_backend_layout(
    *,
    signature_rect: SignatureRect,
    signature_appearance: SigningBackendAppearance,
    stamp_text: str,
    stamp_background: PdfImage | None,
) -> VisibleSignaturePreparation:
    ...
```

The helper uses the production `VisibleSignatureLayoutService`, the existing backend horizontal-ink
measurer, `_layout_fit_issues()`, `decide_visible_signature_fit()`, and
`apply_visible_signature_fit_gate()`. It returns the same immutable preparation consumed by
`_build_stamp_style()` and `PreparedSigningPlan`; it does not alter the `PreparedSigningPlan`,
`BackendReservationEvidence`, `VisibleSignatureLayoutRequest`, or JSON schemas.

## Behavior-preservation map

| Behavior | Before | New owner/evidence |
|---|---|---|
| Canonical signing plan | inline service prepare + fit gate after semantics | `_prepare_backend_layout()` called with the full semantics stamp text |
| Draft validation | independently repeated service prepare + fit gate | same helper; exception-to-`visible_signature_layout_unavailable` mapping unchanged |
| Rendered-ink fallback | `_layout_fit_issues()` fallback ladder | unchanged callback invoked by helper |
| Prepared plan identity | `_build_stamp_style()` requires returned plan identity | same preparation object flows through unchanged |
| Reservation evidence | `build_backend_reservation_evidence()` calls canonical plan | unchanged; parity tests compare its snapshot/error to the helper |
| Invisible signatures | early `PreparedSigningPlan` return | unchanged; helper is only for visible paths |

## Baseline and predicted improvement

Baseline commit: `6ebcfaad1`, clean `main`. `phase3_signing_backend.py` is approximately `1,540`
lines. The service-preparation/fit-gate block appears in `prepare_phase3_signing_plan()` around
lines `570–600` and again in `validate_visible_signature_fit()` around `950–985`; the two paths
must stay manually synchronized. Existing contract tests cover fit codes and evidence, but there is
no direct parity assertion proving both paths use the same prepared geometry for a nonblank signer
label plus multiline detail.

Predicted proxy improvements (0–0.5): navigation friction `0.25`, change amplification `0.40`,
seam-risk reduction `0.40`, boundary-test improvement `0.35`, interface compression `0.30`, cohesion
`0.35`, behavioral-uncertainty reduction `0.35`; predicted Actual Improvement `0.34`.

## Implementation steps

1. Add `_prepare_backend_layout()` with the exact interface above and move the duplicated service,
   ink-measurer, fit-issue, and fit-gate choreography into it.
2. Route `prepare_phase3_signing_plan()` and `validate_visible_signature_fit()` through the helper;
   preserve all public signatures, early invisible path, exception mapping, and style-plan identity.
3. Add focused tests for canonical/full stamp text with a signer label and multiline detail, parity of
   layout dimensions/fit verdicts, stable `visible_signature_layout_unavailable` errors, and evidence
   snapshot equivalence. Do not revive or broaden test-only arbitrary-text helpers.
4. Update `docs/ARCHITECTURE.md`, this plan, the parent ledger, and the stale
   `single_line_manual_harness_regressions_execplan.md` note to distinguish the resolved caller
   duplication from any future true title-band geometry work.
5. Run Ruff, diff checks, focused/full pytest, import isolation, CLI help, offscreen acceptance and
   preview parity matrices. Remove explicit temporary roots, audit processes/dialogs, and commit on
   `main`.

## Acceptance contract

- `prepare_phase3_signing_plan()` remains the only production semantics/title composition source.
- Both visible planning and draft validation use the same helper and preparation policy; no duplicate
  service/fit-gate block remains.
- `PreparedSigningPlan`, `BackendReservationEvidence`, fit issue codes/messages, CLI commands, JSON
  keys, artifact paths, and phase3 nomenclature remain unchanged.
- Focused parity tests pass for signer-label-bearing multiline text, including intentional fit errors;
  full suite and all offscreen matrices retain prior counts/expectations.
- Actual Improvement ≥ `0.15`, no component regression below `-0.10`, and the worktree/process/temp
  state is clean after commit.

## Out of scope

Do not add a title-band reservation DTO, alter `VisibleSignatureLayoutPlan` geometry, relax fit policy,
rename phase3 contracts, delete arbitrary-text test helpers without consumer migration, or redesign
the Qt preview in this slice.

## Status

- [x] (2026-08-06) Added `_BackendLayoutPreparation` and `_prepare_backend_layout()`; canonical
  signing-plan construction and draft validation now share one service/ink/fallback/fit-gate path.
- [x] (2026-08-06) Added signer-label-bearing multiline parity coverage and stable fit-error assertions;
  focused backend/layout tests passed (`136` tests including the new parity case).
- [x] (2026-08-06) Ruff, diff checks, full suite (`1,058 passed, 11 skipped, 1 warning`), application
  import isolation, CLI help, and offscreen acceptance passed. Acceptance retained `10/7/3`, `18/18`,
  and `3/3` matrix outcomes; `/tmp/foliaseal-backend-layout-acceptance` was removed and the process
  audit found no FoliaSeal/Python application process.
- [x] (2026-08-06) Updated architecture documentation and reconciled the historical manual-harness
  plan. Proxy measures are navigation friction `0.25`, change amplification `0.40`, seam-risk
  reduction `0.40`, boundary testability `0.40`, interface compression `0.35`, cohesion `0.40`, and
  behavioral-uncertainty reduction `0.35`; `Actual Improvement = 0.36` versus predicted `0.34`, with
  no component regression below `-0.10`.
- [ ] Committed on `main`; fresh three-explorer rescan started.
