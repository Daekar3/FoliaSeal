---
role: standalone
state: complete
depends_on: []
---

# Show the packaged version in About

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` current. Maintain this plan in accordance with `/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The installed FoliaSeal package currently identifies itself as `Development checkout` in Help > About. After this change, About shows the version that is bundled in the running application, such as `Version 0.1.0`. A user can then use About to identify the installed build during release review and support work.

This plan resolves a release-blocking observation from the installed-package human-in-the-loop matrix in `docs/ExecPlans/ui_installed_package_hitl_release_matrix_execplan.md`. The correction must be rebuilt into a fresh Debian package and observed in the installed application before that matrix continues.

## Child ExecPlan Dependencies

- [x] No prerequisite ExecPlans.

## Progress

- [x] (2026-09-19 22:14Z) Test-first red evidence: the new real-Qt About assertion failed against the original literal because the dialog did not contain the expected packaged version and still exposed `Development checkout`.
- [x] (2026-09-19 22:14Z) Replaced the hard-coded development label with the package version exported by `foliaseal` and added the focused real-Qt assertion that requires `Version {__version__}` and rejects `Development checkout`.
- [x] (2026-09-19 22:14Z) Green validation: the focused integration test passed; the full suite passed with `1668 passed, 20 skipped, 1 warning` (the warning is the existing Pillow warning); Ruff and `git diff --check` were clean.
- [x] (2026-09-19 22:14Z) Recorded the release-matrix failure and correction ownership in the legacy release ExecPlan.
- [x] (2026-09-19 22:14Z) Built and audited package `foliaseal_0.1.0_amd64.deb` from correction commit `158777339782b3b5b97dd28dec58f2c4e6561568`, installed it through authenticated `pkexec`, and verified clean package state.
- [x] (2026-09-19 22:14Z) Human reviewer confirmed the installed Help > About text exactly as `FoliaSeal\nVersion 0.1.0`.
- [x] (2026-09-19 22:14Z) Reconciled this plan and the release plan; the focused correction is complete and the broader release matrix resumes at its remaining HITL gates.

## Surprises & Discoveries

- Observation: The defect is a literal presentation string rather than missing package metadata.
  Evidence: `src/foliaseal/presentation/qt/support_dialogs.py` passes `FoliaSeal\nDevelopment checkout` to `AboutDialog`, while `src/foliaseal/__init__.py` exports `__version__ = "0.1.0"` and `pyproject.toml` declares the same version.

## Decision Log

- Decision: Read the displayed version from `foliaseal.__version__`.
  Rationale: The module is present in source and in the PyInstaller bundle. `importlib.metadata.version()` would depend on distribution metadata that the one-directory bundle does not intentionally include.
  Date/Author: 2026-09-19 / Codex
- Decision: Show the semantic application version in both checkout and packaged runs.
  Rationale: `__version__` identifies the running FoliaSeal code in both environments and satisfies the support contract's version alternative. The dialog does not claim that a checkout is installed. Detecting the packaging channel would add a second runtime branch that is not needed for the release defect.
  Date/Author: 2026-09-19 / Codex
- Decision: Keep version-source consolidation outside this correction.
  Rationale: Synchronizing `pyproject.toml` and `src/foliaseal/__init__.py` belongs to release tooling. The current release defect needs the smallest viable presentation change and both existing values already agree.
  Date/Author: 2026-09-19 / Codex
- Decision: Use one behavior commit followed by one release evidence/status commit.
  Rationale: Source and test changes form the behavior correction. Package build evidence and living-plan reconciliation form a separate documentation/status update after human verification.
  Date/Author: 2026-09-19 / Codex
- Decision: Record the release failure and remediation as new dated items in the legacy release plan's `Progress` section.
  Rationale: `docs/ExecPlans/ui_installed_package_hitl_release_matrix_execplan.md` predates current frontmatter and helper validation. This slice will preserve its established format instead of migrating a large active release record during a small correction.
  Date/Author: 2026-09-19 / Codex

## Outcomes & Retrospective

