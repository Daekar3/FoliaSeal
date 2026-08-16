# Move Concrete Signing-Artifact Materialization Behind the Existing Layout Adapter

> **Archived completed plan (2026-08-16).** Retained for provenance; current
> work belongs to the durable acceptance/evidence owners. Do not execute as an
> active implementation queue.

This living ExecPlan follows `.agents/skills/write-execplan/PLANS.md` and the fixed architecture
loop in `docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`. It is one complete DevLoop
slice: move concrete PyHanko/Pillow artifact construction behind the existing application materializer,
add boundary tests, preserve signing and preview behavior, update documentation, validate release
matrices, clean artifacts, and commit the result.

## Purpose / Big Picture

FoliaSeal already separates neutral visible-signature geometry from target-specific materialization.
The implementation now places concrete PyHanko/Pillow artifact construction in
`visible_signature_artifact_adapters.py`; `visible_signature_layout_adapters.py` is the layout
composition edge and no longer reaches back into the 1,538-line `phase3_signing_backend.py`. This
keeps layout tests independent of unrelated certificate, TSA, and fit-policy code while preserving
the existing materializer boundary.

After this slice, the user-visible signed PDF, canonical preview, fit rejection messages, evidence
JSON, and phase3 CLI contracts remain unchanged, but the existing `SignatureAppearanceMaterializer`
boundary owns all concrete PyHanko/Pillow artifact work. A fake materializer can exercise prepared
layout behavior without loading the backend. The result is observable through import-isolation tests,
adapter boundary tests, the full suite, and the offscreen signed acceptance matrices.

## Child ExecPlan Dependencies

- [x] Parent scan round 20 found the convergent `phase3_signing_backend_deepening` cluster at
  Candidate Priority `65.99` and confidence `0.921` from two independent evidence records.
- [x] Parent Design Selection 21 compared minimal, flexible, and common-caller shapes and selected
  the existing materializer common-caller shape at Refactor Shape Score `87.7`.
- [x] Clean implementation baseline is commit `2f5f49975`; `docs/SPEC.md` hash is
  `d929e189269f0f057c6a72b43fd2d430965a975be720b55139fdb1d92afe282b`.
- [x] Existing layout, preview, backend, evidence, and signing tests characterize the behavior to
  preserve; no frozen SPEC or phase3 external contract is being changed.

## Progress

- [x] (2026-08-06) Created this self-contained plan after Scan Round 20 and Design Selection 21.
- [x] (2026-08-06) Completed preimplementation reconnaissance of the materializer protocol,
  concrete backend helpers, lazy imports, callers, tests, and compatibility aliases.
- [x] (2026-08-06) Moved concrete PyHanko/Pillow artifact implementations into the new
  `visible_signature_artifact_adapters.py` module; the existing layout adapter now consumes the
  concrete engine/style helpers without importing `phase3_signing_backend`.
- [x] (2026-08-06) Removed the backend's dead template-layout helper functions and moved the workflow's
  image-background import to `application.stamp_background`.
- [x] (2026-08-06) Preserved neutral layout policy, backend fit orchestration, plan identity, and
  public behavior while the focused suite passed 246 tests; migrated moved-helper tests to the new
  owner and removed the now-unused backend compatibility aliases.
- [x] (2026-08-06) Updated `docs/ARCHITECTURE.md` to record concrete artifact-adapter ownership,
  the one-way dependency into neutral layout, and the dated backend-delegate retirement criterion.
- [x] (2026-08-06) Added direct owner-boundary tests for concrete metrics, import isolation, exact-once
  materializer memoization, and option propagation.
- [x] (2026-08-16) Compliance review, full/offscreen validation, documentation update, cleanup,
  measurement, commit, and architecture rescan are recorded in the completed outcomes below;
  implementation commit `cf1a8d0a1` is archival.

## Surprises & Discoveries

The typed boundary already exists. `SignatureAppearanceMaterializer` in
`visible_signature_layout.py` and the memoized `VisibleSignaturePreparation.signing()` and
`preview()` methods are the dominant common caller; introducing a second artifact request/result
port would duplicate an existing lifecycle and is explicitly rejected by Design Selection 21.

