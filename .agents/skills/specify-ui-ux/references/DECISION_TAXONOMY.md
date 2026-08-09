# UI/UX Decision Taxonomy

Use this reference when deciding where a UI decision belongs and how strongly it should be governed.

## 1. Experience invariant

An experience invariant describes a user-visible property that should survive platform and toolkit changes.

Examples:

- The document remains the dominant workspace while reviewing.
- Signing never occurs merely because a preset was selected.
- Cancelling an edit does not destroy the previously committed value.
- Error feedback identifies a next action when recovery is possible.
- Essential placement can be adjusted without fine pointer control.

**Put in:** normative sections of `UI_SPEC.md`.

**Do not encode as:** a specific widget, exact pixel size, or framework class unless that mechanism is itself part of the product contract.

## 2. Application design choice

An application design choice is intentionally specific to this product, but is not inherently tied to a platform API.

Examples:

- Certificate setup lives in a secondary management surface rather than the primary workflow.
- The application uses one document at a time.
- Completed setup collapses to a summary while preserving an explicit edit action.
- Search and selection are review tools rather than signing controls.

**Put in:** `UI_SPEC.md` with a stable requirement ID when implementation or tests need to cite it.

## 3. Platform convention

A platform convention is behavior the application should inherit from the operating system, browser, device class, or established platform HIG.

Examples:

- standard Open/Save interactions
- standard dialog button order
- conventional menu placement
- system focus behavior
- standard keyboard shortcuts
- system text scaling and high-contrast behavior

**Put in:** `UI_SPEC.md` Platform Realization, usually as “follow platform convention.”

Promote a platform convention to an invariant only when the product intentionally requires the same behavior everywhere.

## 4. Toolkit realization

A toolkit realization is a concrete implementation mechanism.

Examples:

- `QSplitter`
- `NavigationView`
- `GtkPaned`
- CSS grid columns
- SwiftUI `NavigationSplitView`
- exact signal/event wiring

**Put in:** architecture documentation, implementation plans, or code.

**Normally do not freeze in `UI_SPEC.md`.** A realization note may name a likely/native pattern when it clarifies feasibility, but it should not masquerade as a cross-platform requirement.

## 5. Cosmetic implementation detail

These details are usually too low-level for a frozen UI contract unless brand, accessibility, measurement fidelity, or a special interaction makes them important.

Examples:

- 8 px versus 10 px gap
- exact corner radius
- exact shadow blur
- internal object names
- one toolkit’s default control height

Prefer platform/system defaults and keep these out of the canonical spec.

## Classification test

Ask these questions in order:

1. **If the app were reimplemented on a different platform, would changing this alter the intended user experience?**
   - Yes: likely an invariant or application design choice.
2. **Would a competent implementation naturally choose a different answer because the platform convention differs?**
   - Yes: likely a platform convention.
3. **Does the statement name a framework class, event, layout primitive, or pixel mechanism rather than user-visible behavior?**
   - Yes: likely toolkit realization.
4. **Would two implementations that differ on this point still be obviously the same approved interface to a user?**
   - Yes: probably too low-level to freeze.

## Strength of language

Use **Must/Must not** for requirements that define conformance.
Use **Should** when deviation may be legitimate but must be justified.
Use **May** for explicitly permitted alternatives.
Use **Preference** in interview notes for user taste that has not become a requirement.
Use **Open question** when the branch is unresolved.

Do not silently upgrade preferences or current implementation facts into requirements.
