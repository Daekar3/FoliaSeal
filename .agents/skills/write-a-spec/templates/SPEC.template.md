# <Product> Product Specification

This document is the canonical product specification for `<Product>`.

Use this document for product goals, anti-goals, user-visible workflow, and release criteria.
Use `docs/SCHEMAS.md` for the canonical persistent object model.
Use `docs/ARCHITECTURE.md` for the codebase as it exists today.

This specification describes the intended product direction. It may supersede older implementation assumptions.

## Document Governance
State whether this document is editable, frozen, or requires explicit approval for changes.

## Product Boundary

Describe what the product is in one short paragraph.

The product is not:

NGO01. <non-goal 1>
NGO02. <non-goal 2>
NGO03. <non-goal 3>

## Product Posture

State the current delivery posture and decision bias. Examples:

- optimize for clarity over compatibility
- optimize for stability over speed of change
- treat old persisted shapes as disposable during V1

## Primary User Story

The core story is:

1. <user opens or starts something>
2. <user reviews or configures it>
3. <user performs the primary action>
4. <user verifies the outcome>

## Goals

### 1. <Goal name>

Describe the user-facing outcome this goal protects.

Must support:

CAP01. <capability>
CAP02.- <capability>

### 2. <Goal name>

Describe the user-facing outcome this goal protects.

Must support:

CAP03.- <capability>
CAP04.- <capability>

### 3. <Goal name>

Describe the user-facing outcome this goal protects.

Must support:

CAP05. - <capability>
CAP06.- <capability>

Add or remove goal sections as needed. Prefer a small number of clear goals.

## Reusable Object Semantics

Only include this section if the product has named reusable user-facing objects.

### <Object name>

OBJ01. Responsibility: <what this object means to the user>
OBJ01. Supports: <create/edit/delete/rename/select/etc.>
OBJ01. Does not imply: <important non-behavior or non-ownership>

## Output Behavior

State what the primary output is, what counts as success, and any important save/export/reopen expectations.

## UI Principles

UIP01. <principle>
UIP02. <principle>
UIP03. <principle>

Keep these product-facing. Do not drift into widget or module design here.

## Anti-Goals

AG01. <explicitly out of scope item>
AG02. <explicitly out of scope item>
AG03. <explicitly out of scope item>

## Future Direction

Capture likely next-step expansion without turning it into a current commitment.

## Release Bar

The release is ready when:

OBS01. <observable acceptance condition>
OBS02. <observable acceptance condition>
OBS03. <observable acceptance condition>
