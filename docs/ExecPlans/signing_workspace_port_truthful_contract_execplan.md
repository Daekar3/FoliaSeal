# Make the signing workspace port contract truthful

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the shell-owned workspace port in `src/foliaseal/presentation/qt/signing_shell_port.py` will tell the truth about what it returns. A contributor or caller reading the contract will see that `refresh_certificate_configurations()` returns the live `CertificateCatalog` produced by the shell instead of claiming it returns nothing. The visible application behavior does not change: `File > Save As...`, live application-settings propagation, and certificate-refresh flows still work the same way.

The user-visible proof is test-based. Focused app-frame and workspace-open tests must continue to pass, and a new forwarding regression must prove that `QtSigningWorkspacePort` preserves `widget()`, `choose_output_pdf_path()`, `apply_app_settings(...)`, and `refresh_certificate_configurations()` exactly as exposed by the concrete shell widget.

## Child ExecPlan Dependencies

- [x] (2026-06-22 22:20Z) `docs/ExecPlans/signing_workspace_shell_port_ownership_execplan.md` is already complete; the shell owns the workspace bootstrap/port/factory seam before this tracer-bullet correction begins.
- [x] (2026-06-22 22:20Z) No child ExecPlans are required for this bounded contract-correction slice.

## Progress

- [x] (2026-06-22 22:20Z) Re-read `src/foliaseal/presentation/qt/signing_shell_port.py`, `tests/unit/test_qt_app_frame.py`, `tests/unit/test_qt_app_frame_workspace_open.py`, and the relevant `docs/ARCHITECTURE.md` entries to confirm the current live contract and callers.
- [x] (2026-06-22 22:20Z) Completed the required `explorer-light` dev-loop audit and fixed the first slice at a truthful return-type correction plus forwarding coverage, not the broader harness seam.
- [x] (2026-06-22 22:22Z) Updated `SigningWorkspacePort` and `QtSigningWorkspacePort` so `refresh_certificate_configurations()` returns `CertificateCatalog`, and the adapter now returns the concrete shell result instead of discarding it.
- [x] (2026-06-22 22:24Z) Added focused tests proving the concrete port adapter forwards `widget()`, `choose_output_pdf_path()`, `apply_app_settings(...)`, and `refresh_certificate_configurations()` unchanged, and aligned the workspace-open test fakes to the truthful return contract.
- [x] (2026-06-22 22:24Z) Ran focused validation with `.venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py`, `.venv/bin/python -m ruff check ...`, and `git diff --check`; all passed.
- [x] (2026-06-22 22:24Z) Re-read `docs/ARCHITECTURE.md` and `docs/SPEC.md`; no wording change was required because both already describe the live shell-port seam behaviorally rather than with the stale `None` type.
- [x] (2026-06-22 22:24Z) Completed the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan. No follow-on corrective slice was required.
- [ ] Create the git commit for the finished slice.

## Surprises & Discoveries

- Observation: the narrow workspace port is already behaviorally correct, but its type contract is stale.
  Evidence: `src/foliaseal/presentation/qt/signing_shell_port.py` declares `SigningWorkspacePort.refresh_certificate_configurations() -> None`, while `signing_workspace_shell_surface.py` and `signing_shell.py` return `CertificateCatalog`.

- Observation: the existing app-frame tests already prove the broad production seam and only lack a direct forwarding assertion for the concrete port adapter.
  Evidence: `tests/unit/test_qt_app_frame.py` already verifies `QtSigningWorkspaceFactory().create(...)` delegates to `build_qt_signing_shell(...)`, and `tests/unit/test_qt_app_frame_workspace_open.py` already proves the app-frame workspace-open path installs and uses a shell port.

- Observation: one workspace-open fake port still mirrored the stale `None` contract even after the production port was corrected.
  Evidence: the compliance review found `tests/unit/test_qt_app_frame_workspace_open.py` still returned `None` from the fake `refresh_certificate_configurations()` method; updating the fake kept the test boundary aligned with the truthful contract without changing production behavior.

