---
name: specify-ui-ux
description: Establish or update a governing UI/UX specification through product-document review, current-interface exploration, codebase inspection, visual wireframing, workflow and state analysis, platform-convention research, and iterative user interview. Use when the user wants to define how an interactive application should be organized, behave, and feel; resolve GUI topology or interaction patterns; replace prototype UI with an intentional design; or document UI decisions for implementation agents. Establish platform-independent experience requirements first and record platform/toolkit realization separately.
---

# Specify UI/UX

Use this skill to turn product intent into an explicit, durable UI/UX contract that implementation agents can follow without rediscovering design decisions.

The skill is intentionally platform- and toolkit-neutral. It may be used for desktop, web, mobile, embedded, or other interactive applications. Do not assume Qt, GTK, WinUI, Cocoa, Electron, Flutter, a browser, or any other implementation technology unless the project establishes it.

## Core principles

1. **Specify intent before realization.** Establish what the user must experience before deciding how a toolkit implements it.
2. **Separate invariants from implementation choices.** A requirement such as “the document remains the dominant workspace” may be normative; a particular `QSplitter`, CSS grid, or WinUI control usually is not.
3. **Treat current UI as evidence, not authority.** Existing screens and code reveal behavior, debt, terminology, and constraints. Prototype structure does not become a product requirement merely because it exists.
4. **Do not reopen upstream product decisions casually.** Read governing product, schema, architecture, brand, accessibility, and platform documents first. If they conflict, surface the conflict to the user rather than silently choosing a winner.
5. **Show spatial decisions whenever words are likely to be ambiguous.** Use low-fidelity wireframes, annotated screenshots, topology diagrams, or interactive prototypes when layout, hierarchy, navigation, or state is under discussion.
6. **Never make a visual artifact the sole contract.** Pair every approved visual with textual requirements describing purpose, hierarchy, behavior, state, and adaptation rules.
7. **Progress from coarse to fine.** Resolve mental model, information architecture, workflows, topology, and state transitions before colors, spacing, iconography, or widget details.
8. **Prefer native/platform conventions unless the product has a reason to diverge.** Record the product requirement and the reason for any deliberate exception.
9. **Accessibility and alternate input are design requirements, not polish.** Essential functionality must not depend solely on pointer precision, color, hover, or a single input modality.
10. **Avoid specification cruft.** Create only artifacts that carry durable design information. Do not create separate documents for every design concern when `UI_SPEC.md` or a referenced visual artifact is sufficient.

## Decision classes

Classify material decisions while interviewing and documenting them:

- **Experience invariant** — must hold across supported platforms and toolkits.
- **Application design choice** — product-specific UI structure or behavior that should remain stable unless explicitly revised.
- **Platform convention** — should follow the active platform’s accepted behavior unless a stronger product requirement overrides it.
- **Toolkit realization** — concrete implementation mechanism; normally belongs in architecture or an implementation plan, not the frozen UI specification.

Use `references/DECISION_TAXONOMY.md` when a decision is difficult to classify.

## Canonical outputs

The default durable output is:

- `docs/UI_SPEC.md` — intended user-interface and interaction contract; **frozen** and changed only with explicit user approval.

Optional supporting artifacts live under:

- `docs/ui/` — approved wireframes, annotated screenshots, state diagrams, or other visual references cited by `UI_SPEC.md`.

Do not create a second UI architecture document by default. Current implementation structure, widget composition, toolkit boundaries, and code drift belong in the project’s existing architecture documentation or implementation plans.

Use `templates/UI_SPEC.template.md` as the starting shape. Remove sections that do not apply; add sections when the product requires them.

## Workflow

You may skip a step only when the information is already explicit and verified.

### 1. Establish scope and governing sources

Identify the application, feature area, supported or intended platforms, and implementation maturity.

Read the highest-authority project documents before interviewing. Typical sources include:

- product specification and anti-goals
- canonical object/domain model
- architecture documentation
- requirements, issue, or execution plan for the feature
- accessibility requirements
- brand/design-system documents, if one exists
- existing UI specification, if updating one

Before interviewing, record each governing document’s responsibility and authority. Do not assume a universal precedence order. If the project does not define one, default to product scope first, canonical domain/object semantics second, UI/UX realization third, followed by platform and toolkit conventions.