The pre-extraction adapter imported `PyHankoSignatureTextBoxEngine`, `RoundedBorderTextStampStyle`,
`_hex_to_rgb`, and `_solid_background_for_color` from `phase3_signing_backend.py` inside methods.
That dependency-direction defect is now addressed by the dedicated artifact adapter; remaining
backend names are intentionally thin compatibility delegates until the documented retirement grep
is clean. The move preserves the exact half-point font-size handling, extra multiline height point,
rounded-border PDF command stream, color conversion, and error strings.

## Decision Log

- Decision: reuse `SignatureAppearanceMaterializer` instead of adding a new artifact port.
  Rationale: it is already the stable application boundary and exact-once common caller for both
  signing and canonical preview; a second DTO/protocol would broaden migration and duplicate
  `VisibleSignaturePreparation`. Date/Author: 2026-08-06, Codex.
- Decision: move only concrete artifact construction. Rationale: certificate semantics, signer/TSA
  handling, rendered-ink fallback, fit policy, `PreparedSigningPlan`, and evidence snapshots remain
  behavior-bearing backend responsibilities and must not move with the adapter. Date/Author:
  2026-08-06, Codex.
- Decision: retain backend concrete names as thin compatibility wrappers during this slice.
  Rationale: existing tests and internal callers still import some names; wrappers are safe only with
  the explicit retirement criterion that `rg` shows no first-party consumers after migration. Date/
  Author: 2026-08-06, Codex.

## Outcomes & Retrospective

Implementation and validation evidence (2026-08-06):

- Focused suite: `249 passed` across layout, boundary, preview, backend, and draft-workflow tests.
- Full suite: `1,094 passed`, one pre-existing Pillow deprecation warning, no new skips or failures.
- Import firewall: both `visible_signature_layout_adapters.py` and
  `visible_signature_artifact_adapters.py` contain no backend import; isolated subprocess imports
  confirm neither adapter loads `phase3_signing_backend`.
- Boundary behavior: direct artifact-owner tests cover half-point font metrics, multiline height
  correction, color/font resolution, exact-once signing/preview materialization, prepared-plan identity,
  and option propagation. The existing style/error/layout suites remain green.
- Offscreen evidence: signed acceptance `10` scenarios / `7` successful signings; preview parity
  `18/18`; fit rejection `3/3`.
- Cleanup: the exact evidence root, summary, and canonical-preview directories were removed; the
  post-run process audit found no FoliaSeal/Python/Qt process outside the active Codex sandbox.
- Cruft removal: dead backend template-layout helpers and all moved concrete-helper compatibility
  aliases were removed after `rg` found no first-party consumers; image loading is imported directly
  from `application.stamp_background`.
- Conservative Actual Improvement measurement using the same boundary inventory: navigation `0.00`
  and change amplification `0.00` (not claimed without a repeatable unit count), seam reduction
  `1.00` (two adapter-to-backend imports to zero), boundary-test improvement `0.50` (`0.25` to
  `0.75` inventory fraction), interface compression `0.50` (moved helper entry points no longer
  exposed by the backend), and boundary isolation `1.00` (two forbidden adapter paths to zero).
  Weighted Actual Improvement is `0.46`, above the `0.15` gate and the predicted `0.42`, with no
  component below `-0.10`.
- Independent post-first-pass review found no unresolved critical or major findings after the docs,
  owner-boundary tests, direct import migration, and compatibility cleanup were applied.

Commit: `cf1a8d0a1` (`Extract visible-signature artifact adapters`). Fresh Scan Round 23 found no
remaining critical or major issue in this slice; the next candidate is recorded in the parent loop
ledger. This child is complete.

## Context and Orientation

`src/foliaseal/application/visible_signature_layout.py` owns neutral visible-signature geometry,
fit reservations, and the `SignatureAppearanceMaterializer` protocol. Its
`VisibleSignaturePreparation` stores one immutable layout plan and lazily memoizes concrete signing
or preview materialization. `src/foliaseal/application/visible_signature_layout_adapters.py` is the
layout composition edge for Pillow image probing and plan-to-artifact bridging;
`visible_signature_artifact_adapters.py` owns the concrete PyHanko/Pillow text, style, color, and
background materializers.

