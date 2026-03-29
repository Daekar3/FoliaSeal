# Phase 3 Parallel Implementation Plan

Date prepared: 2026-03-28
Prepared by: Codex agent

## Purpose

This document turns the Phase 3 milestone into a parallelizable implementation plan that can be used across multiple chats and by multiple agents at the same time.

The goal of Phase 3 is to deliver the first end-user signing workflow on top of the completed Phase 2 viewer platform:

- Acrobat/PDF-XChange-style signing flow
- signature placement and adjustment
- signature properties editing
- real-time appearance preview
- GUI-driven signing request submission

Primary requirements source:

- `FR-3`, `FR-3A`, `FR-3B` in `pdf_signing_app_feasibility.md`
- Phase 3 milestone and exit criteria in `pdf_signing_app_feasibility.md`

Current implementation baseline:

- Phase 1: headless signing orchestration exists
- Phase 2: viewer, coordinate mapping, timing, and Qt interaction platform exist

This phase should bridge those pieces into a real signing UX.

## Scope Boundary

Phase 3 includes:

- appearance-template-driven signing flow
- place/resize/fine-tune signature rectangle
- editable signature property system
- inline validation
- live preview
- GUI integration with signing request creation

Phase 3 does not need full preset lifecycle management yet.

That belongs primarily to Phase 4:

- create/edit/duplicate/delete/import/export preset persistence UX
- default/last-used preset behavior
- corruption recovery flows

It is acceptable in Phase 3 to support:

- built-in appearance templates
- a single in-memory current draft
- temporary serialization helpers needed by the model layer

## Design Principles

1. Keep business rules out of Qt widgets.
2. Keep `ViewerWorkflow` focused on rendering and coordinate transforms.
3. Introduce a dedicated signing draft workflow for UI state, validation, and preview normalization.
4. Expand the domain model before building the full UI.
5. Keep final signing integration incremental by extending the existing `SignPdfUseCase`, not replacing it.
6. Minimize merge conflicts by assigning disjoint write ownership.

## Recommended Parallel Workstreams

### Workstream A: Domain and config model expansion

Purpose:

- define the Phase 3 contract used by all other workstreams

Primary outputs:

- richer signing request model
- signature appearance domain models
- validation rules
- expanded persisted config schema for appearance-capable presets

Suggested owned files:

- `src/foliaseal/domain/models.py`
- `src/foliaseal/infra/config/schemas.py`
- new tests under `tests/unit/`

Avoid editing:

- `src/foliaseal/presentation/qt/`
- signing-engine integration code unless absolutely necessary

Deliverables:

- expand `SigningRequest` with page index, rectangle, and appearance payload
- add domain types such as:
  - `SignatureAppearance`
  - `SignatureFieldVisibility`
  - `SignatureFieldSource`
  - `SignatureLayoutTemplate`
  - `SignatureTextStyle`
  - `SignatureBoxStyle`
  - `SignaturePreviewModel` or equivalent normalized preview payload
- support source rules:
  - derived from certificate
  - manual override
  - hidden
- support appearance controls for:
  - visible fields
  - prefix label text
  - date/time format
  - timezone mode
  - layout template
  - font size/style/color
  - background and border style
  - optional image stamp reference
- add validation helpers for invalid field combinations
- update schema round-trip coverage and invalid-payload tests

Acceptance criteria:

- all new models serialize deterministically
- invalid appearance combinations fail with actionable validation messages
- other workstreams can depend on stable model names and fields

### Workstream B: Application signing draft workflow

Purpose:

- provide the non-Qt orchestration layer that converts user interactions into a valid signing draft and final request

Primary outputs:

- signing draft state machine
- preview normalization
- inline validation state
- request-building logic

Suggested owned files:

- new files under `src/foliaseal/application/`
- tests under `tests/unit/`

Potential filenames:

- `src/foliaseal/application/signing_workflow.py`
- `src/foliaseal/application/signature_preview.py`

Avoid editing:

- most Qt widget files
- schema files owned by Workstream A

Deliverables:

- create a dedicated signing workflow object that:
  - accepts placement rectangles from the viewer
  - supports numeric fine-tuning of x/y/width/height
  - holds appearance/property draft state
  - emits inline validation issues
  - emits a normalized preview model
  - builds an enriched `SigningRequest`
