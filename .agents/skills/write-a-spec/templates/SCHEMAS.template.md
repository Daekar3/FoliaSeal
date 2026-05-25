# <Product> Canonical Schemas

This document defines the canonical persistent object model for `<Product>`.

Use this document for intended names, responsibilities, relationships, and persistence rules of user-facing objects.
Use `docs/SPEC.md` for product goals and anti-goals.
Use `docs/ARCHITECTURE.md` for the current implementation and its drift from this target model.

This document is product-facing. It may describe the desired object model even when current code still uses older names or storage shapes.

## Document Governance
State whether this document is editable, frozen, or requires explicit approval for changes.

## Compatibility Stance

State whether persisted-object compatibility is a priority, optional, or intentionally de-emphasized.

## Canonical Object Set

List the primary persistent object types:

- `<ObjectTypeOne>`
- `<ObjectTypeTwo>`
- `<ObjectTypeThree>`

If there is transient or operational state, say whether it is canonical or secondary.

## Global Rules

### 1. <Rule name>

State a cross-object rule such as identity, naming, reference depth, or secret handling.

### 2. <Rule name>

State another cross-object rule that all object types must follow.

### 3. <Rule name>

State another cross-object rule that all object types must follow.

## <ObjectTypeOne>

`<ObjectTypeOne>` is the canonical user-facing object for `<purpose>`.

### Responsibility

Describe what this object owns.

### Does not own

- <non-responsibility>
- <non-responsibility>

### Canonical fields

```json
{
  "schema_version": 1,
  "<object_id_field>": "uuid-or-stable-id",
  "display_name": "Example Name"
}
```

### Rules

- <identity rule>
- <reference rule>
- <validation or lifecycle rule>

## <ObjectTypeTwo>

`<ObjectTypeTwo>` is the canonical user-facing object for `<purpose>`.

### Responsibility

Describe what this object owns.

### Canonical fields

```json
{
  "schema_version": 1,
  "<object_id_field>": "uuid-or-stable-id"
}
```

### Rules

- <rule>
- <rule>

Repeat the object section pattern for each canonical object type.

## Per-Session Inputs

Only include this section if some important inputs are session-only rather than persisted.

### Canonical fields

```json
{
  "<field>": "<value>"
}
```

### Rules

- <session-state rule>

## Review and Draft State

Only include this section if the product has non-canonical in-progress state that still needs clear shape or naming.

## Storage and File-Ownership Rules

### <Storage area name>

- Location: <where data lives conceptually>
- Ownership: <who creates, edits, deletes it>
- Notes: <backup/import/export/security constraints>

## Current Implementation Drift

List the highest-signal mismatches between the canonical model and the current code or storage shape.
