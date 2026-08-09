# FoliaSeal UI/UX Specification

This document is the canonical user-interface and interaction specification for FoliaSeal.
Use [`SPEC.md`](SPEC.md) for product scope, [`SCHEMAS.md`](SCHEMAS.md) for persistent objects, and
[`ARCHITECTURE.md`](ARCHITECTURE.md) for current implementation structure. Existing UI code does
not override this intended experience.

## Document Governance

**Status: Frozen.** Normative requirements may not change without explicit user approval. When an
implementation constraint conflicts, document the conflict, user-visible impact, and alternatives
before requesting approval. Normative visuals preserve topology, hierarchy, and state—not exact
pixels, fonts, colors, or toolkit widgets.

## 1. Source Precedence and Decision Language

Each governing document is canonical within its own responsibility. When requirements genuinely
conflict, precedence is:

1. `SPEC.md` for product scope, capabilities, goals, anti-goals, and release bar.
2. `SCHEMAS.md` for canonical persistent objects, relationships, and persistence semantics.
3. This document for interface organization, workflows, commands, interaction, and presentation
   within those product and object-model boundaries.
4. Project-specific accessibility and other governing requirements.
5. Platform human-interface conventions.
6. Toolkit conventions.
7. Current implementation behavior.

The documents should ordinarily complement rather than override one another. A contradiction with
an upstream governing document must be surfaced and reconciled with explicit approval; it must not
be silently resolved inside this specification. **Must**, **must not**, **should**, and **may** are
normative in their ordinary requirements sense.

## 2. Experience Goals and Anti-goals

- **UXG01 — Document first.** The PDF remains the dominant workspace; signing controls are a
  stable supporting surface.
- **UXG02 — Predictable.** Controls retain memorable positions and disable or quietly de-emphasize
  when unavailable. Context changes must not cause needless movement or reflow.
- **UXG03 — Preset first.** Users explicitly select a reusable signature preset, place one visible
  signature, preview it on the page, then sign and save.
- **UXG04 — Trustworthy.** On-page preview, saved appearance, signing time, and verification report
  agree. FoliaSeal never silently weakens document protections or hides a failed verification.
- **UXG05 — Understandable.** Primary feedback is plain language with at most one recommended next
  action; technical detail is available but secondary.
- **UXG06 — Offline and local.** Core signing, help, and verification work offline without
  telemetry, uploads, or mandatory accounts.
- **UXG07 — Input independent.** Every essential workflow is keyboard operable and does not depend
  on color, hover, dragging, or fine pointer precision alone.

V1 must avoid general PDF editing, printing, printer integration, multi-document tabs, multiple
pending signatures, recent-file lists, automatic preset selection, setup wizards, dashboard-like
status clutter, freeform signature design, and exposing routine cryptographic internals.

## 3. User Mental Model and Terminology

| Term | Meaning to the user | Must not imply |
|---|---|---|
| Signature Library | Modeless management window for reusable signing objects | A second signing path |
| Preset / Signature preset | Named signing setup; always includes an Appearance | A flattened copy of components |
| Certificate | Managed signing identity and its local configuration | Universal third-party trust |
| Appearance | Visible signature content and styling | Arbitrary page composition |
| Placement | Optional reusable fixed page and rectangle | Document identity matching |
| Signature placement | One pending rectangle or selected unsigned field in the open PDF | A completed signature |
| Document Signatures | Existing signatures and unsigned signature fields | General PDF properties |
| Sign and save | One atomic sign, write, and local verification operation | Ordinary editable-document Save |

Ordinary UI must not say Certificate Configuration, Managed Certificate, PKCS#12 object,
Appearance Profile, Placement Profile, annotation widget, or other schema/backend terms. Help and
technical details may use them when needed.

Identity fields (common name, distinguished name, email, title, company) come read-only from the
selected certificate. Reason and Location are the only user-entered signing fields. Signing time
comes from the system clock. Missing optional identity fields are omitted; V1 has no identity
overrides or arbitrary visible fields.

## 4. Information Architecture and Topology

