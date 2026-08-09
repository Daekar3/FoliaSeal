# FoliaSeal Canonical Schemas

This document defines the canonical persistent object model for FoliaSeal V1.

Use this document for the intended names, responsibilities, relationships, and persistence rules of
user-facing objects.
Use [`SPEC.md`](SPEC.md) for product goals and anti-goals.
Use [`UI_SPEC.md`](UI_SPEC.md) for the canonical interface and interaction contract.
Use [`ARCHITECTURE.md`](ARCHITECTURE.md) for the current
implementation and its drift from this target model.

This document is intentionally product-facing. It may describe the desired object model even when
current code still uses older names or older storage shapes.

## Document Governance
This document is currently frozen.  No changes may be made to it without explicit user permission.  If you believe changes are necessary, escalate that to the user with a full description of what changes are necessary, why, and what the impact of not making the changes will be.

## Compatibility Stance

V1 does not prioritize backward compatibility for persisted local objects.

Schema evolution should favor cleaner naming and cleaner object boundaries over migration shims,
unless a migration materially reduces user pain without complicating the codebase.

## Canonical Object Set

FoliaSeal V1 has six primary persistent object types:

- `AppSettings`
- `ManagedCertificate`
- `CertificateConfiguration`
- `AppearanceProfile`
- `PlacementProfile`
- `SignaturePreset`

The app may persist additional operational state internally, but these are the canonical user-facing
objects.

## Global Rules

### 1. User-facing names are metadata, not storage keys

Each persistent object should have:

- a stable internal identifier
- a user-facing display name

Renaming an object should not require changing its internal identity.

### 2. References are shallow

`SignaturePreset` composes other objects by reference only.

V1 does not support inheritance or partial override semantics between presets and their referenced
objects.

### 3. Secret material is not stored in ordinary config payloads

Certificate passwords, when persisted, should live in the OS credential store or an explicitly
supported secure fallback. They must not be stored as plain text in ordinary configuration files.

### 4. Catalog names and pins are stable metadata

Display names are trimmed, required, and case-insensitively unique within their own catalog. Names
may repeat across different catalogs. Presets, certificate entries, appearances, and placements
support persistent pin metadata; renaming does not change pin state and duplication starts unpinned.

## AppSettings

`AppSettings` stores environment-level preferences that are not part of reusable signing behavior.

### Responsibility

Own global application behavior such as default output location and similar environment-level
choices.

### Does not own

- certificate identity data
- visible signature appearance choices
- placement choices
- signing object composition

### Canonical fields

```json
{
  "schema_version": 1,
  "default_output_directory": "/home/user",
  "default_open_directory": "/home/user",
  "ui": {
    "appearance_mode": "system",
    "main_window_geometry": "toolkit-owned-opaque-value-or-null",
    "main_window_maximized": false,
    "signing_rail_width": 320,
    "signing_rail_divider": "toolkit-owned-relative-value",
    "library_window_geometry": "toolkit-owned-opaque-value-or-null",
    "library_column_widths": [180, 300, 520],
    "library_last_catalog": "presets",
    "library_sort": "name_ascending"
  }
}
```

### Notes

- `default_output_directory` defaults to the user home directory until explicitly changed.
- Settings should remain distinct from reusable signing objects.
- UI layout preferences may be persisted, but open documents, unsigned drafts, dialogs, active
  presets, and Library open state must not be restored across launches.
- `appearance_mode` is one of `system`, `light`, or `dark`, with `system` as default.

## ManagedCertificate

`ManagedCertificate` is the application-managed certificate file record.

### Responsibility

Represent a certificate file that the app owns in managed storage, whether it was:

- created in-app
- imported and copied into managed storage

### Canonical fields

```json
{
  "schema_version": 1,
  "managed_certificate_id": "uuid-or-stable-id",
  "display_name": "Board Secretary 2026",
  "storage_filename": "cert_7f4a9b2f.p12",
  "source_kind": "created",
  "created_at": "2026-05-05T12:00:00Z",
  "pinned": false,
  "subject_summary": {
    "common_name": "Morgan Ellery",
    "distinguished_name": "CN=Morgan Ellery,O=Northwind Ledger Holdings",
    "email": "morgan@example.com",
    "title": "Board Secretary",
    "company": "Northwind Ledger Holdings"
  },
  "issuer_summary": "Morgan Ellery",
  "valid_from": "2026-05-05T12:00:00Z",
  "valid_until": "2031-05-05T12:00:00Z",
  "fingerprint_sha256": "hex-encoded-fingerprint"
}
```

### Rules

- `storage_filename` is app-assigned and stable.
- The file lives in a controlled, user-accessible application data directory.
- The app does not reference arbitrary external certificate paths after import.
- The managed record stores public inspection metadata only; private-key presence and password
  validity are checked against the managed PKCS#12 file when needed.
