---
name: architecture-steward
description: Create, audit, and maintain a project-level architecture document describing code structure, ownership, object models, contracts, dependencies, data flow, and cross-component interactions.
---

# Architecture Steward Skill

Use this skill when the user asks to:
- create an architecture document for a new or existing project
- explain the structure of a codebase
- document module ownership, object models, public APIs, contracts, or dependencies
- update code in a way that changes project structure or cross-component behavior
- check whether architecture documentation matches the code
- prevent architectural drift

The canonical document is:

`docs/ARCHITECTURE.md`

If the repository uses a different architecture document, ask before changing the canonical path unless the user has already specified the path.

## Primary goal

Maintain a single project-level source of truth that describes how the project is structured, what each major piece owns, how those pieces interact, what contracts exist between them, and what design rules should guide future changes.

The document must describe the code as it actually exists, not as it is wished to exist.

## Operating principles

1. Prefer accuracy over polish.
2. Distinguish confirmed facts from inferred design intent.
3. Do not invent architecture.
4. Do not silently normalize inconsistencies.
5. Treat public APIs, persisted data formats, configuration schemas, CLI commands, database schemas, file formats, and external integrations as contracts.
6. Keep the document useful for future maintainers, not just the current task.
7. When the code and document disagree, say so plainly.
8. When a design decision needs user judgment, ask for feedback before encoding it as settled architecture.
9. Keep historical rationale only when it helps future maintainers understand why the current structure exists.
10. Update the document in the same change as architecture-affecting code changes.

## When creating the document for an existing project

First inspect the repository before drafting.

Survey:
- top-level files and directories
- package or project manifests
- application entry points
- build, test, and deployment configuration
- source directory structure
- major classes, modules, packages, or services
- public interfaces and exported symbols
- database, persistence, file, or message schemas
- configuration surfaces
- external integrations
- tests that reveal intended behavior

Then produce a first-pass architecture map.

Classify findings as:
- Confirmed by code
- Confirmed by tests
- Confirmed by existing documentation
- Inferred
- Unclear / needs user feedback

Do not present inferred material as fact.

## When creating the document for a new project

Start by asking the user for design intent when necessary.

Useful questions:
- What is the project supposed to do?
- What are the major user-facing surfaces?
- What are the non-negotiable constraints?
- What data or files must remain backward compatible?
- What parts should be easy to replace later?
- What parts are intentionally simple for now?
- What future expansion is likely?

If the user has already supplied enough information, proceed without asking.

For a new project, create an initial document that separates:
- Current implementation
- Intended architecture
- Open decisions
- Deferred decisions

## Required document structure

Use the architecture sections below as a starting point.  Refer to references/architecture-template.md for a markdown template and references/architecture-review-checklist.md for a review checklist.

# Architecture

## 1. Purpose and scope

Briefly describe what the project does and what this document governs.

## 2. Architectural principles

List the practical rules that should guide future changes.

Examples:
- Keep UI logic separate from persistence logic.
- Treat file formats as stable contracts.
- Keep platform-specific code isolated.
- Prefer boring dependencies.
- Avoid circular dependencies between major layers.

## 3. Repository map

Describe the major directories and files.

Use a table:

| Path | Owner / responsibility | Notes |
|---|---|---|

“Owner” means architectural responsibility, not necessarily a human owner.

## 4. Major components

For each major component, document:

### Component name

- Location:
- Responsibility:
- Owns:
- Does not own:
- Key collaborators:
- Main entry points:
- Important types/classes/functions:
- Known constraints:

## 5. Object model / domain model

Document the important domain objects, DTOs, entities, services, commands, events, or data structures.

Use tables where practical:

| Object | Defined in | Responsibility | Important fields | Notes |
|---|---|---|---|---|

## 6. Contracts and boundaries

Document stable interfaces and boundaries.

