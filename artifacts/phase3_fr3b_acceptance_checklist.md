# Phase 3 FR-3B Acceptance Checklist and Task Worksheet

Date: 2026-03-28  
Owner: FoliaSeal engineering

Source requirements:

- `FR-3B` in `pdf_signing_app_feasibility.md`
- Phase 3 milestone in `phase3_parallel_plan.md`

Purpose:

- Use this worksheet during manual acceptance and parity testing once the Phase 3 UI and preview work lands.
- Capture task-level pass/fail results, notes, and any observed parity gaps against Acrobat or PDF-XChange style workflows.
- Keep this file as a planning and QA artifact only.

Current status note:

- Phase 3 is not yet accepted.
- Overlay interaction quality during placement and resize is no longer the primary blocker.
- Named appearance profile save/select behavior is now implemented in the shell, including:
  - saving the current appearance under a user-provided name
  - confirming overwrite when a name already exists
  - selecting a saved profile from a dropdown
- The concrete signing backend now produces a genuinely cryptographically signed PDF.
- The current open workflow gaps are TSA-backed timestamping, timestamp-required flows, and the
  final end-to-end acceptance pass against representative signed output.
- Some worksheet items below are therefore not yet testable in the current build and should be
  marked as such rather than treated as failures.

## Overlay remediation gate

Complete this section first. If the overlay gate fails, stop the acceptance run and record notes before moving on to broader FR-3B tasks.

- [ ] Resize handles no longer snap or jump unexpectedly during drag.
- [ ] Placement remains visually stable while the overlay is being resized.
- [ ] No placement exception is raised during overlay resize or reposition.
- [ ] Overlay state remains synchronized with the viewer after repeated drags.
- [ ] Zoom or pan does not cause obvious overlay drift during placement or resize.

Gate result:

- [ ] Overlay gate passed
- [ ] Overlay gate failed

Overlay notes:

- Record which handle or drag path was used.
- Record whether the failure was visual drift, snapping, inversion, exception, or stale synchronization.
- If this gate fails, the rest of the worksheet should be treated as informational only.

## Session setup

- [ ] Launch the Phase 3 desktop build in an environment with the relevant PDF signing UI enabled.
- [ ] Open a representative PDF that includes at least one page suitable for signature placement.
- [ ] Confirm the signature properties flow is reachable from the main signing UI.
- [ ] Confirm the viewer preview renders before any signing action is attempted.
- [ ] Confirm the selected PDF can be used without unexpected dependency or backend errors.

Notes:

- Document the PDF used for testing, including page count and any notable page rotation or crop behavior.
- Document any environment-specific limitations that affect appearance preview or overlay placement behavior.

## FR-3B Acceptance Tasks

### 1. Create a new appearance

Goal:

- Verify that a user can start from and edit the current visible signature appearance draft in the
  focused properties flow.

Checks:

- [x] The current appearance draft can be edited without leaving the signing flow.
- [ ] The focused properties panel shows the available appearance controls.
- [ ] The appearance preview updates when the user changes appearance settings.
- [ ] The created appearance can be applied to the current signature draft.

Pass/Fail:

- [ ] Pass
- [ ] Fail

Notes:

- Record which controls were changed and whether the preview updated immediately.
- Record any controls that were missing, mislabeled, or required a fallback path.
- Saved appearance profiles are covered separately below; use the named-profile section for
  save/select/overwrite behavior.

### 2. Include or exclude identity fields

Goal:

- Verify that the user can include or exclude identity-related fields such as DN, common name, email, title, and company.

Checks:

- [ ] DN can be shown or hidden as intended.
- [ ] Common name can be shown or hidden as intended.
- [ ] Email can be shown or hidden as intended.
- [ ] Title can be shown or hidden as intended.
- [ ] Company can be shown or hidden as intended.
- [ ] The preview reflects the field visibility changes.
- [ ] The final sign action preserves the chosen visibility settings.

Pass/Fail:

- [ ] Pass
- [ ] Fail

Notes:

- Record which fields were included and which were excluded.
- Record any mismatches between preview text and final signed appearance.

### 3. Place signature on page

Goal:

- Verify that a user can place the signature rectangle on the target page using the Phase 3 placement workflow.

Checks:

- [ ] The user can choose the target page before placement.
- [ ] The user can draw a signature rectangle on the preview.
- [ ] The rectangle preview appears while dragging.
- [ ] The resulting placement lands on the expected page area.
- [ ] The placement respects zoom and pan state.
- [ ] The overlay does not drift, snap, or jump during the placement interaction.

Pass/Fail:

- [ ] Pass
- [ ] Fail

Notes:

- Record the page number and approximate location of the placed rectangle.
- Record any coordinate drift, clipping, snapping, jumping, or selection ambiguity.

### 4. Resize or fine-tune signature placement

Goal:

- Verify that a placed signature rectangle can be resized or adjusted with numeric fine-tuning where supported in the Phase 3 scope.

Checks:

- [ ] The placed rectangle can be resized or repositioned in the workflow.
- [ ] Numeric x/y/width/height fine-tuning is available when expected.
- [ ] Fine-tuned values are reflected in the preview.
- [ ] Fine-tuned values remain valid after the user changes other appearance settings.
- [ ] Resize handle dragging feels predictable enough for end users.
- [ ] No resize step causes the rectangle to invert or jump unexpectedly.
- [ ] No exception appears during resize or fine-tuning.

