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

## Current Status

As of 2026-03-29, Phase 3 should still be treated as in implementation.

Validated so far:

- core placement and resize mechanics now behave well enough in the Qt harness
- the richer signing request, draft workflow, preview semantics, and signing integration exist
- the harness is useful for validating geometry, settings propagation, and request capture
- named profile save/select UI is now in place with explicit overwrite confirmation
- persistent named profile storage and delete-current-profile behavior are implemented
- the shell can drive an executor-backed sign/apply-output path and surface success/failure
- the concrete backend now produces a genuinely cryptographically signed PDF through `pyHanko`
- the preview panel width/aspect-ratio behavior is materially more stable than earlier in the
  remediation wave
- the checked-in baseline `single_line`, `multi_line`, and `wrapped_block` preview matrices are
  currently structurally green across the repository
- the checked-in stress matrices are now the active content-density regression frontier and still
  expose remaining green-path clipping cases under realistic long-form inputs
- preview-matrix summaries now separate signable risk counts from rejected risk counts for both
  text and stamp diagnostics, so intentionally blocked bad layouts do not read like unresolved
  green-path regressions
- stamp warnings now represent border-facing near-border crowding only; text-facing stamp/text
  conflicts are tracked by the text overlap/clipping diagnostics instead
- after anti-aliased stamp-content detection was tightened, a remaining 1px border-facing gap is
  treated as acceptable raster clearance; actual contact still shows up in the explicit
  stamp edge-touch counts
- the baseline preview matrices are structurally green, but the stress matrices are intentionally
  not green yet and should be treated as the current preview-fidelity work queue rather than as
  product-ready acceptance proof
- preview validation and signed-output acceptance are separate concerns:
  - preview matrices prove layout geometry and content-density behavior,
  - signed-output evidence is the end-to-end proof layer that must verify the actual signed PDF
    against the reviewed preview
- harness evidence is now stricter: saved manual captures with `summary_json_path` are expected to
  preserve preview render artifacts and diagnostics; missing preview image paths are treated as an
  evidence-contract defect rather than a benign omission
- preview typography semantics are now intended to be layout-invariant: the selected point size
  should mean the same thing in `single_line`, `multi_line`, and `wrapped_block`, with layout mode
  affecting reservation geometry and fit behavior rather than silently rescaling text
- the `single_line` layout path has been simplified so preview composition and pre-submit fit
  validation now share the same backend-owned text/layout input rules
- Phase 3 harness artifacts now include a machine-validated evidence contract and explicit
  `engineering_run` / `gate_candidate` classification

Not yet achieved:

- a final Acrobat-like signing workflow suitable for true `FR-3B` acceptance
- a fully acceptance-ready appearance workflow and product-quality preview/signing flow
- complete preview/output parity for all realistic rectangle/layout combinations
- remediation of the new stress-matrix green-path regressions across `single_line`, `multi_line`,
  and `wrapped_block`
- manual harness revalidation of the simplified `single_line` path with real user assets
- trustworthy transparent-GIF stamp handling in final signed output
- TSA-backed timestamping and timestamp-required signing flows
- final end-to-end FR-3B acceptance against representative signed output
- a documented certificate compatibility matrix and manual QA pass across supported PKCS#12
  variations

Interpretation:

- `phase3-signing-harness` is an engineering validation tool
- it is not the final Phase 3 GUI target
- harness success should be treated as implementation progress, not final acceptance
- the executor seam now has a concrete cryptographic backend
- the remaining backend gap is honest TSA/timestamp support rather than basic PDF signing
- certificate support should be treated as PKCS#12-scoped for v1 until a broader identity model is
  explicitly planned
- the acceptance/governance gap is now much smaller because the harness can distinguish debugging
  runs from gate candidates automatically
- the remaining Phase 3 finish work is now concentrated in a few stubborn visible-signature fidelity
  gaps and acceptance confirmations rather than broad missing infrastructure
- the next acceptance wave should be framed as signed-output validation rather than another
  preview-matrix sweep; the preview work is now a prerequisite, not the final proof
- `artifacts/phase3_handoff_2026-04-03.md` should be treated as the tactical jump-in note for the
  next finishing wave, while this file remains the broader coordination document

## Proposed Next Instrumentation Wave

Status note: most of the originally proposed instrumentation wave has now landed. Keep this section
as historical context plus a checklist for any remaining evidence gaps; do not treat it as a
statement that preview-card capture, matrix sweeps, or stamp-content diagnostics are still absent.

The current harness and JSON capture are now useful, but the latest manual runs show that we still
need stronger evidence about the actual human experience of preview vs final output. The next
instrumentation upgrade should therefore stay above the display-server layer and focus on
application-visible artifacts.

Proposed instrumentation phases:

1. UI-state capture
- record preview-card geometry, inner body geometry, stamp/text widget bounds, scrollbar state,
  active layout metadata, and validation state at key interaction moments

2. Visual artifact capture
- capture the live preview card as an artifact
- capture a rendered crop of the signed annotation region from the final output PDF

3. Scripted interaction replay
- support deterministic replay of common signing scenarios so manual reruns become narrower and more
  reproducible

4. Visual comparison support
- add optional preview-vs-output comparison artifacts, including simple image diffs or structured
  comparison summaries where practical

Scope boundary for this wave:
- prefer app-level instrumentation and rendered artifacts
- do not introduce X11/Wayland/compositor tracing unless later evidence proves app-level capture is
  insufficient

Current harness instrumentation note:

- `phase3-signing-harness` can now write preview-card PNGs and preview widget geometry/border-distance
  metrics when `--artifacts-dir` is supplied
- successful signing runs should also capture signed-output render evidence and preview/output
  comparison data so acceptance review can inspect the actual signed PDF rather than only the
  preview
- the interactive harness now has a `Capture State` action so one manual GUI session can preserve
  several chosen preview/validation/backend snapshots in the same summary JSON
- `phase3-signing-preview-matrix` can apply a JSON scenario manifest and write per-scenario preview
  captures plus a summary JSON for batch fidelity sweeps
- `phase3-signing-acceptance-matrix` now exists for representative end-to-end signing runs and
  writes:
  - signed outputs per scenario
  - cryptographic verification snapshots
  - rendered signed-annotation crops
  - preview-vs-signed-output parity evidence
- the matrix now also writes a stamp-focused debug crop for stamped scenarios, with overlay boxes
  for the reserved stamp band, rendered pixmap, and projected non-transparent content bounds
- `artifacts/phase3_preview_matrix_template.json` is the hand-editable starting point for those
  sweeps
- `artifacts/preview_sweep_assets/` now contains a repository-local PDF/certificate/stamp suite plus
  `single_line_matrix.json` for unattended single-line preview regression sweeps
- matrix scenarios can now override `visible_fields` explicitly, which makes compact-layout sweeps
  easier to interpret and avoids conflating field-volume problems with geometry problems
- the checked-in single-line matrix now includes explicit text-size variation scenarios so preview
  regressions can be exercised across more than one `font_size_pt`
- the summary JSON now records alpha-aware stamp-content bounds plus explicit “touches edge” and
  “within warning distance” diagnostics so agents can distinguish “tiny but intact” from actual
  clipping risk

## Certificate Compatibility Profile

Phase 3 and the current backend should be planned against the following certificate scope:

- supported identity containers:
  - `.p12`
  - `.pfx`
- supported key families for release:
  - RSA
  - ECDSA
- expected container contents:
  - one signing identity with private key
  - one end-entity signing certificate
  - optional embedded chain certificates

Legacy/variation expectations:

- legacy `.pfx` naming is in scope
- older PKCS#12 encryption/MAC profiles are in scope only when they remain readable through the
  selected Python/OpenSSL stack
- malformed containers, unreadable legacy encodings, missing-key containers, and unsupported key
  algorithms must fail explicitly with actionable diagnostics
- multi-identity containers must not be handled by silent first-match selection; either reliable
  alias selection is implemented or the flow fails safely with guidance

Out of scope for current Phase 3 unless separately approved:

- PEM + private-key pairs
- PKCS#11 / smart-card tokens
- OS-native certificate stores
- hardware-backed providers that do not present as PKCS#12

## Scope Boundary

Phase 3 includes:

- appearance-template-driven signing flow
- place/resize/fine-tune signature rectangle
- editable signature property system
- inline validation
- live preview
- GUI integration with signing request creation

Historical note:

- The original roadmap assumed broader preset lifecycle work would wait for a later phase.
- In practice, Phase 3 already absorbed a substantial part of named-profile lifecycle work:
  - save,
  - select,
  - persistent reload across relaunch,
  - overwrite confirmation,
  - delete with confirmation.
- Remaining profile portability/completion work now belongs to the smaller post-Phase-3 roadmap
  slices in `pdf_signing_app_feasibility.md`, not a monolithic old “Phase 4” bucket.

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
7. Bias architectural decisions toward ruthless elimination of complexity.
   - Keep one backend-owned visible-signature fit gate.
   - Keep preview visual rather than interpretive.
   - Keep validation UI factual rather than duplicating preview semantics.