```text
FoliaSeal process (single instance)
├── Main window (one PDF or no-document state)
│   ├── Menu bar
│   ├── Document command toolbar
│   ├── PDF canvas / no-document landing
│   ├── Fixed right signing rail
│   │   ├── Signing controls
│   │   └── Signing status
│   └── Bottom application status
├── Signature Library (modeless, at most one)
│   ├── Catalog navigation
│   ├── Searchable master list
│   └── Transactional detail/editor
├── Document Signatures (modeless)
└── Modal settings, confirmations, passwords, and destructive decisions
```

- **LAY01.** V1 has one process, one main window, and one open PDF. No tabs or parallel document
  windows. An OS open request routes to the existing instance.
- **LAY02.** The main frame remains present with no document. Opening a PDF is primary; Manage
  Signature Library is secondary. No recent files appear.
- **LAY03.** On 16:9/16:10 displays, the PDF canvas owns available space and the signing rail stays
  vertically on the right. The toolbar owns commands; it must not own signing status.
- **LAY04.** The Library is modeless and independent of an open PDF. Presets are its dominant
  landing catalog; Certificates, Appearances, and Placements are secondary catalogs.

## 5. Primary Workflows

### WF01 — Open and review

Open one PDF by File > Open, OS association, or dropping exactly one content-validated PDF. Validate
password, page count, restrictions, and first-page render before replacing the current document.
Dirty drafts use the same action-specific discard prompt. Mount after the first page and lazy-render
others. A later page failure is page-local and offers Retry, Previous, Next, and details.

Direct launch shows the stable no-document frame. File > Close returns there; Exit closes the app.
FoliaSeal does not restore PDFs or unsigned drafts across launches.

Ordinary drafts have no crash autosave. If a crash interrupts an active signing transaction,
restart may detect only a secret-free recovery journal and app-owned temporary/final artifact. It
must verify before offering Open, Save copy as, Replace when appropriate, or Discard. FoliaSeal must
never delete unrelated temporary files or imply an unverified artifact is safe.

### WF02 — Select setup and place

Every new PDF begins with no active preset. The user selects a preset through the normal Signature
Library-backed selector; there is no manual assembly path. A preset must reference an Appearance
and may omit Certificate and Placement. Missing optional components are selected per document.

Preset selection does not itself create a placement. A compatible saved Placement becomes a
provisional proposal with its stored fixed page; otherwise the user explicitly enters Place mode.
Only one pending signature is permitted. Existing eligible visible unsigned signature fields may be
selected through Document Signatures or the explicit context-menu command Use for new signature.

Switching presets applies Appearance and Certificate immediately but does not silently replace a
completed document placement or session-edited Reason/Location. A single review prompt appears only
when choices conflict, with Keep current as the default for placement and signing details. A preset
with no Placement preserves the current document placement. An incompatible stored Placement enters
the normal provisional mismatch flow.

### WF03 — First use

With no presets, Create preset opens the Library. The user creates the required Appearance through
a nested editor, may create/import a Certificate, and may capture a Placement from the current PDF
or use blank-page setup. Saving nested objects returns and attaches them to the suspended preset
draft. Saving the preset does not silently apply it; the user selects it in the rail.

### WF04 — Preview, readiness, and sign

The on-page preview is authoritative. Readiness evaluates, in order: document safety, preset,
certificate, placement, appearance content/glyph/image/fit, then Ready. Password and output path are
promptable and not readiness blockers. Caveats do not displace Ready.

Sign and save requests an output path when needed, freezes the displayed signing time, and presents
a concise modal summary of preset, certificate, path, page/field, exact time, and caveats. Cancel is
lossless. After confirmation, password prompting precedes a short non-cancellable
prepare/write/verify transaction. Successful verified signing is terminal for that workspace.
Adding another signature requires reopening the signed output.

### WF05 — Recover from signing failure

Wrong passwords retry before the transaction. Pre-final failures remove app-owned temporary output
and preserve the draft/path. Post-write verification failure preserves the artifact, clearly says it
must not yet be relied upon, and offers Verify again, Return to draft, Open preserved copy, and
technical details. Source replacement never changes the original until a sibling temporary output
has signed and verified successfully.

### WF06 — Manage reusable objects