Extract already-decided UI constraints and label them as inherited decisions. Do not ask the user to decide them again unless a genuine conflict or ambiguity exists.

### 2. Explore the current interface and code

When an implementation exists:

- inspect the relevant presentation/UI code and composition boundaries
- run the application or relevant harness when practical
- capture representative current states when tooling permits
- inventory top-level windows/screens, persistent surfaces, transient surfaces, dialogs, menus/commands, modes, navigation, and major feedback states
- note prototype assumptions, duplicated controls, hidden behavior, and terminology drift

Produce a short **current-state UI map** before prescribing changes.

Keep observation separate from recommendation. “The current sidebar is 40% of the window” is evidence; “the sidebar should remain 40%” is a design decision requiring justification.

### 3. Research applicable platform conventions

Do this only after the target platform/toolkit is known enough for the research to matter.

Prefer authoritative, current sources:

1. operating-system or platform Human Interface Guidelines
2. toolkit/framework design and accessibility guidance
3. applicable accessibility standards
4. established application-category conventions

Research conventions for commands, menus, dialogs, keyboard behavior, focus, accessibility, file interactions, windowing/navigation, touch/pointer behavior, scaling, and other relevant surfaces.

Do not copy platform conventions into the invariant layer. Record them in the platform-realization section unless the user deliberately promotes a behavior to a cross-platform product requirement.

See `references/PLATFORM_REALIZATION.md` for the source-precedence and exception rules.

### 4. Build the design tree

Identify unresolved design branches in dependency order. Resolve broad choices before dependent details.

Typical order:

1. user mental model
2. information architecture
3. primary workflows and task priority
4. application/screen topology
5. command model and navigation
6. surface responsibilities
7. interaction modes and state transitions
8. feedback, validation, errors, and completion states
9. adaptive/resizing behavior
10. accessibility and alternate input
11. visual hierarchy and density
12. platform/toolkit realization
13. cosmetic details that materially affect usability or brand

Do not spend interview time on low-impact styling while a structural branch remains unresolved.

### 5. Interview to shared understanding

Interview the user aggressively enough to eliminate material ambiguity, but do not ask questions whose answers are already established by source documents.

For each meaningful branch:

- state the decision that needs to be made
- explain why it affects later decisions
- present two or three concrete alternatives when useful
- describe the tradeoff of each alternative
- recommend a default when evidence supports one
- obtain the user’s decision before descending into dependent branches

Prefer concrete questions over abstract taste questions.

Good:

- “When setup is complete, should the signing surface remain visible, collapse to a summary, or disappear until reopened?”
- “If the user cancels placement, should the previous valid placement return or should the draft become unplaced?”

Weak:

- “What kind of interface do you like?”
- “Should it look modern?”

Record decisions as **requirement**, **preference**, **platform convention**, or **open question**. Do not silently turn a preference into a requirement.

### 6. Use visual artifacts for spatial and state-heavy decisions

Create visual alternatives when discussing:

- screen/window topology
- relative prominence of regions
- navigation structure
- dense forms or inspectors
- dialogs/wizards
- responsive/adaptive transitions
- drag/drop or direct-manipulation flows
- multi-step modes
- before/after states that are hard to describe reliably

Start low fidelity. Prefer simple boxes, labels, and annotations until topology is approved.

Use `references/VISUAL_ARTIFACTS.md` for artifact rules and naming.

When presenting alternatives, change only the design variable under discussion where practical. Do not bury a topology choice under unrelated changes to color, typography, and copy.

### 7. Specify workflows, states, and transitions

For each primary workflow, define:

- entry conditions
- major steps
- state transitions
- permitted backward/cancel paths
- persistence of in-progress state
- destructive or irreversible boundaries
- validation timing
- success outcome
- recoverable failure behavior
- terminal failure behavior

For interaction modes, explicitly define entry, cursor/focus or mode indication, permitted actions, Escape/Back/Cancel behavior, and exit conditions.

Do not rely on happy-path wireframes alone.

### 8. Specify command and surface semantics

Define commands independently from the controls that invoke them.

For each important command, capture:

- user-facing intent
- availability/enabled conditions
- whether it is primary, secondary, contextual, destructive, or expert-only
- whether multiple invocation surfaces are expected
- whether a conventional platform shortcut should be used

For each major surface, capture:

- purpose
- information/actions it owns
- information/actions it must not own
- persistence (always present, contextual, modal, transient, etc.)
- relationship to other surfaces
- priority/prominence
- adaptation behavior

### 9. Specify accessibility and input independence

At minimum, consider:

- keyboard-only or non-pointer operation for essential tasks
- logical focus order and visible focus
- assistive-technology names/roles/state exposure where applicable
- system text/font scaling and high-DPI behavior
- contrast and non-color cues
- alternatives to dragging and fine pointer placement
- minimum practical target sizes for touch-oriented platforms
- reduced motion or animation dependence where applicable
- screen-reader/semantic reading order where applicable
- error identification and recovery without relying on color or position alone

Do not invent universal numeric thresholds when the applicable platform or standard already defines them. Put platform-specific thresholds in platform realization.

### 10. Resolve visual language after structure

Specify only the visual rules that matter to the product:

- hierarchy
- density
- grouping
- alignment
- emphasis
- semantic color roles
- typography roles
- icon semantics
- whitespace philosophy
- brand constraints

Prefer system/native styling by default when the product does not require a custom visual system.

Do not freeze incidental pixel values, exact control classes, or platform chrome unless they are genuinely necessary to preserve the intended experience.

### 11. Document platform realization separately

For each supported implementation target, record:

- platform
- toolkit/framework
- native conventions relied upon
- mappings from invariant requirements to platform patterns
- deliberate deviations and their rationale
- platform-specific accessibility/input requirements
- known realization constraints that affect but do not redefine product intent

If two platforms legitimately realize the same invariant differently, document both mappings rather than weakening the invariant.

### 12. Validate the design before freezing

Before writing the final specification, walk the user through representative scenarios and verify:

- every product-critical workflow has a coherent UI path
- primary content/actions have the intended prominence
- users can recover from mistakes without surprising state loss
- command availability is understandable
- empty/loading/error/success states are accounted for
- resize/adaptation does not destroy essential functionality
- keyboard/alternate-input paths exist for essential actions
- approved visuals and textual requirements agree
- no UI decision contradicts upstream frozen product/schema requirements
- toolkit details have not leaked into invariant requirements without justification

Surface unresolved conflicts explicitly.

### 13. Write and freeze `UI_SPEC.md`

Use `templates/UI_SPEC.template.md`.

Use stable IDs for requirements that implementation plans or tests will need to cite. Prefer a small, meaningful set of IDs over numbering every sentence.

Recommended prefixes:

- `UXG` — experience goals
- `IA` — information architecture
- `WF` — workflow
- `LAY` — topology/layout
- `SUR` — surface responsibility
- `CMD` — command semantics
- `INT` — interaction behavior
- `STA` — state/feedback
- `ADP` — adaptive/resizing behavior
- `VIS` — visual hierarchy/language
- `ACC` — accessibility/input
- `PLAT` — platform realization
- `OBS` — observable acceptance condition

Mark `UI_SPEC.md` frozen. Changes to normative requirements require explicit user approval.

Visual artifacts may be revised only when the corresponding normative decision is approved for change. Cosmetic cleanup that does not alter meaning is allowed, but must not quietly change topology, hierarchy, or behavior.

## Relationship to implementation planning

This skill specifies the intended interface; it does not implement it.

Implementation plans should cite `UI_SPEC.md` requirement IDs and approved visual artifacts. They may choose toolkit mechanisms that satisfy the contract.

If implementation reveals a genuine conflict:

1. do not silently reinterpret the UI requirement
2. identify the conflicting requirement and implementation constraint
3. explain the user-visible consequence
4. propose alternatives
5. obtain explicit approval before changing the frozen specification

Current implementation drift belongs in architecture documentation or the active implementation plan, not as a rewrite of the intended UI contract.

## Completion standard

The skill is complete when another competent implementation agent can answer, without guessing:

- what the user is trying to accomplish
- what concepts and surfaces the user sees
- what is primary versus secondary
- how the main workflows progress and can be cancelled/reversed
- what each major command and surface means
- what important states and errors look like behaviorally
- how the interface adapts
- what accessibility/input guarantees must hold
- which choices are invariant versus platform-specific
- which visual artifacts are normative references
- what remains intentionally undecided

If those questions still require interpreting prototype code or inferring intent from screenshots, the specification is not finished.
