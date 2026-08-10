# FoliaSeal V1 SPEC and UI_SPEC Compliance Parent Plan

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It governs the dependency-ordered child plans that
implement the frozen product contract in docs/SPEC.md and docs/UI_SPEC.md.

In this document, AFK means “agent can implement and validate without a pending human product
decision.” A Qt port is a small typed interface between application behavior and Qt widgets. A
compatibility surface is an adapter retained only for old callers. “phase3” is legacy evidence or
harness nomenclature, not a product feature name. A vertical slice is one complete path from stored
data through application logic and the GUI to a user-observable result. A red test is a focused test
that fails before the behavior exists; green means it passes after implementation. CRUD means create,
read, update, and delete. PKCS#12 is the password-protected certificate bundle format used by
`.p12`/`.pfx` files. A glyph is one rendered character shape; DPI is display pixel density;
headless means without a display; and display-backed means running with a real display for human
interaction or screenshots.

## Purpose / Big Picture

After this parent plan is complete, a non-expert user will be able to launch FoliaSeal as a
document-centric Linux desktop application, review one PDF, create and select reusable signing
objects, place one visible approval signature by pointer or keyboard, preview the exact signed
appearance, sign and save safely, verify locally, and reopen the result for another approval when
permissions allow. Each child is a thin vertical slice with an observable user outcome; no child
is merely a horizontal refactor.

The governing documents are already written and frozen. This plan implements their requirements; it
does not silently revise them. The persistent model remains governed by docs/SCHEMAS.md. Existing
compatibility paths, manual-assembly paths, and product-facing phase3 labels may be removed when a
child migrates their consumers, provided the child records the retirement evidence.

This parent and its 29 `ui_*` children are the active UI implementation corpus. Older `gui_*`,
`phase3_*`, and completed migration plans elsewhere in `docs/ExecPlans/` are historical records or
superseded slices unless this parent names them as a prerequisite. Their retrospective dependency
notes are not additional execution edges; do not select one as active work without first marking its
status and reconciling it with this parent.

## Child ExecPlan Dependencies

The following children are grouped into dependency tranches. A child may begin only when its listed
predecessors are checked off in this parent and in the child plan itself. The foundation tranche is
deliberately small: it settles application startup, typed restart settings, and placement storage
before any reusable-object or signing UI is allowed to persist data.

Foundation tranche:

- [x] docs/ExecPlans/ui_launch_no_document_execplan.md
- [ ] docs/ExecPlans/ui_command_model_shortcuts_execplan.md
- [x] docs/ExecPlans/ui_zoom_command_surface_execplan.md — typed View Zoom In/Out/Reset actions
  route through the public workspace session port; broader View Back/Forward and remaining command
  families remain open with their owning children.
- [x] docs/ExecPlans/ui_signing_rail_stage_status_execplan.md — fixed 320px signing rail, protected
  read-only status region, typed recommended action, and offscreen geometry evidence are complete
  in `8d67d1652`; asynchronous/state-machine follow-up remains open.
- [x] docs/ExecPlans/ui_window_theme_responsive_execplan.md — fixed rail/window theme and responsive
  geometry implementation and focused/full validation are complete; final acceptance remains in the
  product-support/release tranche.
- [x] docs/ExecPlans/ui_placement_editor_transaction_execplan.md

Document-flow tranche:

- [ ] docs/ExecPlans/ui_single_instance_open_routing_execplan.md
- [ ] docs/ExecPlans/ui_document_lifecycle_recovery_execplan.md
- [x] docs/ExecPlans/ui_pdf_navigation_zoom_pan_execplan.md — typed fit, zoom, pan, and navigation
  behavior is implemented and validated; final handoff status is reconciled here.
- [x] docs/ExecPlans/ui_document_search_selection_execplan.md — bounded text search, selection,
  highlighting, copy, and keyboard traversal are implemented and validated; final handoff status is
  reconciled here.
- [x] docs/ExecPlans/ui_document_signatures_review_execplan.md — bounded signature projection and
  modeless review surface are committed; the bounded later-approval permission gate is now covered
  by the verification-recovery child, while broader reopen/display policy remains open.
- [ ] docs/ExecPlans/ui_safe_links_external_changes_execplan.md
- [x] docs/ExecPlans/ui_pdf_link_inspection_execplan.md — neutral QtPdf link extraction and
  PDF-space rectangle normalization are implemented; activation and reload remain with safe-links.
- [x] docs/ExecPlans/ui_safe_links_source_safety_contracts_execplan.md — pure destination safety
  and source-change decision contracts are implemented and tested; renderer and draft-preserving
  workspace integration remain open in the safe-links and lifecycle children.
- [x] docs/ExecPlans/ui_safe_links_contract_hardening_execplan.md — conservative unknown-source,
  mode-gating, malformed-destination, and bounded-display corrections implemented and validated
  (24 focused; 1342 full-suite; committed in `45e5187d2`).

Reusable-object and certificate tranche:

- [x] docs/ExecPlans/ui_signature_library_topology_execplan.md — bounded modeless topology, catalog
  navigation/search, certificate projection, and transactional name draft landed; nested editors,
  certificate create/import/configure flows and dirty prompts remain open; catalog
  pin/duplicate/name/sort behavior is covered by the completed follow-on child.
- [x] docs/ExecPlans/ui_catalog_search_sort_pinning_execplan.md — persistent pins, duplicate
  semantics, normalized names, configured-first certificate projection, Name sorting, certificate
  pin/rename/delete routing, confirmation-safe mutation lifecycle, expiration preference propagation,
  and Library preferences validated in the current follow-up slice.
- [x] docs/ExecPlans/ui_signature_preset_transactions_execplan.md — production Preset Create/Edit
  now uses the Library-owned nested Preset → Appearance editor path with child-first resolution,
  stable-reference return, and full focused/offscreen regression evidence.
- [x] docs/ExecPlans/ui_appearance_editor_transaction_execplan.md
- [x] docs/ExecPlans/ui_first_use_preset_setup_execplan.md — empty-preset entry is Presets-first
  without changing navigation preference; nested saves refresh the live rail while selection stays
  explicit.
- [x] docs/ExecPlans/ui_certificate_import_configuration_execplan.md — typed inspection,
  atomic import, and retained-file Configure are committed in `ad712ad7e` and `498d5c791`;
  expiration sorting is completed by the dedicated validity child; the broader certificate
  lifecycle remains open.