The Library uses explicit Save/Cancel transactions. Switching a dirty editor or closing prompts
Save, Discard, or Continue editing. A nested component editor replaces the detail pane with a
breadcrumb; the parent draft remains suspended. Exit resolves child, parent, then document draft.

Names are trimmed, required, and case-insensitively unique within each catalog. Presets,
Appearances, and Placements support Rename, Duplicate, Delete; Certificates support Rename/Delete.
Referenced-object deletion prevents dangling references and offers appropriate remove/replace
resolution. Pinning is available in all four catalogs and pinned entries sort first.

If a placed signature uses an object being materially changed or deleted, confirm Remove the placed
signature and continue? with safe Cancel default. Confirming removes it immediately; later editor
cancel does not restore it. Rename, pinning, and unrelated edits do not invalidate placement.

## 6. Surface Contracts

### SUR01 — Main workspace

Owns document review, one ephemeral signing draft, page preview, and signing invocation. It must not
own full reusable-object editors. The canvas is primary; menu/toolbar and signing rail remain stable.
Normative references: `ui/main-workspace-document-open-exploratory.svg` and
`ui/main-workspace-no-document-exploratory.svg`.

### SUR02 — Right signing rail

Persistent, signing-only, and approximately 320 logical pixels initially. Its upper controls region
has pinned preset selection, Manage Library, certificate/details/placement, and a bottom-pinned Sign
and save action. Its lower read-only status region has protected minimum height. A user-adjustable,
remembered divider separates them; each interior scrolls as needed. Neither auto-collapses.

### SUR03 — Signature Library

Modeless three-column master-detail window: stable catalog navigation, searchable/sortable object
list, and detail editor with fixed Save/Cancel footer. The detail column absorbs resizing and scrolls
vertically. Presets are the landing view. Normative reference:
`ui/signature-library-presets-exploratory.svg`.

### SUR04 — Appearance editor

Content-first editor with sticky synthetic preview, visible field order, image controls, then
secondary layout/typography/style. Synthetic sample data is labeled and never persisted; on-page
preview remains authoritative. Normative reference: `ui/appearance-profile-editor-exploratory.svg`.

### SUR05 — Placement editor

Creates fixed-page, visible-page-relative geometry from current PDF or blank page. It exposes direct
handles and compact Page/Left/Top/Width/Height points. It stores no source PDF identity or content.
Normative reference: `ui/placement-profile-editor-exploratory.svg`.

### SUR06 — Document Signatures

Modeless list of signed visible/invisible signatures and unsigned signature fields. Default order is
document order; signing-order sort is optional. Primary information is integrity/validity;
certificate trust is secondary. Selecting a visible item jumps and temporarily highlights it.

### SUR07 — Status surfaces

The right status region owns durable signing readiness/result. The bottom application status owns
only transient activity such as Ready, copied text, or navigation feedback. A condition-only banner
overlays the canvas for external source changes and consumes no permanent space.

## 7. Command Model

All menus are fully keyboard navigable with unique mnemonics, arrow navigation, Enter activation,
Escape dismissal, visible shortcut labels, and accessible disabled state.

- **File:** Open, Save, Save As, Close, Exit. Save aliases Sign and save; first Save behaves Save As;
  Save As always chooses a path.
- **Edit:** Undo, Redo, Cut, Copy, Paste, Select All. Behavior is focus-sensitive. Viewer Select All
  selects extractable text on the current page only.
- **View:** Pan, Select Text, Previous/Next Page, zoom, Fit Page, Fit Width, Find, Document
  Signatures, Back, Forward.
- **Signing:** Signature Library, Place Signature, Adjust Placement, Remove Placement, Sign and Save.
- **Settings:** Application Settings.
- **Help:** FoliaSeal Help, Keyboard Shortcuts, Data Locations, Open Diagnostic Logs Folder, About.

Conventional shortcuts include Ctrl+O, Ctrl+S, Ctrl+Shift+S, Ctrl+W, Ctrl+Q, Ctrl+F, Ctrl+C,
Ctrl+A, Ctrl+Z, Ctrl+Shift+Z, Ctrl++/Ctrl+-, Ctrl+0, Page Up/Down, Ctrl+Home/End, Alt+Left/Right,
and F1. Platform-equivalent alternatives may be used when established conventions differ.