`src/foliaseal/application/phase3_signing_backend.py` owns certificate loading, signing semantics,
TSA behavior, rendered-ink fallback, fit-gate orchestration, and stable evidence/error contracts. Its
historical concrete `RoundedBorderTextStamp`, `RoundedBorderTextStampStyle`,
`PyHankoSignatureTextBoxEngine`, `_hex_to_rgb`, `_solid_background_for_color`, and related PyHanko
helpers now live in `visible_signature_artifact_adapters.py`; backend exports remain thin delegates
only while first-party consumers remain.
The backend must continue to call `_prepare_backend_layout()` and consume
`preparation.signing().stamp_style` exactly as before.

`src/foliaseal/application/signing_preview_renderer.py` and the Qt harness use the same prepared
layout path for WYSIWYG preview. `tests/unit/test_visible_signature_layout.py`,
`tests/unit/test_visible_signature_layout_boundary.py`, `tests/unit/test_signing_preview_renderer.py`,
and `tests/unit/test_phase3_signing_backend.py` characterize style, text metrics, layout rules, fit
fallbacks, evidence, and signed output. The phase3 nomenclature retirement remains a separate atomic
plan and is out of scope here.

## Plan of Work

First inventory all consumers with `rg` before moving code. Create no second materializer service.
Move `RoundedBorderTextStamp` and `RoundedBorderTextStampStyle` together into the concrete adapter
module (or a tightly owned concrete helper imported only by that adapter), along with the PyHanko
text-box engine implementation, font-family resolution helpers, `_hex_to_rgb`, solid-color
background creation, and any private support required by their exact behavior. Keep imports one-way:
the adapter may import neutral layout/domain types, Pillow, and PyHanko; it must not import
`phase3_signing_backend`.

Keep the existing public-shaped adapter methods and protocol. `PyHankoTextMeasurer.measure()` must
continue returning `TextMetrics`; `PillowStampImageProbe.inspect()` must preserve missing/unreadable
image errors; `PyHankoSignatureAppearanceAdapter.build_stamp_style()` must validate fit issues,
consume the supplied `layout_plan` without replanning, preserve border/background flags, and return
an object exposing `inner_content_layout` and `background_layout`. Keep the existing
`application.stamp_background` loader as the single image-background owner; first-party callers now
target it directly and the backend no longer carries an image-loader compatibility export.

Remove old backend concrete names once `rg` proves no first-party consumers remain; this slice has
completed that migration for the extracted helpers. The backend's `_build_stamp_style()` must remain a plan-identity and fit-gate
guard that returns `preparation.signing().stamp_style`; it must not construct a second style. Update
all production imports to target the adapter boundary and keep the invisible-signature path free of
materializer calls.