Historical-plan note:

- The remainder of this file includes both current coordination guidance and older implementation
  wave records.
- When a later section conflicts with the current-status summary above or a newer living ExecPlan,
  prefer the newer source rather than assuming every older remediation note is still active.

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

Until those conditions are met in the intended end-user workflow, Phase 3 should remain open even
if the harness validates individual mechanics successfully.

## Remaining Product Work Before FR-3B Acceptance

The current harness exposed an important distinction: implementation validation has progressed
meaningfully, but the intended signing workflow is not complete enough for final acceptance.

Remaining Phase 3 product-facing work should focus on:

- introducing a real visible-appearance concept in the GUI rather than exposing only raw settings
- shaping those controls into an intentional signing flow comparable to Acrobat/PDF-XChange
- adding a meaningful appearance preview rather than a primarily diagnostic readout
- replacing placeholder or awkward controls with more intentional product controls
  - example: constrained font selection instead of free-text font entry
- validating the resulting flow against representative Acrobat-like user tasks only after that UI exists

Future Phase 3 reviews should clearly separate:

- implementation validation
- true feature acceptance

Current execution rule:

- no Phase 3 completion claim is valid without a release-gating FR-3B run
- harness terminal success by itself counts only as engineering evidence unless the generated
  artifacts are machine-validated and the FR-3B worksheet records an explicit human gate verdict

## Remaining Phase 3 Build Plan

This section defines the remaining product-facing Phase 3 work needed before true `FR-3B`
acceptance should be attempted.

Reference model:

- Adobe Acrobat's visible-signature workflow supports selecting or creating a signature appearance,
  choosing which text/graphic elements appear, placing the signature on the page, reviewing a
  meaningful appearance, and then confirming the sign action.
- Relevant Adobe references consulted on 2026-03-29:
  - custom signature appearances:
    `https://www.adobe.com/devnet-docs/acrobatetk/tools/DigSigDC/appearances.html`
  - personalize digital signatures:
    `https://helpx.adobe.com/acrobat/desktop/e-sign-documents/fill-sign-documents/personlize-digital-sign.html`
  - modify e-signatures:
    `https://helpx.adobe.com/acrobat/kb/change-e-signature.html`

### Intended User Flow

The remaining FoliaSeal Phase 3 flow should aim for this shape:

1. Enter signing mode for the current PDF.
2. Choose an appearance or start editing the current appearance draft.
3. Configure meaningful appearance options in a focused UI.
4. Place the signature on the page.
5. Adjust placement with direct manipulation and numeric refinement.
6. Review a meaningful appearance preview that resembles the final visible signature.
7. Confirm/sign from the same focused flow.

The current harness helps validate mechanics underneath this flow, but should not be treated as
the destination UI.

### Product Gaps To Close

The current implementation still needs:

- a real user-facing "appearance" concept
- a clearer distinction between appearance editing and low-level/debug settings
- a meaningful appearance preview instead of mostly textual readout
- a more intentional signing flow shell
- more product-grade controls for constrained values
  - font family/style should not remain raw free-text if a controlled list is more appropriate
- final manual validation against the intended user flow rather than the harness alone

### Recommended Workstreams For The Remaining Phase 3 Work

#### Workstream F: Signing Flow UX architecture

Purpose:

- turn the current shell/harness structure into a coherent end-user signing flow

Primary outputs:

- revised signing flow structure
- clearer stage progression in the GUI
- focused action model around edit appearance, place signature, preview, and sign

Owned files:

- `src/foliaseal/presentation/qt/signing_shell.py`
- adjacent Qt flow/layout modules as needed

Deliverables:

- define a clear entry into signing mode
- structure the shell around the intended signing steps
- remove or demote implementation/debug affordances that should not dominate the final UI
- make the sign action feel like the final step of a coherent flow rather than a bare command button

Acceptance target:

- a user can describe what stage of signing they are in without reading developer notes

#### Workstream G: Appearance model to product UI mapping

Purpose:

- introduce a real "appearance" concept in the UI, even if full preset lifecycle remains Phase 4

Primary outputs:

- appearance section or panel that feels intentional
- explicit notion of current appearance draft
- clearer mapping between visible fields, graphics, and layout choices

Owned files:

- `src/foliaseal/presentation/qt/signing_shell.py`
- appearance-oriented presentation modules if split out
- limited application-layer glue if required

Deliverables:

- present appearance editing as a named concept in the UI
- group controls by appearance concerns rather than exposing an undifferentiated settings dump
- support the current draft appearance clearly
- leave full saved preset management for Phase 4

Acceptance target:

- `FR-3B` task language like "create a new appearance" or "modify the current appearance" makes sense to a tester

#### Workstream H: Real appearance preview

Purpose:

- make the preview feel like a visible signature preview rather than a diagnostic text area

Primary outputs:

- improved preview rendering in the Qt UI
- better visual relationship between appearance settings and the preview

Owned files:

- preview-related Qt presentation code
- preview renderer integration points

Deliverables:

- show the current visible signature in a more product-like preview form
- make image, text fields, layout, and style choices legible in that preview
- keep preview semantics aligned with the signing payload

Acceptance target:

- a tester can understand what the final visible signature will roughly look like without interpreting internal fields manually

#### Workstream I: Product-grade controls and form affordances

Purpose:

- replace obviously placeholder controls with more intentional ones

Primary outputs:

- dropdowns/choice controls where appropriate
- improved labels and grouped controls
- reduced dependence on free-text entry for constrained values

Owned files:

- Qt form/panel code

Deliverables:

- audit current controls for product readiness
- convert constrained fields to dropdowns/selectors where appropriate
- reduce ambiguity in labels and validation messages

Acceptance target:

- the form feels like a product UI, not just a parameter editor

#### Workstream J: Final Phase 3 acceptance pass

Purpose:

- validate the rebuilt flow against the intended `FR-3B` experience

Primary outputs:

- rewritten acceptance worksheet aligned to the actual Phase 3 UI
- final manual validation notes

Owned files:

- `artifacts/phase3_fr3b_acceptance_checklist.md`
- `artifacts/phase3_fr3b_acceptance_results.md`
- supporting docs as needed

Deliverables:

- replace harness-centric or misleading checklist language
- validate the final user flow rather than raw mechanics only
- record follow-up items that properly belong to Phase 4

Acceptance target:

- acceptance artifacts match the actual product being evaluated

### Safe Parallelization Plan

These remaining workstreams can still be parallelized carefully:

1. Start `Workstream F` first.
   - It defines the high-level shell and interaction model other UI work should fit into.

2. Start `Workstream G` shortly after F defines the shell structure.
   - G can shape the appearance concept and grouping without waiting for every preview detail.

3. Start `Workstream H` once G exposes the appearance grouping and F stabilizes where preview lives.
   - H should avoid inventing a competing UX structure.

4. Start `Workstream I` after F/G identify which controls are real product controls versus temporary placeholders.
   - This is a good sidecar stream because it can improve form affordances without owning the whole shell.

5. Start `Workstream J` only after F/G/H/I have landed enough UI to be honestly testable as a user flow.

### Coordination Notes

- Keep the harness, but treat it as a developer validation tool.
- Do not confuse harness success with user-flow acceptance.
- If the desired Acrobat-style flow needs clarification at any point, prefer checking with the user
  before locking down major UI structure.

## Agent-Ready Briefs For Remaining Phase 3 Work

These briefs are for the remaining product-facing Phase 3 work, after the harness and geometry
layers have been stabilized.

### Brief F: Signing Flow UX Architecture

You are implementing the remaining Phase 3 signing flow shell using an Acrobat-like workflow as the
reference model.

Objectives:

- turn the current shell/harness structure into a coherent end-user signing flow
- make the flow stages legible to users
- ensure the sign action feels like the final step of a guided flow rather than a bare command

Primary files you own:

- `src/foliaseal/presentation/qt/signing_shell.py`
- adjacent Qt flow/layout modules as needed
- relevant UI tests

Files you should avoid editing unless absolutely necessary:

- deep domain/config internals
- signing-engine implementation
- preview renderer internals owned by Brief H

Requirements to satisfy:

- FR-3
- FR-3B
- the intended Acrobat-like visible-signature flow in `phase3_parallel_plan.md`

Expected deliverables:

- a clearer signing-mode shell
- explicit structure around:
  - edit appearance
  - place signature
  - review preview
  - confirm/sign
- demotion or removal of debug-style affordances that should not dominate the product UI

Implementation notes:

- reuse the existing viewer and stable rectangle behavior
- do not invent a competing data model in the UI
- prefer layout/flow clarity over adding more low-level controls

Definition of done:

- a tester can understand what stage of signing they are in without reading developer notes

When to assign:

- first in the next Phase 3 wave

### Brief G: Appearance Concept and UI Mapping

You are introducing a real user-facing "appearance" concept in the Phase 3 GUI.

Objectives:

