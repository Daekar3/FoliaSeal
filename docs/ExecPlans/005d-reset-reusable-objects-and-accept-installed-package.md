---
role: child
state: planned
parent: 005-simplify-appearance-sizing-and-reset-reusable-signing-objects.md
depends_on:
  - 005c-simplify-qt-appearance-editing-and-previews.md
---

# Perform the authorized reusable-object reset and accept the new installed build

This is a living ExecPlan maintained under `/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The breaking release starts with no obsolete reusable objects or managed signature images. Newly created objects persist normally thereafter. Installation is accepted only when the simplified editor and actual signed output are useful on the owner desktop.

## Child ExecPlan Dependencies

- [ ] `005c-simplify-qt-appearance-editing-and-previews.md`.

## Progress

- [ ] Implement and test an explicit narrow user-context reset operation on disposable roots.
- [ ] Commit the complete source and build one clean package; pass all package audits.
- [ ] Stop relevant app sessions, reset exact authorized live stores, install and verify the exact artifact.
- [ ] Obtain installed human and ordinary-scale PDF acceptance; reconcile old plan/release matrix and commit evidence.

## Surprises & Discoveries

Current source combines a persisted manual-size/prominence model with different text-only/image preview scaling paths. The installed owner has rejected both oversized image cropping and unreadable fitted text. Source geometry/image-presence tests alone have not proved usable typography. Catalog readers also have legacy migration and loose version checks; simply deleting controls would leave old behavior loadable.

## Decision Log

The owner chose automatic text-first sizing and a complete reset rather than preserving old saved choices (conversation on 2026-10-04). No compatibility modes or migration are required. The proposed numeric policy and frozen amendments remain approval-pending until 005a records explicit approval. The implementation uses existing canonical preparation rather than another widget rendering model. Reset is an explicit user-context release step to avoid deleting newly created data on future startup.

## Outcomes & Retrospective

Planning has completed five fresh read-only reviews; identified contract, renderer, DPR and reset gaps were incorporated. The isolated five-plan family passes helper validation; directory-wide historical metadata failures remain recorded, unrelated debt. Implementation has not started; no live user data has been deleted. Owner approval of the concrete frozen packet remains required in 005a. No implementation or release pass is claimed.

## Context and Orientation

Work from `/home/daekar/FoliaSeal`. Governing authority is `docs/SPEC.md`, then `docs/SCHEMAS.md`, then `docs/UI_SPEC.md`; these documents are frozen. `docs/ARCHITECTURE.md` describes current ownership. Follow `/home/daekar/.codex/skills/write-execplan/PLANS.md`. Use the existing Python/PySide6/PyHanko/Pillow stack with no new runtime dependency. A point is 1/72 inch in PDF space. Device pixels are raster resolution, not a text-size policy. The Library minimum is 1000 by 650 logical pixels; the main window minimum is 1100 by 700.

The owner approved simplifying Appearance choices and deleting existing reusable Presets, Appearances, Placements, and their managed image assets, with no compatibility requirement. Certificates, certificate configurations, secret storage, trust settings, application preferences, source image files, recovery records, and existing PDFs are excluded. No signed PDF is rewritten. This planning request does not approve the exact proposed frozen amendments; child 005a must present them and record explicit approval before editing frozen artifacts or activating dependent implementation.

`SignaturePresetCatalogStore` in `src/foliaseal/infra/config/profile_storage.py` owns `profiles.json` at `$XDG_DATA_HOME/FoliaSeal/Signature Profiles/` (default `$HOME/.local/share/FoliaSeal/Signature Profiles/`). All reusable Presets, Appearances, Placements are in that one catalog. `ManagedSignatureImageStore` uses its `signature-images/` child directory. `Certificates/`, config/settings, recovery records, secrets and external PDFs are separate. Never delete the whole FoliaSeal data directory. Debian installation runs as root and cannot reliably choose the owner's HOME/XDG paths; do not put deletion in postinst.

The prior installed package from compact-editor correction remains an older model. Any new behavior change requires a new source commit, checksum, audits and reinstall. The current release matrix has open accessibility/human gates; this slice cannot silently close unrelated high-contrast/Orca/Wayland claims.

## Milestones

Begin only after 005a approval and completion of 005b and 005c (the metadata chain provides these transitive prerequisites). First create a simple explicitly invoked `scripts/reset_reusable_signing_objects.py` release utility, defaulting to an inventory-only mode with `--apply` required for deletion. Resolve the storage directory through the same profile-store function under the owner environment; reject relative HOME/XDG values and verify the expected FoliaSeal/Signature Profiles suffix under the resolved owner data root. Any explicit test-root override is restricted to an owned disposable temporary directory, not an unrestricted live deletion path. Dry inventory records the same absolute resolved targets later used by --apply. The command names its two targets and exclusions, removes assets before resetting the catalog, and fails clearly on any deletion error. The reset writes a new empty schema3 catalog only after owned old assets have been removed. It is not an app startup hook or compatibility migration. Repeated dry runs are safe; repeated apply is deliberately destructive and must not be automatically invoked after new data exists.

Second finish tests/commits, build a fresh Debian package and run offline/private/X11 audits. Third stop relevant FoliaSeal sessions, resolve and inventory the real owner's active HOME/XDG location, and perform the already authorized deletion exactly once for that profile. Do not guess disposable test roots are the real owner catalog. Record targets/counts/result without retaining deleted object contents. Install the audited artifact via desktop authentication, verify executable equality and clean dpkg state, restart the installed app and complete owner review. An authentication timeout blocks only the dependent installation, not audit work.

Lastly create a new Appearance and Preset, append a signature to a disposable generated PDF already containing a valid synthetic signature, verify both signatures and retained prior revision integrity, and inspect the output at an ordinary viewing scale, restart and confirm new data remains. Owner acceptance closes this child and the parent, then reconciles superseded 004 and release matrix status honestly.

## Plan of Work

Test reset with populated catalog, shared image assets, orphan images and an empty/missing store, plus relative XDG, out-of-scope override and redirected/changed symlink paths. Tests prove refusal leaves both targets and outside sentinels intact. Preserve byte-identical certificate/config/secret/recovery/PDF/source-image sentinels. Use lstat/no-follow checks for the data root and every descendant path component through FoliaSeal, Signature Profiles, catalog and image directory, revalidate before mutation, and use traversal that cannot follow replaced links. Refuse symlinked storage/targets/ancestors or unexpected target types; never follow image-directory symlinks to outside paths. No broad recursive HOME/XDG deletion or source-path image deletion. Inventory only files under the exact owned image directory, refuse unexpected subdirectories unless a known owned layout is proved, and perform deletion without retaining backups because the owner explicitly requested removal. Failed asset removal leaves the old catalog untouched and reports failure. A crash between deletion and catalog reset requires rerunning the explicit command before opening the app; no app writes may occur during the reset. Use the existing atomic catalog writer for the final empty file.

Remove legacy readers in 005b, not through an automatic startup cleanup. A restored old catalog must fail with actionable unsupported-version guidance; it must not be loaded or wiped automatically. No persistent reset marker, old-schema importer, dual-mode sizing or recurring reset runs are needed. Since schemas break, normal future startups read only the new strict shape and preserve new objects.

Record one clean source commit and package hash. Allowed generated artifacts are temporary bundle/packages/audits and sanitized release reports; personal images or old catalog content must not be committed. If installed owner review fails, reopen the responsible child, make a new commit/package and repeat audits; an earlier artifact cannot prove new source behavior.

## Proposed Shared Behavior

The proposed automatic policy tries 10, 9.5, then 9 pt, selecting the largest candidate that fits the complete actual content and any selected image. These values are application policy, never persisted Appearance properties. Measure using the exact bundled face, including bold/italic, and the actual signing text with the frozen signing time. Reserve border/margins and a text/image gap, then the required text region; give the image the maximal aspect-preserving fit in the remaining region, with its original alpha semantics; no additional prominence cap applies. Compact stays one line without truncation or wrapping; Stacked stays one visible field per line. Never omit a selected field, signing statement, or nonempty selected image to obtain a fit. A selected image must have a displayed shorter side of at least 12 PDF points; if a candidate cannot satisfy this plus text fit, try the next candidate. For Left/Right, reserve the measured text block width across the inner height and put the image region on the chosen side after the approved gap; reject text taller than the inner box. For Above/Below, reserve the measured text block height across the inner width and put the image region above/below after that gap; reject text wider than the inner box. Center the aspect-fitted image in its remaining region; retain left-aligned text and center its block on the orthogonal axis. Margins/gaps are deterministic PDF-point budgets from the canonical layout, not Qt theme pixels; the first child records their exact values before approval. No gap is reserved when either region is absent. Image-only content uses the inner box. A visible signing statement consumes text space when enabled, including image-bearing signatures, but statement-only content remains invalid under the existing meaningful-content rule. Text-only content reserves no image region. Fully transparent/empty images follow the existing meaningful-content validation, not a fabricated image reservation.

If none fits, report: `This box is too small for the selected content. Enlarge it, choose Stacked, show fewer fields, or remove the image.` Disable signing, preserve the draft, and show a non-success preview state. Unsupported glyphs remain errors, not reasons to shrink or substitute fonts. There is no upward font scaling above 10 pt. Increasing box size provides image space and whitespace rather than large text. Prefer existing native metric-derived margins and gaps; do not introduce a theme/layout framework.

The Library uses one 216 by 72 point (3 by 1 inch) synthetic example, presented at 96 logical pixels per inch: a 288 by 96 logical-pixel signature inside the preview pane. Preserve this logical display scale across DPR changes; raster at the appropriate resolution without fitting the entire stamp down to the pane. This sample is labeled `Example signature · 3 × 1 in`, uses deterministic synthetic data, and is never saved. If content does not fit this example, show explicit sample-fit guidance but allow saving a meaningful Appearance that could fit a larger real placement. Actual document fit still blocks signing. No preview zoom, sideways detail viewport, duplicate overview/detail panes, automatic box growth, or silent layout switching. The normal PDF viewer zoom remains unchanged.

## Concrete Steps

Run rendering-heavy suites and display captures sequentially. From the repository root run:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/unit
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/integration -k 'not real_offscreen_transaction_polls_without_blocking_qt'
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/integration/test_signing_transaction_progress.py::test_real_offscreen_transaction_polls_without_blocking_qt
    .venv/bin/python -m ruff check src tests scripts
    git diff --check

Expect passing tests and no new warning/failure; existing skips and the Pillow deprecation warning must be reported rather than hidden. The isolated polling command avoids the previously observed order-dependent integration hang. Do not execute destructive reset as part of an ordinary test; tests use temporary roots and preservation sentinels.

Validate the family with the source-backed helper, using a temporary Cargo target to avoid writing into the skill installation:

    CARGO_TARGET_DIR=/tmp/foliaseal-plan-helper cargo run --quiet --manifest-path /home/daekar/.codex/skills/write-execplan/helper/Cargo.toml -- check --directory docs/ExecPlans

The historical directory contains legacy plans without frontmatter. Record those pre-existing failures explicitly; validate this complete family in an isolated copy of its five files as well as individual source files, without silently migrating unrelated history. A family PASS verifies metadata/status consistency only, not correct behavior.

From a clean source commit, build and audit sequentially in a fresh owned /tmp root:

    .venv/bin/python -m foliaseal.build.debian_packaging --output-dir "$release_root/dist"
    sha256sum "$release_root/dist/foliaseal_0.1.0_amd64.deb"
    .venv/bin/python scripts/deb_package_audit.py "$deb" --artifacts-dir "$release_root/offline"
    .venv/bin/python scripts/deb_package_audit.py "$deb" --artifacts-dir "$release_root/private" --package-manager-root "$release_root/dpkg-root"
    DISPLAY=:0 QT_QPA_PLATFORM=xcb .venv/bin/python scripts/deb_package_audit.py "$deb" --artifacts-dir "$release_root/x11" --display-backed

Set release_root using mktemp -d and deb to the actual generated artifact; do not assume version0.1.0 if the approved release version changes. Expect each audit status passed and display-backed startup started. Then run the reset inventory in the owner environment, compare its exact targets to the contract, run the explicit --apply once, install the artifact with pkexec dpkg -i, run dpkg --audit and dpkg --verify foliaseal and compare installed executable to extracted payload. Launch /usr/bin/foliaseal gui after stopping the old process. No audit failure permits installation.

## Validation and Acceptance

The owner Library has zero reusable Presets/Appearances/Placements and zero old managed signature assets after reset, but all existing certificates/configurations/settings/PDFs remain. The owner can create a new Appearance with no size/prominence controls, see readable text and reasonable image scale, choose a Preset and place/sign using exactly the validated result. Test a too-small box and readable Compact/Stacked outputs. Installed keyboard/tab order, image actions, Style disclosure, scrollbar/footer, rename/edit and save workflows pass. New objects and assets survive restart with no repeating deletion. Signature verification and prior-signature integrity still pass. Human normal-scale readability is an explicit gate, not a screenshot inference.

## Idempotence and Recovery

Tests and samples use owned temporary roots. Repeat contract edits only within the approved packet and never discard unrelated changes. Source rollback uses ordinary corrective commits, not a destructive git reset. A live reset is intentionally irreversible under the owner's deletion decision; it does not preserve old-object backups. The explicit reset is never rerun after creating new objects without a new deletion request. Authentication or owner acceptance can remain pending with an exact artifact and state recorded; neither elapsed time nor successful automated tests counts as owner approval.

## Artifacts and Notes

Retain the frozen approval reference, actual measurement/raster evidence, commands/results, package identity and reset completion evidence during execution. Planned values above are not observed results. Keep owner signature artwork and personal catalogs out of repository evidence. Primary change classes are contract documentation in 005a, behavior in 005b/005c, and reset/release evidence in 005d; do not mix unrelated changes.

## Interfaces and Dependencies

The reset utility is a narrowly scoped release tool using the existing profile/image storage owners; it is not a new GUI feature or backward-compatible loader. Existing dpkg/PyInstaller/audit tools remain. User authorization for deletion is recorded here; desktop authentication is still required by the operating system. If actual storage contains an unexpected type/symlink, stop the reset with the exact target and obtain clarification rather than broadening deletion.

Revision note: Authored 2026-10-04 after owner approved the simplification and clean deletion scope; exact frozen contract changes await 005a approval.