## Decision Log

- Decision: keep the first dev-loop slice at the truthful production-port contract instead of beginning with the Phase 3 harness seam.
  Rationale: the explorer audit found that the production port already exists and only needs a small correctness fix plus direct forwarding coverage, while the harness seam still depends on broad shell anatomy and would widen risk immediately.
  Date/Author: 2026-06-22 / Codex

- Decision: do not rename interfaces or change export ordering in this slice.
  Rationale: `signing_workspace_composition.py` still installs compatibility exports before the narrow shell surface, and changing that wiring would mix a broader behavior change into what should remain a contract-correction slice.
  Date/Author: 2026-06-22 / Codex

## Outcomes & Retrospective

This slice is implemented and validated. The shell-owned workspace port now truthfully advertises that certificate-refresh returns a `CertificateCatalog`, the concrete adapter returns that catalog unchanged, and focused tests prove the port forwards the full four-method production contract.

No architecture or spec changes were needed because the documentation already described the seam behaviorally. The only follow-on that surfaced during compliance review was a stale fake return type in `tests/unit/test_qt_app_frame_workspace_open.py`; that was corrected inside the slice, so no separate cleanup plan is required for this tracer bullet.

## Context and Orientation

The signing workspace boundary between the Qt app frame and the concrete signing shell lives in `src/foliaseal/presentation/qt/signing_shell_port.py`. In this repository, a “port” means a narrow interface that one module depends on instead of depending directly on a large concrete object. `SigningWorkspaceBootstrap` carries the workflows, settings, stores, and callbacks required to build one live signing workspace. `QtSigningWorkspaceFactory` calls `build_qt_signing_shell(...)` and wraps the returned concrete widget in `QtSigningWorkspacePort`.

The narrow production port is intentionally small. `app_frame.py` uses it for four behaviors: central-widget installation through `widget()`, save-as routing through `choose_output_pdf_path()`, live settings propagation through `apply_app_settings(...)`, and certificate-configuration refresh through `refresh_certificate_configurations()`. The concrete shell already returns a `CertificateCatalog` from that last method because `signing_workspace_shell_surface.py` forwards the catalog returned by `SigningWorkspaceActionBridge.refresh_certificate_configurations()`. The stale part is only the protocol and adapter type contract in `signing_shell_port.py`, which still says `None`.

