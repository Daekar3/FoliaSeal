# Platform Realization Guidance

The purpose of platform realization is to map approved experience requirements onto the conventions of each supported target without allowing incidental platform mechanics to redefine the product.

## Source precedence for platform research

Prefer current authoritative sources in this order:

1. operating-system or platform Human Interface Guidelines
2. official toolkit/framework design and accessibility documentation
3. applicable accessibility standards
4. established conventions for the application category
5. high-quality third-party guidance only when primary sources do not answer the question

Verify that guidance is current for the versions the project actually supports.

## What belongs in platform realization

Typical topics:

- application/window model
- menu and command placement
- standard keyboard shortcuts and access keys
- dialogs, sheets, alerts, and confirmation behavior
- file pickers and save/open conventions
- focus, keyboard navigation, and default/cancel actions
- pointer, touch, pen, gamepad, remote, or other target input methods
- text scaling, display scaling, high contrast, reduced motion, and system themes
- assistive-technology semantics and accessibility APIs
- native navigation patterns
- title bar/window chrome behavior
- platform-standard destructive action treatment

## What should remain invariant

Do not weaken a product requirement merely because platforms implement it differently.

Example invariant:

> The primary content remains dominant while contextual configuration stays readily reachable.

Possible realizations:

- desktop: resizable inspector/side pane
- tablet: adaptive side sheet or split view
- phone: secondary route/sheet with state-preserving return
- web: responsive side panel that moves below or behind an explicit control at narrow widths

The realization changes; the hierarchy and reachability requirement does not.

## Native-by-default rule

When `UI_SPEC.md` does not intentionally define a custom behavior, follow the platform convention.

Prefer statements such as:

- “Use the platform-standard Open command and file chooser.”
- “Order dialog actions according to the active platform convention.”
- “Use the platform’s conventional shortcut for Save As.”

Avoid freezing one platform’s answer as a universal requirement unless the user explicitly wants cross-platform uniformity.

## Deviation rule

A deliberate platform deviation should record:

- the governing requirement ID
- the native convention
- the proposed deviation
- why the native convention fails the product need
- user-visible cost of the deviation
- accessibility implications

Do not deviate merely to make multiple platforms look mechanically identical.

## Accessibility baseline

The skill should always consider broad accessibility principles even when the exact compliance standard differs by target:

- essential functionality available without a pointer-only path
- visible and logical focus
- semantic names/roles/states for assistive technology where supported
- no meaning conveyed by color alone
- usable text/display scaling
- alternatives to drag-only interaction
- controls/targets suitable for the target input device
- clear error identification and recovery

Where a platform or applicable standard provides numeric thresholds or more specific rules, record those in the relevant platform-realization subsection rather than treating one platform’s numbers as universal.

## Useful authoritative starting points

These are starting points, not frozen dependencies; verify current URLs/guidance when the skill runs.

- W3C Web Accessibility Initiative / WCAG: https://www.w3.org/WAI/standards-guidelines/wcag/
- Microsoft Windows app design guidance: https://learn.microsoft.com/windows/apps/design/
- Apple Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines/
- GNOME Human Interface Guidelines: https://developer.gnome.org/hig/
- KDE Human Interface Guidelines: https://develop.kde.org/hig/

Use the relevant platform’s primary documentation instead of attempting to synthesize a universal faux-platform convention.