- Deleting a `ManagedCertificate` is a separate action from deleting a
  `CertificateConfiguration`.

## CertificateConfiguration

`CertificateConfiguration` is the user-facing signing identity selection object.

### Responsibility

Capture how the app should use a managed certificate for signing.

### Canonical fields

```json
{
  "schema_version": 1,
  "certificate_configuration_id": "uuid-or-stable-id",
  "display_name": "Corporate Records Signing",
  "managed_certificate_id": "uuid-or-stable-id",
  "save_password": true,
  "password_secret_ref": "credential-store-key-or-null",
  "notes": "optional freeform note",
  "pinned": false
}
```

### Rules

- There is one primary `CertificateConfiguration` per `ManagedCertificate` in V1.
- Missing managed certificate files must fail gracefully with helpful feedback.
- `save_password` is allowed only when secure storage is available.
- `CertificateConfiguration` supports create, save, rename, edit, and delete only.
- No disable/archive/retire/revoke states in V1.

## AppearanceProfile

`AppearanceProfile` captures signing-specific visible appearance behavior.

### Responsibility

Persist the bounded, signing-specific appearance model used for preview and final visible output.

### Canonical fields

```json
{
  "schema_version": 2,
  "appearance_profile_id": "uuid-or-stable-id",
  "display_name": "Board Approval",
  "pinned": false,
  "text_layout": "compact",
  "image_position": "left",
  "image_prominence": "primary",
  "show_field_names": true,
  "show_signing_statement": true,
  "datetime_format_preset": "compact_numeric",
  "timezone_display_mode": "utc",
  "visible_field_order": [
    "common_name",
    "title",
    "company",
    "signing_time"
  ],
  "hidden_fields": [
    "email",
    "location",
    "reason"
  ],
  "text_style": {
    "font_family": "Sans Serif",
    "font_size_pt": 10.0,
    "bold": false,
    "italic": false,
    "text_color_hex": "#000000"
  },
  "box_style": {
    "show_border": false,
    "border_color_hex": "#000000",
    "border_thickness": "thin",
    "background_color_hex": "#FFFFFF",
    "transparent_background": false
  },
  "image_asset": {
    "managed_asset_id": "optional-stable-id-or-null",
    "storage_filename": "image_7f4a9b2f.png",
    "original_filename": "wet-signature.gif",
    "width_px": 1400,
    "height_px": 620,
    "has_alpha": true
  }
}
```

### Rules

- Appearance remains bounded to the signing domain.
- Users may choose field visibility and order.
- The bounded field set is Common Name, Distinguished Name, Email, Title, Company, Signing Time,
  Reason, and Location.
- Arbitrary custom field content is not part of the canonical end-user model.
- Preview/output fidelity takes priority over preserving every possible appearance option.
- `text_layout` is `compact` or `stacked`; `image_position` is `left`, `right`, `above`, or
  `below`; `image_prominence` is `supporting`, `balanced`, or `primary`.
- `datetime_format_preset` is a bounded product enum, not a raw formatting string. UTC is default.
- Font family is one of the exact bundled Sans Serif, Serif, or Monospace assets; size is 6–48 pt.
- Managed images are normalized PNG assets. They preserve imported alpha but contain no source-path
  dependency or retained EXIF/comments/location metadata. Multiple appearances may reference one
  immutable asset; unreferenced assets may be garbage-collected.
- `transparent_background` controls compositing only. False flattens transparent image pixels to
  white; true preserves existing alpha and does not manufacture transparency.
- The standardized signing statement is fixed/localizable text, not arbitrary user content.
- An appearance must be capable of resolving meaningful signing text or an image. Styling and the
  signing statement alone are insufficient.

## PlacementProfile

`PlacementProfile` captures repeatable placement behavior.

### Responsibility

Persist a named reusable placement setup without binding it to document identity.

### Canonical fields

```json
{
  "schema_version": 2,
  "placement_profile_id": "uuid-or-stable-id",
  "display_name": "Purchase Requisition Bottom Right",
  "pinned": false,
  "page_number": 3,
  "source_page": {
    "visible_width_pt": 612.0,
    "visible_height_pt": 792.0,
    "rotation_degrees": 0
  },
  "rect": {
    "left_pt": 360.0,
    "top_pt": 666.0,
    "width_pt": 180.0,
    "height_pt": 54.0
  }
}
```

### Rules

- Placement profiles are not document-specific in V1.
- Users manage them by name.
- Mouse placement and numeric placement are both first-class product behavior.
- The UI for numeric placement should be compact and efficient.
- `page_number` is fixed and one-based. The geometry is relative to the visible, already-rotated
  page with a top-left origin. PDF-internal bottom-left transforms occur only at the PDF boundary.