- make "appearance" a meaningful concept in the UI
- group visible-signature controls into an intentional appearance-editing experience
- support the current draft appearance clearly, without taking on full Phase 4 preset lifecycle work

Primary files you own:

- `src/foliaseal/presentation/qt/signing_shell.py`
- appearance-oriented presentation modules if split out
- limited application-layer glue if required
- relevant tests

Files you should avoid editing unless absolutely necessary:

- signing-engine implementation
- broad flow architecture decisions owned by Brief F
- preview rendering internals owned by Brief H

Requirements to satisfy:

- FR-3
- FR-3A
- FR-3B language around creating or modifying a visible appearance

Expected deliverables:

- a named appearance section or mode in the UI
- grouped controls for text fields, graphics, and layout choices
- a clearer distinction between appearance editing and placement controls

Implementation notes:

- the goal is not full saved preset management yet
- the goal is to make "current appearance draft" understandable to a human tester

Definition of done:

- `FR-3B` task language like "create a new appearance" or "modify the current appearance" makes sense in the UI

When to assign:

- after Brief F establishes the shell structure, or shortly after if the shell direction is already clear

### Brief H: Real Appearance Preview

You are making the visible-signature preview feel like an actual appearance preview rather than a
diagnostic text area.

Objectives:

- improve the preview so users can understand what the visible signature will roughly look like
- keep preview semantics aligned with the signing payload

Primary files you own:

- preview-related Qt presentation code
- preview renderer integration points
- relevant tests

Files you should avoid editing unless absolutely necessary:

- broad shell structure owned by Brief F
- appearance grouping decisions owned by Brief G
- signing-engine implementation

Requirements to satisfy:

- FR-3A real-time preview requirement
- the remaining product-preview goals in `phase3_parallel_plan.md`

Expected deliverables:

- a more product-like preview surface
- visible representation of image/text/layout/style choices
- tests that keep the preview aligned with the underlying signing payload

Implementation notes:

- do not overfit to the temporary harness
- the preview should be understandable without reading raw field names

Definition of done:

- a tester can look at the preview and meaningfully infer the final visible signature appearance

When to assign:

- after F/G clarify where the preview belongs and how appearance is grouped

### Brief I: Product-Grade Controls and Form Affordances

You are upgrading obviously placeholder controls into more intentional product controls.

Objectives:

- reduce dependence on raw free-text for constrained values
- improve labels, grouping, and general form usability

Primary files you own:

- Qt form/panel code
- relevant UI tests

Files you should avoid editing unless absolutely necessary:

- signing engine integration
- broad flow architecture owned by Brief F
- preview ownership from Brief H

Requirements to satisfy:

- the product-readiness goals in `phase3_parallel_plan.md`

Expected deliverables:

- an audit of current controls that still feel like developer placeholders
- improved control types where appropriate
  - example: dropdown/select controls for constrained font choices
- clearer labels and more intentional affordances

Implementation notes:

- optimize for end-user clarity, not parameter completeness
- coordinate with F/G so control upgrades support the intended flow instead of fighting it

Definition of done:

- the form feels like a product UI rather than a parameter editor

When to assign:

- after F/G identify which controls belong in the true product flow

### Brief J: Final Phase 3 Acceptance Alignment

You are preparing the final acceptance pass for the rebuilt Phase 3 user flow.

Objectives:

- align the acceptance artifacts with the actual product UI
- stop using harness-centric language as a proxy for final workflow acceptance

Primary files you own:

- `artifacts/phase3_fr3b_acceptance_checklist.md`
- `artifacts/phase3_fr3b_acceptance_results.md`
- supporting README/docs updates if needed

Files you should avoid editing unless absolutely necessary:

- core product implementation code

Requirements to satisfy:

- FR-3B acceptance alignment
- the implementation-vs-acceptance distinction established in `phase3_parallel_plan.md`

Expected deliverables:

- a rewritten acceptance checklist tied to the actual end-user flow
- final manual validation notes structure
- clear separation between Phase 3 acceptance and Phase 4 follow-up items

Implementation notes:

- do not start this too early
- this brief should follow actual UI progress, not lead it

Definition of done:

- acceptance artifacts match the product being evaluated instead of the temporary harness

When to assign:

- only after F/G/H/I have landed enough UI to be honestly evaluated as a user flow

## Follow-Up Preview Cleanup Wave

This short follow-up wave exists because the rebuilt shell is now directionally correct, but the
preview still contains product-UI leftovers and space-inefficient rendering choices.

The goals of this wave are:

- remove non-essential summary chrome from the product shell
- ensure the preview contains only plausible visible-signature output
- improve field ordering so signer identity reads naturally
- make the stamp region and overall preview behave more like a compact real signature box

The preview in this wave should be treated as output-facing, not as a place to restate settings.

### Preview Cleanup Acceptance Target

This wave should be considered complete when:

- the `Current appearance draft` summary block is gone from the product shell
- preview footer metadata like layout mode or timezone mode is gone
- visible fields appear in a signer-first order that feels natural to users
- the stamp area adapts sensibly to image aspect ratio
- the preview feels plausible for small real-world signatures instead of a roomy info panel

### Brief K: Preview UX Cleanup

You are cleaning up the visible-signature preview so it behaves like output rather than settings
instrumentation.

Objectives:

- remove redundant summary chrome from the product shell
- ensure the preview shows only what plausibly belongs in the visible signature
- reorder fields so signer identity reads naturally

Primary files you own:

- `src/foliaseal/presentation/qt/signing_shell.py`
- relevant preview-facing tests in `tests/unit/test_qt_signing_shell.py`

Files you should avoid editing unless absolutely necessary:

- signing-engine implementation
- low-level viewer geometry code
- harness CLI wiring except where strictly needed to keep tests aligned

Requirements to satisfy:

- the product-facing preview goals in this follow-up wave

Expected deliverables:

- remove the `Current appearance draft` summary section from the shell
- remove preview footer metadata such as layout mode and timezone mode
- ensure settings like field lists, placement values, and raw configuration labels do not appear
  inside the visible signature preview
- reorder rendered fields so signer identity fields appear before signing time and other
  signature-event details

Implementation notes:

- treat the preview as output-only
- controls may influence rendering, but control names/settings should not appear inside the
  preview unless they correspond to actual rendered text

Definition of done:

- the preview no longer feels like a diagnostic card with settings leakage

When to assign:

- immediately

### Brief L: Stamp and Compact Preview Layout

You are making the preview compact and visually plausible for small real-world signatures.

Objectives:

- improve stamp sizing and aspect-ratio behavior
- reduce wasted space in the preview layout
- make the preview work better at small signature sizes

Primary files you own:

- `src/foliaseal/presentation/qt/signing_shell.py`
- relevant preview/layout tests in `tests/unit/test_qt_signing_shell.py`

Files you should avoid editing unless absolutely necessary:

- broad shell flow decisions outside the preview region
- application/domain model layers unless a tiny preview contract fix is needed

Requirements to satisfy:

- compact visible-signature preview behavior for Phase 3 product UI

Expected deliverables:

- stamp region that adapts more naturally to image aspect ratio
- tighter spacing, sizing, and typography for compact signature previews
- preview layout that feels plausible for small signatures instead of a spacious info card

Implementation notes:

- optimize the preview for the common case where signatures are relatively small
- preserve readability while reducing unnecessary padding and empty space

Definition of done:

- the preview remains legible but no longer feels oversized or rigid

When to assign:

- immediately, in parallel with Brief K

### Brief M: Preview Cleanup Review

You are doing a review-only pass on the preview cleanup wave.

Objectives:

- verify that the preview now contains only plausible output content
- catch remaining settings leakage, ordering mistakes, or compact-layout regressions

Primary files you own:

- none for implementation