## 8. Viewer and Placement Interaction

- V1 is single-page. Wheel/scrollbars pan and never advance pages. The editable one-based page field
  shows `of N`; Page Up/Down navigate; Ctrl+Home/End go first/last. Fit Page is default; Fit Width
  and exact 10%–800% zoom are supported.
- Pan, Select Text, and Place Signature are one mutually exclusive mode group even though Place is
  in the rail. Active tool buttons appear depressed; inactive appear raised. Pan is default.
- Ctrl+F searches the whole PDF with current/total, previous/next, Enter/Shift+Enter, strong current
  and quiet same-page highlights. Search and selection are independent.
- Text selection is current-page only. Page/mode/close clears it. Ctrl+C reports Copied text in the
  bottom status. FoliaSeal distinguishes image-only, no extractable text, permission, and parser
  failures without implying OCR.
- Place mode creates nothing on entry. Pointer drag creates a rectangle; click alone does not. With
  the page focused, Enter creates an explicit centered 3×1-inch placement (or largest proportional
  on-page size with explanation). Enter accepts; Escape cancels unfinished work or returns to Pan
  while preserving a completed placement.
- Arrow moves 1 point; Shift+Arrow moves 10; Ctrl+Arrow resizes 1 from bottom/right; Ctrl+Shift+Arrow
  resizes 10. Tab traverses placement and numeric fields; Delete removes it. Removal is undoable.
- Snap only to visible-page edges and centers with guides. Alt temporarily disables pointer snap.
  Numeric/keyboard operations are exact and never snap.
- Completed placement remains visible in all modes; handles appear only in Place. Existing selected
  signature fields are fixed and cannot resize. Fully off-page placements remain recoverable through
  nearest-edge indication and Move fully onto page; no silent clamp or scale occurs.

Undo/Redo covers placement create/move/resize/numeric/profile apply/remove. One drag is one step;
Escape during a drag reverts it. History clears on setup changes, Open/Close, successful signing,
or discard. Text fields use native local undo; signing and Library commits are not undoable.

## 9. Appearance Requirements

An Appearance is valid only if it can resolve meaningful signing text or an image. Border,
background, spacing, empty image region, and the standardized signing statement alone do not count.

- Text layout is Compact (one line; no wrap/truncation) or Stacked (one field per line).
- Image position is independently Left, Right, Above, or Below. Image prominence is Supporting,
  Balanced, or Primary (default), internally allocating 35%, 55%, or 75% on the relevant axis.
  Image-only uses all available area.
- Supported imports are content-validated PNG, JPEG, and static GIF. Animated/multiframe and vector
  images are rejected. Imports normalize to managed PNG: apply EXIF orientation, sRGB, preserve
  alpha, strip metadata, and retain original filename only for recognition. Over 25 MP or 20 MB is
  rejected; otherwise an explicitly confirmed optimized copy may reduce to 2048×2048.
- Transparent background controls compositing, not background removal. True preserves existing
  alpha; false flattens transparent pixels to white. Opaque images remain opaque.
- Fonts are exact bundled Sans Serif, Serif, or Monospace, 6–48 pt (default 10), bold/italic.
  Unsupported glyphs block signing with field/character guidance; no silent system fallback.
- Time formats are bounded: `2026-08-08 14:35`, `Aug 8, 2026, 2:35 PM`, or ISO
  `2026-08-08T18:35:00Z`. UTC is default; a zone indicator is always shown.
- Show “Digitally signed by” is standardized/localizable, default On, and remains available for
  image-only wet signatures. Compact separators are ` • `; labels use colons; empty values leave no
  placeholders or trailing separators.
- Text/background/border colors use a full solid-color picker with visual HSV selection, RGB,
  editable `#RRGGBB`, swatches, live preview, and eyedropper where supported; no alpha or gradient
  fills. Background defaults white; text/border black; border defaults Off and Thin when enabled.
- Text never silently shrinks. Exact fit validation blocks signing and recommends adjustment.

## 10. Placement Profile Application