- [x] docs/ExecPlans/ui_certificate_create_export_password_execplan.md — guided five-year create,
  password-confirmed identity fields, password-validated encrypted backup, secure remember/
  preserve/disable, and deletion/reference behavior are implemented and validated in the current
  slice; expiration sorting is completed by the dedicated validity child and password change remains
  open.
- [x] docs/ExecPlans/ui_certificate_validity_expiration_sort_execplan.md — persist public issuer,
  validity, subject-DN, and fingerprint metadata and expose the already-declared expiration sort;
  focused/full validation and cleanup are recorded in the child.
- [x] docs/ExecPlans/ui_certificate_selection_readiness_execplan.md — catalog-backed certificate
  selection, typed readiness projection, self-signed caveat, expiry warning, and blocking invalid
  material are implemented and validated in `42bbbb421`; broader certificate lifecycle remains in
  its owning plans.

Placement, preview, and signing tranche:

- [x] docs/ExecPlans/ui_pointer_signature_placement_execplan.md — pointer placement, Pan/Place
  topology, page-guide snapping, Alt bypass, and off-page indication are implemented and reconciled.
- [x] docs/ExecPlans/ui_keyboard_numeric_placement_execplan.md — keyboard creation/movement/resize,
  numeric-field history, Delete/undo/redo, snap bypass, off-page recovery, and lifecycle clearing
  are implemented and reconciled.
- [x] docs/ExecPlans/ui_signature_field_targeting_profiles_execplan.md — explicit Use for new
  signature from Document Signatures, existing-field-only backend signing, fixed target geometry,
  and placement-profile mismatch rejection are implemented and validated in the current tranche.
- [x] docs/ExecPlans/ui_appearance_content_layout_execplan.md — managed PNG import/normalization,
  schema-v2 immutable image assets, image position/prominence/alpha controls, explicit Primary
  75% allocation, staged-file cleanup, image-only layout, and save/reload preview-signing parity
  are implemented and validated; final authoritative preview fidelity, glyph coverage, frozen-time,
  and preview-specific fit/readiness evidence remain with the preview child, while document-safety
  readiness is owned by the readiness-caveats child.
- [ ] docs/ExecPlans/ui_preview_fidelity_fit_validation_execplan.md
- [ ] docs/ExecPlans/ui_readiness_caveats_status_execplan.md
- [x] docs/ExecPlans/ui_readiness_projection_contract_execplan.md — typed ordered readiness
  projection and action vocabulary landed in the current slice; document-safety source gating is
  now implemented by the readiness-caveats child, while the remaining full rail state machine
  remains with its owning children.
- [ ] docs/ExecPlans/ui_sign_confirmation_output_policy_execplan.md
- [x] docs/ExecPlans/ui_atomic_sign_write_safety_execplan.md — default executor and verified staging
  are committed; confirmation/source policy is now bounded in its follow-on child, while async
  recovery and package acceptance remain open.
- [ ] docs/ExecPlans/ui_verification_recovery_reopen_execplan.md

Release tranche:

- [ ] docs/ExecPlans/ui_product_support_and_release_execplan.md

## Progress

- [ ] (2026-08-09) Confirm the frozen SPEC/UI_SPEC baseline and current implementation map.
- [x] (2026-08-09) Created and structurally reviewed all 29 child ExecPlans in dependency order.
- [x] (2026-08-09) Added requirement traceability, exact live paths, executable validation commands,
  schema/SVG ownership, and milestone/evidence requirements before implementation.
- [x] (2026-08-09) Reordered the corpus into foundation, document-flow, reusable-object/certificate,
  placement/preview/signing, and release tranches; placement storage and typed settings now precede
  any child that persists reusable objects.
- [ ] (2026-08-09) Resolve the live contract blockers identified during review: default GUI signing
  execution, placement-schema alignment, Library/AppSettings restart state, and a real
  single-instance process boundary. The first three now have bounded implementations and evidence;
  the remaining acceptance limitation is display-backed single-instance forwarding in this
  environment, which still reports `SingleInstanceUnavailable` with an isolated endpoint.
- [x] (2026-08-09) Completed the first foundation slice: no-document launch now exposes direct Open
  PDF and Signature Library actions with focused unit/integration evidence and clean teardown.
- [x] (2026-08-09) Completed the File-command foundation slice: a typed registry now routes Open,
  Save, Save As, Close, and Exit with shortcuts, mnemonics, Qt-supported descriptions, and an
  explicit first-Save output-path seam; the command-model child remains open for its remaining
  menus and signed-state policy.
- [x] (2026-08-09) Loop 5 completed: the typed command registry now includes truthful View Previous
  Page and Next Page actions through the public workspace session port, with boundary-aware
  enablement and viewer-owned navigation synchronization; Fit/zoom/search behavior remains deferred
  to dependent viewer/document seams.
- [x] (2026-08-09) Loop 6 completed its bounded signing-rail correction: the fixed 320px rail now
  separates interactive signing controls from a read-only protected status region, exposes typed
  recommended-action styling/accessibility, and has coordinator plus real offscreen sidebar evidence.
  The full UI_SPEC state machine, asynchronous progress, verification/recovery, independently
  scrollable regions, and remembered divider remain open in this child and their owning children.
- [x] (2026-08-09) Loop 7 completed the bounded main-window geometry/restart slice: validated
  `MainWindowGeometry` survives settings round-trip, restores before display, captures after the
  event loop (including controlled cleanup), and preserves unknown UI keys. Rail-divider, Library,
  full monitor/DPI, and toolbar persistence remain open in the window child.
- [x] (2026-08-09) Loop 8 completed the bounded Settings command-model increment: the five existing
  Settings callbacks now use the shared typed registry with unique mnemonics, stable IDs/object
  names, Qt descriptions, and callback-routing tests. Edit, Signing, Help, and remaining View
  commands remain open until their truthful behavior seams exist.
- [x] (2026-08-10) Completed the bounded placement foundation slice: PlacementProfile v2 now stores
  explicit source-page metadata, fixed page number, pinned state, and visible top-left geometry;
  PDF↔visible conversion is centralized; SavePlacement/workflow capture require explicit context;
  transactional numeric editing is reachable from Library create/edit actions and survives reload.
  Pointer handles, keyboard placement, and snapping/undo remain open in their owning children; the
  bounded three-column Library topology now lands in its own completed child below.
