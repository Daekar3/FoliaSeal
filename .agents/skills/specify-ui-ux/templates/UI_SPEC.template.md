# <Product> UI/UX Specification

This document is the canonical user-interface and interaction specification for `<Product>`.

Use this document for intended experience, information architecture, workflows, application topology, command semantics, interaction behavior, state/feedback behavior, adaptive behavior, accessibility/input requirements, visual hierarchy, and platform-realization rules.

Use the product specification for product goals, capabilities, and anti-goals.
Use the schema/domain specification for canonical user-facing objects and persistence semantics.
Use the architecture document for current implementation structure and implementation reality.

This document describes the intended interface. Existing UI code or screenshots do not override it unless explicitly incorporated here.

## Document Governance

**Status: Frozen.**

Normative requirements in this document may not be changed without explicit user approval. If implementation constraints appear to require a change, document the conflict, user-visible impact, and alternatives before requesting approval.

Supporting visual artifacts referenced by this document are part of the approved design when identified as normative. Cosmetic cleanup may not alter their approved topology, hierarchy, or behavior.

## 1. Source Precedence

When sources conflict, use this precedence unless the project explicitly establishes another order:

1. explicitly approved decisions in this document
2. governing product specification and anti-goals
3. canonical object/domain semantics
4. project-specific accessibility or brand requirements
5. active platform conventions and Human Interface Guidelines
6. toolkit/framework conventions
7. current implementation behavior

Current implementation is evidence, not authority over intended design.

## 2. Decision Language

Normative keywords:

- **Must** — required for conformance.
- **Must not** — prohibited.
- **Should** — expected unless a documented reason justifies deviation.
- **May** — permitted, not required.

Decision classes:

- **Invariant** — must hold across supported platforms/toolkits.
- **Application-specific** — product design decision that remains stable until explicitly revised.
- **Platform convention** — delegated to the active platform unless overridden here.
- **Realization note** — implementation guidance, not a cross-platform product requirement.

## 3. Experience Goals

Describe the desired high-level user experience. Keep these outcome-oriented rather than widget-oriented.

UXG01. <experience goal>

UXG02. <experience goal>

### Experience anti-goals

UXA01. <experience the product should avoid>

UXA02. <experience the product should avoid>

## 4. User Mental Model

Describe the concepts the interface should encourage users to think in.

| Concept | What it means to the user | What it must not imply |
|---|---|---|
| `<concept>` | <mental model> | <important misconception to avoid> |

## 5. Information Architecture

Define how user-facing concepts and task areas are grouped.

IA01. <grouping/ownership rule>

IA02. <separation rule>

### Information hierarchy

```text
<Application>
├── <primary area>
│   ├── <child area>
│   └── <child area>
└── <secondary area>
```

State which areas are primary, secondary, contextual, or management-oriented.

## 6. Primary Workflows

### WF01 — <Workflow name>

**Goal:** <what the user is trying to achieve>

**Entry conditions:**
- <condition>

**Flow:**
1. <step>
2. <step>
3. <step>

**Backward/cancel behavior:**
- <rule>

**State preservation:**
- <what survives navigation/cancel/reopen>

**Success:**
- <observable outcome>

**Failure/recovery:**
- <recoverable failure behavior>
- <terminal failure behavior if relevant>

Repeat for each product-critical workflow.

## 7. Application Topology

Describe the major surfaces and their relationships without assuming a particular toolkit control.

LAY01. <topology rule>

LAY02. <relative prominence or spatial relationship>

### Canonical topology

```text
<Application>
├── <global command surface>
├── <primary workspace>
│   ├── <primary content surface>
│   └── <contextual/secondary surface>
└── <feedback/status surface>
```

### Window/screen model

State whether the product is single-window, multi-window, tabbed, document-based, route-based, split-view, etc., and identify which aspects are invariant versus platform conventions.

## 8. Surface Contracts

### SUR01 — <Surface name>

**Purpose:** <why the surface exists>

**Owns:**
- <information/action>

**Must not own:**
- <important exclusion>

**Presence:** <persistent / contextual / modal / transient / management-only / other>

**Prominence:** <primary / secondary / quiet / interruptive>

**Relationship to other surfaces:**
- <relationship>

**Adaptive behavior:**
- <resize/collapse/reflow behavior>

**Normative visual reference:** `docs/ui/<artifact>` or `None`

Repeat for each major surface.

## 9. Command Model

Define user intents separately from buttons, menu items, gestures, or shortcuts.

| ID | Command | User intent | Availability | Priority | Invocation expectations |
|---|---|---|---|---|---|
| CMD01 | <command> | <intent> | <enabled conditions> | primary/secondary/contextual/destructive/expert | <surfaces or platform convention> |

Where standard platform shortcuts or menu placement exist, state “follow platform convention” rather than freezing a platform-specific value in the invariant layer.

## 10. Interaction Model

### INT01 — <Interaction or mode>

**Trigger/entry:** <how it begins>

**User indication:** <how the user knows the state/mode is active>

**Permitted actions:**
- <action>

