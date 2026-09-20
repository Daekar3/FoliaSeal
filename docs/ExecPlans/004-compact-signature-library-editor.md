---
role: standalone
state: planned
depends_on: []
---

# Replace Signature Library columns with compact selectors

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` current. Maintain this plan in accordance with `/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The installed Signature Library currently gives most of its minimum-size window to two permanent navigation columns. The four-item catalog and normally small saved-object collection remain visible while the user edits, leaving the actual Appearance editor and preview cramped. After this change, catalog, saved-object selection, sort, and management actions occupy a compact header. One dominant transactional editor receives nearly all remaining space, with a stable full-width Cancel/Save footer.

A user can open Manage Reusable Signing Objects, select a catalog and saved object from compact selectors, search from the saved-object selector, manage the selected object, and edit an Appearance with a wide form and substantial sticky preview. Dirty catalog/object switches, nested Preset/Appearance editing, persistence, and object mutations retain their existing semantics. The installed-package release matrix remains paused until this corrected Library passes behavior tests, iterative image review, package audits, and human review.

## Child ExecPlan Dependencies

- [x] No prerequisite ExecPlans. Governing topology revision commit `9e66bd593` is already complete.

## Progress

- [ ] Migrate topology tests to the approved compact-header contract and prove they fail against the current three-column implementation.
- [ ] Replace permanent catalog/master columns and the active splitter with compact selectors and contextual actions.
- [ ] Preserve search, sort, selection identity, dirty transitions, nested editors, catalog-specific mutations, and preferences.
- [ ] Prove the dominant editor, sticky Appearance preview, and stable footer at 1000×650 through real-Qt geometry tests.
- [ ] Run the focused and full automated validation and complete requirements/compliance review.
- [ ] Run a bounded screenshot feedback loop for Presets and Appearance default, selected-image, and scrolled states.
- [ ] Commit the source correction, build and audit a fresh package, install it, and complete human Library acceptance.
- [ ] Reconcile this plan and the installed-package release matrix, commit final evidence/status, and resume the remaining release gates.

## Surprises & Discoveries

- Observation: The installed fresh-profile Library rendered its empty Catalog and Saved objects columns at approximately half the 1100×700 window while the active Appearance editor and preview shared the remaining width.
  Evidence: session capture `/tmp/foliaseal-about-version-tYIwnn/hitl/library-current.png`; human review rejected the layout philosophy, not only its splitter proportions.
- Observation: The application session already owns catalog selection, case-insensitive search, pinned-first sorting, selected typed references, and dirty-name state independently of Qt list widgets.
  Evidence: `src/foliaseal/application/signature_library_session.py`; code exploration before this plan.
- Observation: Splitter widths are persisted in `AppUiSettings`, but the revised `UI_SPEC.md` explicitly permits the new topology to ignore legacy saved Library column widths.
  Evidence: `src/foliaseal/infra/config/app_settings_ui.py` and `docs/UI_SPEC.md` section 12.

## Decision Log

- Decision: Use native compact combo-box selectors for both catalog and saved object.
  Rationale: There are exactly four catalogs, and the saved collections are normally small. Permanent columns consume editor space without providing proportional value. The saved-object selector will be editable so its line edit provides case-insensitive live search.
  Date/Author: 2026-09-19 / User and Codex
- Decision: Keep `SignatureLibrarySession` as the sole owner of filtering, sorting, selection, and dirty state; keep prompt presentation and transition orchestration in the Qt shell.
  Rationale: The application boundary already implements the required state behavior. Reimplementing it in Qt would create a second semantic model, while user-visible Save/Discard/Continue prompts remain presentation concerns.
  Date/Author: 2026-09-19 / Codex
- Decision: Keep the legacy `library_splitter_sizes` settings field readable but stop applying or recapturing it.
  Rationale: Ignoring the value preserves settings compatibility without retaining a dead visual mechanism. Removing the persisted field would broaden this release correction into a schema migration.
  Date/Author: 2026-09-19 / Codex