- [x] (2026-08-10) Completed the bounded Signature Library topology slice: the AppFrame now owns one
  modeless Presets-first three-column surface with searchable typed rows, injected certificate
  projections, and an isolated Save/Cancel name draft. Nested editors, certificate mutations,
  Duplicate/Pin, dirty prompts, and Library-specific preferences remain open in their owning plans.
- [x] (2026-08-10) Implemented the catalog search/sort/pinning foundation: persistent pins now cover
  reusable and certificate records, duplicate objects reset pin state, names are case-insensitively
  unique, pinned rows sort first, and Library catalog/sort preferences persist. Certificate validity
  metadata and expiration sorting now live in the dedicated child; typed certificate
  pin/rename/delete routing, confirmation-safe mutation, and configured rows before retained
  unconfigured files are covered here.
- [x] (2026-08-10) Closed the Library mutation-lifecycle follow-up: successful retained-certificate
  Configure refreshes/reselects the open modeless row; reusable-object and certificate Delete
  actions require explicit Yes confirmation before dispatch; expiration preference propagation and
  pinned-versus-configured precedence have focused coverage. Full regression is `1277 passed, 20
  skipped, 1 warning`; bounded GUI launch remains limited by the isolated single-instance endpoint.
- [x] (2026-08-10) Added the document-independent preset-editor increment: Library Create/Edit now
  open a modal Save/Cancel editor that writes stable appearance, placement, and certificate
  references without an active PDF; Appearance editing, reason/location defaults, dirty prompts,
  and active-placement invalidation remain open in the preset/appearance children.
- [x] (2026-08-10) Added the bounded document-independent Appearance editor increment: Library
  Create/Edit now expose a modal Save/Cancel editor backed by the existing visible-signature
  controls, with stable-id-aware `SaveAppearance` persistence and no active-document mutation.
  Nested breadcrumb/detail-pane navigation, labeled sample preview, suspended preset return,
  reason/location defaults, dirty prompts, and active-placement invalidation remain open.
- [x] (2026-08-10) Completed the production nested Appearance detail-pane increment in
  `3f571f9d2`: `AppearanceProfileEditorWidget` replaces the Library detail column with a breadcrumb,
  sticky labeled synthetic preview, content-only controls, stable-id Save, and typed
  Save/Discard/Continue resolution; `ReusableObjectLibraryDialog` suspends/restores the parent
  catalog selection/name draft and removes child widgets on exit. The modal dialog is now only a
  compatibility/test wrapper. Preset-child return, reason/location defaults, active-placement
  invalidation, and final preview fidelity remain open in their owning children. Full validation is
  1357 passed and 20 skipped; the bounded launch audit's isolated single-instance error is recorded
  as an environment limitation with cleanup confirmed.
- [x] (2026-08-10) Completed the production nested Signature Preset transaction increment:
  `SignaturePresetEditorWidget` now replaces the modal production path, mounts one nested
  `AppearanceProfileEditorWidget`, returns a stable appearance reference to the suspended preset
  draft, and resolves child before parent Save/Discard/Continue on Back, close, and catalog switch.
  The dialog is a compatibility/test wrapper only; focused validation is `72 passed`, full
  regression is `1363 passed, 20 skipped, 1 warning`, and the bounded launch audit left no process
  or temporary-config debris. Reason/location, placement/certificate creation, active-placement
  invalidation, and final preview-fidelity work stays in owning children.
- [x] (2026-08-10) Added the bounded first-use preset entry increment: an empty preset catalog now
  gives explicit no-preset guidance in the signing rail and routes `Create or manage presets…`
  through typed workspace composition to the existing modeless Presets-first Library. Opening the
  Library does not mutate the active draft. The nested Preset → Appearance → Preset return path is
  now complete in the preset transaction child; first-use Presets-first intent, live rail refresh,
  explicit selection, and per-document input prompts remain open in the first-use/certificate
  children.
- [x] (2026-08-10) Completed the first-use preset selection follow-up: the rail's Library action
  focuses Presets without persisting `library_last_catalog`, nested Appearance/Preset saves notify
  the active shell so the new row is visible, and no preset is auto-selected. Real offscreen
  first-use integration is green (`4 passed`); full regression is `1367 passed, 20 skipped, 1
  warning`; optional certificate/placement creation and missing per-document prompts remain in
  their owning children.
- [x] (2026-08-10) Added the bounded certificate-readiness increment: the catalog-backed signing
  rail now projects selected PKCS#12 identity, private-key presence, validity, expiry warnings,
  blocking states, password-promptability, and the exact neutral self-signed caveat through a typed
  application contract. Import/configuration, create/export/password management, retained
  unconfigured rows, and the complete signing-rail stage machine remain open in their children.
- [x] (2026-08-10) Added the bounded certificate-import inspection increment: Settings Import now
  has a typed, non-mutating Inspect step for identity, issuer, validity, private-key presence, and
  warnings, then revalidates before the existing atomic configured-entry commit. Retained-file
  Configure is now reachable from the Library and creates a typed configuration without changing
  the managed file; expiration sorting is now covered by the validity child, while create/export/
  password lifecycle remains open here.
- [x] (2026-08-10) Implemented the certificate create/export/password lifecycle slice: guided
  five-year self-signed creation now accepts full-name identity fields with confirmation, backup
  export validates the existing encrypted PKCS#12 password, and management Save preserves,
  enables, or explicitly disables remembered passwords through the secure-secret boundary. Full
  suite and bounded GUI evidence remain at the child commit gate.
- [x] (2026-08-10) Implemented the certificate validity-metadata and expiration-sort child: new
  managed records persist public subject-DN, issuer, validity, and SHA-256 facts; old records read
  as unknown; Library sorting honors expiration within the existing configured/pinned partitions;
  the Qt choice uses the existing `expiration_soonest` AppSettings value. Focused `74 passed`, full
  `1269 passed, 20 skipped`, Ruff/diff clean, and bounded launch cleanup are recorded in the child.
- [x] (2026-08-10) Added the first safe-signing increment: the production GUI now receives a
  neutral lazy executor instead of silently returning an unexecuted request, and the signing use
  case verifies sibling staged output before replacement. Asynchronous progress/recovery and
  package acceptance remain open in the signing children.