Include:
- public APIs
- CLI commands
- configuration schemas
- database schemas
- file formats
- network protocols
- events/messages
- plugin interfaces
- environment variables
- UI-to-backend boundaries
- external service contracts

For each contract:

### Contract name

- Producer:
- Consumer:
- Stability:
- Backward compatibility requirements:
- Validation:
- Error behavior:
- Source files:

## 7. Control flow

Describe important runtime flows.

Use concise numbered sequences.

Examples:
- application startup
- user opens a file
- user saves a change
- request handling
- background job execution
- import/export
- error handling

## 8. Data flow and persistence

Describe:
- where data enters
- how it is transformed
- where it is stored
- serialization formats
- migration/versioning behavior
- caching
- temporary files
- error recovery

## 9. Dependency rules

Document which layers or components may depend on which others.

Include forbidden dependencies.

Example:

| From | May depend on | Must not depend on |
|---|---|---|

## 10. Extension points

Document places intended for future growth:
- plugin points
- replaceable adapters
- strategy interfaces
- feature flags
- provider abstractions
- intentionally isolated modules

## 11. Testing architecture

Describe:
- test layout
- unit/integration/end-to-end boundaries
- fixtures
- mocks/fakes
- golden files
- contract tests
- minimum tests expected when changing each component

## 12. Known architectural debt

Track real issues, not vague complaints.

Use this format:

| Issue | Impact | Current workaround | Preferred direction |
|---|---|---|---|

## 13. Open questions

Track decisions that need user or maintainer input.

Use this format:

| Question | Why it matters | Options | Recommendation |
|---|---|---|---|

## 14. Change log

Record meaningful architecture-document updates.

Use reverse chronological order.

| Date | Change | Reason |
|---|---|---|

## Maintenance workflow

When updating code, check whether the change affects architecture.

Architecture-affecting changes include:
- new module, package, layer, service, or major class
- renamed or moved major code surface
- changed public API
- changed object model
- changed persistence model
- changed file format
- changed configuration schema
- changed dependency direction
- new external integration
- changed startup, save, load, import, export, or request flow
- changed error-handling contract
- changed test architecture
- removal of a component described in the document

If yes:
1. Read `docs/ARCHITECTURE.md`.
2. Identify the sections affected.
3. Update the document.
4. Add a short entry to the architecture change log.
5. Mention the architecture-document update in the final response.

If no:
- Say that no architecture-document update appeared necessary.

## Existing-project audit workflow

When asked to create or audit the architecture document for an existing project:

1. Inventory the repository.
2. Identify major components.
3. Identify entry points.
4. Identify public contracts.
5. Identify object/domain models.
6. Identify dependency direction.
7. Identify runtime flows.
8. Identify data flow and persistence.
9. Compare findings to existing documentation.
10. Produce or update `docs/ARCHITECTURE.md`.
11. Flag uncertain areas for user review.

## User feedback checkpoints

Ask for user feedback before treating any of the following as settled:
- naming of major layers
- intended long-term boundaries
- public API stability
- backward compatibility requirements
- whether a messy current implementation is intentional or accidental
- whether to document current architecture, desired architecture, or both
- whether to mark a design issue as technical debt
- whether to bless an inferred dependency direction

When feedback is needed, present a concise decision table:

| Decision | Option A | Option B | Recommendation |
|---|---|---|---|

Do not ask for feedback on trivial formatting or obvious facts confirmed by code.

## Output expectations

When completing architecture work, report:
- what files were inspected
- what sections were created or changed
- what facts are confirmed
- what remains inferred or uncertain
- what user decisions are needed
- whether code and documentation disagree

## Quality bar

The document is not acceptable if:
- it merely repeats the directory tree
- it omits contracts
- it omits ownership boundaries
- it fails to distinguish current state from intended design
- it describes aspirations as facts
- it ignores tests
- it ignores configuration and persistence
- it fails to identify architectural debt
- it becomes too vague to guide future code changes