A Placement stores a fixed one-based page, source visible width/height, source rotation, and
top-left-relative Left/Top/Width/Height in PDF points (72 points = 1 inch). It is reusable but not
document-bound.

Exact geometry applies exactly and jumps to its page. Dimension/rotation mismatch produces a
provisional exact proposal requiring Use, Adjust, or Place manually; never auto-scale, clamp, or
move. Missing target page creates no placement, navigates to the last page for orientation, and
offers Place on current page. Saving current placement as a reusable Placement never mutates the
document or active preset unless the user explicitly edits that preset.

## 11. State, Validation, and Feedback

Signing status states are: No document open; Select a signature preset; Setup required; Ready to
sign; Signing; Signed and verified locally; Saved but not verified; Signing failed. Each has one
primary heading, concise explanation, and at most one recommended next action, using icon, text, and
color. Self-signed normal copy is `Self-signed certificate — ready for local signing`; expanded
detail explains local validation without implying universal recognition.

The title is `FoliaSeal`, `filename.pdf — FoliaSeal`, or `filename.pdf * — FoliaSeal`. Reason,
Location, placement changes/removal, and confirmed output path make the unsigned draft dirty; preset
selection alone does not. Dirty Open/Close/Exit asks `Discard unsigned signing draft?`, defaults to
Continue editing, conditionally offers Sign and save when ready, and uses an explicit discard verb.

Candidate loading and signing progress are suppressed under about one second. Signing shows a real
stage after about one second, calm longer-than-expected copy after about ten seconds, and useful
technical activity after materially longer operation. It never shows fake percentages or imposes a
destructive timeout.

Destination suggestion is `<stem>-signed.pdf` with collision-safe numeric suffixes. The app never
silently renames after confirmation. Explicit source overwrite is permitted only after a safe,
Cancel-default warning and verified sibling temporary output. Existing destinations use standard
Replace confirmation. Encryption and restrictions must be preserved; inability to guarantee this
blocks signing.

External source changes never auto-reload. A condition-only banner blocks signing and offers Reload
or Ignore; missing source offers Locate or Close. Certification restrictions are preflighted; V1
blocks known or uncertain violations and has no Sign Anyway.

Dialogs use consequence verbs. Destructive choices are never default or initially focused; Escape
and window close cancel. Final signing defaults to Sign and save. Recovery defaults maximize data
preservation.

## 12. Resizing, Theme, and Visual Language

- Main minimum is 1100×700 logical pixels; Library minimum 1000×650. Below this V1 has no alternate
  compact/mobile layout. Toolbar overflows rather than wraps; Library preserves three columns and
  avoids ordinary horizontal scrolling.
- Follow system scale and device-pixel ratio; rerender PDF/preview while preserving semantic zoom
  and overlay alignment. Restore/clamp window geometry to available monitors.
- Settings offers System (default), Light, Dark. Use native palette and system accent. PDF and
  Appearance colors never change with app theme; transparency uses checkerboard.
- Use system UI font/metrics, neutral surfaces, familiar symbolic icons plus text for important
  actions, restrained borders/spacing, strong focus, and minimal nonmoving fades. No branded title
  bar, gradients, heavy shadows, dense web cards, or unnecessary motion.
- Persist window geometry/maximized state, rail width/divider, Library geometry/column widths, theme,
  default folders, and last Library catalog/sort. Do not reopen documents, drafts, dialogs, or the
  Library automatically.

## 13. Accessibility and Privacy

Tab order follows spatial/semantic order. Focus is strong and always visible. Essential actions have
accessible names, roles, state, and non-pointer alternatives. Preview has a textual summary; field
ordering supports keyboard Move Up/Down. Status and errors never rely on color or position alone.
Support system font scaling, high DPI, high contrast, broad Unicode user data, and translation-ready
strings. V1 UI language is English; full RTL behavior is not claimed.

Logs never contain passwords, credential-store values, private keys, PDF contents, selected text,
Reason, or Location. Prefer internal IDs over full identities. Paths may appear when necessary and
Help warns users. Logs are local, bounded/rotated, never uploaded automatically, and technical
details are copyable with error code, stage, and actionable cause.