Pass/Fail:

- [ ] Pass
- [ ] Fail

Notes:

- Record the before/after rectangle values.
- Record any mismatch between the on-screen rectangle and the saved placement values.
- Record which resize path was used and whether the issue was interaction quality or data mismatch.

### 5. Confirm and sign from the focused properties flow

Goal:

- Verify that the user can complete the signing action from the focused properties workflow and inspect the produced signed PDF from the current backend path.

Checks:

- [ ] The sign action is available from the properties flow.
- [ ] The app shows the expected confirmation or summary before signing, if applicable.
- [ ] The signing action completes successfully for a valid non-timestamp-required request using the current backend path.
- [ ] The signed output is produced at the expected location.
- [ ] The signed output can be opened and inspected after signing.
- [ ] The produced signed PDF matches the intended preview and settings closely enough for acceptance.
- [ ] The worksheet distinguishes true cryptographic signing from still-missing TSA-backed timestamping.
- [ ] The UI reports success or failure clearly after the sign action.
- [ ] The run record captures the output file path and any backend failure code if signing fails.
- [ ] If timestamp-required signing is attempted without TSA support, the failure is reported clearly.

Pass/Fail:

- [ ] Pass
- [ ] Fail

Notes:

- Record any signing validation warnings shown to the user.
- Record the output file path, whether the output can be opened, and any preview-vs-output
  differences.
- Record any backend failure code, exception message, or signed-output mismatch if signing fails.
- Record whether timestamping was intentionally disabled, unavailable, or explicitly rejected.

### 6. Reuse prior configuration shape in-session

Goal:

- Verify that a user can reuse the current appearance shape or in-session configuration without
  rebuilding the entire appearance from scratch, if the current build exposes such a workflow.

Checks:

- [ ] The current appearance configuration can be reused for another signature draft in the same session.
- [ ] Reused settings preserve the prior visible field choices.
- [ ] Reused settings preserve layout and style choices.
- [ ] Reused settings do not unexpectedly reset rectangle placement defaults unless intentionally changed.

Pass/Fail:

- [ ] Pass
- [ ] Fail

Notes:

- Record what was reused and whether it matched the earlier configuration shape.
- Record whether reuse was explicit, automatic, or via a preset-like in-session action.
- If the current build does not yet expose a reusable profile flow, mark this section as not yet
  testable and note the limitation explicitly.

### 7. Save and select a named appearance profile

Goal:

- Verify that a user can save, relaunch, reselect, and delete named appearance profiles from the shell.

Checks:

- [ ] The current appearance can be saved under a user-provided name.
- [ ] Saving with an existing name prompts for explicit overwrite confirmation.
- [ ] Saved profiles appear in a dropdown list.
- [ ] Selecting a profile from the dropdown restores its appearance settings.
- [ ] Selecting a profile from the dropdown restores its placement defaults when intended.
- [ ] Saved profiles are still available after relaunch.
- [ ] Persisted profiles live in a clearly labeled `Signature Profiles` directory.
- [ ] Persisted profiles are stored in a human-readable JSON or similarly inspectable text format.
- [ ] The UI offers a delete-current-profile action.
- [ ] Deleting a profile prompts for explicit confirmation.
- [ ] Canceling delete leaves the profile intact.
- [ ] Deleted profiles no longer appear in the dropdown after confirmation.
- [ ] Deleted profiles remain absent after relaunch.

Pass/Fail:

- [ ] Pass
- [ ] Fail

Notes:

- Record whether the profile name was user-entered, overwritten, or selected from the list.
- Record where persisted profiles are stored on disk and whether the location is understandable to
  a user inspecting the filesystem.
- Record whether deletion removed only the intended profile, whether cancel preserved it, and
  whether the confirmation copy was clear.

## Parity observations

Use this section to capture comparison notes against Acrobat or PDF-XChange style behavior.

- [ ] Overlay placement and resize behavior is now stable enough to compare fairly with Acrobat or PDF-XChange.
- [ ] Interaction pattern feels comparable for the representative task set.
- [ ] Layout and properties workflow are understandable without fallback dialogs.
- [ ] Preview behavior matches the signed output closely enough for acceptance.
- [ ] Error messages are actionable and appear near the relevant control or flow step.

Notes:

- Record any major UX differences.
- Record any design decisions that are intentionally different from Acrobat or PDF-XChange.

## Issues and follow-ups

- [ ] No blocking issues observed.
- [ ] Non-blocking follow-up items captured below.

Follow-up notes:

- Use this area for bugs, UI refinements, parity deltas, or test data gaps.
- Include file paths, screenshots, or reproduction notes if helpful.

## Acceptance summary

Overall result:

- [ ] Accepted
- [ ] Accepted with follow-up
- [ ] Not accepted

Summary notes:

- Record the final judgment for FR-3B acceptance.
- Include any constraints that should be carried into the smaller post-Phase-3 roadmap slices or future parity testing.
- If the overlay gate failed, call that out explicitly as the reason Phase 3 remains blocked.
- If TSA-backed timestamping or timestamp-required flows remain unsupported in the current build,
  call that out explicitly as the reason timestamp-oriented acceptance is not yet complete.