- [x] (2026-08-10) Added the bounded confirmation/output-policy increment: final signing now
  synchronizes the authored setup, summarizes preset/certificate/output/page/field/frozen time and
  caveats, uses consequence-labeled `Sign and save`/`Cancel` controls with a Cancel default, offers
  collision-safe signed-output suggestions, and permits source replacement only after explicit
  session-local authorization and staged verification. Focused `158 passed`, full `1285 passed,
  20 skipped, 1 warning`, Ruff/diff clean; display-backed acceptance remains blocked by the isolated
  single-instance endpoint and exact existing-field identity remains with the field-targeting child.
- [x] (2026-08-10) Added the bounded verification-recovery increment: post-write verification
  failures now preserve an explicitly untrusted sibling artifact, expose its path through
  `SigningResult`, and project Verify again, Return to draft, and Open preserved copy through typed
  coordinator/boundary/sidebar actions. Broader reopen policy remains open; focused
  recovery/coordinator/sidebar/application coverage was green (`205 passed`), full suite was
  `1288 passed, 20 skipped, 1 warning`, and the bounded GUI launch remained limited by the isolated
  single-instance endpoint with cleanup confirmed.
- [x] (2026-08-10) Extended recovery with a distinct untrusted preserved-copy reopen intent and a
  permission-aware later-approval gate: reopened recovery workspaces block signing until every
  signature verifies and DocMDP permissions are known to allow approval changes; lifecycle disposal
  cleans the app-owned recovery artifact. Focused app-frame/action/sidebar coverage is `64 passed`;
  current full suite is `1292 passed, 20 skipped, 1 warning`.
- [x] (2026-08-10) Added the bounded pointer-placement cancellation contract: existing pointer drags
  already cross the typed viewer/session/workspace bridge into a page-local `SignatureRect`; Escape
  now cancels unfinished placement or handle drags without emitting a new rectangle. Focused viewer/
  interaction and offscreen integration coverage is `40 passed`; current full suite is `1296 passed,
  20 skipped, 1 warning`. Broader explicit Pan/Place tool topology, keyboard placement, snap/guides,
  undo history, and off-page recovery remain open in later placement work.
- [x] (2026-08-10) Completed the explicit Pan/Place topology follow-up: the production viewer now
  starts in Pan, exposes checkable Pan and Place tools through the typed session boundary, prevents
  accidental placement while panning, and preserves completed overlays across mode changes. Focused
  shell/viewer/composition/integration validation is `156 passed`; full-suite validation is `1297
  passed, 20 skipped, 1 warning`, and final commit gates remain. Keyboard placement, snap/guides,
  undo history, and off-page recovery remain open.
- [x] (2026-08-10) Added the first keyboard-placement tracer bullet: Place-mode Enter creates a
  centered 3×1-inch placement with proportional small-page fitting, while Arrow/Shift+Arrow move
  it by exact 1/10-point deltas through the typed ViewerInteractionSession/runtime seam. Focused
  viewer/session/shell/composition/integration validation is `165 passed`; current full suite is
  `1301 passed, 20 skipped, 1 warning`. Resize, Delete/history, snap/guides, and off-page recovery
  remain open in the keyboard-placement child.
- [x] (2026-08-10) Added the typed placement-history increment: Place-mode Delete removes the
  active overlay, Ctrl+Z/Ctrl+Shift+Z restore local mutations, Escape returns to Pan while retaining
  a completed overlay, and external overlay synchronization clears stale history. Focused
  viewer/history/runtime/composition/offscreen validation is `159 passed`; the full suite remains
  `1304 passed, 20 skipped, 1 warning`; resize, numeric traversal, snap/guides, and off-page
  recovery remain open.
- [x] (2026-08-10) Added exact Place-mode Ctrl+Arrow/Ctrl+Shift+Arrow resize through the typed
  application/runtime seam, anchored at bottom/left and rejecting invalid shrink without silent
  clamping; resize joins placement history. Focused viewer/application/runtime validation is green
  and the full suite is `1307 passed, 20 skipped, 1 warning`. Numeric traversal, snap/guides, and
  off-page recovery remain open.
- [x] (2026-08-10) Made direct placement-field edits history-aware and exposed accessible,
  deterministic Page/Left/Bottom/Width/Height tab order in the setup form. Focused viewer/form/runtime
  validation is green; the full suite is `1308 passed, 20 skipped, 1 warning`. Richer numeric
  traversal commands, snap/guides, and off-page recovery remain open.
- [x] (2026-08-10) Added pointer-only visible-page edge/center snapping with an 8-point threshold,
  Alt bypass, and rendered guide lines; keyboard/numeric edits remain exact and unsnapped. Focused
  coordinate/viewer validation is green; off-page recovery remains open.
- [x] (2026-08-10) Added explicit off-page recovery through the typed application/runtime seam:
  Place-mode `M` moves a non-oversized placement fully onto the visible page without scaling,
  oversized rectangles report an actionable resize requirement, and red page-edge indicators make
  crossing visible. Focused viewer/application/integration validation is green; the full suite is
  `1314 passed, 20 skipped, 1 warning`. Numeric traversal remains open.
- [x] (2026-08-10) Completed placement-history lifecycle clearing: non-placement setup changes and
  successful signing invalidate local placement history, while placement-field edits remain
  undoable and external overlay synchronization drops stale branches. The keyboard-placement child
  now has no remaining behavior tranche; final audit/closeout remains.
- [x] (2026-08-10) Closed the pointer and keyboard placement child corpus after the full interaction
  tranche landed. Current validation is `1314 passed, 20 skipped, 1 warning`; bounded GUI launch
  exits at the known isolated single-instance endpoint and leaves no process or temporary audit-root
  debris.
- [x] (2026-08-10) Implemented existing unsigned-field targeting: Document Signatures exposes
  Use for new signature for eligible visible fields, the typed draft/request carries the field name,
  pyHanko fills the existing field only, targeted geometry controls are locked, and mismatched
  placement profiles are rejected with a manual-resolution explanation. Full validation is
  `1318 passed, 20 skipped, 1 warning`; bounded GUI cleanup is clean and the isolated socket
  limitation remains the only launch-audit blocker.
- [x] (2026-08-10) Reconciled the already-landed certificate-selection/readiness slice against
  its implementation commit `42bbbb421`: catalog-backed selection, typed ready/warning/blocked
  projections, self-signed caveat, and password-promptable handling are complete; broader
  certificate lifecycle and signing-rail stage-machine work remain explicitly open.
