# Architecture

This document is the project-level architecture map for `<Project>`. It describes the code as it exists in this repository, with facts marked by evidence level.

Status markers used in this document:

- **Confirmed by code**: Verified from source files.
- **Confirmed by tests**: Verified from test coverage names and assertions.
- **Confirmed by docs**: Verified from checked-in documentation.
- **Inferred**: Reasonable interpretation of current code, but not explicitly stated.
- **Needs review**: Requires maintainer confirmation.
- **Debt**: Current structure is known or suspected to be transitional or problematic.

## 1. Purpose and scope

Describe what the project does and what this document governs.

State the canonical document split if relevant:

- `docs/SPEC.md`: intended product requirements, goals, and anti-goals
- `docs/SCHEMAS.md`: intended persistent object model and naming
- `docs/ARCHITECTURE.md`: current code structure and implementation reality

## 2. Architectural principles

| Principle | Reason | Status |
|---|---|---|
| <principle> | <why it exists> | <status marker> |

## 3. Repository map

| Path | Responsibility | Notes |
|---|---|---|
| `<path>` | <what lives here> | <important caveat> |

## 4. Major components

### <Component name>

- Location: `<path>`
- Responsibility: <what this component does>
- Owns: <state, policies, or workflows it controls>
- Does not own: <important exclusions>
- Key collaborators: <adjacent modules or boundaries>
- Main entry points: <classes, functions, commands>
- Important types/classes/functions: <high-signal API surface>
- Known constraints: <runtime, layering, or lifecycle constraints>
- Status: <status marker>

Repeat for each major component. Prefer fewer deeper sections over exhaustive file-by-file inventory.

## 5. Object model / domain model

| Object | Defined in | Responsibility | Important fields | Notes |
|---|---|---|---|---|
| `<object>` | `<path>` | <role> | <important fields> | <constraints or drift> |

## 6. Contracts and boundaries

### <Contract name>

- Producer: <who emits or owns it>
- Consumer: <who depends on it>
- Stability: <internal, semi-stable, user-facing, persisted, CLI, etc.>
- Backward compatibility requirements: <what can or cannot change freely>
- Validation: <where malformed inputs are rejected>
- Error behavior: <how failures surface>
- Source files: `<paths>`
- Status: <status marker>

## 7. Control flow

### <Flow name>

1. <step>
2. <step>
3. <step>

## 8. Data flow and persistence

| Data | Source | Transformations | Storage | Format/schema | Notes |
|---|---|---|---|---|---|
| `<data>` | <source> | <transformations> | <where it ends up> | <shape> | <constraints> |

## 9. Dependency rules

| From | May depend on | Must not depend on | Notes |
|---|---|---|---|
| `<layer/module>` | <allowed deps> | <forbidden deps> | <why> |

## 10. Extension points

| Extension point | Location | Intended use | Constraints |
|---|---|---|---|
| `<extension>` | `<path>` | <purpose> | <guardrails> |

## 11. Testing architecture

| Test area | Location | What it protects | Expected when changing |
|---|---|---|---|
| `<area>` | `<path>` | <behavior or contract> | <required test updates> |

## 12. Known architectural debt

| Issue | Impact | Current workaround | Preferred direction |
|---|---|---|---|
| <debt item> | <why it hurts> | <temporary mitigation> | <desired end state> |

## 13. Open questions

| Question | Why it matters | Options | Recommendation |
|---|---|---|---|
| <question> | <impact> | <choices> | <current best answer> |

## 14. Change log

| Date | Change | Reason |
|---|---|---|
| YYYY-MM-DD | <summary> | <why this doc changed> |