- Decision: Preserve `controls.search_input` as an alias to the editable saved-object combo's line edit during this slice.
  Rationale: The alias limits test and caller churn while the visible standalone search field is removed. It is a control reference, not a second behavior path.
  Date/Author: 2026-09-19 / Codex
- Decision: Implement a small `SearchableObjectComboBox` with an editable combo and a case-insensitive `QCompleter` popup.
  Rationale: Native editable combos do not filter their own popup reliably, and query text is not object identity. The selector uses `NoInsert`, a source item model containing display text plus typed references, a case-insensitive filter proxy, and `QCompleter` popup completion. `lineEdit().textEdited` updates the proxy and immediately opens or refreshes the completer popup while focus stays in the query field. Up/Down navigates results; Enter activates one completer result exactly once; activation commits its typed reference and restores the selected label. A small event-filter object on the line edit handles Escape by hiding the popup and restoring the selected label; focus-out without activation does the same. Typing never changes session selection or triggers a dirty prompt. Extend the Qt bindings and fakes only for `QCompleter`, the item/proxy models, `QObject`/event handling, and model-index activation required by this selector.
  Date/Author: 2026-09-19 / Codex
- Decision: Add one resolver for ordinary detail drafts before catalog/object changes and window close.
  Rationale: The application session exposes `detail_dirty`, but the current dialog resolves only nested editor dirtiness. The resolver offers Save, Discard, or Continue editing; Continue restores the prior selector state. Filtering alone is not a transition and never invokes the resolver. The implementation must clear or restore stale draft/original state instead of using `select(None)` as implicit cleanup.
  Date/Author: 2026-09-19 / Codex
- Decision: Use one Library-wide footer for generic detail, Preset, and Appearance transactions.
  Rationale: SUR03 requires one stable action area. Preset's visible `Back` becomes `Cancel` while preserving its `request_cancel` and dirty-confirmation semantics. The footer swaps the active editor's Cancel/Save actions without moving as the editor scrolls.
  Date/Author: 2026-09-19 / Codex
- Decision: Header Rename focuses and selects the active editor's Name field; it does not open a second rename dialog.
  Rationale: Names are already part of explicit Save/Cancel transactions. When a nested editor is active, Rename focuses its Name field; when generic detail is active, it focuses the generic name draft. Empty catalogs hide header New and show one primary New action in the editor, avoiding duplicate creation paths.
  Date/Author: 2026-09-19 / Codex
- Decision: Distinguish an empty catalog from a search with no matches through a nonmutating session count.
  Rationale: Empty-state creation is based on the unfiltered active catalog. A nonempty catalog with zero filtered rows keeps the query and selected editor, shows `No matches`, and never swaps to the empty-catalog New surface. Add a small session query for the unfiltered row count rather than clearing and restoring search as a side effect.
  Date/Author: 2026-09-19 / Codex
- Decision: Use at most three autonomous visual candidates, followed by one owner-authorized focused pass if needed.
  Rationale: The screenshot loop must correct material findings without turning release work into unlimited redesign. The earlier Appearance pilot used the same bounded pattern successfully.
  Date/Author: 2026-09-19 / Codex

## Outcomes & Retrospective

Implementation has not started. Completion requires installed human acceptance; source geometry tests and screenshot review cannot substitute for that gate.

## Context and Orientation

`docs/UI_SPEC.md` is the frozen interface authority. Commit `9e66bd593` revised LAY04, WF06, SUR03, resizing rules, Library scale rules, the decision log, and the normative Library/Appearance wireframes. The approved Library has a compact context header above one dominant editor. `docs/GUI_STYLE_GUIDE.md` maps this contract to native Qt behavior.