Primary files to review:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_qt_signing_shell.py`

Requirements to satisfy:

- use the review-agent template in this document
- return findings, residual risks, and go/no-go

Definition of done:

- the team has a concrete review gate before the next manual pass

When to assign:

- after Brief K and Brief L land

## Follow-Up Preview and Form Refinement Wave

This short wave exists because the shell is now much closer to a product UI, but there are still
layout-efficiency and preview-composition issues that make it feel heavier than it should.

The goals of this wave are:

- increase form density on the right-side controls without reducing clarity
- remove redundant preview chrome
- make the preview composition respond more meaningfully to layout template choice
- keep the preview compact and plausible for small real-world signatures
- make UTC the default timezone consistently

### Refinement Acceptance Target

This wave should be considered complete when:

- the right-side controls use space more efficiently
- the preview no longer shows an overlapping internal title
- layout-template changes produce visibly different preview composition
- UTC is the default timezone for a fresh workflow
- visible-field checkboxes read naturally without redundant checkbox text

### Brief N: Form Density and Labeling

You are refining the signing form so it uses space more efficiently and reads more naturally.

Objectives:

- make the right-side controls denser without harming clarity
- improve visible-field labeling
- set UTC as the default timezone consistently

Primary files you own:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `src/foliaseal/domain/models.py` only if needed for the default timezone contract
- relevant tests in `tests/unit/test_qt_signing_shell.py`
- relevant model tests in `tests/unit/test_signature_appearance_models.py` if the default contract changes

Files you should avoid editing unless absolutely necessary:

- signing-engine code
- low-level viewer geometry
- harness CLI behavior

Requirements to satisfy:

- the follow-up refinement goals in this document

Expected deliverables:

- denser `Text and layout` rows where compatible controls can share horizontal space
- denser `Placement` rows for page/coordinates/size
- visible-field checkboxes moved immediately to the left of the actual field labels
- removal of the redundant checkbox text `Visible`
- UTC as the default timezone for a fresh workflow

Implementation notes:

- prefer layout clarity over maximum compression
- if the timezone default changes at the domain level, update tests so the contract is explicit

Definition of done:

- the form feels meaningfully tighter and the fresh-workflow timezone default is UTC

When to assign:

- first in this wave

### Brief O: Layout-Template-Specific Preview Composition

You are refining the visible-signature preview so its structure changes meaningfully with the
selected layout template.

Objectives:

- remove redundant preview title chrome
- make the signer label prefix the top element
- give `single_line` and `multi_line` visibly different, useful compositions

Primary files you own:

- `src/foliaseal/presentation/qt/signing_shell.py`
- relevant preview/layout tests in `tests/unit/test_qt_signing_shell.py`

Files you should avoid editing unless absolutely necessary:

- domain/application layers unless a tiny preview contract tweak is truly needed
- unrelated shell flow code

Requirements to satisfy:

- the preview-composition goals in this document

Expected deliverables:

- remove the extra internal `Visible signature preview` text from the preview area
- signer label prefix always appears as the top element
- `single_line` layout places stamp below the prefix and content below the stamp
- `multi_line` layout places stamp to the left and multiline content to the right
- preserve compact vertical space where possible

Implementation notes:

- the preview should stay output-facing and compact
- optimize for small signatures, not poster-sized cards

Definition of done:

- layout-template changes produce meaningfully different preview composition without reintroducing
  settings leakage

When to assign:

- after Brief N or immediately after if the shell structure is still compatible

### Brief P: Form/Preview Refinement Review

You are doing a review-only pass on the refinement wave.

Objectives:

- verify that the denser form still reads clearly
- verify that preview composition behaves correctly for `single_line` and `multi_line`
- catch remaining redundancy, overlap, or wasted-space regressions

Primary files to review:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `src/foliaseal/domain/models.py` if the timezone default changed
- `tests/unit/test_qt_signing_shell.py`
- `tests/unit/test_signature_appearance_models.py` if touched

Requirements to satisfy:

- use the review-agent template in this document
- return findings, residual risks, and go/no-go

Definition of done:

- the team has a concrete review gate before the next manual pass

When to assign:

- after Brief N and Brief O land

## Follow-Up Visible Fields Simplification Wave

This short wave exists because the visible-fields area still carries redundant controls and more
label clutter than the intended signing workflow needs.

The goals of this wave are:

- remove redundant visibility controls
- make the visible-fields section denser and easier to scan
- add an appearance-level `Show field names` toggle so users can choose labeled or value-only
  preview text

This wave should be handled in sequence because the `Show field names` setting is a shared contract
change that the shell simplification should build on directly.

### Visible Fields Simplification Acceptance Target

This wave should be considered complete when:

- field visibility is controlled by source selection alone
- the redundant visibility checkboxes are gone
- the visible-fields section uses space more efficiently
- `Show field names` defaults to `False`
- the preview clearly switches between labeled and value-only rendering

### Brief Q: Visible Fields Simplification

You are simplifying the visible-fields UI so it no longer carries redundant visibility controls.

Objectives:

- remove the separate visibility checkbox layer
- make the field rows denser and easier to scan
- rely on the source control as the single truth for whether a field is shown

Primary files you own:

- `src/foliaseal/presentation/qt/signing_shell.py`
- relevant shell tests in `tests/unit/test_qt_signing_shell.py`

Files you should avoid editing unless absolutely necessary:

- domain/application model layers
- signing-engine code
- viewer geometry

Requirements to satisfy:

- the visible-fields simplification goals in this document

Expected deliverables:

- remove the visible-field checkboxes from the shell
- ensure `hidden` in the source control is the only not-shown mechanism
- compress the visible-fields layout where practical without harming readability

Implementation notes:

- do not add the `Show field names` contract here unless a tiny compatibility hook is unavoidable
- keep this brief focused on shell simplification

Definition of done:

- the visible-fields area is less redundant and more space-efficient

When to assign:

- first in this wave

### Brief R: Show Field Names Contract and Preview Behavior

You are adding a user-facing `Show field names` setting and wiring it through preview behavior.

Objectives:

- add an appearance-level toggle named `Show field names`
- default it to `False`
- make the preview render either `Label: value` or `value` based on that toggle

Primary files you own:

- `src/foliaseal/domain/models.py`
- `src/foliaseal/application/signing_draft_workflow.py`
- `src/foliaseal/presentation/qt/signing_shell.py`
- relevant tests in:
  - `tests/unit/test_signature_appearance_models.py`
  - `tests/unit/test_signing_draft_workflow.py`
  - `tests/unit/test_qt_signing_shell.py`

Files you should avoid editing unless absolutely necessary:

- signing-engine integration
- unrelated shell flow/layout work

Requirements to satisfy:

- the visible-fields rendering goals in this document

Expected deliverables:

- new appearance-level `show_field_names` setting
- default contract set to `False`
- preview rendering that shows labels only when enabled
- test coverage for both labeled and value-only modes

Implementation notes:

- preserve the existing field-order and layout-template behavior
- this is a contract change, so update tests at every affected layer

Definition of done:

- preview text cleanly switches between labeled and value-only rendering

When to assign:

- after Brief Q lands

### Brief S: Visible Fields Review

You are doing a review-only pass on the visible-fields simplification wave.

Objectives:

- verify the source-only visibility model is clearer
- verify `Show field names` behaves correctly for the preview
- catch remaining redundancy, ambiguity, or missing tests

Primary files to review:

- `src/foliaseal/domain/models.py`
- `src/foliaseal/application/signing_draft_workflow.py`
- `src/foliaseal/presentation/qt/signing_shell.py`
- relevant tests in `tests/unit/`

Requirements to satisfy:

- use the review-agent template in this document
- return findings, residual risks, and go/no-go

Definition of done:

- the team has a concrete review gate before the next manual pass

When to assign:

- after Brief Q and Brief R land

## Follow-Up Named Profiles and Real Output Wave

This wave now consists primarily of finishing the concrete production signing backend behind the
executor seam before true acceptance:

- reusable named appearance profiles are implemented in the current shell workflow
- executor-backed signed-output application is available at the shell seam
- the remaining gap is the concrete production signing backend and final acceptance validation

For this wave to count as complete, the resulting UX must let a user:

- save the current appearance configuration as a profile with a distinct user-provided name
- see saved appearance profiles in a dropdown list
- reselect a saved profile from that dropdown in the current signing flow
- relaunch the app or harness and still see previously saved profiles
- delete a no-longer-needed profile from the UI with a confirmation step

### Named Profiles and Real Output Acceptance Target

This wave should be considered complete when:

- a user can save the current appearance as a named profile
- a user is prompted for an explicit overwrite confirmation when saving a duplicate profile name
- saved profiles are selectable from a dropdown in the signing UI
- selecting a saved profile repopulates the current appearance state correctly
- named profiles persist across relaunches in a clearly labeled `Signature Profiles` directory
- persisted profiles are stored in a human-readable JSON or similarly inspectable text format
- the shell provides a delete-current-profile action with explicit confirmation
- the shell can drive an executor-backed sign/apply-output path rather than request capture alone
- a concrete production signing backend is wired into that executor seam
- the acceptance artifacts can distinguish implemented profile reuse from still-future preset work

### Brief T: Named Appearance Profile Contract and Persistence

You are implementing the profile model and persistence needed for named appearance reuse in Phase 3.

Objectives:

- support saving the current appearance configuration as a named profile
- support loading named profiles into the current signing workflow
- keep the scope focused on named appearance profiles rather than full Phase 4 preset management

Primary files you own:

- `src/foliaseal/domain/models.py`
- `src/foliaseal/infra/config/schemas.py`
- relevant persistence/application glue as needed
- tests in `tests/unit/`

Files you should avoid editing unless absolutely necessary:

- most Qt layout/shell code
- signing-engine integration

Requirements to satisfy:

- named appearance profiles with distinct user-provided names
- a contract suitable for dropdown selection in the UI

Expected deliverables:

- a profile model or schema that includes a user-visible profile name
- persistence support sufficient for the UI to list profiles across relaunches
- load/save behavior for named profiles
- a storage layout rooted in a clearly labeled `Signature Profiles` directory
- a human-readable JSON or similarly inspectable on-disk format for saved profiles
- tests covering:
  - save a named profile
  - reject invalid or duplicate names if required by the chosen design
  - restore a saved profile into appearance state
  - reload saved profiles after process restart or catalog reload

Implementation notes:

- this is not full preset lifecycle parity yet; keep the scope to what Phase 3 needs
- optimize for the UI requirement that profiles appear in a dropdown and can be reselected

Definition of done:

- the shell can depend on a stable, named profile contract for save/select behavior

When to assign:

- first in this wave

### Brief U: Named Profile UI and Dropdown Workflow

You are implementing the Phase 3 UI for saving and selecting named appearance profiles.

Objectives:

- let the user save the current appearance with a distinct name
- present saved profiles in a dropdown
- reload a selected profile into the current appearance draft
- prompt for explicit overwrite confirmation when the user saves a duplicate profile name
- let the user delete the currently loaded profile with explicit confirmation

Primary files you own:

- `src/foliaseal/presentation/qt/signing_shell.py`
- related Qt support modules if needed
- relevant shell tests in `tests/unit/test_qt_signing_shell.py`

Files you should avoid editing unless absolutely necessary:

- signing-engine code
- deeper persistence/model work owned by Brief T

Requirements to satisfy:

- named profile save/select UX in the current signing shell

Expected deliverables:

- profile dropdown in the signing UI
- save-current-profile action with user-provided name
- explicit overwrite confirmation for duplicate names
- delete-current-profile action with explicit confirmation for the selected profile
- selection behavior that reapplies the chosen profile to the current appearance
- tests covering save/select/delete behavior and profile repopulation

Implementation notes:

- optimize for a focused Phase 3 workflow, not broad profile management screens
- keep the UI understandable without opening a separate profile-management mode

Definition of done:

- a user can save a named profile, reselect it from a dropdown after relaunch, and delete it safely from the same signing flow

Status:

- implemented

### Brief V: Real Sign-and-Apply Output Flow

You are replacing request-capture-only behavior with a real sign/apply-output path from the shell.

Objectives:

- let the shell perform the actual sign/apply-output flow
- make it possible to verify signed output from the user workflow rather than only captured requests

Primary files you own:

- application/signing integration code
- shell wiring needed to trigger the real flow
- relevant integration tests

Files you should avoid editing unless absolutely necessary:

- named-profile schema/UI ownership unless a small integration touch is required

Requirements to satisfy:

- real signed-output application from the current shell

Expected deliverables:

- shell-triggered signing path that produces real output
- user-visible success/failure handling
- tests covering valid output creation and failure reporting

Implementation notes:

- preserve the richer appearance payload already built in Phase 3
- keep the workflow compatible with named profile reuse

Definition of done:

- a user can sign from the shell and inspect a real output PDF
- the executor seam is ready for the concrete production backend

When to assign:

- after T/U are stable enough that the final workflow inputs are not moving heavily

### Brief W: Named Profiles and Real Output Review

You are doing a review-only pass on the named-profiles and real-output wave.

Objectives:

- verify named profile save/select behavior
- verify dropdown-driven profile reuse matches the saved configuration
- verify saved profiles survive relaunch through the on-disk profile directory
- verify delete-profile UX uses explicit confirmation and removes the profile from subsequent sessions
- verify the shell now supports real sign/apply-output behavior
- identify regressions or remaining acceptance blockers

Primary files to review:

- profile contract/persistence files from Brief T
- shell files from Brief U
- signing integration files from Brief V
- relevant tests in `tests/unit/`

Requirements to satisfy:

- use the review-agent template in this document
- return findings, residual risks, and go/no-go

Definition of done:

- the team has a concrete review gate before the next acceptance-oriented manual pass

When to assign:

- after T, U, and V land

## Follow-Up Profile Persistence and Deletion Wave

This wave focused on closing the remaining named-profile lifecycle gaps discovered during manual
review.

Implemented in this wave:

- saved profiles persist across relaunches
- persisted profiles live in a clearly labeled `Signature Profiles` directory
- persisted profiles are stored in a human-readable JSON or similarly inspectable text format
- the shell supports deleting the currently selected profile with explicit confirmation

### Profile Persistence and Deletion Acceptance Target

This wave is considered complete when:

- a user can save a named profile and still see it after relaunching the app or harness
- persisted profiles are written beneath a clearly labeled `Signature Profiles` directory
- persisted profiles use a human-readable JSON or similarly inspectable text format
- selecting a persisted profile repopulates the current appearance state correctly
- the shell offers a delete-current-profile action
- deleting a profile requires explicit confirmation
- a deleted profile no longer appears in the dropdown after confirmation or relaunch

### Brief X: Persistent Profile Storage

Status: implemented

You implemented on-disk persistence for named appearance profiles.

Objectives:

- persist named appearance profiles across relaunches
- use a clearly labeled `Signature Profiles` directory
- use a human-readable JSON or similarly inspectable text format
- keep the contract focused on Phase 3 profile lifecycle needs rather than full preset management

Primary files you own:

- `src/foliaseal/infra/config/schemas.py`
- `src/foliaseal/application/signing_draft_workflow.py`
- new infra/application persistence helpers as needed
- relevant tests in `tests/unit/`

Files you should avoid editing unless absolutely necessary:

- most Qt layout/shell code
- signing backend integration

Requirements to satisfy:

- stable load/save behavior for named profiles across process restart
- a storage location understandable to a user inspecting the filesystem

Expected deliverables:

- persistence helpers for reading and writing the profile catalog
- a clearly named storage directory contract for saved profiles
- human-readable serialized profile files
- tests covering:
  - save profiles to disk
  - reload profiles from disk
  - preserve stable dropdown ordering if required by the chosen design
  - handle empty/missing storage directories gracefully

Implementation notes:

- optimize for clarity and inspectability over cleverness
- avoid dragging in broad Phase 4 preset-management scope

Definition of done:

- the shell can rely on a persistent profile catalog that survives relaunches

### Brief Y: Delete Profile UI and Persistence Wiring

Status: implemented

You implemented safe delete behavior and wired the shell to the persistent profile catalog.

Objectives:

- load persisted profiles into the shell on startup
- let the user delete the currently selected profile
- require explicit confirmation before deletion
- keep save/select/delete behavior coherent in the same focused workflow

Primary files you own:

- `src/foliaseal/presentation/qt/signing_shell.py`
- any light application glue needed to load persisted profiles into the shell
- relevant shell tests in `tests/unit/test_qt_signing_shell.py`

Files you should avoid editing unless absolutely necessary:

- deeper persistence/model work owned by Brief X
- signing backend integration

Requirements to satisfy:

- persisted profiles appear in the shell after relaunch
- delete-current-profile UX with explicit confirmation

Expected deliverables:

- shell wiring that loads the persistent profile catalog
- delete-current-profile action in the named-profiles area
- explicit confirmation before deleting the selected profile
- dropdown refresh behavior after delete/save/select
- tests covering:
  - persisted profiles appear after reload
  - delete confirmation accept path
  - delete confirmation cancel path
  - deleted profiles no longer appear in the dropdown

Implementation notes:

- keep the UI focused and compact
- optimize for preventing accidental destructive clicks

Definition of done:

- a user can save, relaunch, reselect, and delete profiles safely from the shell

### Brief Z: Profile Persistence and Deletion Review

Status: completed

This review-only pass covered persistent named profiles and safe deletion.

Objectives:

- verify persisted profiles survive relaunch
- verify storage location and format are understandable
- verify delete-current-profile behavior is safe and explicit
- identify regressions or remaining acceptance blockers

Primary files to review:

- persistence files from Brief X
- shell and integration files from Brief Y
- relevant tests in `tests/unit/`
- related docs and acceptance artifacts if changed

Requirements to satisfy:

- use the review-agent template in this document
- return findings, residual risks, and go/no-go

Definition of done:

- the team has a concrete review gate before the next manual save/relaunch/delete pass

## Follow-Up Concrete Signing Backend and End-to-End Acceptance Wave

This wave focused on the main remaining Phase 3 engineering gap:

- wiring a concrete production signing backend into the shell's executor seam
- replacing the current output-artifact bridge with a true cryptographic signing backend
- validating that the end-to-end output is a genuinely signed PDF whose visible appearance matches
  the configured placement and appearance closely enough for Phase 3 acceptance work to become
  meaningful

### Concrete Backend and Acceptance Target

This wave is considered complete when:

- the shell can trigger a concrete backend path that writes a genuinely signed PDF
- success/failure messaging is coherent in the shell for the real backend path
- the harness/manual flow can inspect a truly signed output file rather than only an output artifact
- acceptance artifacts clearly distinguish real-output verification from remaining Phase 4 work
- the team has a concrete review gate and a focused manual end-to-end pass

### Brief AA: Concrete Signing Backend Integration

You are implementing the concrete production signing backend behind the executor seam.

Objectives:

- connect the current shell executor path to a true cryptographic signing backend
- replace the current output-artifact bridge with genuinely signed output from the Phase 3 flow
- keep the integration incremental by extending existing signing orchestration rather than
  replacing it

Primary files you own:

- `src/foliaseal/application/sign_pdf_use_case.py`
- relevant application/backend integration files
- light shell wiring only where needed to connect the executor seam
- relevant tests in `tests/unit/`

Files you should avoid editing unless absolutely necessary:

- broad profile lifecycle UI
- unrelated documentation artifacts

Requirements to satisfy:

- true cryptographic signed-output generation from the shell flow
- user-visible success/failure handling for the concrete backend path
- compatibility with the richer Phase 3 appearance payload
- use a real signing-capable Python dependency if needed rather than trying to build PDF signing
  directly on top of raw `openssl` calls alone

Expected deliverables:

- a concrete cryptographic executor/backend path usable by the signing shell
- shell-triggered output creation that writes a genuinely signed PDF where expected
- tests covering successful output creation and failure reporting
- dependency updates required for the chosen signing backend

Implementation notes:

- preserve the existing executor seam rather than bypassing it
- keep the workflow compatible with named profile reuse and the current preview model
- prefer adopting a PDF-signing-capable Python library, with `pyHanko` as the default direction
  unless a better-integrated alternative is justified
- do not spend time polishing the current output-artifact bridge; replace its placeholder
  certificate loader, signer, and verifier internals with real implementations

Definition of done:

- a user can sign from the shell and inspect a genuinely signed PDF

### Brief AB: End-to-End Acceptance Artifact Prep

You are preparing the acceptance artifacts for real-output testing.

Objectives:

- update the Phase 3 acceptance checklist/results so the next manual pass can record
  concrete backend execution and true signed-output inspection
- keep the artifacts honest about what is now implemented versus what remains Phase 4 work

Primary files you own:

- `artifacts/phase3_fr3b_acceptance_checklist.md`
- `artifacts/phase3_fr3b_acceptance_results.md`

Files you should avoid editing unless absolutely necessary:

- shell code
- backend integration files

Requirements to satisfy:

- the next manual pass can record:
  - real sign execution
  - true signed-output creation
  - output inspection versus preview/settings
  - remaining backend or fidelity gaps

Expected deliverables:

- refined acceptance checks for end-to-end true signed-output validation
- clearer note sections for preview-vs-output comparison
- removal of stale wording that treats output-artifact creation as true signing

Definition of done:

- the acceptance artifacts are ready for a true signed-output manual pass once the cryptographic backend lands

### Brief AC: Backend Integration Reconnaissance

You are doing a low-risk read-only pass to identify the concrete integration points for the
production signing backend.

Objectives:

- identify what already exists in `SignPdfUseCase` and related backend contracts
- identify the narrowest path to connect the shell executor to true cryptographic signing
- surface risks before the main worker lands changes

Primary files to inspect:

- `src/foliaseal/application/sign_pdf_use_case.py`
- related backend/application files
- `src/foliaseal/presentation/qt/signing_shell.py`
- relevant tests in `tests/unit/`

Requirements to satisfy:

- do not edit files
- return a short integration-risk memo with likely touch points and risks

Definition of done:

- the main backend worker has a clearer map of the integration surface

### Brief AD: Concrete Backend Review

You are doing a review-only pass on the concrete backend integration wave.

Objectives:

- verify the concrete backend path is actually wired end-to-end and performs true signing
- verify shell success/failure handling is coherent
- verify acceptance artifacts match the new true signed-output behavior
- identify regressions or remaining Phase 3 blockers

Primary files to review:

- backend integration files from Brief AA
- relevant shell wiring
- acceptance artifacts from Brief AB
- relevant tests in `tests/unit/`

Requirements to satisfy:

- use the review-agent template in this document
- return findings, residual risks, and go/no-go

Definition of done:

- the team has a concrete review gate before the next end-to-end manual pass

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

## Follow-Up Visible Appearance Parity Wave

This wave focuses on the current Phase 3 blocker after real cryptographic signing landed:

- the final visible signature written into the PDF does not yet match the shell preview closely
  enough for acceptance
- derived field mapping needs to stay semantically correct between preview and backend output
- harness artifacts need richer signing/output diagnostics so manual review can distinguish
  cryptographic success from appearance-parity failure

### Appearance Parity Target

This wave should be considered complete when:

- the final PDF appearance obeys the selected layout template closely enough to compare fairly with
  the shell preview
- stamp image placement and text placement in the output are no longer centered/squashed in ways
  that contradict the preview
- derived field mapping is semantically correct for DN/common name/email/title/company/location
- harness capture includes enough post-sign diagnostics to support appearance-parity debugging
- a focused review and manual pass can judge output fidelity instead of guessing from sparse logs

### Brief AE: Backend Appearance Parity

You are implementing the backend visible-appearance parity fixes for the Phase 3 signing path.

Objectives:

- make the final visible signature in the written PDF match the shell preview semantics more
  closely
- correct derived-field output behavior so the backend does not invent placeholder labels or
  duplicate decomposed fields unnecessarily
- improve text/image positioning so the visible signature is actually readable in the output PDF

Primary files you own:

- `src/foliaseal/application/phase3_signing_backend.py`
- relevant backend-oriented tests in `tests/unit/`

Files you should avoid editing unless absolutely necessary:

- broad shell UI layout
- README / acceptance artifacts

Requirements to satisfy:

- derived-field mapping must be semantically correct
  - DN should be treated as its own field
  - decomposed fields should not silently duplicate DN content unless the request explicitly asks
    for both
  - title/location/reason should not fall back to nonsense placeholders in signed output
- the output appearance should respect the selected layout template closely enough for manual
  comparison against the preview
- text should not be shrunk into unreadability when the rectangle has reasonable space
- stamp image placement should no longer default to visually useless centered composition

Expected deliverables:

- backend appearance-composition improvements in the signing path
- tests covering derived-field semantics and output-oriented appearance behavior
- no regression in cryptographic signing or failure-code mapping

Definition of done:

- the backend writes a signed PDF whose visible appearance is materially closer to the preview
- focused backend tests pass

### Brief AF: Harness Diagnostics Enrichment

You are enriching the Phase 3 harness artifacts so manual appearance-parity debugging has enough
 evidence to be useful.

Objectives:

- add richer post-sign capture about the final output and current preview state
- make it easier to diagnose whether a problem is preview semantics, backend output, or UX
  communication

Primary files you own:

- `src/foliaseal/presentation/qt/phase3_harness.py`
- `tests/unit/test_phase3_harness.py`
- tiny shell touches only if needed to expose already-existing result data

Requirements to satisfy:

- capture signing result success/failure and message
- capture whether the output file exists, its size, and embedded signature count
- capture current preview text/state helpful for appearance-parity review
- keep the harness output stable and readable

Expected deliverables:

- richer JSON capture and seeded acceptance artifact summary
- regression tests for the new capture fields

Definition of done:

- a manual run yields enough artifact detail to reason about appearance mismatch without guessing

### Brief AG: Visible Appearance Review

You are doing a review-only pass on the appearance-parity wave.

Review scope:

- `src/foliaseal/application/phase3_signing_backend.py`
- `src/foliaseal/presentation/qt/phase3_harness.py`
- affected tests under `tests/unit/`

Tasks:

- inspect for bugs in derived-field mapping semantics
- inspect for preview/output contract drift
- inspect for remaining layout-template mismatches that would keep the output visibly unusable
- inspect for missing tests or missing diagnostics in the richer harness output

Definition of done:

- findings are concrete and scoped to backend appearance parity and harness diagnostics

## Final Appearance Parity Follow-Up

This wave addresses the remaining no-go findings from the visible appearance review:

- the stamp is not yet maximized within the available rectangle while preserving the requested text size
- `wrapped_block` does not yet have its own backend layout contract
- harness artifacts still do not capture enough final-output appearance detail to reason confidently

### Brief AH: Max-Fit Stamp and Template Parity

You are fixing the backend visible-appearance layout so the written PDF output better matches the
 preview contract and uses the available rectangle more intelligently.

Objectives:

- make stamp sizing responsive to the available rectangle and surrounding text needs
- preserve the requested text size instead of shrinking text away unnecessarily
- give `wrapped_block` its own explicit backend layout semantics instead of treating it as
  `multi_line`
- keep the cryptographic signing path and failure semantics intact

Primary files you own:

- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_phase3_signing_backend.py`

