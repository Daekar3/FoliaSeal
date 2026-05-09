# FoliaSeal Canonical Schemas

This document defines the canonical persistent object model for FoliaSeal V1.

Use this document for the intended names, responsibilities, relationships, and persistence rules of
user-facing objects.
Use [`docs/SPEC.md`](/home/daekar/FoliaSeal/docs/SPEC.md) for product goals and anti-goals.
Use [`docs/ARCHITECTURE.md`](/home/daekar/FoliaSeal/docs/ARCHITECTURE.md) for the current
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
  "linux_packaging_channel": "primary",
  "ui": {
    "last_window_layout": "optional"
  }
}
```

### Notes

- `default_output_directory` defaults to the user home directory until explicitly changed.
- Settings should remain distinct from reusable signing objects.

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
  "subject_summary": {
    "common_name": "Morgan Ellery",
    "email": "morgan@example.com",
    "title": "Board Secretary",
    "company": "Northwind Ledger Holdings"
  }
}
```

### Rules

- `storage_filename` is app-assigned and stable.
- The file lives in a controlled, user-accessible application data directory.
- The app does not reference arbitrary external certificate paths after import.
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
  "notes": "optional freeform note"
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
  "schema_version": 1,
  "appearance_profile_id": "uuid-or-stable-id",
  "display_name": "Board Approval",
  "layout_template": "single_line",
  "stamp_position": "top",
  "show_field_names": true,
  "datetime_format": "%Y-%m-%d %H:%M",
  "timezone_display_mode": "local",
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
    "font_size_pt": 8.5,
    "bold": false,
    "italic": false,
    "text_color_hex": "#000000"
  },
  "box_style": {
    "show_border": true,
    "border_color_hex": "#000000",
    "border_width_pt": 1.0,
    "background_color_hex": "#FFFFFF"
  },
  "image_stamp_ref": "optional-managed-image-ref-or-null"
}
```

### Rules

- Appearance remains bounded to the signing domain.
- Users may choose field visibility and order.
- Arbitrary custom field content is not part of the canonical end-user model.
- Preview/output fidelity takes priority over preserving every possible appearance option.

## PlacementProfile

`PlacementProfile` captures repeatable placement behavior.

### Responsibility

Persist a named reusable placement setup without binding it to document identity.

### Canonical fields

```json
{
  "schema_version": 1,
  "placement_profile_id": "uuid-or-stable-id",
  "display_name": "Purchase Requisition Bottom Right",
  "page_selection_mode": "current_page",
  "rect": {
    "left_pt": 360.0,
    "bottom_pt": 72.0,
    "width_pt": 180.0,
    "height_pt": 54.0
  },
  "numeric_fine_tuning_enabled": true
}
```

### Rules

- Placement profiles are not document-specific in V1.
- Users manage them by name.
- Mouse placement and numeric placement are both first-class product behavior.
- The UI for numeric placement should be compact and efficient.

## SignaturePreset

`SignaturePreset` is a lightweight composition object.

### Responsibility

Combine references to other reusable objects for faster setup.

### Canonical fields

```json
{
  "schema_version": 1,
  "signature_preset_id": "uuid-or-stable-id",
  "display_name": "Board Approval Default",
  "certificate_configuration_id": "optional-id-or-null",
  "appearance_profile_id": "optional-id-or-null",
  "placement_profile_id": "optional-id-or-null"
}
```

### Rules

- All three references are optional in V1.
- The preset does not override its referenced objects.
- Loading a preset applies immediately to the current draft.
- Loading a preset without a certificate reference leaves an existing active certificate in place.

## Per-Signing Session Inputs

These values are part of the current signing session, not long-lived identity objects.

### Canonical fields

```json
{
  "reason": "Approved for board circulation",
  "location": "Charlottesville, Virginia",
  "output_path": "/home/user/Documents/signed.pdf"
}
```

### Rules

- `reason` and `location` are per-signing inputs with optional defaults from reusable objects.
- `signing_time` is always system-generated at signing time and is never user-editable.

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

## Storage and File-Ownership Rules

### Managed certificate storage

- App-created certificates always go to the app-managed default location.
- Imported certificates are copied into the managed location.
- Export is the portability mechanism.

### Reusable object storage

- Reusable object catalogs should be stored in human-readable local files.
- It is acceptable for V1 to replace old shapes rather than maintain compatibility shims.

## Current Implementation Drift

The current codebase has moved most persisted reusable signing objects toward this canonical model:

- `SignaturePreset` is now a reference-only composition object.
- reusable appearance and placement data are split into `AppearanceProfile` and `PlacementProfile`.
- certificate identity data is represented through `ManagedCertificate` and `CertificateConfiguration`.
- `AppSettings` exists as a first-class app-wide preferences object.

Some older implementation vocabulary remains, including:

- the historical `profile_storage.py` module name
- the historical user-visible storage path `Signature Profiles/profiles.json`
- some older "profile" terminology in internal documentation and migration history

Those remaining differences are implementation drift, not the intended long-term product vocabulary.