- keep `ViewerWorkflow` focused on render/geometry duties
- add deterministic tests for:
  - placement from selection
  - numeric edits
  - source-rule switching
  - hidden vs visible field behavior
  - preview refresh after state mutation
  - can-sign vs blocked state

Acceptance criteria:

- the workflow can be driven entirely by unit tests without Qt
- the workflow exposes enough state that the UI can remain thin

### Workstream C: Qt signing UI shell and properties panel

Purpose:

- implement the actual user-facing Phase 3 desktop flow

Primary outputs:

- signing window/form shell
- properties panel or dialog
- UI-state synchronization with the workflow layer
- inline field-level validation

Suggested owned files:

- `src/foliaseal/presentation/qt/`
- UI tests if practical

Potential filenames:

- `src/foliaseal/presentation/qt/main_window.py`
- `src/foliaseal/presentation/qt/signing_form.py`
- `src/foliaseal/presentation/qt/signature_properties_panel.py`
- `src/foliaseal/presentation/qt/result_dialog.py`

May coordinate with existing:

- `src/foliaseal/presentation/qt/viewer_widget.py`

Avoid editing:

- domain schema internals
- signing-engine implementation

Deliverables:

- wire the signing flow to follow this sequence:
  - choose template or appearance mode
  - place or resize signature
  - adjust properties
  - confirm and sign
- add controls for:
  - field toggles
  - source-mode selection
  - prefix label
  - date/time format and timezone display
  - layout template
  - font controls
  - color controls
  - background and border controls
  - freeform values like reason, location, title, company
- display inline validation near the relevant control
- preserve keyboard affordances for primary actions
- keep widget logic focused on rendering inputs and dispatching events to the application workflow

Acceptance criteria:

- the full flow works without fallback dialogs for representative FR-3B tasks
- UI logic mostly delegates to the application layer rather than embedding rules in event handlers

### Workstream D: Preview rendering and parity harness

Purpose:

- make the live preview trustworthy and testable

Primary outputs:

- preview renderer or formatter
- preview regression tests
- parity-oriented acceptance helper

Suggested owned files:

- new preview-oriented files under `src/foliaseal/application/` or `src/foliaseal/presentation/qt/`
- tests under `tests/unit/`

Avoid editing:

- signing engine integration
- broad UI shell ownership from Workstream C unless coordinating closely

Deliverables:

- build a live preview path driven by normalized appearance data
- make sure preview updates on any meaningful property change
- cover:
  - field ordering
  - hidden/derived/override behavior
  - layout templates
  - date formatting
  - optional image stamp presence
  - border/background style rules
- add a lightweight acceptance harness for comparing preview semantics against the final signing payload

Acceptance criteria:

- preview state changes are deterministic
- preview payload matches the final signing payload semantics

### Workstream E: Signing pipeline enrichment and integration

Purpose:

- connect the richer Phase 3 request model to the existing signing use case

Primary outputs:

- enriched request handling in application layer
- stable failure mapping maintained
- integration coverage for visible appearance parameters

Suggested owned files:

- `src/foliaseal/application/sign_pdf_use_case.py`
- future signing backend adapters as needed
- integration-oriented tests

Avoid editing:

- most Qt files
- schema definitions after Workstream A stabilizes them

Deliverables:

- update signing orchestration to accept the richer request contract
- map appearance payload through to the signing backend layer
- keep stable result/failure semantics intact
- add tests for:
  - successful enriched request handling
  - invalid appearance rejection before sign execution
  - standards summary still emitted on success
  - rectangle/appearance parameters preserved through request flow

Acceptance criteria:

- GUI-created signing requests can flow through the existing signing pipeline
- Phase 1 behaviors are preserved while supporting richer input

## Dependency and Sequencing Plan

### Order of work

1. Workstream A starts first and defines the contract.
2. Workstream B begins once the draft model shape is clear.
3. Workstreams C and D begin once B has exposed a usable workflow API.
4. Workstream E begins once the enriched `SigningRequest` contract is stable.
5. Final integration pass merges B, C, D, and E.

### Critical contract checkpoints

Before parallel work expands, align on:

- names and fields for the appearance model
- how validation issues are represented
- how preview payload is represented
- how rectangle fine-tuning is represented
- what fields are required by final signing

## Merge-Conflict Avoidance Rules

1. Each workstream owns a small, disjoint write set.
2. If a shared interface must change, the owning workstream updates it and communicates the revised contract.
3. Avoid wide refactors during Phase 3 unless they are directly needed for the signing flow.
4. Prefer adding new files over heavily editing existing multi-owner files.
5. Do not reformat unrelated code.