The relevant test owners are `tests/unit/test_qt_app_frame.py`, which already exercises the shell-owned factory and app-frame seam, and `tests/unit/test_qt_app_frame_workspace_open.py`, which already verifies that workspace-open composition produces a shell port and compatibility state. This slice should not widen into `phase3_harness_workspace.py`, `signing_workspace_compatibility_surface.py`, or a generic shell-surface cleanup.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/signing_shell_port.py`. Import `CertificateCatalog` from `foliaseal.infra.config.schemas`, then change both `SigningWorkspacePort.refresh_certificate_configurations()` and `QtSigningWorkspacePort.refresh_certificate_configurations()` to return `CertificateCatalog`. The adapter implementation must return the result of `self.shell_widget.refresh_certificate_configurations()` instead of discarding it.

Second, strengthen the focused tests. In `tests/unit/test_qt_app_frame.py`, add or extend a direct forwarding regression for `QtSigningWorkspacePort` or `QtSigningWorkspaceFactory` that proves all four production methods delegate unchanged to the concrete shell widget. If needed, adjust `_FakeShell` so it returns a sentinel catalog and records the received settings. In `tests/unit/test_qt_app_frame_workspace_open.py`, only make compatibility adjustments if the fake port type signatures need to return the catalog to match the truthful contract; do not broaden those tests into shell internals.

Third, run focused validation. Use app-frame and workspace-open tests as the main proof, and run a targeted `test_qt_signing_shell.py` subset only if changing the adapter or fake shell plumbing requires it. After tests and lint pass, review `docs/ARCHITECTURE.md` to see whether any wording still implies the stale `None` contract. In the implemented slice, no wording change was needed because the docs already describe the seam behaviorally.

Finally, run the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan. If the review finds a mismatch, fix only the mismatch inside this slice and record the decision here before creating the final commit.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Update the truthful port contract and adapter forwarding.

       apply_patch ... on src/foliaseal/presentation/qt/signing_shell_port.py

2. Add focused forwarding coverage and adjust any fakes to match the truthful contract.

       apply_patch ... on tests/unit/test_qt_app_frame.py
       apply_patch ... on tests/unit/test_qt_app_frame_workspace_open.py

3. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_shell_port.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py
       git diff --check

4. If shell export plumbing is touched indirectly, run the narrow shell regression subset.

       .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py -k "named_compatibility_surface or choose_output_pdf_path or refresh_certificate_configurations"

5. Reconcile `docs/ARCHITECTURE.md` and this plan if needed, rerun any affected checks, then complete the compliance review and create the commit.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `SigningWorkspacePort.refresh_certificate_configurations()` truthfully advertises a `CertificateCatalog` return value.
- `QtSigningWorkspacePort.refresh_certificate_configurations()` returns the live catalog instead of discarding it.
- a focused regression proves that the concrete port adapter forwards `widget()`, `choose_output_pdf_path()`, `apply_app_settings(...)`, and `refresh_certificate_configurations()` unchanged.
- the app-frame workspace-open path still installs and consumes a shell port without behavioral changes.
- no harness, compatibility-surface, or shell-export rewiring is mixed into this slice.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_shell_port.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py
    git diff --check

If shell export plumbing changes unexpectedly, also run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py -k "named_compatibility_surface or choose_output_pdf_path or refresh_certificate_configurations"

Acceptance is behavioral and typed. The application should behave the same, but the narrow contract must now match the real return value.

## Idempotence and Recovery

This is a behavior-preserving contract correction inside local Qt code. It is safe to retry. If a test fails because a fake shell or fake port still returns `None`, update the fake to return a sentinel `CertificateCatalog` rather than changing the production port back to the stale contract.

If a type-only change unexpectedly reveals a broader shell wiring issue, stop at the adapter boundary and fix only the missing forwarding. Do not recover by widening this slice into `phase3_harness_workspace.py`, `signing_workspace_compatibility_surface.py`, or app-frame behavior changes.

## Artifacts and Notes

The key evidence for this slice is:

- a diff in `src/foliaseal/presentation/qt/signing_shell_port.py` showing the truthful `CertificateCatalog` return type and adapter return statement;
- a focused test proving `QtSigningWorkspacePort` forwards the four production methods unchanged;
- passing focused validation output for app-frame and workspace-open tests;
- the compliance result that `docs/ARCHITECTURE.md` and `docs/SPEC.md` already match the implemented behavior, so no doc patch was required.

Expected validation evidence after implementation:

    $ .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py
    ...................                                                      [100%]
    19 passed in 0.37s

    $ .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_shell_port.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py
    All checks passed!

    $ git diff --check
    <no output>

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the shell-owned interface family must include:

    from foliaseal.infra.config.schemas import AppSettings, CertificateCatalog

    class SigningWorkspacePort(Protocol):
        def widget(self) -> Any: ...
        def choose_output_pdf_path(self) -> str | None: ...
        def apply_app_settings(self, settings: AppSettings) -> None: ...
        def refresh_certificate_configurations(self) -> CertificateCatalog: ...

    @dataclass(frozen=True)
    class QtSigningWorkspacePort:
        shell_widget: Any

        def refresh_certificate_configurations(self) -> CertificateCatalog:
            return self.shell_widget.refresh_certificate_configurations()

The fake shell and fake port types used by the focused app-frame tests should match that truthful contract. This slice must not introduce a harness-facing port yet; that is a later dev-loop on the broader hybrid direction.

Revision note: Created on 2026-06-22 by Codex as the first `dev-loop` tracer bullet for the proposed hybrid signing-workspace boundary. The slice intentionally corrects the narrow production port contract before wider harness extraction begins.