The correction is complete. The installed package built from the correction commit passed all three audits, installed successfully through authenticated `pkexec`, and was accepted by human observation in Help > About. The broader release matrix remains open at its unrelated HITL gates.

Verification:
- Action: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/integration/test_accessibility_acceptance.py` and `.venv/bin/python -m pytest -q`
  Result: pass
  Evidence: `Artifacts and Notes`, focused and full-suite validation record (`1668 passed, 20 skipped, 1 warning`)
- Action: `scripts/deb_package_audit.py` offline, private install-root, and display-backed audits for the corrected package
  Result: pass
  Evidence: `/tmp/foliaseal-about-version-tYIwnn/{offline,install-root,evidence}/audit.json`; display-backed `qt_platform=xcb`, `gui_startup.status=started`
- Action: authenticated `pkexec dpkg -i` followed by `dpkg --audit` and `dpkg --verify foliaseal`
  Result: pass
  Evidence: `Artifacts and Notes`, clean installed-package verification
- Action: human Help > About observation in the freshly installed package
  Result: pass
  Evidence: `Artifacts and Notes`, exact text `FoliaSeal\nVersion 0.1.0`

## Context and Orientation

`src/foliaseal/presentation/qt/support_dialogs.py` contains the small modeless support dialogs used by the application frame. Its `AboutDialog` currently supplies a literal development-checkout label to the shared `SupportDialog` text control. `src/foliaseal/__init__.py` exposes the application version as `foliaseal.__version__`. `tests/integration/test_accessibility_acceptance.py` creates the real Qt application frame with the offscreen Qt platform and already opens the About dialog, which makes it the correct place to prove the visible text.

The Debian package is a PyInstaller one-directory bundle installed through `/usr/bin/foliaseal`. Package validation has three layers: an offline extracted-package audit, a private install-root audit, and a display-backed X11 audit. The ongoing release session already used these layers for the package built from commit `ff14d7851c012bc86a24ab68d0cc5b074eb22425`. Because this correction changes bundled Python code, a new package must pass the same audits and replace the installed package before the human reviewer checks About again.

The allowed generated artifacts are the source correction, focused test evidence, a fresh Debian package in a session-owned `/tmp` directory, audit reports in that directory, and documentation/status updates in this plan and the release matrix. Do not commit the package or temporary audit output. Do not change version numbers, package layout, Help topology, dialog geometry, signing behavior, or shared layout policy in this slice.

## Milestones

First, correct and test the About text. Import `__version__` from `foliaseal` in `src/foliaseal/presentation/qt/support_dialogs.py`, format the body as `FoliaSeal\nVersion {__version__}`, and extend the existing real-Qt support-surface assertions in `tests/integration/test_accessibility_acceptance.py`. The focused test must fail against the original literal and pass after the change. Run the relevant lint check and the full test suite to establish that the presentation-only change does not affect the rest of the application.

Second, commit the behavior correction, update the owning release matrix with the observed failure and remediation state, and build a new Debian package from that exact commit. Record its source commit and SHA-256 checksum. Run the offline, private install-root, and real X11 audits against that exact artifact. Each audit must report success before installation.

Third, close the old running application, install the audited package through the already authorized desktop authentication workflow, and launch a new `/usr/bin/foliaseal gui` process with the release session's disposable HOME and XDG directories. The human reviewer opens Help > About and confirms that the dialog shows `FoliaSeal` and `Version 0.1.0`, with no `Development checkout` label. Record the result, reconcile both plans, and commit the documentation/status update. If the observation fails, keep this plan active and diagnose the installed-byte or runtime-source mismatch before the broader HITL matrix continues.

## Plan of Work

Edit `src/foliaseal/presentation/qt/support_dialogs.py` to import the public `__version__` value from the package root and use it when constructing `AboutDialog`. Do not add a fallback string: a missing package version is a build defect and must fail visibly during testing or packaging.

Edit `tests/integration/test_accessibility_acceptance.py` where the test opens `frame.show_about()`. Identify the About dialog by its `about_dialog` object name or by the returned dialog object. Assert that its plain text contains `FoliaSeal`, contains `Version 0.1.0` through the imported public version value, and does not contain `Development checkout`. Preserve the existing dialog lifecycle assertions.

Append dated items to the `Progress` section of `docs/ExecPlans/ui_installed_package_hitl_release_matrix_execplan.md`: first record that the installed About check found this defect and paused the matrix; after correction, record the new package identity, audit results, installation result, and human result. Preserve that plan's legacy format and do not claim that the current ExecPlan helper validated it. Keep this plan current after every milestone.

No architecture-document update is expected because the change uses the existing public package version and does not change a module boundary, data model, persistence contract, control flow, or external interface. The compliance review must verify that conclusion against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, `docs/UI_SPEC.md`, and the support-surface requirement in `docs/ExecPlans/ui_support_surfaces_execplan.md`.

Compliance result (2026-09-19): reviewed the affected support surface against the governing specification and architecture documentation. No architecture update is needed; this change only replaces presentation text with the existing public version constant and adds its real-Qt assertion.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`. For the source correction and focused validation, use:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/integration/test_accessibility_acceptance.py
    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/support_dialogs.py tests/integration/test_accessibility_acceptance.py
    .venv/bin/python -m pytest -q
    git diff --check