## Shared Contract Proposal

The team should converge early on a normalized contract similar to the following shape. This is not a final API mandate, but it should guide implementation conversations.

### Signing request additions

- input PDF path
- output PDF path
- certificate path
- passphrase
- TSA URL
- timestamp policy
- target page index
- target PDF rect
- normalized appearance object

### Appearance concerns to model explicitly

- field visibility
- field value source
- override text values
- text ordering
- label formatting
- layout template
- date formatting
- timezone display mode
- font styling
- text color
- background style
- border style
- optional image stamp path or asset reference

### Validation concerns

- visible field with no resolvable source
- image-enabled layout without image source
- unsupported numeric ranges
- impossible or empty rectangle geometry
- invalid formatting combinations

## Detailed Backlog

### P3-01 Domain and schema expansion

- enrich the appearance-capable domain model
- enrich config schemas enough to represent Phase 3 appearance state
- add validation helpers and tests

### P3-02 Signing draft workflow

- draft state container
- mutation methods for placement and field changes
- validation result generation
- final request builder

### P3-03 Placement refinement support

- numeric fine-tuning of placement rectangle
- reconcile drag placement with form edits
- preserve authoritative PDF-coordinate placement

### P3-04 Properties panel behavior

- dedicated property controls for FR-3A options
- inline validation display
- update propagation to preview

### P3-05 Live preview

- generate preview model from draft
- keep preview synchronized with field and style edits
- test semantic parity between preview and signing payload

### P3-06 GUI sign execution

- submit enriched request from GUI
- show progress and result state
- preserve current failure-code behavior

### P3-07 Acceptance and parity checks

- task-based FR-3B walkthroughs:
  - create new appearance
  - include/exclude identity fields
  - place and resize signature
  - reuse prior configuration shape in-session

## Phase 3 Done Criteria

Phase 3 should be considered complete when all of the following are true:

- a user can place a signature rectangle on the rendered PDF
- a user can resize or fine-tune the rectangle before signing
- a user can edit all required FR-3A appearance properties in a focused properties UI
- invalid combinations are blocked inline with actionable guidance
- preview updates immediately when properties change
- the preview semantics match the final signing payload
- the GUI can submit an enriched signing request through the existing signing pipeline
- representative FR-3B parity tasks can be completed without fallback dialogs

## Agent-Ready Assignment Briefs

These briefs are written so they can be copied into separate agent threads with minimal editing.

### Brief A: Domain and Config Contracts

You are implementing the Phase 3 domain and config contract for signature appearance editing.

Objectives:

- expand the signing request and appearance-related domain models
- replace the minimal appearance preset/config shape with a Phase-3-capable schema
- add strong validation and serialization coverage

Primary files you own:

- `src/foliaseal/domain/models.py`
- `src/foliaseal/infra/config/schemas.py`
- relevant new tests in `tests/unit/`

Files you should avoid editing unless absolutely necessary:

- `src/foliaseal/presentation/qt/`
- `src/foliaseal/application/sign_pdf_use_case.py`

Requirements to satisfy:

- FR-3
- FR-3A
- enough FR-3C groundwork to represent appearance state, but not full preset lifecycle UX

Expected deliverables:

- richer `SigningRequest`
- appearance-related dataclasses and enums
- validation helpers
- round-trip config schema tests
- invalid-input tests

Implementation notes:

- prefer explicit typed fields over generic dictionaries
- optimize for downstream use by workflow and UI code
- keep the model normalized and deterministic

Definition of done:

- tests pass
- downstream agents can build against the contract without guessing field semantics

### Brief B: Signing Draft Workflow

You are implementing the application-layer workflow for the Phase 3 signing draft.

Objectives:

- convert placement and property edits into a validated signing draft
- expose inline validation state
- produce a normalized preview payload
- build the final signing request

Primary files you own:

- new files under `src/foliaseal/application/`
- relevant tests in `tests/unit/`

Files you should avoid editing unless absolutely necessary:

- `src/foliaseal/presentation/qt/`
- schema internals owned by the domain/config workstream

Requirements to satisfy:

- FR-3
- FR-3A
- support the Phase 3 flow in the milestone plan

Expected deliverables:

- a dedicated signing workflow object
- rectangle fine-tuning support
- validation issue model
- preview normalization path
- request builder
- deterministic unit tests

Implementation notes:

- keep Qt-free logic in the application layer
- do not overload `ViewerWorkflow` with appearance concerns
- optimize for a thin UI integration layer

Definition of done:

- the workflow can be driven entirely from unit tests
- the UI workstream can use it without reproducing business rules

### Brief C: Qt Signing UI Shell

You are implementing the Phase 3 Qt signing experience on top of the existing viewer platform.

Objectives:

- create the end-user signing flow
- add a focused signature properties UI
- display inline validation and keep it synchronized with application workflow state

Primary files you own:

- `src/foliaseal/presentation/qt/`
- UI tests if feasible

Files you should avoid editing unless absolutely necessary:

- deep domain/config internals
- signing-engine implementation

Requirements to satisfy:

- FR-3
- FR-3A
- FR-3B

Expected deliverables:

- signing shell or main window
- properties panel or dialog
- controls for required appearance settings
- event wiring into the application workflow
- inline validation presentation

Implementation notes:

- reuse existing viewer integration where possible
- do not bury validation rules in widget event handlers
- keep the flow close to:
  - choose appearance
  - place/resize
  - edit properties
  - confirm/sign

Definition of done:

- representative Phase 3 tasks can be completed from the GUI without fallback dialogs

### Brief D: Preview Rendering and Parity

You are implementing the live signature appearance preview path and its regression harness.

Objectives:

- make preview trustworthy
- ensure preview semantics stay aligned with final signing payload semantics

Primary files you own:

- new preview-specific files under `src/foliaseal/application/` or `src/foliaseal/presentation/qt/`
- relevant tests in `tests/unit/`

Files you should avoid editing unless absolutely necessary:

- signing engine integration
- broad shell UI ownership

Requirements to satisfy:

- FR-3A real-time preview requirement
- Phase 3 exit criterion requiring preview/final consistency

Expected deliverables:

- preview renderer or formatter
- update path for property changes
- preview regression tests
- semantic parity helper or harness

Implementation notes:

- prioritize deterministic preview data over pixel-perfection at first
- ensure hidden/derived/override rules are faithfully represented

Definition of done:

- preview updates are deterministic
- preview semantics track the final signing payload semantics closely enough to support acceptance testing

### Brief E: Signing Integration

You are integrating the richer Phase 3 signing request into the existing signing pipeline.

Objectives:

- extend the current signing use case to accept the enriched request
- preserve stable failure mapping and standards reporting

Primary files you own:

- `src/foliaseal/application/sign_pdf_use_case.py`
- signing backend adapter files as needed
- integration-oriented tests

Files you should avoid editing unless absolutely necessary:

- most Qt UI files
- shared schema work owned by Workstream A

Requirements to satisfy:

- FR-4
- FR-5
- FR-6
- support GUI-driven Phase 3 request integration

Expected deliverables:

- enriched request handling
- backend mapping for appearance payload
- regression coverage for new request shape

Implementation notes:

- preserve current success/failure behavior where possible
- reject invalid appearance requests before attempting sign execution
- avoid unnecessary rewrite of the Phase 1 orchestration

Definition of done:

- a GUI-created rich signing request can flow through the signing pipeline with stable result behavior

## Suggested Integration Pass Checklist

After the parallel workstreams merge, run an integration pass that checks:

- model imports are stable across layers
- no duplicate validation logic exists in UI and application layers
- preview uses the same normalized data consumed by final signing
- placement rectangle remains authoritative in PDF coordinates
- failure messages remain user-facing first
- tests cover the happy path and at least one invalid-property-path case

## Phase 3 Overlay Remediation Wave

This section applies after the first manual Phase 3 acceptance run exposed that the
current overlay interaction is not acceptable for FR-3B.

### Trigger for this wave

Manual acceptance found:

- persistent odd snapping/jumping while dragging overlay resize handles
- resize behavior that does not feel predictable enough for end users
- acceptance cannot proceed on the placement/resize task until overlay behavior is fixed

### Goal

Stabilize the visible signature overlay so placement and resize feel intentional,
predictable, and acceptance-testable.

### Scope for this wave

In scope:

- overlay interaction model
- resize-handle behavior
- overlay synchronization between viewer and shell
- overlay-specific regression tests
- acceptance/docs updates that reflect the corrected behavior

Out of scope for this wave:

- broader preset lifecycle work
- non-overlay appearance features
- large redesigns of signing orchestration
- unrelated parity refinements unless directly required by overlay correctness

### Remediation workstreams

#### Overlay-Fix

Primary owner:

- `presentation.qt` implementation worker

Responsibilities:

- correct the resize interaction model
- eliminate snapping/jumping caused by unstable handle math or coordinate conversions
- keep overlay updates synchronized with the existing draft workflow contract
- preserve current placement semantics unless a narrow, clearly justified change is required

Suggested owned files:

- `src/foliaseal/presentation/qt/viewer_widget.py`
- `src/foliaseal/presentation/qt/signing_shell.py`

Expected deliverables:

- stable handle dragging
- rectangle resizing that does not invert or jump unexpectedly
- better behavior across zoom/pan states
- no uncaught placement exceptions from overlay interaction

#### Overlay-Verification

Primary owner:

- focused test/review agent

Responsibilities:

- add or expand overlay-specific regression tests
- verify all four corners behave predictably
- verify overlay behavior remains stable with zoom/pan and repeated drags
- verify shell synchronization after overlay updates
- verify no new regressions were introduced in the viewer widget or shell

Suggested owned files:

- `tests/unit/test_qt_viewer_widget.py`
- `tests/unit/test_qt_signing_shell.py`
- optional focused review notes if needed

Expected deliverables:

- regression coverage for the reported manual bug
- confidence that overlay behavior is stable enough for another acceptance run

#### Overlay-Docs

Primary owner:

- docs/planning worker

Responsibilities:

- keep README and acceptance artifacts honest about the current overlay state
- update any acceptance guidance that changed because of the overlay fix
- avoid overpromising capabilities that remain future work

Suggested owned files:

- `README.md`
- `artifacts/phase3_fr3b_acceptance_checklist.md`
- optional acceptance notes artifact

Expected deliverables:

- concise documentation of the corrected overlay interaction
- clear acceptance instructions for the next manual pass

### Acceptance bar for ending this wave

Do not resume broader Phase 3 work until all of the following are true:

- overlay handle dragging no longer feels erratic in manual use
- no placement exception is raised during overlay resizing
- focused overlay/viewer/shell tests pass
- acceptance instructions are current
- a fresh manual rerun confirms the placement/resize task is no longer blocked by overlay behavior

## Recommended Reference Use In Future Chats

When opening a new chat or spawning a new agent, reference this file directly:

- `phase3_parallel_plan.md`

Suggested instruction:

"Please use `phase3_parallel_plan.md` as the Phase 3 coordination document. Follow the ownership boundaries and deliverables for the assigned workstream, and avoid unrelated refactors."

## Reusable Review Agent Template

Use this template when spawning a review-only agent so the review output stays concrete and consistent.

### When to use it

Use this template for:

- pre-merge review passes
- post-stabilization regression checks
- pre-integration checks before starting a downstream workstream
- final acceptance-oriented review sweeps

### Review prompt template

Copy and adapt the following:

```text
Use /home/daekar/SignPDF/Scratch/phase3_parallel_plan.md as the shared coordination document. This is a review-only task.

Review scope:
- <list the exact workstreams, files, or follow-up patches>

Your tasks:
- inspect for bugs
- inspect for regressions introduced by recent changes
- inspect for contract drift between the relevant layers
- inspect for missing tests, especially around the changed semantics
- inspect for docs/export/update gaps that could confuse downstream work

Return exactly this structure:
1. Findings
- ordered by severity, highest first
- each finding must include concrete file references
- focus on correctness issues, behavioral mismatches, API inconsistencies, missing tests, or docs/export gaps
- if there are no findings, write exactly: No findings

2. Residual risks
- brief

3. Go/no-go recommendation
- one of: go, go with caveats, hold
- one sentence why

Important constraints:
- findings first
- do not return an acknowledgment, plan, or status note
- do not make code changes unless a tiny clarification patch is clearly necessary; prefer reporting
- avoid unrelated refactors
```

### Coordinator notes

To keep review agents on task consistently:

1. Always require a fixed output structure.
2. Always forbid acknowledgment-only or plan-only responses.
3. Keep review scope narrow and explicit.
4. Require concrete file references in every finding.
5. Require an explicit go/no-go recommendation at the end.
6. If a reviewer returns a scope acknowledgment instead of findings, interrupt immediately and restate the required structure.