## 14. Settings, Help, and Library Scale

Application Settings is a small modal transaction with Appearance (System/Light/Dark), default open
folder, and default signed-output folder; paths use Choose and Restore defaults, with Save/Cancel.

Help is canonical packaged Markdown with stable topic IDs, structured headings/keywords/related
links, and machine-readable index. The modeless in-app viewer renders safe local HTML from that same
corpus with search, Back/Forward, and contextual F1. No JavaScript or remote assets. CLI discovery is
`foliaseal help --list`, `foliaseal help <topic>`, `--format markdown`, and `--path`.

Catalog search is case-insensitive and live. Default sort is Name A–Z, optional Z–A; Certificates
also offer Expiration soonest. Search lasts only while Library is open. Persistent pins exist in all
catalogs, sort first, survive rename, and are retained in merged search results. No tags, folders,
usage counts, recent ordering, individual profile import/export, or separate Image Library in V1.

## 15. Certificate Workflows

The user-facing Certificates catalog combines the managed certificate file and its signing
configuration. A retained file without configuration remains visible as `Not configured for
signing`, sorts below configured certificates, and offers Configure, Export backup, or Delete; it is
not preset-selectable.

- **Import:** accept content-validated `.p12`/`.pfx`, request password when needed, inspect identity,
  issuer, validity, private-key presence, and warnings, then request a unique display name and
  optional Remember password. Copy into managed storage atomically. Reject missing private key,
  duplicates, unsupported content, and partial/cancelled imports without residue.
- **Create:** require common/full name and password confirmation; allow email, title, organization;
  prefill display name. Create one opinionated self-signed signing certificate with fixed five-year
  validity. Do not expose algorithms or key-size tuning. Offer Export backup after success.
- **Backup:** export an encrypted `.p12` through Save As using the existing password, prompting and
  validating if unavailable. Never reveal the password, emit an unencrypted private key, create a
  sidecar secret, or change managed state. Report the exact successful path.
- **Remember password:** enable only with secure storage and validate before saving. Disabling removes
  the stored secret but does not change the `.p12` password. Missing/rejected secret falls back to a
  manual prompt; V1 has no certificate-password change workflow.

Readiness treats valid/private-key-present as ready; expiry within 30 days warns but permits signing;
expired, not-yet-valid, missing file, or missing private key blocks. Password required is promptable.
Self-signed/local trust is neutral and nonblocking. The normal detail is: `This certificate was
created locally. The signature can be validated, but other systems may not independently recognize
the signer unless they trust this certificate.`

## 16. Document Safety and Review Boundaries

- Password-protected PDFs prompt before replacing the current document. Password is session-memory
  only and clears on Close, replacement, successful signing, or Exit. V1 respects permissions and
  provides no bypass.
- Certification and ordinary signatures are preflighted. A known or uncertain prohibited change
  blocks signing. Final verification evaluates all signatures; an unexpected validity change
  prevents finalization and preserves a recovery copy.
- Document Signatures distinguishes valid, changed after signature (including permitted change),
  invalid, could not verify, and unsigned. It distinguishes claimed signing time from a trusted
  timestamp and does not perform internet trust lookup.
- Ordinary PDF form fields are read-only; unsigned signature fields are the only V1 form exception.
- Pan mode may follow internal links and records lightweight Back/Forward history. External
  `http`, `https`, and `mailto` destinations show the destination and ask first. File, executable,
  JavaScript, arbitrary scheme, and embedded launch actions are blocked. Select/Place clicks never
  activate links.
- Annotations render but cannot be edited or interacted with; attachments and annotation popups are
  outside V1.
- The viewer honors page rotation already recorded in the PDF but provides no temporary or
  persistent rotation command.
- An external open request during active signing is deferred in memory, shown with filename and
  Cancel pending open, and processed only after success or recovery. A newer request replaces the
  pending request with notice.

## 17. Platform Realization

- **Platform:** Debian-family Linux desktop
- **Toolkit:** Qt (current target)
- **Status:** V1