Requirements to satisfy:

- the stamp should scale up as large as practical within the signature rectangle while still
  leaving room for the selected text at the specified font size
- `single_line`, `multi_line`, and `wrapped_block` must each have explicit backend layout behavior
- add focused tests that lock in the new layout contract and prevent regression
- do not weaken the real signing, PKCS#12 loading, or verification behavior

Expected deliverables:

- backend layout/scaling improvements for visible signatures
- focused regression tests for stamp sizing and all three layout templates

Definition of done:

- the backend no longer relies on a fixed-size/no-scaling stamp path
- `wrapped_block` is explicitly represented in code and tests

### Brief AI: Output-Side Appearance Diagnostics

You are enriching the harness/output diagnostics so preview-to-output mismatches are more concrete
 after a real signing run.

Objectives:

- capture more facts about the final output appearance without guessing
- help reviewers compare requested appearance, preview snapshot, and output-side facts

Primary files you own:

- `src/foliaseal/presentation/qt/phase3_harness.py`
- `tests/unit/test_phase3_harness.py`
- minimal test-side support changes only if clearly necessary

Requirements to satisfy:

- keep existing capture fields stable
- add output-side appearance facts if supportable from current code paths or post-sign inspection
- prefer structured capture over free-form text where possible
- do not claim geometry or layout facts you cannot actually observe

