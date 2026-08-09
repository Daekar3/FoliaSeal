# Visual Artifact Guidance

Visual artifacts exist to remove ambiguity from spatial, hierarchical, and state-heavy UI decisions. They support the textual specification; they do not replace it.

## When to create one

Create a visual artifact when at least one of these is true:

- relative prominence or layout is hard to communicate in prose
- the user is choosing between topologies
- a surface contains multiple regions whose relationships matter
- interaction depends on before/after state
- responsive/adaptive behavior changes the topology
- a current screenshot reveals a problem that needs to be discussed concretely
- implementation agents are likely to interpret the same prose differently

Do not create visuals merely to decorate the specification.

## Fidelity progression

### 1. Topology sketch

Use boxes and labels only. Resolve:

- what exists
- what is adjacent/nested
- what is primary/secondary
- what is persistent/contextual/transient

Do not spend time on typography, color, icons, or exact spacing.

### 2. Annotated wireframe

After topology is approved, show:

- major controls and labels
- grouping
- action hierarchy
- important status/feedback areas
- representative content

### 3. State variants

Create separate artifacts only when the state materially changes layout, available actions, or hierarchy.

Examples:

- empty vs document-open
- editing vs ready
- warning/error vs normal
- narrow vs wide layout

### 4. High-fidelity reference

Use only when exact visual treatment is itself an approved product requirement or when implementation is sufficiently mature that detailed visual review is worthwhile.

## Acceptable formats

Choose the simplest format the available tools can reliably produce:

- SVG wireframe
- HTML/CSS mockup
- annotated screenshot
- diagram
- simple image mockup
- text/ASCII topology diagram when no visual tooling is available

Do not block specification work merely because image-generation or design software is unavailable.

## Artifact rules

Every approved artifact should identify:

- product/feature
- surface or workflow state
- whether it is **Exploratory**, **Current-state evidence**, or **Normative**
- relevant requirement IDs
- version/date when useful

Recommended naming:

`docs/ui/<surface>-<state>-<purpose>.<ext>`

Examples:

- `docs/ui/main-workspace-ready-wireframe.svg`
- `docs/ui/signing-placement-mode-wireframe.svg`
- `docs/ui/main-workspace-current-2026-08-08.png`

Avoid filenames such as `final2-revised-new.png`.

## Normative visuals

A visual becomes normative only when:

1. the user has approved the represented decision, and
2. `UI_SPEC.md` lists the artifact as **Normative** and cites the governing requirement IDs.

The textual requirements remain authoritative for behavior that cannot be seen in the image.

If a normative visual and textual requirement conflict, stop and resolve the conflict rather than choosing whichever is easier to implement.

## Comparing alternatives

When showing alternatives for one decision:

- keep unrelated variables constant
- label each option clearly
- state the tradeoff being tested
- avoid polishing one option more than another
- identify the recommended option separately from the drawing itself

For example, when deciding whether a secondary panel is persistent or collapsible, do not simultaneously change the menu model, colors, typography, and button wording.

## Annotating current screenshots

Current screenshots are evidence, not target design.

Use annotations to mark:

- current regions/surfaces
- duplicated or competing controls
- unclear hierarchy
- problematic empty space or density
- state-dependent behavior
- terminology inconsistencies
- platform-convention conflicts

Never allow an unapproved screenshot to become a de facto requirement merely because it is checked into `docs/ui/`.

## Spatial information that text should accompany

For each normative visual, ensure `UI_SPEC.md` states the important semantics that an image cannot reliably encode:

- which region is primary
- resize/collapse rules
- focus and keyboard order
- what appears/disappears by state
- commands that have multiple invocation surfaces
- whether a surface is modal or modeless
- what happens on Cancel/Back/Escape
- what state persists
- accessibility requirements