Use native Qt menus, dialogs, focus semantics, palette roles, accessibility exposure, standard
shortcuts, window management, and full color dialog where needed for consistent RGB/Hex. Top-level
menu mnemonics must be unique even though Signing and Settings share an initial letter. Advisory file
locks may be attempted but are not a safety mechanism; external-change monitoring and atomic output
replacement remain required. Follow system scale and high-contrast behavior.

The fixed right rail and single-page viewer are deliberate product choices. The non-cancellable
post-confirmation transaction deliberately favors file integrity over a conventional Cancel button.

## 18. Visual Artifact Index

| Artifact | Status | Scope |
|---|---|---|
| [`ui/main-workspace-document-open-exploratory.svg`](ui/main-workspace-document-open-exploratory.svg) | Normative topology | Open-document frame, toolbar/canvas/right rail/status hierarchy |
| [`ui/main-workspace-no-document-exploratory.svg`](ui/main-workspace-no-document-exploratory.svg) | Normative topology | Direct-launch stable frame and empty state |
| [`ui/signature-library-presets-exploratory.svg`](ui/signature-library-presets-exploratory.svg) | Normative topology | Preset-dominant three-column Library |
| [`ui/appearance-profile-editor-exploratory.svg`](ui/appearance-profile-editor-exploratory.svg) | Normative topology | Content-first Appearance editor and sticky preview |
| [`ui/placement-profile-editor-exploratory.svg`](ui/placement-profile-editor-exploratory.svg) | Normative topology | Fixed-page Placement editor |
| [`ui/sign-and-save-states-exploratory.svg`](ui/sign-and-save-states-exploratory.svg) | Normative state hierarchy | Confirmation, active transaction, verification recovery |

Filenames retain `exploratory` as provenance; this index promotes their approved topology/state
hierarchy to normative status. Text requirements govern behavior not visible in the drawings.

## 19. Observable Acceptance Scenarios

1. Direct launch shows stable disabled document controls, primary Open PDF, secondary Library, and no
   recent files; keyboard alone can open menus and a PDF.
2. A new PDF has no preset selected. Selecting a partial preset visibly requests only its missing
   Certificate/Placement and never silently places a signature.
3. Pointer and keyboard users can create, adjust, remove, undo, and restore one placement; no
   off-page placement becomes unreachable.
4. An eligible unsigned signature field can be chosen only through an explicit command and remains
   fixed; an ineligible field explains why.
5. Preview and signed output use identical content, image alpha behavior, font, geometry, and frozen
   time; unsupported glyphs or overflow block signing before submission.
6. Source overwrite leaves the original untouched through signing and verification; failure exposes
   a preserved artifact and safe recovery.
7. Encrypted/restricted PDFs remain equally protected or signing is blocked.
8. A screen-reader/keyboard user can create a preset and Appearance, select it, place with Enter and
   arrows, invoke Sign and save, enter a password, and understand the result without pointer/color.
9. At minimum supported window sizes and across DPI/monitor changes, the canvas remains primary,
   rail remains right, toolbar does not wrap, and controls remain reachable.
10. Help topics are searchable in-app and readable as ordinary Markdown through the documented CLI
    and installed path without network access.

## 20. Open Questions

None for V1. Human usability testing may justify an explicitly approved revision, especially to
status copy, right-rail proportions, or V2 scope; it does not silently alter this contract.

## 21. Decision Log

| Date | Decision | Rejected alternative | Reason |
|---|---|---|---|
| 2026-08-09 | Preset-required, one-signature workflow | Parallel manual assembly; multiple pending signatures | One coherent path and bounded state |
| 2026-08-09 | Fixed right signing rail | Bottom signing bar; moving contextual controls | Preserve vertical space and spatial memory |
| 2026-08-09 | Library-centered reusable editing | Live-document-first reusable editors | Separate reusable management from per-document action |
| 2026-08-09 | Fixed-page reusable Placement | Current-page semantic; automatic scaling | Controlled multi-page forms require deterministic page/geometry |
| 2026-08-09 | Explicit source overwrite allowed | Refuse source destination | Respect deliberate intent while preserving original until verified |
| 2026-08-09 | No printing or general PDF properties in V1 | General viewer parity | Keep product focused on review/sign/save/verify |