- [x] (2026-08-10) Added the typed signing-readiness projection child: the active workspace now
  derives one ordered preset/setup/placement/review/ready state and recommended action through a
  Qt-free application contract; signed/recovery/no-document precedence remains at the existing
  presentation edges. Focused validation is `181 passed`, the full suite is `1349 passed, 20
  skipped, 1 warning`, and the bounded launch audit cleaned its isolated root and processes after
  the known `SingleInstanceUnavailable` endpoint limitation.
- [x] (2026-08-10) Added the typed View zoom command child: Zoom In/Out and Reset Zoom are real
  frame actions routed through the public session port and existing clamped viewer policy. Focused
  validation is `206 passed`, the full suite is `1351 passed, 20 skipped, 1 warning`, and the
  bounded launch audit cleaned its isolated root and processes after the known endpoint limitation.
- [x] (2026-08-10) Closed the managed Appearance-image evidence follow-up: staged normalized files
  are removed on replacement, Remove, discard, and Cancel; catalog reload preserves the managed
  asset identity and image semantics; the catalog-local resolver supplies the runtime path, and
  canonical preview and signing materializers receive that same path and shared layout plan.
  Explicit production Primary now reserves 75% while low-level compatibility callers omit the field.
  Focused lifecycle/parity validation is green; full regression is `1384 passed,
  20 skipped, 1 warning`. The bounded offscreen GUI launch still exits at the isolated
  `SingleInstanceUnavailable` endpoint and leaves no process or temporary-root debris; no SVG changed.
- [x] (2026-08-10) Added the first authoritative preview-fidelity gate: exact bundled font cmap
  coverage now emits field/character blocking issues through semantics, coordinator readiness, and
  final request construction; frozen preview time remains the value carried into signing; and a
  materialized preview/backend layout-plan parity test covers the glyph-safe path while the blocked
  path proves submission is rejected. Full regression is `1390 passed, 20 skipped, 1 warning`.
- [x] (2026-08-10) Closed the rendered preview/signed-appearance parity evidence portion of the
  preview child: `tests/integration/test_preview_signed_output_parity.py` signs a real PDF,
  renders the embedded annotation appearance through the Qt PDF backend, and asserts an exact
  RGBA match with the frozen canonical preview. Parameterized managed-image cases cover preserved
  and flattened alpha normalization; exact-fit workflow/readiness/request rejection remains
  covered. The preview child still has the display-backed/test-adapter GUI walkthrough open because
  the isolated launch reaches `SingleInstanceUnavailable` before window creation. Current full
  regression is `1393 passed, 20 skipped, 1 warning`.
- [x] (2026-08-10) Added the first document-safety readiness increment: workspace composition now
  captures metadata-only source identity, the rail prioritizes changed/missing/unknown source
  status before preset/certificate setup, and direct workflow request construction rejects an
  unresolved source. Focused validation is `49 passed`; full regression is `1398 passed, 20
  skipped, 1 warning`. Reload/Locate/Ignore banners and draft-preserving reload remain open in the
  safe-links/lifecycle children.
- [ ] (2026-08-09) Document-lifecycle slice implemented and validated: dirty projection protects
  placement, appearance/content, and confirmed output-path changes; typed maintenance verbs clear
  drafts/secrets; Open composes candidates before the discard decision; File Close, Exit, and native
  close use consequence-verb policy with conditional Sign and save. Focused tests, real offscreen
  native-close integration, and the full suite are green; display-backed acceptance remains
  environment-blocked by unavailable xcb `DISPLAY=:0`, and crash recovery remains a separate plan.
- [ ] Implement, validate, document, and commit each child without mixing unrelated change classes.
- [ ] Run the final live GUI, offline, accessibility, and packaged-install acceptance pass.
- [ ] Reconcile architecture/status documentation and retire obsolete product-facing terminology.

## Surprises & Discoveries

- Observation: the repository contains substantial domain, signing, certificate, viewer, and Qt
  infrastructure, but current UI surfaces do not yet satisfy the new topology and interaction
  contract end to end.
  Evidence: current files include app_frame.py, viewer_widget.py, reusable_signing_models.py,
  certificate-management dialogs, and signing-workspace modules, while UI_SPEC.md still requires
  a modeless three-column Library, fixed signing rail, and keyboard-equivalent workflows.
- Observation: existing phase3-named modules are primarily evidence/harness infrastructure rather
  than the user-facing product path.
  Evidence: phase3-prefixed files occur under application evidence and Qt acceptance tooling.
  Their product-facing labels must not leak into the V1 UI; migrations must preserve evidence meaning
  while removing obsolete nomenclature where safe.
- Observation: the first live implementation loop completed with real-Qt offscreen evidence, while
  the display-backed audit was blocked by the current xcb session.
  Evidence: `tests/integration/test_gui_launch_no_document.py` passed under
  `QT_QPA_PLATFORM=offscreen`, while `DISPLAY=:0 ... scripts/live_gui_parent_audit.py` exited 134
  because xcb could not connect; cleanup found no FoliaSeal processes.
- Observation: the second implementation loop can safely land the File lifecycle independently, but
  the full command-model child still depends on viewer, signing-rail, support, and signed-output
  policy slices for truthful enablement and complete menu coverage.
  Evidence: `ui_command_model_shortcuts_execplan.md` records the bounded File acceptance and its
  deferred Edit/View/Signing/Settings/Help owners.
- Observation: the bounded signing rail can be made truthful before the full state machine exists,
  but only if interactive action controls stay out of the read-only status region and the remaining
  UI_SPEC states are named as deferrals.
  Evidence: Loop 6 compliance review and `ui_signing_rail_stage_status_execplan.md` revision note
  dated 2026-08-09.
- Observation: main-window geometry persistence can use the existing `AppSettings.ui` merge and
  atomic store without a schema-version bump, but the full UI_SPEC responsive contract is broader
  than one rectangle and maximized flag.
  Evidence: Loop 7 explorer review, `MainWindowGeometry`, and the window child ExecPlan's explicit
  rail/Library/monitor/DPI/toolbar deferrals.
- Observation: safe document replacement requires composing and validating the candidate before
  discarding the active dirty draft.
  Evidence: `SigningWorkspaceLifecycle.prepare()` / `replace_prepared()` and the lifecycle-focused
  failed-candidate test.
- Observation: the current environment has no usable xcb display and cannot claim the local-instance
  socket under the sandbox, but real offscreen Qt tests provide deterministic close-event evidence.
  Evidence: bounded CLI audit exited `1` with `SingleInstanceUnavailable`; display audit exited `134`
  with xcb `DISPLAY=:0`; exact temporary roots and owned processes were cleaned; real offscreen
  lifecycle integration passed.