`src/foliaseal/presentation/qt/app_frame_profile_library.py` owns `ReusableObjectLibraryDialog` and `ReusableObjectLibraryControls`. Its current `_build_controls()` constructs a catalog list, a separate search field, a saved-object list, a detail column, and a three-widget `QSplitter`. Rendering and signal handlers assume list row indexes. The same class also mounts nested Appearance and Preset editors and moves their action row into a stable footer host.

`src/foliaseal/application/signature_library_session.py` owns the UI-independent state. `SignatureLibrarySession` selects catalogs and objects, filters rows, sorts them, stages a draft name, and commits or cancels detail transactions. `SignatureLibraryRow.ref` contains stable `ReusableObjectRef` or `CertificateLibraryRef` identity. The Qt migration must store those references as combo item data rather than infer identity from a filtered row index.

`src/foliaseal/infra/config/app_settings_ui.py` and `src/foliaseal/presentation/qt/app_frame.py` currently pass and store `library_splitter_sizes`. Preserve the settings schema and unrelated geometry/catalog/sort preferences, but make splitter sizes inert for the new Library. `tests/unit/test_qt_app_frame_profile_library.py` uses fake bindings for behavior, while `tests/integration/test_signature_library_topology.py` uses real Qt for composition, geometry, nested editor, and persistence evidence.

The allowed change classes are behavior change in the Qt Library shell and test fakes, evidence refresh in focused tests and visual captures, and documentation/status updates in this plan and the release matrix. Do not change catalog persistence schemas, signing semantics, object identity, certificate storage, placement coordinates, Appearance content rules, or application-layer policy. Do not create a general theme, layout metrics framework, model/view framework, or new runtime dependency.

## Milestones

First, establish red evidence for the new topology. Update focused fake-binding and real-Qt tests to require compact catalog and saved-object combo boxes, the absence of a permanent splitter/navigation column, a dominant editor, guarded live search, reference-safe activation, contextual action enablement, ordinary and nested dirty resolution, and one stable full-width footer. Add a compatibility case with stale splitter settings. Run only those focused tests and record the expected failures against the current implementation.

Second, migrate the Library shell without changing filtering or sorting policy. Replace the two lists and separate search control with a noneditable catalog combo and the `SearchableObjectComboBox` defined in the Decision Log. Its completer popup provides live filtered results while the query field retains focus; only completer activation requests an object transition. Put sort and applicable management actions in a compact header. Remove the splitter from active composition, let the editor host expand, and keep the nested-editor replacement host and Library-wide footer. A truly empty unfiltered catalog hides header New and shows one clear primary New action in the editor. A no-match query on a nonempty catalog preserves the selected editor and query and shows `No matches` without changing creation topology.

Third, preserve every existing workflow and close the existing ordinary-detail transaction gap. Add one Save/Discard/Continue resolver before activated catalog/object transitions and close. Continue restores the prior selectors and editor; filter queries do not invoke it. Run and update tests for catalog switching, live case-insensitive search, typed activation, pinned-first and certificate sorting, rename/duplicate/delete/pin, certificate actions, placement callbacks, ordinary and nested dirty prompts, nested Preset/Appearance return, selected-image staging cleanup, geometry/catalog/sort persistence, and workspace refresh. Stale splitter values must neither affect geometry nor be normalized or rewritten: capture/store/reload preserves the legacy value verbatim while no active splitter exists.

Fourth, validate composition through the `$qt-gui-work` process. Retain reproducible final evidence under `docs/visual-evidence/compact-library/`: the failing baseline, final Presets, final empty catalog, final Certificates, and Appearance default, selected-image, and substantially scrolled PNGs; matching geometry/environment JSON; and reviewer findings. Keep intermediate candidates only in an owned `/tmp` root. A visual reviewer must open the PNGs and judge hierarchy, density, clipping, wrapping, grouping, catalog-specific actions, selector/action prominence, preview usefulness, footer relationship, empty space, and native Qt coherence without pixel-matching the SVG. A material finding reopens implementation and requires equivalent recapture and re-review. Stop after three autonomous candidates; use one additional focused pass only with owner direction.