**Pointer/touch behavior:** <if relevant>

**Keyboard/non-pointer behavior:** <required alternate path>

**Cancel/Back/Escape behavior:** <rule>

**Exit conditions:** <rule>

**State after exit:** <what is preserved or discarded>

Repeat for direct manipulation, drag/drop, selection modes, editing modes, wizards, and other stateful interactions.

## 11. State, Validation, and Feedback

Define important observable states rather than only the happy path.

| ID | State | User must understand | Primary feedback | Available recovery/action |
|---|---|---|---|---|
| STA01 | <state> | <meaning> | <feedback> | <recovery/action> |

Cover as applicable:

- empty/initial
- loading/working
- ready
- incomplete/invalid
- warning/caveat
- destructive confirmation
- success
- recoverable error
- terminal error
- offline/degraded mode
- unsaved/in-progress state

State when validation happens and whether invalid actions are disabled, allowed with explanation, or rejected at submit time.

## 12. Adaptive and Resizing Behavior

ADP01. <minimum usable behavior>

ADP02. <what shrinks/reflows/collapses first>

ADP03. <what must remain visible or reachable>

Address as relevant:

- narrow/small windows or displays
- very large displays
- split/tiled windows
- orientation changes
- system text scaling
- high DPI / display scaling
- touch versus pointer density
- virtual/on-screen keyboard intrusion

Avoid universal pixel thresholds unless the product truly depends on them. Put platform-specific thresholds in Platform Realization.

## 13. Accessibility and Input Requirements

ACC01. Essential functionality must be operable without requiring fine pointer precision.

ACC02. <keyboard/focus requirement>

ACC03. <assistive-technology semantic requirement>

ACC04. <contrast/non-color requirement>

ACC05. <text/scaling requirement>

Add product-specific requirements as needed.

Explicitly identify justified exceptions.

## 14. Visual Language and Hierarchy

Describe product-level visual intent without inventing a toolkit-independent pixel-perfect theme.

### Hierarchy

VIS01. <primary content emphasis rule>

VIS02. <primary action emphasis rule>

### Density and grouping

VIS03. <density/grouping rule>

### Color semantics

VIS04. <semantic color rule; do not rely on color alone>

### Typography

VIS05. <role/hierarchy rule; prefer platform/system typography unless brand requires otherwise>

### Iconography

VIS06. <semantic/icon rule; prefer familiar platform conventions where possible>

### Motion

VIS07. <motion rule, if relevant>

## 15. Content and Terminology

Define user-visible terminology that must remain consistent.

| Term | Use for | Do not use for |
|---|---|---|
| `<term>` | <meaning> | <confusable meaning> |

### Message style

TXT01. <plain-language/error guidance rule>

TXT02. <label/action wording rule>

## 16. Platform Realization

The sections above are authoritative for intended experience. Platform mappings below explain how each implementation target should realize those requirements idiomatically.

### <Platform / toolkit target>

- **Platform:** <Windows/macOS/Linux/Web/iOS/Android/etc.>
- **Toolkit/framework:** <if established>
- **Status:** <current / planned / exploratory>

#### Native conventions relied upon

PLAT01. <convention delegated to platform>

PLAT02. <convention delegated to platform>

#### Requirement mappings

| Invariant requirement | Platform realization | Notes |
|---|---|---|
| LAY01 | <native pattern> | <constraints> |
| CMD01 | <native command/menu/shortcut pattern> | <constraints> |

#### Deliberate deviations

| Requirement | Native convention | Deviation | Reason |
|---|---|---|---|
| <ID> | <expected behavior> | <product behavior> | <why> |

#### Platform-specific accessibility/input requirements

- <requirement>

#### Realization constraints

- <constraint that implementation plans must account for without redefining intent>

Repeat for each supported target.

## 17. Visual Artifact Index

Only artifacts explicitly marked **Normative** participate in the design contract.

| Artifact | Status | Surfaces/states covered | Governing requirement IDs | Notes |
|---|---|---|---|---|
| `docs/ui/<file>` | Normative / Exploratory / Current-state evidence | <scope> | <IDs> | <notes> |

A screenshot of current behavior is not normative unless explicitly promoted here with user approval.

## 18. Observable Acceptance Scenarios

Write these from the user’s perspective. They should be testable by a reviewer without inspecting implementation internals.

OBS01. <scenario and expected observable result>

OBS02. <scenario and expected observable result>

OBS03. <scenario and expected observable result>

Include representative keyboard/alternate-input and resize/adaptation scenarios where relevant.

## 19. Open Questions

| Question | Why it matters | Dependencies | Options/current recommendation |
|---|---|---|---|
| <question> | <impact> | <what depends on it> | <options> |

Do not treat unresolved questions as requirements.

## 20. Decision Log

Record only decisions whose rejected alternatives are likely to be reconsidered later.

| Date | Decision | Alternatives rejected | Reason | Requirement IDs |
|---|---|---|---|---|
| YYYY-MM-DD | <decision> | <alternatives> | <reason> | <IDs> |