## Decision Log

- Decision: use thin vertical slices instead of the former broad GUI plans.
  Rationale: each slice must produce a demoable behavior and keep implementation, validation, and
  rollback narrow.
  Date/Author: 2026-08-09 / Codex
- Decision: treat SPEC.md as the product authority, SCHEMAS.md as the persistence authority, and
  UI_SPEC.md as the interface authority.
  Rationale: this is the explicit precedence contract and prevents implementation behavior from
  silently redefining product requirements.
  Date/Author: 2026-08-09 / Codex
- Decision: mark implementation slices AFK.
  Rationale: the frozen documents already resolve topology and interaction choices; a later human
  usability review may provide evidence but is not an implementation dependency.
  Date/Author: 2026-08-09 / Codex
- Decision: keep crash recovery/autosave out of the document-lifecycle slice until the signing
  transaction exposes owned temporary/final artifact paths.
  Rationale: a recovery journal without an ownership boundary could present unsafe artifacts or
  delete unrelated files; the current slice now protects in-memory drafts and secrets without
  overstating restart recovery.
  Date/Author: 2026-08-09 / Codex
- Decision: remove legacy compatibility and product-facing phase3 cruft only after each migration
  proves its concrete callers are gone; retain or rename production evidence/backend imports in a
  separate neutral migration first.
  Rationale: SPEC.md prioritizes V1 clarity, but current fit validation and acceptance tooling still
  import phase3-named modules, so a broad rename would break production behavior and evidence.
  Date/Author: 2026-08-09 / Codex
- Decision: treat the current implementation mismatches recorded in child plans as explicit
  prerequisites, not assumptions hidden inside later GUI work.
  Rationale: the default signing executor, placement schema fields, restart settings, and process
  routing determine whether the UI contract can be exercised end to end.
  Date/Author: 2026-08-09 / Codex
- Decision: make the placement v2 schema and AppSettings key ownership explicit before dependent
  children persist data.
  Rationale: the live placement model and untyped `ui` mapping otherwise allow parallel children to
  invent incompatible serialized contracts.
  Date/Author: 2026-08-09 / Codex
- Decision: treat placement schema migration and typed AppSettings as foundation work, while keeping
  the placement editor’s Library mounting in the reusable-object tranche.
  Rationale: persistence contracts must be settled before Library, preset, certificate, or signing
  UI can safely write data; separating the schema milestone avoids a circular dependency between the
  placement editor and the Library that hosts it.
  Date/Author: 2026-08-09 / Codex
- Decision: use the normalized ten-scenario matrix as the sole acceptance-owner map.
  Rationale: several scenarios intentionally span multiple children, but a single primary owner is
  needed to prevent duplicate or missing acceptance decisions at the final gate.
  Date/Author: 2026-08-09 / Codex

## Outcomes & Retrospective

The first eight bounded implementation loops established and committed a usable foundation rather
than full SPEC/UI_SPEC compliance. Proven slices include no-document launch, typed File lifecycle
commands, single-instance open routing, app-frame appearance/minimum sizing, View Previous/Next
Page navigation, a fixed signing rail with a read-only status region and typed recommended action,
main-window geometry/maximized persistence, and typed Settings command metadata/callback routing.
Focused and full validation remained green through the final loop (`1185 passed, 20 skipped,
1 warning`), with bounded CLI audits cleaning up their isolated roots and recording the environment's
`SingleInstanceUnavailable` local-endpoint limitation.

The parent is not complete. Several child checkboxes remain open because the remaining requirements
include full document lifecycle/recovery, nested Library transactions and editors, certificate flows,
pointer/keyboard placement, preview fidelity, atomic sign/write/verification/recovery, complete
Edit/View/Signing/Help command surfaces, rail divider/Library/monitor/DPI persistence, accessibility
and packaged-release acceptance. The bounded slices deliberately recorded these gaps instead of
claiming compliance from narrow tests.

## Context and Orientation

FoliaSeal is a Python/Qt Linux desktop PDF signing application. The CLI entry point is
src/foliaseal/__main__.py. The top-level Qt frame is
src/foliaseal/presentation/qt/app_frame.py. The signing workspace is assembled through
signing_shell.py, signing_workspace_composition.py, and related bridge/sidebar modules. Viewer
behavior is split between application viewer workflows and presentation/qt/viewer_widget.py.
Reusable objects persist through application models and infra/config stores. Certificate creation,
import, secrets, and export live in application and presentation certificate modules. Tests are
under tests/unit.

The product story is open -> review -> select preset/certificate -> place -> preview/readiness ->
sign/save -> verify/reopen. The UI contract additionally requires one open PDF, a stable right rail,
a modeless Signature Library, keyboard-accessible equivalents, plain-language status, safe atomic
output, and offline operation. The anti-goals in both governing documents remain out of scope.

## Requirement Traceability and Evidence Ownership

The final child must rerun this evidence map. Each row names the owning children and the observable
proof that must be recorded; headless tests do not substitute for GUI or package evidence.

| Requirement | Owning children | Evidence |
|---|---|---|
| SPEC primary story: open/review | launch, lifecycle, navigation, search children | No-document launch, validated open, page and text walkthrough |
| SPEC primary story: reusable setup | Library through first-use children | CRUD/nested transaction tests and first-use GUI walkthrough |
| SPEC primary story: certificate | certificate import through readiness children | Import/create/export/delete/password/readiness tests and GUI evidence |
| SPEC primary story: placement | placement children | Pointer, keyboard, field, profile, and on-page placement evidence |
| SPEC primary story: preview/readiness | appearance through readiness children | Render parity, frozen-time, fit/glyph, and state evidence |
| SPEC primary story: sign/save/verify/reopen | confirmation through verification children | Atomic output, verification, recovery, reopen/add-approval evidence |
| UI_SPEC scenarios 1–4 | foundation/review/placement children | Keyboard launch, partial preset, placement undo, field targeting |
| UI_SPEC scenarios 5–7 | appearance/signing children | Preview parity, source overwrite, restriction and verification checks |
| UI_SPEC scenarios 8–10 | product support/release child | Accessibility, minimum-size/DPI, offline Help, and package evidence |
| Normative SVG topology/state artifacts | rail, Library, appearance, placement, confirmation children | Review every file under docs/ui/ and record agreement |
| Global V1 anti-goals | product support/release child | Negative audit for tabs, printing, page editing, restoration, cloud/plugins, ordinary forms, trust/timestamp controls, arbitrary fields, and multiple pending signatures |