Fifth, complete release proof. After automated and visual acceptance, commit the source correction, build one fresh Debian package from that exact commit, record its checksum, and run offline, private install-root, and display-backed X11 audits. Install the exact package through the already authorized desktop-authentication workflow, launch it with disposable HOME/XDG roots, and obtain human acceptance of the compact Library, Appearance layout, keyboard focus/order, selected image, scrolling, and object edit/rename stability. Record any failure as a focused correction before the release matrix resumes.

## Plan of Work

Change `ReusableObjectLibraryControls` in `src/foliaseal/presentation/qt/app_frame_profile_library.py` so `catalog_selector` and `object_selector` are combo boxes. Keep `search_input` temporarily as the editable object combo's line edit. Retain the existing action-button fields and editor hosts. Rename the Appearance-specific footer host to a Library-wide footer host. Remove `splitter` from active behavior; it may remain as `None` in the dataclass only if that avoids unnecessary external churn.

Rewrite `_build_controls()` to create a compact header, dominant editor host, and stable footer. The header must remain usable at the 1000×650 Library minimum. Use native layout stretch and size policies. Do not add fixed control heights or local colors. Move object-management actions from the editor body to the header. Route catalog-specific New/Edit/Configure behavior through the existing callbacks and handlers.

Refactor `_render_catalog_navigation()`, `_render_master_list_contents()`, catalog/object signal handlers, `_selected_object()`, and selector helpers for combo semantics. Add a focused `SearchableObjectComboBox` module or local class with the completer/model/event behavior defined in the Decision Log; do not build a general widget framework. Store each row's typed reference in source-model item data and route only completer activation to selection. Extend fake bindings for the same observable query, completion, activation, Escape, and focus-out behavior. Popup rows may expose details through accessible text or tooltips, but essential status must also appear in the dominant editor and cannot be tooltip-only.

Add a nonmutating `SignatureLibrarySession` query for the unfiltered active-catalog row count. Use it to distinguish true empty state from zero filtered results. Searching to zero matches must not clear the selected typed reference or replace its editor; the selector popup shows `No matches` and Escape restores the selected label.

Add an ordinary-detail transition resolver around `SignatureLibrarySession.detail_dirty`. Save calls the existing explicit save boundary, Discard calls the explicit cancel boundary, and Continue leaves the draft and selection intact. Apply it to activated catalog/object changes and window close. Do not treat search filtering or sort display refresh as object transitions. Correct any stale draft/original state exposed when selection becomes absent.

Move generic detail Save/Cancel and nested Appearance/Preset actions into one footer host that spans the Library. Update `SignaturePresetEditorWidget` as needed to expose or reparent its action row in the same manner as the Appearance editor. Show `Cancel`, not `Back`, while preserving `request_cancel`. Header Rename focuses/selects the active Name field. Empty state contains the only New button; header New is hidden until the catalog has at least one row.

Stop applying and capturing splitter sizes in `ReusableObjectLibraryDialog`. Preserve `current.ui_settings.library_splitter_sizes` verbatim when capturing other settings. AppFrame may continue passing the ignored constructor value for compatibility. Do not normalize, delete, or change the serialized setting. Tests must prove a stale nondefault value survives capture/store/reload unchanged while `controls.splitter is None` and the real dialog has no `QSplitter` descendant.

Update fake combo/binding support and focused tests. Deterministically verify accessible names or label buddies for catalog, saved object, sort, and actions; logical tab order; and the full keyboard sequence: typing opens/refreshes the filtered completer popup while focus stays in the query field, Up/Down navigates, Enter activates once, and Escape restores the selected label without a transition. Prefer stable behavior and geometry assertions over exact pixel positions. Real-Qt tests must prove the editor receives most of the content width at 1000×650, header controls and footer remain visible, Appearance and Preset footer positions remain stationary while content scrolls, and no horizontal scrollbar is ordinarily required. Cover case-insensitive filtering, identical display labels with distinct typed references, selection restoration after pin/sort/rename, Continue restoration, exactly one dirty prompt for nested/header switches, true-empty creation state, and nonempty no-match state that preserves selection/query.

