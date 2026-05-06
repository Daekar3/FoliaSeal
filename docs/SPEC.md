# FoliaSeal Product Specification

This document is the canonical product specification for FoliaSeal.

Use this document for product goals, anti-goals, user-visible workflow, and release criteria.
Use [`docs/SCHEMAS.md`](/home/daekar/FoliaSeal/docs/SCHEMAS.md) for the canonical persistent object model.
Use [`docs/ARCHITECTURE.md`](/home/daekar/FoliaSeal/docs/ARCHITECTURE.md) for the codebase as it exists today.

This specification describes the intended V1 product direction. It is allowed to supersede older
implementation assumptions and older persisted-object behavior.

## Document Governance
This document is currently frozen.  No changes may be made to it without explicit user permission.  If you believe changes are necessary, escalate that to the user with a full description of what changes are necessary, why, and what the impact of not making the changes will be.

## Product Boundary

FoliaSeal is a Linux desktop PDF signing application with a GUI.

V1 is a signing-and-review product, not a general PDF editor. The app may be architected so V2 can
add page operations such as add, remove, move, and crop, but those are not V1 features.

FoliaSeal is not:

- a document management system
- a cloud workflow product
- an enterprise trust administration tool
- a broad PDF manipulation framework
- a general page-design or signature-card design tool

## V1 Product Posture

V1 is in a move-fast-and-break-things stage.

Compatibility with previously saved profiles, presets, or similar local objects is not a V1
priority. If the product model becomes cleaner by replacing an old schema or workflow, V1 should
prefer replacement over compatibility layers.

Internal architecture should favor clarity, replaceability, and user-facing coherence over
preserving existing module boundaries, UI structure, or persisted shapes.

## Primary User Story

The core V1 story is:

1. Open a PDF in a familiar desktop application.
2. Review the document comfortably.
3. Choose or create a signing certificate.
4. Choose or refine a signing setup.
5. Place a visible approval signature.
6. Preview the signed appearance on the document page.
7. Confirm readiness.
8. Save the signed output to a user-chosen path.
9. Reopen and verify the result.
10. Add another approval signature later if document permissions allow it.

## V1 Goals

### 1. Familiar desktop-document workflow

The main window should be document-centric, not control-centric.

The app should follow standard desktop conventions such as:

- `File > Open`
- `File > Save As`
- settings/preferences
- expected keyboard shortcuts

The main workflow should be explicitly staged but not rigid:

`Open -> Review -> Choose preset/certificate -> Place -> Preview readiness -> Sign -> Save -> Verify`

The user should be able to revisit earlier stages without friction.

### 2. Full signing workflow for non-expert users

V1 must support a complete GUI signing workflow, not merely a headless signing engine with a thin
wrapper.

That workflow includes:

- open one PDF at a time
- navigate pages
- zoom and pan
- search document text
- select/copy document text
- inspect existing signatures
- place a visible signature with mouse-driven placement
- fine-tune placement numerically
- preview the visible result directly on the document page
- sign with a local certificate
- save the output through a standard file-save dialog
- verify the signed result with plain-language guidance

### 3. Visible approval signatures as the primary path

V1 is centered on visible approval signatures.

Invisible signatures are not a primary V1 UX concern.
Certification signatures and document-permission policy controls are not part of the main V1 GUI
surface.

The app must support reopening a previously signed PDF and adding another approval signature when
document permissions allow it. The product should not default to locking the file against future
signatures.

### 4. WYSIWYG trust between preview and final output

The on-page visible signature preview is the canonical user-facing representation.

The product should optimize first for “this is what the signed document will look like,” with
technical summaries and metadata details remaining secondary.

Preview/output fidelity is a product principle. If a control or behavior undermines trust between
preview and signed output, the product should constrain, move, or remove that control.

V1 should prefer a small number of high-confidence appearance/layout combinations over maximum
theoretical expressiveness.

### 5. Reusable signing objects

V1 should support reusable named signing objects:

- `Certificate Configuration`
- `Appearance Profile`
- `Placement Profile`
- `Signature Preset`

These objects are separate and are composed through `Signature Preset`.
`Signature Preset` may be partial. It does not need to include a certificate reference.

Reusable-object management should exist both:

- in the main signing workflow for quick selection and quick reuse
- in a dedicated library/settings area for full create/edit/delete management

Editing `Appearance Profile` and `Placement Profile` must remain contextual. Live-document editing
is the primary workflow. Synthetic/template preview contexts are secondary fallback tools.

### 6. Managed certificate workflow

V1 certificate handling is a product feature, not an implementation detail.

V1 must support:

- importing an existing PKCS#12 certificate
- creating a new self-signed or otherwise locally managed signing certificate in-app
- saving and loading certificate configurations
- optional saved certificate passwords
- exporting/backing up app-managed certificates
- deleting app-managed certificates

Certificate creation should be:

- guided
- opinionated
- suitable for non-expert users
- limited to one recommended signing-certificate flavor

V1 does not cover:

- CA procurement flows
- enterprise certificate lifecycle management
- revocation infrastructure
- archival/retirement states

### 7. Clear signing readiness and failure handling

V1 should present a clear ready-to-sign state that summarizes whether certificate, placement,
appearance, and document constraints are satisfied.

The GUI should prevent obviously invalid signing actions early when it can do so confidently, while
still validating again at submit time.

Verification and signing errors must:

- use plain-language explanations
- provide explicit recommended next actions when possible
- offer technical detail in expanded views, not as the primary presentation

### 8. Offline-first core workflow

The core V1 signing workflow must work fully offline.

Offline verification is also required. The app should provide its best local assessment honestly and
should distinguish between what it can know offline and what depends on external trust context.

Timestamping and broad trust-policy controls should stay out of the normal V1 GUI workflow.

### 9. Packaged Linux desktop distribution

V1 is not a source-only developer tool.

Packaged Linux desktop distribution is part of the product requirement. The project may target one
primary Linux packaging/distribution mode first rather than multiple formats at once.

## Reusable Object Semantics

### Certificate Configuration

A `Certificate Configuration` is the user-facing app object used to select and configure a managed
certificate for signing.

It supports create, save, rename, edit, and delete.

Deleting a certificate configuration does not automatically delete the underlying managed
certificate file.

### Appearance Profile

An `Appearance Profile` captures signing-specific visible appearance choices.

It may include rich signing appearance customization, but it remains bounded by the signing domain.
It must not become a freeform design system or general page composition tool.

Visible content should stay semantically tied to certificate/signing metadata. Users may hide
fields, reorder fields, and configure presentation, but arbitrary decorative field content is not a
V1 product goal.

### Placement Profile

A `Placement Profile` is a named reusable placement setup. It is not document-bound.

The app should not try to infer document identity or automatically match placements to known
documents. Users can name placements according to their own conventions.

### Signature Preset

A `Signature Preset` composes references to reusable objects. In V1 it stores references only and
does not partially override component objects.

Loading a partial preset:

- leaves the current certificate selection untouched if one is already active
- makes clear that the preset did not define a certificate
- still requires explicit certificate selection before signing if none is active

## Output Behavior

The app should always use an explicit save dialog for signed output.

The default output directory is the user’s home directory unless the user changes that global app
setting.

Overwrite confirmation should use the normal OS warning when available. If the platform dialog does
not provide that warning, the app must require explicit confirmation before overwriting an existing
file.

## UI Principles

The main V1 window should be document-centric.

The product should bias toward a `Signature Preset`-first setup flow, while still allowing manual
assembly of certificate, appearance, and placement when needed.

The app should support a quick-sign path for experienced users once a valid setup and document are
in place, but quick sign must still stop at an explicit readiness/sign confirmation step.

That confirmation step should:

- stay simple and unintimidating
- keep the signature preview on the document page as the primary focus
- show a concise summary of the active signing objects, output target, and any caveats

V1 may aggressively simplify and reorganize the current GUI to serve this workflow, even if some
existing low-level controls move into secondary views or disappear from the main path.

## V1 Anti-Goals

The following are explicit V1 anti-goals:

- opportunistic PDF-editing creep beyond signing and review
- tabbed or multi-document workflows
- multi-signature staging in one unsaved draft
- broad trust-policy configuration in the primary GUI
- timestamping in the primary GUI path
- enterprise trust administration
- organizational certificate lifecycle management
- revocation infrastructure
- audit/reporting workflows as a product feature
- cloud/account integrations
- plugin/extensibility frameworks
- general-purpose signature-card design tooling
- arbitrary custom visible-signature fields or rich-text composition

## V2 Direction

The intended V2 direction includes page operations such as:

- add pages
- remove pages
- move/reorder pages
- crop pages

Those operations should influence architecture decisions when they clearly affect current object
boundaries, but they must not be opportunistically added to V1.

## Release Bar

V1 is done when a non-expert user can do the following in a packaged Linux desktop app:

- create or import a certificate
- manage certificate configurations
- review a PDF
- search/select/copy as needed
- choose or assemble a signing setup
- place a visible approval signature
- save and reuse appearance, placement, and preset objects
- sign offline
- save to a user-chosen output path
- reopen the signed file
- verify signatures with plain-language guidance
- add another approval signature when permissions allow

If a feature does not materially support that end-to-end story, it is secondary to V1.