Expected deliverables:

- richer harness capture for final-output appearance analysis
- focused tests for the added capture fields

Definition of done:

- a post-sign artifact gives materially better evidence about output-side appearance than before

### Brief AJ: Final Appearance Review

You are doing a review-only pass on the final appearance-parity follow-up.

Review scope:

- `src/foliaseal/application/phase3_signing_backend.py`
- `src/foliaseal/presentation/qt/phase3_harness.py`
- affected tests under `tests/unit/`

Tasks:

- inspect whether stamp sizing is now truly max-fit relative to remaining text space
- inspect whether `wrapped_block` has distinct backend semantics and coverage
- inspect whether the harness now captures enough output-side appearance evidence
- inspect for regressions in signing, verification, and field-derivation behavior

Definition of done:

- findings clearly answer whether visible appearance parity is ready for another real manual run

## Appearance Tightening Pass

This pass addresses the remaining hold from the final appearance review:

- stamp sizing is still only best-effort rather than an explicitly constrained max-fit policy
- output-side diagnostics still do not expose enough reserved-space facts to judge parity cleanly

### Brief AK: Deterministic Stamp Reservation

You are tightening the backend visible-appearance logic so the stamp/text split is more
 deterministic and inspectable than the current best-effort pyHanko composition.

Objectives:

- make the reserved text area and remaining stamp area explicit from the actual signature rectangle
- strengthen the contract around how much space is reserved for text at the requested font size
- improve the honesty of the max-fit policy, even if a mathematically perfect solver is not
  practical with pyHanko

Primary files you own:

- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_phase3_signing_backend.py`

Requirements to satisfy:

- compute and retain explicit reserved-space facts for text vs stamp
- keep `single_line`, `multi_line`, and `wrapped_block` distinct
- preserve cryptographic signing, PKCS#12 handling, and verification behavior
- add focused tests that lock in the stronger reservation/sizing contract

Expected deliverables:

- tighter backend layout policy for stamp/text partitioning
- focused tests for reservation behavior and template-specific sizing outcomes

Definition of done:

- the backend has a more explicit stamp/text area policy than simple stretch-to-fit after implicit
  reservation

### Brief AL: Reserved-Space Output Diagnostics

You are enriching the harness/output artifacts with the backend-reserved appearance facts needed to
 reason about final layout.

Objectives:

- capture the reserved text/stamp sizing facts if available from the backend
- expose enough structured data to compare request, preview, and backend reservation decisions

Primary files you own:

- `src/foliaseal/presentation/qt/phase3_harness.py`
- `tests/unit/test_phase3_harness.py`
- minimal support changes only if clearly necessary

Requirements to satisfy:

- keep existing capture fields stable
- add structured reservation/appearance facts only when they can be observed honestly
- prefer additive JSON snapshots over prose

Expected deliverables:

- richer post-sign artifacts for appearance debugging
- focused tests for the new capture fields

Definition of done:

- manual harness artifacts expose materially better evidence about backend reservation choices

### Brief AM: Tightening Review

You are doing a review-only pass on the appearance tightening pass.

Review scope:

- `src/foliaseal/application/phase3_signing_backend.py`
- `src/foliaseal/presentation/qt/phase3_harness.py`
- affected tests under `tests/unit/`

Tasks:

- inspect whether stamp/text reservation is now explicit enough to support the max-fit claim more
  honestly
- inspect whether the new output-side diagnostics are sufficient to make the next manual run
  materially more trustworthy
- inspect for regressions in signing, verification, and field derivation

Definition of done:

- findings clearly state whether the next manual run is now worth doing

## Corrective Wave: Harness, Zoom, and Fit

This wave addresses the new regressions and blockers found during the latest real harness/manual
 run:

- harness capture serialization can crash when richer diagnostics are present
- viewer zoom can shrink content without shrinking the apparent page bounds
- final visible signature output can still produce unusable image/text fit

### Brief AN: Harness and Viewer Regression Fixes

You are fixing the non-signing regressions surfaced by the latest manual run.

Objectives:

- make harness capture serialization robust even with richer nested diagnostics
- fix the viewer zoom/page-bound regression so page bounds track the rendered content correctly
- add regression tests for both issues

Primary files you own:

- `src/foliaseal/presentation/qt/phase3_harness.py`
- `src/foliaseal/presentation/qt/viewer_widget.py`
- `tests/unit/test_phase3_harness.py`
- `tests/unit/test_qt_viewer_widget.py`

Requirements to satisfy:

- `capture.to_json()` must not fail due to non-serializable nested objects
- zoom in/out must keep page bounds visually in sync with rendered content
- add tests that would have caught the current regression

Expected deliverables:

- robust harness serialization
- viewer zoom regression fix
- focused regression tests

Definition of done:

- the harness no longer crashes while writing artifacts
- zoomed page bounds match the rendered page content closely enough in the widget

### Brief AO: Visible Signature Fit Correction

You are fixing the remaining visible-signature fit problems in the written PDF output.

Objectives:

- stop the stamp image from overwhelming the reserved rectangle
- ensure text remains visible and placed inside the reserved text region
- make fit/overflow behavior more defensive and explicit

Primary files you own:

- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_phase3_signing_backend.py`

Requirements to satisfy:

- preserve image aspect ratio while fitting into the reserved stamp region
- keep text readable and top-left aligned within its reserved region
- tighten behavior for very small/awkward rectangles so output is not silently unusable
- preserve signing, verification, PKCS#12 handling, and derived-field semantics

Expected deliverables:

- improved visible-signature fit policy
- focused tests for image+text fit and awkward rectangles

Definition of done:

- a real signed PDF should no longer reduce text to effectively invisible output in normal use

### Brief AP: Corrective Review

You are doing a review-only pass on the corrective wave.

Review scope:

- `src/foliaseal/presentation/qt/phase3_harness.py`
- `src/foliaseal/presentation/qt/viewer_widget.py`
- `src/foliaseal/application/phase3_signing_backend.py`
- affected tests under `tests/unit/`

Tasks:

- inspect whether the harness serialization path is now robust
- inspect whether the zoom/page-bound regression is actually prevented
- inspect whether visible-signature fit is materially safer and less likely to generate useless
  output
- inspect for regressions in signing, verification, and field derivation

Definition of done:

- findings clearly state whether another real harness/manual run is worth doing

## Compact Rectangle Compliance Wave

This wave corrects implementation drift against the already-approved visible appearance sizing
 contract:

- text size in points should be honored first
- text space should be reserved first
- the stamp should then maximize within the remaining permitted area
- ordinary compact signature lines on common forms should not be rejected as if they were unusable

The latest manual harness run showed that a realistic form-line rectangle was rejected even though
 it should be supported under the existing contract.

### Brief AQ: Compact Rectangle Backend Compliance

You are correcting the backend fit policy so realistic compact rectangles succeed when they should
 under the text-first sizing contract.

Objectives:

- relax over-conservative fit heuristics for ordinary compact rectangles
- preserve the text-first contract: honor requested text size first, then maximize the stamp within
  the remaining area
- keep too-small rectangles failing honestly, but stop rejecting normal form-line cases

Primary files you own:

- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_phase3_signing_backend.py`

Requirements to satisfy:

- add a realistic regression case close to the observed manual run:
  - roughly `262 pt x 21 pt`
  - small visible field set
  - image stamp present
  - `6 pt` text
  - should succeed
- keep truly tiny/absurd rectangles failing honestly
- preserve cryptographic signing, verification, PKCS#12 handling, and derived-field behavior

Expected deliverables:

- backend fit-policy correction for realistic compact rectangles
- regression tests for realistic compact success and truly-too-small failure

Definition of done:

- ordinary compact form-line rectangles no longer fail just because the policy is too aggressive

### Brief AR: Shared Fit Validation Alignment

You are aligning shell/harness validation with backend fit decisions so the UI does not say
 `Ready to sign` for requests the backend will reject.

Objectives:

- make preview validation, submit readiness, and backend acceptance agree on fit viability
- surface compact-rectangle failures honestly before the user presses sign

Primary files you own:

- `src/foliaseal/application/signing_draft_workflow.py`
- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_signing_draft_workflow.py`
- `tests/unit/test_qt_signing_shell.py`

Requirements to satisfy:

- the shell must not report `Ready to sign` when the backend fit policy would reject the request
- validation should use the same fit logic or a faithful shared predicate
- preserve the rest of the existing preview and signing behavior

Expected deliverables:

- aligned fit-validation behavior across preview and sign
- regression tests for the previous mismatch

Definition of done:

- shell readiness and backend acceptance agree for compact-rectangle fit decisions

### Brief AS: Compact Rectangle Review

You are doing a review-only pass on the compact rectangle compliance wave.

Review scope:

- `src/foliaseal/application/phase3_signing_backend.py`
- `src/foliaseal/application/signing_draft_workflow.py`
- `src/foliaseal/presentation/qt/signing_shell.py`
- affected tests under `tests/unit/`

Tasks:

- inspect whether the backend now complies with the text-first sizing contract for realistic
  compact rectangles
- inspect whether the shell validation and backend fit policy are aligned
- inspect for regressions in signing, verification, PKCS#12 handling, field derivation, and
  preview behavior
- explicitly decide whether another real manual harness run is worth doing

Definition of done:

- findings clearly state whether the realistic compact-rectangle case is ready for another manual
  run

## Corrective Wave: Blank Output, Optional Prefix, and Preview Parity

This wave addresses the latest real-run blockers:

- the signed PDF can succeed cryptographically while leaving the visible signature box blank
- the signer label prefix is behaving as if it were required, even though it should be optional
- compact `single_line` preview/output parity is still inconsistent
- backend reservation diagnostics are still returning `null` in runs where they should be useful

### Brief AT: Visible Signature Content Rendering Fix

You are fixing the backend so successful signed PDFs do not produce an empty visible signature box.

Objectives:

- ensure visible signature content is actually rendered when the request includes visible fields
- preserve cryptographic signing behavior
- keep image/no-image cases working

Primary files you own:

- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_phase3_signing_backend.py`

Requirements to satisfy:

- add a regression case for successful signing with visible fields and no image stamp
- add a regression case for successful signing with visible fields and an image stamp
- successful output must not leave the visible signature box blank
- preserve current failure behavior for truly too-small rectangles

Expected deliverables:

- backend rendering fix for blank visible signature output
- focused regression tests

Definition of done:

- a successful signing run no longer yields an empty visible signature box

### Brief AU: Optional Prefix and Compact Preview Parity

You are fixing the signing-shell/preview side so the signer label prefix is truly optional and
 compact `single_line` preview behavior matches the backend more closely.

Objectives:

- allow empty signer label prefix with no reserved blank line/space
- make compact `single_line` preview behavior reflect wrapped backend behavior more honestly
- keep visible-field semantics intact

Primary files you own:

- `src/foliaseal/application/signing_draft_workflow.py`
- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_signing_draft_workflow.py`
- `tests/unit/test_qt_signing_shell.py`

Requirements to satisfy:

- empty prefix must be allowed and should free space in preview/output behavior
- preview must stop implying a flat one-line `single_line` result when the backend will wrap it
- do not auto-drop user-selected visible fields

Expected deliverables:

- optional-prefix behavior aligned across preview and sign
- improved compact `single_line` preview parity
- focused regression tests

Definition of done:

- prefix can be omitted without leaving dead space, and compact preview behavior is more honest

### Brief AV: Reservation Snapshot Reliability

You are fixing the harness/backend diagnostics path so reservation snapshots are reliably available
 when a signing request is otherwise valid.

Objectives:

- stop `backend_reservation_snapshot` from silently becoming `null` in useful runs
- preserve diagnostic honesty

Primary files you own:

- `src/foliaseal/presentation/qt/phase3_harness.py`
- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_phase3_harness.py`

Requirements to satisfy:

- successful or near-successful signing runs should produce a useful reservation snapshot when the
  backend can compute one
- if a snapshot truly cannot be computed, that reason should be visible/debuggable rather than
  silently swallowed

Expected deliverables:

- more reliable reservation diagnostics
- focused regression tests

Definition of done:

- reservation snapshot data is no longer unexpectedly absent in normal debugging runs

### Brief AW: Blank Output Review

You are doing a review-only pass on this corrective wave.

Review scope:

- `src/foliaseal/application/phase3_signing_backend.py`
- `src/foliaseal/application/signing_draft_workflow.py`
- `src/foliaseal/presentation/qt/signing_shell.py`
- `src/foliaseal/presentation/qt/phase3_harness.py`
- affected tests under `tests/unit/`

Tasks:

- inspect whether successful signing now reliably renders visible content
- inspect whether empty prefix behavior is truly optional and space-free
- inspect whether compact `single_line` preview/output parity is materially improved
- inspect whether reservation snapshots are now reliable enough for debugging
- explicitly decide whether another real manual harness run is worth doing

Definition of done:

- findings clearly state whether the blank-output/prefix/parity blockers are resolved enough for
  another manual run

## Documentation Review Wave

The roadmap and requirement docs should stay aligned with the implementation strategy so workers do
 not follow stale or contradictory guidance.

### Brief AX: Documentation Alignment Review

You are reviewing the roadmap and requirement docs for stale scope boundaries, contradictory layout
 guidance, or wording that could push implementers toward the wrong behavior.

Review scope:

- `README.md`
- `Agents.md`
- `pdf_signing_app_feasibility.md`
- `phase3_parallel_plan.md`
- `artifacts/phase3_fr3b_acceptance_checklist.md`
- `artifacts/phase3_fr3b_acceptance_results.md`

Tasks:

- inspect for stale phase boundaries or phase names that no longer reflect the refactored roadmap
- inspect for wording that contradicts the current visible-fields, text-first sizing, or no-trimming
  contracts
- inspect for any remaining ambiguity that could cause workers to implement the wrong behavior
- inspect for mismatches between README guidance and the working plan

Definition of done:

- findings clearly state whether the docs could be confusing or misleading for future implementation

## Documentation Review Wave

The roadmap and requirement docs should stay aligned with the implementation strategy so workers do
 not follow stale or contradictory guidance.

### Brief AX: Documentation Alignment Review

You are reviewing the roadmap and requirement docs for stale scope boundaries, contradictory layout
 guidance, or wording that could push implementers toward the wrong behavior.

Review scope:

- `README.md`
- `Agents.md`
- `pdf_signing_app_feasibility.md`
- `phase3_parallel_plan.md`
- `artifacts/phase3_fr3b_acceptance_checklist.md`
- `artifacts/phase3_fr3b_acceptance_results.md`

Tasks:

- inspect for stale phase boundaries or phase names that no longer reflect the refactored roadmap
- inspect for wording that contradicts the current visible-fields, text-first sizing, or no-trimming
  contracts
- inspect for any remaining ambiguity that could cause workers to implement the wrong behavior
- inspect for mismatches between README guidance and the working plan

Definition of done:

- findings clearly state whether the docs could be confusing or misleading for future implementation

## Next Requirement: Rectangle-Aware Preview Parity

The next product requirement after the current backend appearance-parity fixes is to make the shell
 preview geometry-aware so it reflects the actual placed signature rectangle rather than a generic
 preview card.

Why this matters:

- users draw and resize a signature box with a specific width/height ratio
- the final PDF appearance has to adapt to that real rectangle
- a preview that does not reflect the same aspect ratio and layout constraints is only an
  approximation and can mislead the user about readability, wrapping, and image/text balance

Requirement statement:

- once a signature rectangle exists, the visible signature preview must adapt to that rectangle's
  effective aspect ratio and layout constraints
- the preview and backend should follow the same layout policy for:
  - margins
  - image/text composition
  - font sizing rules
  - wrapping rules
  - overflow/fallback behavior
- the preview should make it obvious when a chosen rectangle is too small or awkward for the
  selected content/layout instead of silently implying a cleaner result than the backend can produce

Acceptance intent:

- drawing or resizing the rectangle should materially change the preview shape and composition
- preview/output parity should improve for wide, tall, and compact rectangles
- the user should be able to trust the preview as a meaningful approximation of the final visible
  signature

## Visible Appearance Sizing Contract

The visible signature layout should follow an explicit text-first sizing contract rather than a
 generic “scale everything until it fits” rule.

Contract:

- text size is specified in typographic points and should be honored in the final visible signature
  output
- the backend should reserve space for the selected text at that font size before sizing the image
  stamp
- the image stamp should preserve aspect ratio and scale to the largest size that fits inside the
  remaining permitted stamp region
- the system should not silently shrink text into unreadable output just to make the signature fit
- when an image stamp is present, the stamp may shrink aggressively before the system refuses the
  layout, provided the preview makes the resulting balance clear to the user

Overflow behavior:

- if the chosen rectangle is too small to honor the selected text size and requested content/layout,
  the app should surface that honestly through validation, warning, or another explicit degraded
  policy
- “microscopic but technically present” text is not acceptable output
- a very small image stamp can still be acceptable if the text remains honest and the preview makes
  that tradeoff obvious before signing

Preview implication:

- the preview should ultimately reflect this same text-first sizing rule so users can trust that
  the stamp fills remaining space after the text has been laid out at the requested size
- because the preview is the user’s contract, the system can allow more aggressive stamp shrinkage
  than it otherwise might, as long as the preview clearly shows the real result the user is asking
  for

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