Schema ownership is explicit: `src/foliaseal/infra/config/schemas.py` and matching codecs,
`src/foliaseal/application/reusable_signing_models.py`, certificate models, and AppSettings are
owned by the relevant Library, placement, certificate, and product-support children. Any migration
must include a before/after serialized fixture and a backwards-read or deliberate rejection test.
The placement child owns the `top_pt` versus live `bottom_pt` decision and `page_number`/`source_page`
mapping; no other child may persist placement fields before that decision is recorded.

Normative UI artifacts are individually owned: `docs/ui/main-workspace-no-document-exploratory.svg`
and `docs/ui/main-workspace-document-open-exploratory.svg` by launch/lifecycle;
`docs/ui/sign-and-save-states-exploratory.svg` by rail, readiness, and confirmation;
`docs/ui/signature-library-presets-exploratory.svg` by Library; and
`docs/ui/appearance-profile-editor-exploratory.svg` plus
`docs/ui/placement-profile-editor-exploratory.svg` by appearance and placement. The repository has
no separate signing-rail SVG; rail ownership must cite the relevant state file and UI_SPEC text.
Each owner records the file path and observed agreement in its Evidence Record.

The ten scenario rows are also cross-linked to their contributing children: scenario 1 owns launch,
open/lifecycle, navigation, and search; scenario 2 owns rail, first-use, preset transactions, and
certificate readiness; scenario 3 owns pointer, keyboard, and placement editor; scenario 4 owns
field targeting, placement, and document review; scenario 5 owns appearance, preview, review,
readiness, confirmation, and verification; scenario 6 owns confirmation, atomic write, and
lifecycle; scenario 7 owns atomic write and verification; scenario 8 owns command model, keyboard
placement, Library/editor accessibility, and product support; scenario 9 owns window/theme and
product support; scenario 10 owns product support/release. Each row must cite one focused test,
one GUI evidence artifact, and its owning SVG or explicit “no SVG” decision.

Use this normalized matrix when those cross-links overlap. “Primary owner” is the one child that
checks the scenario evidence row in the parent; “supporting children” may contribute tests or
screenshots but must not create a second acceptance decision. The SVG column is mandatory evidence
when a normative artifact exists and is explicitly “no SVG” for scenarios without one.

| Scenario | Primary owner | Supporting children | SVG or decision |
|---|---|---|---|
| 1 open and review | `ui_launch_no_document_execplan.md` | lifecycle, navigation, search | main-workspace SVGs |
| 2 reusable setup | `ui_signing_rail_stage_status_execplan.md` | first-use, preset transactions, certificate readiness, Library | sign-and-save and Library SVGs |
| 3 placement undo | `ui_pointer_signature_placement_execplan.md` | keyboard placement, placement editor | placement-profile SVG |
| 4 field targeting | `ui_signature_field_targeting_profiles_execplan.md` | placement, document-signatures review | placement-profile SVG |
| 5 preview and verification state | `ui_appearance_content_layout_execplan.md` | preview, review, readiness, confirmation, verification | appearance-profile and sign-and-save SVGs |
| 6 source replacement safety | `ui_sign_confirmation_output_policy_execplan.md` | atomic write, lifecycle | sign-and-save SVG |
| 7 restricted/verified output | `ui_atomic_sign_write_safety_execplan.md` | verification/reopen | sign-and-save SVG |
| 8 accessibility and keyboard paths | `ui_product_support_and_release_execplan.md` | command model, keyboard placement, Library/editor | no SVG |
| 9 minimum size, theme, DPI | `ui_window_theme_responsive_execplan.md` | product support/release | no SVG |
| 10 offline Help and package | `ui_product_support_and_release_execplan.md` | none | no SVG |

The final acceptance record must also cover password-protected PDF prompts and password clearing on
Close/replacement/success/Exit; certification and ordinary-signature preflight; final verification
of every existing signature; page-local render recovery; exact source-overwrite warnings;
retained-but-unconfigured certificates; claimed signing time versus trusted timestamp; network-
disabled operation with no telemetry/uploads/accounts; screen-reader names/roles/tab order;
high-contrast/scaling/Unicode; Markdown/CLI Help parity with no JavaScript or remote assets; and
PyInstaller/.deb launcher plus poppler-utils verification.

## Change Slice

Primary change class: behavior change, with documentation/status reconciliation and final package
acceptance only where a child explicitly owns those outputs. Allowed artifacts are the named source
and test changes, bounded ignored local evidence, and truthful updates to architecture, README, or
ExecPlans. Do not mix speculative V2 features, broad PDF editing, printing, cloud/trust
administration, unrelated architecture scans, or evidence rebaselines into this parent.

## Plan of Work

Execute children in dependency order. Each child starts with a live code/spec audit, adds or
replaces the smallest complete path through model/application/Qt wiring/tests, and names the exact
consumer, grep proof, and deletion condition before removing a compatibility path. A child may add focused acceptance
fixtures or ignored local evidence artifacts, but must not mix unrelated evidence refreshes,
packaging changes, or broad refactors.

After each child, run focused tests, ruff on touched files, the relevant offscreen or display-backed
GUI check, and the full regression suite when the slice changes shared Qt/application behavior.
Record exact observations in the child plan, update docs/ARCHITECTURE.md or README.md only when
their current statements become inaccurate, clean processes/dialogs/temp artifacts, and commit the
narrow change. Check the corresponding child box here only after its acceptance criteria are met.

The product-support/release child owns a separate neutralization audit for the phase3 backend and
evidence import graph. It must inventory every production and test consumer, add neutral names with
temporary adapters, run import-isolation and acceptance tests, and record the deletion proof before
any UI child removes a phase3-named module or command. UI children may remove only product-facing
labels after that audit; they may not rename the backend opportunistically.

## Milestones

Milestone 1 is the contract and foundation gate: confirm the frozen SPEC/UI_SPEC/SCHEMAS requirements,
make startup and typed restart settings work, migrate placement persistence to v2, and make every
child’s focused red test and exact live paths available. At the end of this gate, no later child may
invent a settings or placement shape. Milestone 2 is the dependency-ordered vertical implementation: startup, typed settings,
and placement persistence first; document flow next; reusable objects and certificates next; then
placement interactions, preview, signing, and recovery;
each completed child must leave focused tests and a recorded GUI observation. Milestone 3 is the
release gate: run the two-process routing check, offline/accessibility/help matrix, extracted
package launcher check, all ten UI scenarios, anti-goal audit, and cleanup before checking every
parent box.