- `source_page` records geometry compatibility but no document identity, path, content, or field ID.
- Dimension/rotation mismatch never silently scales, clamps, or moves the rectangle.

## SignaturePreset

`SignaturePreset` is a lightweight composition object.

### Responsibility

Combine references to other reusable objects for faster setup.

### Canonical fields

```json
{
  "schema_version": 2,
  "signature_preset_id": "uuid-or-stable-id",
  "display_name": "Board Approval Default",
  "pinned": false,
  "certificate_configuration_id": "optional-id-or-null",
  "appearance_profile_id": "required-id",
  "placement_profile_id": "optional-id-or-null",
  "reason_default": "optional-string-or-empty",
  "location_default": "optional-string-or-empty"
}
```

### Rules

- `appearance_profile_id` is required. Certificate and placement references are optional.
- The preset does not override its referenced objects.
- Reason and Location defaults are permitted only when the referenced Appearance exposes those
  fields. Changing the Appearance to exclude a nonblank default requires explicit clearing.
- A newly opened document has no active preset. Loading a preset never carries an active certificate
  or placement from a previous document.
- Missing references are never allowed. Deletion must resolve dependent presets atomically.

## Per-Signing Session Inputs

These values are part of the current signing session, not long-lived identity objects.

### Canonical fields

```json
{
  "signature_preset_id": "required-id",
  "certificate_configuration_id": "resolved-id",
  "placement_profile_id": "optional-source-profile-id-or-null",
  "reason": "Approved for board circulation",
  "location": "Charlottesville, Virginia",
  "output_path": "/home/user/Documents/signed.pdf",
  "placement": {
    "page_number": 3,
    "left_pt": 360.0,
    "top_pt": 666.0,
    "width_pt": 180.0,
    "height_pt": 54.0,
    "existing_signature_field_name": "optional-session-only-name-or-null"
  }
}
```

### Rules

- `reason` and `location` are per-signing inputs with optional defaults from reusable objects.
- `signing_time` is system-generated. Preview time is live; Sign and save freezes the exact displayed
  value before final confirmation and uses it for both appearance and PDF metadata.
- Exactly one placement and one pending new signature are permitted in a V1 signing session.
- The output path is confirmed per draft and is not a reusable-object property.

## Review and Signing Draft State

The app may maintain ephemeral draft state while a document is open.

This is not a canonical durable schema in V1. Arbitrary draft crash recovery is out of scope.

Ephemeral draft state may include:

- currently open document
- currently selected certificate configuration
- currently selected appearance profile
- currently selected placement profile
- currently selected signature preset
- current per-signing values such as `reason` and `location`
- current placed signature rectangle
- frozen signing time during a confirmed signing attempt
- undo/redo history for placement operations

Draft state is never restored across process restart. During an active signing transaction only,
FoliaSeal may persist a secret-free recovery journal containing owned paths and operation stage.

## Storage and File-Ownership Rules

### Managed certificate storage

- App-created certificates always go to the app-managed default location.
- Imported certificates are copied into the managed location.
- Export is the portability mechanism.

### Reusable object storage

- Reusable object catalogs should be stored in human-readable local files.
- It is acceptable for V1 to replace old shapes rather than maintain compatibility shims.
- Internal references and schema versions must remain stable and human-readable enough for safe
  folder-level copying. Certificate passwords remain outside these files in the OS credential store.
- Presets, certificates/configurations, appearances, and placements support persistent `pinned`
  metadata. Duplicate objects begin unpinned.
- There is no separate user-facing image catalog; managed immutable image assets are owned through
  Appearance references.

## Current Implementation Drift

The current codebase has moved most persisted reusable signing objects toward this canonical model:

- `SignaturePreset` is now a reference-only composition object.
- reusable appearance and placement data are split into `AppearanceProfile` and `PlacementProfile`.
- certificate identity data is represented through `ManagedCertificate` and `CertificateConfiguration`.
- `AppSettings` exists as a first-class app-wide preferences object.

Known implementation drift includes older persisted shapes or behavior for:

- optional Appearance references in presets
- current-page Placement semantics and PDF-internal bottom-origin rectangles
- raw date/time format strings, older layout names, and incomplete image/transparency fields
- source/output-path restrictions that may reject the user's explicit source-overwrite intent

Some older implementation vocabulary also remains, including:

- the historical `profile_storage.py` module name
- the historical user-visible storage path `Signature Profiles/profiles.json`
- some older "profile" terminology in internal documentation and migration history

Those remaining differences are implementation drift, not the intended long-term product vocabulary.