Update `docs/ARCHITECTURE.md`. Its repository map, Library adapter constraints, settings projection, and historical current-state notes currently describe a three-column splitter and active column-width persistence. Revise current-state claims to the compact-header topology and explain that legacy splitter widths remain readable but inert. Preserve historical facts as historical rather than rewriting what was true at their original date.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`. Start with focused red/green validation:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q \
      tests/unit/test_qt_app_frame_profile_library.py \
      tests/integration/test_signature_library_topology.py \
      tests/unit/test_signature_library_session.py

Run adjacent settings and nested-editor coverage after the first green pass:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q \
      tests/integration/test_app_frame_dirty_lifecycle.py \
      tests/integration/test_signature_library_topology.py \
      tests/unit/test_app_settings_storage.py \
      tests/unit/test_config_schemas.py \
      tests/unit/test_qt_app_frame_profile_library.py \
      tests/unit/test_qt_appearance_image_lifecycle.py \
      tests/unit/test_signature_library_session.py

Then run:

    .venv/bin/python -m ruff check src tests
    .venv/bin/python -m pytest -q
    git diff --check

For visual evidence, use an isolated synthetic catalog and the existing real-Qt capture support where practical. Record requested and actual window geometry, Qt style, application font family/size/metric height, device-pixel ratio, screen, palette, scroll position, and key region geometry. Retain the safe final PNGs, JSON, and review under `docs/visual-evidence/compact-library/`; keep intermediate candidates under an owned `/tmp` root.

After source, tests, architecture, plan progress, and retained visual evidence are committed, require `git status --short` to be empty. Build and audit from that exact clean commit in a fresh owned root:

    package_root=$(mktemp -d /tmp/foliaseal-compact-library-XXXXXX)
    .venv/bin/python -m foliaseal.build.debian_packaging --output-dir "$package_root/dist"
    deb=$(find "$package_root/dist" -name 'foliaseal_*.deb' -type f -print -quit)
    test -n "$deb"
    git rev-parse HEAD
    sha256sum "$deb"
    .venv/bin/python scripts/deb_package_audit.py "$deb" --artifacts-dir "$package_root/offline"
    .venv/bin/python scripts/deb_package_audit.py "$deb" \
      --artifacts-dir "$package_root/install-root" \
      --package-manager-root "$package_root/dpkg-root"
    DISPLAY=:0 QT_QPA_PLATFORM=xcb .venv/bin/python scripts/deb_package_audit.py \
      "$deb" --artifacts-dir "$package_root/evidence" --display-backed

Do not install unless every audit passes. Stop the old release-test process, install the exact audited artifact with `pkexec dpkg -i "$deb"`, require clean `dpkg --audit` and `dpkg --verify foliaseal`, and launch `/usr/bin/foliaseal gui` with disposable HOME/XDG paths for human review. If installed review causes any source correction, commit the correction and plan/evidence updates, restore a clean worktree, build a new package with a new recorded checksum, repeat all three audits, install that exact replacement, and repeat the affected human checks. An earlier artifact cannot be accepted after source changes.

## Validation and Acceptance

Automated acceptance requires focused and full suites, Ruff, and `git diff --check` to pass. Tests must prove compact selectors, live filtering, typed selection identity, catalog-specific actions, dirty transitions, nested editors, geometry/catalog/sort persistence, inert legacy splitter values, dominant editor width, stationary preview/footer during form scrolling, and ordinary 1000×650 reachability without horizontal scrolling.

Visual acceptance requires actual PNG inspection under equivalent conditions. The Library must no longer display permanent catalog or saved-object columns. Selectors/actions must read as a compact context header. The active editor must dominate the window. The Appearance form and preview must both be useful at minimum size, selected images must preserve aspect ratio, and scrolling must leave preview/footer stationary. Remaining whitespace must support grouping rather than reflect abandoned columns.

Installed human acceptance for this plan requires the owner to confirm the same topology in the freshly installed package under the normal system theme, logical keyboard focus order with visible focus, selected-image rendering, stable scroll/footer behavior, and responsive save/edit/same-name/rename-away-and-back workflows. That completes this topology plan and lets the installed release matrix resume. High-contrast and Orca checks remain explicit open gates in the broader release matrix and run after resumption; they are not silently claimed by this normal-theme slice.

## Idempotence and Recovery

Focused tests and captures are repeatable with isolated catalogs and HOME/XDG roots. Keep temporary screenshots, catalogs, packages, and audit output in one owned `/tmp` root per attempt. A failed visual candidate reuses the same deterministic state but receives a new candidate filename. A failed package audit blocks installation and requires a fresh build after correction.

Do not migrate or delete stored splitter settings. If the compact shell fails during implementation, restore a green source state through normal code edits; do not reset or discard unrelated work. Preserve user certificates, presets, and ordinary configuration. At session cleanup, stop only owned FoliaSeal processes and retain the installed package because FoliaSeal was installed before this task.

## Artifacts and Notes

Approved design evidence:

    Governing commit: 9e66bd593 Redesign Library around compact selectors
    Normative Library wireframe: docs/ui/signature-library-presets-exploratory.svg
    Normative Appearance wireframe: docs/ui/appearance-profile-editor-exploratory.svg

The installed failing baseline will be reproduced and retained at `docs/visual-evidence/compact-library/before-default.png` with matching JSON. The original human observation came from:

    Package source commit: 158777339782b3b5b97dd28dec58f2c4e6561568
    Package SHA-256: 3a34429ecbb627bc201fd1abd906ff2040be43c1b8738356760fd837d373c4ae
    Window: Manage Reusable Signing Objects, 1100×700 client
    Observation: permanent empty navigation/list columns consumed approximately half the window

Record test transcripts, candidate review findings, final package identity, and human result here as work proceeds.

## Interfaces and Dependencies

Use existing PySide6 widgets exposed through the project's Qt binding abstraction. The catalog and sort controls are native `QComboBox` selectors. The saved-object control is the focused `SearchableObjectComboBox` described above: editable `QComboBox`, `QCompleter`, source item model, case-insensitive filter proxy, and a small line-edit event filter for Escape/focus restoration. Expose only those Qt types through the binding surface. Do not add a custom popup unless real-Qt evidence proves this selected implementation cannot satisfy the specified keyboard and identity behavior; record and review that course change before implementation continues.

Keep `SignatureLibrarySession` and its `LibraryCatalog`, `LibrarySort`, `SignatureLibraryRow`, `ReusableObjectRef`, and `CertificateLibraryRef` contracts unchanged. Keep the existing mutation commands and nested `AppearanceProfileEditorWidget` / `SignaturePresetEditorWidget` boundaries. Add no runtime dependency.

Revision note: Created on 2026-09-19 after installed human review rejected the three-column Library philosophy and the owner approved the compact-selector governing topology in commit `9e66bd593`.

Revision note: Revised after independent plan review to define query-versus-selection signals, ordinary-detail dirty resolution, the shared footer, Rename and empty-state behavior, inert legacy splitter persistence, mandatory architecture reconciliation, deterministic accessibility checks, durable visual evidence, clean-tree package identity, and the normal-theme boundary of this focused plan.

Revision note: Revised again after re-review to select a concrete completer-backed selector with explicit keyboard/Escape/focus behavior, distinguish true empty catalogs from filtered no-match results, and require the full rebuild/audit/install/review loop after any installed correction.