## Concrete Steps

All commands run from /home/daekar/FoliaSeal.

The checkout must use its virtual environment. If `.venv/bin/python` is absent, create it with
`python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`; if dependency installation
is unavailable, stop with that exact environment blocker rather than falling back to system Python
or system Qt.

    git status --short
    sed -n '1,360p' docs/SPEC.md
    sed -n '1,530p' docs/UI_SPEC.md
    rg -n "phase3|compat|manual assembly|Signature Library|Sign and save" src tests docs

Do not begin the document-flow or reusable-object tranches until the foundation gate is green. Its
observable proof is: `foliaseal gui` starts without a document; a restart preserves only the typed
window/settings keys; a before/after fixture reads or clearly rejects the old settings shape; and a
legacy placement fixture is converted to SCHEMAS.md v2 with a concrete `page_number` and no
serialized `page_selection_mode`.

For each child, follow its exact commands. The common validation baseline is:

    .venv/bin/pytest -q
    .venv/bin/ruff check src tests
    git diff --check

    audit_root=$(mktemp -d /tmp/foliaseal-ui-audit-XXXXXX)
    trap 'pkill -TERM -f "foliaseal|FoliaSeal" 2>/dev/null || true; rm -rf "$audit_root"' EXIT
    set +e
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf
    gui_rc=$?
    set -e
    test "$gui_rc" -eq 0 || test "$gui_rc" -eq 124
    ! ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg '
    rm -rf "$audit_root"
    test ! -e "$audit_root"

The common command is only a lifecycle/cleanup smoke check. Each child that claims a visual or
interactive result must add a bounded display-backed or Qt-test walkthrough that records widget
state, input sequence, expected observation, and an evidence file under ignored `artifacts/`; an
offscreen timeout alone is never accepted as proof of a GUI behavior. Never leave FoliaSeal
processes, dialogs, or generated artifacts behind. Child cleanup must terminate only processes it
owns, remove the exact temporary root with `rm -rf`, and assert that the root is gone; do not hide
cleanup failures behind `rmdir ... || true` or broad `find` deletions.

Use one of these executable evidence paths. For a behavior-specific Qt test, name the exact test
node in the child plan and record the expected `N passed` result; the test must drive widgets and
assert the visible state rather than merely importing a class. For the shared primary workflow, run
the repository audit runner from a display-backed session:

    DISPLAY=:0 timeout --foreground 180s .venv/bin/python scripts/live_gui_parent_audit.py --artifacts-dir "$audit_root/live-gui"

Review its screenshots and JSON report, record the checkpoint relevant to the child, and remove the
audit directory afterward. If no display is available, the child must use a real Qt test or remain
incomplete; an offscreen launch may establish lifecycle health but cannot close the acceptance gate.

## Validation and Acceptance

The parent succeeds only when all children are checked and a novice can complete the primary
SPEC.md story in the packaged application without developer explanation. Acceptance must cover the
ten observable UI_SPEC scenarios, the SPEC.md release bar, keyboard and accessibility paths, offline
verification, safe source overwrite, restriction preservation, and installed Debian-family startup.
Passing unit tests alone is insufficient; record live GUI observations and cleanup evidence.
Every child must identify its new or changed focused test by node id, record red-before/green-after
behavior when adding a new contract, and record the full-suite result (`.venv/bin/pytest -q`) whenever
shared application or Qt code changes.

## Evidence Record

At the final gate, record one row per child and per UI_SPEC scenario: governing requirement, exact
test command/result, GUI input sequence and observed state, evidence path, package/offline result
where applicable, cleanup/process result, and compatibility/schema/SVG grep proof.

## Idempotence and Recovery

Children must use temporary sibling outputs and isolated temporary config roots for destructive or
stateful tests. If a child stops part-way, update its Progress section with done and remaining work,
restore or preserve unrelated user changes, terminate test/GUI processes, and remove only its own
generated artifacts. Do not use broad recursive deletion. Re-running a completed child must be a
no-op at the behavior boundary and must not reintroduce retired compatibility code.

## Artifacts and Notes

Allowed child artifacts are focused tests, bounded local GUI screenshots or JSON evidence under
ignored artifacts/, and documentation/status updates required to keep the repository truthful.
Forbidden mixed changes include unrelated architecture scans, speculative V2 features, broad PDF
editing, printing, cloud/trust administration, or new user-facing phase3 terminology.

## Interfaces and Dependencies

Stable boundaries are the domain models and infra stores in docs/SCHEMAS.md, the application
workflows under src/foliaseal/application/, and the public Qt workspace/frame ports under
src/foliaseal/presentation/qt/. New UI behavior must be expressed through typed application or
presentation contracts rather than test-only widget reach-through. Existing compatibility adapters
are transitional; each child must name its concrete consumer, grep proof, and deletion condition.
Acceptance tooling may remain
headless or interactive, but it must be labeled as developer/acceptance tooling rather than normal
user workflow.

Revision note: 2026-08-09 / Codex
Created after approval of the 29-slice SPEC/UI_SPEC breakdown.
Updated after the second review wave to add schema/SVG ownership, executable package/process
evidence, milestone gates, and explicit GUI-observation requirements.
Updated after blocker review to add explicit implementation tranches and make placement/AppSettings
contracts prerequisites for reusable-object and signing UI work.
Updated after the next review wave to add normalized scenario ownership, executable GUI-evidence
paths, environment preflight, active-versus-historical corpus guidance, and full-suite expectations.
Updated after the document-lifecycle slice review to record candidate prepare/commit ordering,
typed dirty-draft/secret lifecycle seams, consequence-verb close policy, real offscreen native-close
evidence, and the environment-specific display/socket limitations without claiming crash recovery.
Updated after the Library mutation-lifecycle slice to reconcile completed certificate expiration
sorting, confirmation-safe deletion, retained-certificate Configure refresh/reselection, and the
current `1277 passed, 20 skipped, 1 warning` regression evidence; remaining open children are not
treated as complete from these bounded results.
Updated after the preview rendered-parity slice to record actual signed annotation raster evidence,
managed-image alpha-policy coverage, and the remaining display-backed acceptance limitation.