The focused test should report one passing test. Record the actual full-suite counts in `Artifacts and Notes`; do not predict or copy an older count.

Commit the behavior correction before the package build so the artifact has one exact source identity. Create a fresh task directory under `/tmp`, record the resolved package path, `git rev-parse HEAD`, and `sha256sum` result here, and run all three audits:

    package_root=$(mktemp -d /tmp/foliaseal-about-version-XXXXXX)
    .venv/bin/python -m foliaseal.build.debian_packaging --output-dir "$package_root/dist"
    deb=$(find "$package_root/dist" -name 'foliaseal_*.deb' -type f -print -quit)
    test -n "$deb"
    git rev-parse HEAD
    sha256sum "$deb"
    .venv/bin/python scripts/deb_package_audit.py "$deb" \
      --artifacts-dir "$package_root/offline"
    .venv/bin/python scripts/deb_package_audit.py "$deb" \
      --artifacts-dir "$package_root/install-root" \
      --package-manager-root "$package_root/dpkg-root"
    DISPLAY=:0 QT_QPA_PLATFORM=xcb .venv/bin/python scripts/deb_package_audit.py \
      "$deb" --artifacts-dir "$package_root/evidence" --display-backed

Expect all three reports to have an overall passed status and the display-backed report to show GUI startup `started`. Inspect the package identity with:

    dpkg-deb -f "$deb" Package Version Architecture

Close only the release session's currently running FoliaSeal process before installation. Installation is authorized only for the current release session and the host that the user already selected. A future executor without that recorded authorization must stop before the state-changing install command. Record the prior package state, install the exact audited `.deb` with the desktop-authenticated workflow, and verify the installed package:

    dpkg-query -W -f='${Status} ${Version} ${Architecture}\n' foliaseal
    pkexec dpkg -i "$deb"
    dpkg-query -W -f='${Status} ${Version} ${Architecture}\n' foliaseal
    dpkg --audit
    dpkg --verify foliaseal

The two audit commands must produce no output. Relaunch `/usr/bin/foliaseal gui` with the disposable release HOME/XDG environment. Reuse the owned directories from the active release session, or create new directories under `$package_root`, make `XDG_RUNTIME_DIR` mode `0700`, and set `DISPLAY=:0` and `QT_QPA_PLATFORM=xcb` before launch.

## Validation and Acceptance

The automated acceptance is complete when the focused real-Qt test proves the version label and rejects the stale development label, Ruff and `git diff --check` are clean, the full test suite passes, and all three package audits pass for one checksum-identical artifact built from the correction commit.

The user-visible acceptance is complete only when the human reviewer opens Help > About in the newly installed process and reports that it shows `Version 0.1.0` and does not show `Development checkout`. Source tests, screenshots, package metadata, and audit JSON cannot substitute for this installed human observation.