Add boundary tests with a fake materializer that records requests and returns an opaque artifact with
the two required layout attributes. Verify exact-once memoization, prepared-plan identity, fit-error
short-circuiting, preview stamp suppression, option propagation, and that importing neutral layout
modules does not load the backend, Pillow, or PyHanko. Extend concrete adapter tests for half-point
fonts, multiline height correction, image errors, background/layout rules, and rounded-border style
parity. Preserve existing backend compatibility tests until the retirement grep is clean.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`.

    rg -n "PyHankoSignatureTextBoxEngine|RoundedBorderTextStamp|_hex_to_rgb|_solid_background_for_color|stamp_background_for_path|phase3_signing_backend" src/foliaseal/application tests
    .venv/bin/pytest -q tests/unit/test_visible_signature_layout.py tests/unit/test_visible_signature_layout_boundary.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py
    .venv/bin/ruff check src tests scripts

After migration, run the focused boundary suite, then `.venv/bin/pytest -q`, CLI help, subprocess
import isolation, and `git diff --check`. Run the release evidence command with
`QT_QPA_PLATFORM=offscreen` under the exact temporary root `/tmp/foliaseal-artifact-boundary-evidence`.
Record signed acceptance `10` scenarios with `7` successful signings, preview parity `18/18`, and fit
rejection `3/3`, then remove that root, all canonical-preview directories created by this run, and any
summary file. Audit for active FoliaSeal/Python/Qt processes before commit.

## Validation and Acceptance

Acceptance requires no adapter-to-backend import, no neutral application import of Pillow/PyHanko,
unchanged `SignatureAppearanceMaterializer` behavior, exact plan identity and memoization, preserved
text metrics/style bytes/layout rules/error messages, unchanged rendered-ink fit policy and signing/TSA
semantics, and no phase3 CLI/DTO/JSON/fixture/artifact changes. All inventoried production callers must
use the existing materializer boundary; compatibility wrappers may remain only with the explicit grep
retirement criterion. New boundary tests and the full preexisting suite must pass with no added skips,
disabled tests, or weakened assertions. Documentation must describe adapter ownership accurately.

The baseline suite at commit `2f5f49975` is `1,093` tests with one pre-existing Pillow warning. The
candidate inventory before implementation is: nine tracked files mention the concrete artifact helper
names; two production files (`visible_signature_layout_adapters.py` and `phase3_signing_backend.py`)
coordinate the concrete materialization; three neutral/application modules must be followed to explain
the prepared-style path; 28 source/test references mention the materializer entry points; and two
adapter methods directly import the backend. The baseline boundary-test fraction is `0.25` because
existing tests characterize concrete styles but no fake materializer verifies the application protocol.
The baseline proxy vector is navigation `0.25`, change amplification `0.25`, seam reduction `0.00`,
boundary-test improvement `0.25`, interface compression `0.25`, and boundary isolation `0.00`.

Predicted component improvement is navigation `0.35`, change amplification `0.45`, seam reduction
`0.45`, boundary-test improvement `0.40`, interface compression `0.35`, and boundary isolation `0.55`,
for predicted Actual Improvement `0.42` using the fixed weights. Recompute from the same inventory
after migration; if a proxy cannot be measured credibly, record zero rather than inventing a value.

## Idempotence and Recovery

The migration is additive until boundary tests pass: move concrete implementations, retain delegates,
then remove only demonstrably unused duplicates. If a circular import appears, do not restore an
adapter-to-backend import; move the smallest concrete helper into the adapter-owned module or return
once to design selection. If rendered output differs, compare the old and new style stream/layout
snapshots and repair the adapter before changing expectations. Temporary evidence cleanup uses only the
exact named roots and canonical-preview prefixes created by this run.

## Artifacts and Notes

Persistent artifacts are this child plan, the parent ledger, source/test/doc changes, and commits.
Generated PDFs, PNGs, certificates, JSON summaries, and CLI transcripts are temporary evidence only and
must be removed before commit. `docs/SPEC.md` and all phase3 external names remain frozen.

## Interfaces and Dependencies

The application protocol remains:

    class SignatureAppearanceMaterializer(Protocol):
        def build_stamp_style(
            self,
            *,
            appearance: VisibleSignatureAppearancePort,
            stamp_text: str,
            stamp_background: object | None,
            signature_rect: SignatureRect,
            layout_plan: SignatureLayoutPlan,
            allow_fit_issues: bool = False,
            include_border: bool = True,
            include_background: bool = True,
        ) -> object: ...

The concrete `PyHankoSignatureAppearanceAdapter` implements this protocol. Its returned object must
provide `inner_content_layout` and `background_layout`; these remain opaque to neutral layout policy.
`PyHankoTextMeasurer`, `PillowStampImageProbe`, `materialize_background_layout`, and
`pyhanko_layout_rule_from_spec` remain concrete adapter helpers. `SignatureTextBoxEngine` and
`PreviewRasterRenderer` are existing application ports; do not introduce a second artifact registry,
service locator, or public PyHanko/Pillow type into neutral modules. `phase3_signing_backend.py` may
retain thin compatibility delegates until the explicit `rg` inventory proves they can be deleted.

Revision note: created 2026-08-06 after Scan Round 20 and Design Selection 21. The plan intentionally
reuses the existing materializer boundary rather than adding a parallel artifact protocol.