After acceptance, `docs/ExecPlans/ui_installed_package_hitl_release_matrix_execplan.md` resumes at the next incomplete human gate. This plan becomes `complete` only after its behavior commit, package evidence, human result, plan reconciliation, and final evidence/status commit are all recorded.

## Idempotence and Recovery

The source edit and tests are safe to repeat. Every package retry must use a new session-owned `/tmp` directory or first prove that an existing directory belongs to this slice; never select an artifact through an ambiguous wildcard. If any audit fails, do not install that artifact. Correct the failure, rebuild from the new exact commit, and repeat all three audits.

If installation is interrupted, rerun `dpkg -i` for the same audited artifact and then run `dpkg --audit` before launch. Preserve the user's package data and configuration. Do not remove the package during cleanup because FoliaSeal 0.1.0 was installed before this session. At completion, stop only session-owned processes and remove temporary package/audit roots after their essential evidence has been copied into the plans.

## Artifacts and Notes

Initial defect evidence from the installed package:

    Help > About
    FoliaSeal
    Development checkout

The package that exposed the defect was built from `ff14d7851c012bc86a24ab68d0cc5b074eb22425` with SHA-256 `76eebcc126b967f4bb587d54edc1c2cbfc51e951bc7f92b3d5861eaa906fcae8`. Its offline, private install-root, and display-backed X11 audits passed before installation. This identity establishes the failing baseline; it must not be reused as corrected evidence.

Automated correction evidence (2026-09-19): the focused real-Qt About test passed after the source correction, and the full suite completed with `1668 passed, 20 skipped, 1 warning` (the existing Pillow warning).

Corrected package evidence (2026-09-19): commit `158777339782b3b5b97dd28dec58f2c4e6561568` produced `/tmp/foliaseal-about-version-tYIwnn/dist/foliaseal_0.1.0_amd64.deb` with SHA-256 `3a34429ecbb627bc201fd1abd906ff2040be43c1b8738356760fd837d373c4ae`. Offline, private install-root, and display-backed audits passed; the display-backed audit reported Qt `xcb` startup `started`. The exact package installed successfully through authenticated `pkexec`; `dpkg --audit` and `dpkg --verify foliaseal` were clean. The build retained the known nonblocking `pycparser` generated-table and optional `libtiff.so.5` warnings.

Human acceptance evidence (2026-09-19): Help > About in the newly installed process displayed exactly `FoliaSeal\nVersion 0.1.0`; the stale `Development checkout` label was absent.

## Interfaces and Dependencies

Use the existing public constant `foliaseal.__version__: str`. `AboutDialog` remains a subclass of `SupportDialog` with its existing constructor and object name. No new runtime dependency or public API is required.

The Debian package version comes from `pyproject.toml`, while About reads `src/foliaseal/__init__.py`. They both contain `0.1.0` for this release. This slice verifies their equality through package identity and installed observation but does not remove the duplication. Future version changes must keep both values synchronized until release tooling centralizes the source.

Use PySide6 only through the existing real-Qt integration test. Use the existing `scripts/build_deb.sh` and `scripts/deb_package_audit.py` packaging boundaries. The supported release environment remains Linux Mint/Cinnamon on X11 with Qt's `xcb` platform plugin.

Revision note: Created on 2026-09-19 to resolve the installed-package About version failure before the release HITL matrix continues. Revised after plan review to define checkout semantics, make the build/audit/install steps self-contained, preserve the host-authorization boundary, and record the legacy release-plan update location.

Revision note: Activated on 2026-09-19 when test-first implementation started.

Revision note: Completed on 2026-09-19 after the corrected package was built from commit `158777339782b3b5b97dd28dec58f2c4e6561568`, audited, installed through authenticated `pkexec`, and accepted by human About observation. Existing build warnings for `pycparser` generated tables and optional `libtiff.so.5` remained nonblocking; no architecture update was needed. The broader installed-package release matrix resumes at its remaining HITL gates.
