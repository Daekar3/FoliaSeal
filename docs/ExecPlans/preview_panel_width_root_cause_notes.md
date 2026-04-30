# Preview Width And Properties Pane Width Root-Cause Notes

Date: 2026-04-01
Scope: trace only the two persistent UI behaviors

1. The preview never uses more than roughly half the available width in the settings pane.
2. Drawing a rectangle can make the settings pane widen and show a horizontal scrollbar.

This file records the code path, the relevant values, and the direct evidence gathered from real Qt in offscreen mode.

## Files examined

- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_qt_signing_shell.py`

## High-confidence root causes

### Behavior 1: preview width is self-limited by its own fixed width

The preview width is controlled by this chain:

1. `SignaturePropertiesPanel.load_from_workflow()`
2. `SignaturePropertiesPanel.refresh_preview()`
3. `SignaturePropertiesPanel._update_preview_controls(preview)`
4. `_preview_available_width(preview, container=self._preview_controls.container)`
5. `_preview_body_size(preview, available_width_px=...)`
6. `_set_widget_width_limit(...)` and `setFixedSize(...)` calls back onto the preview widgets

The important constants are:

- `_PREVIEW_MAX_WIDTH_PX = 520`
- `_PREVIEW_MAX_HEIGHT_PX = 180`
- `_PREVIEW_DEFAULT_WIDTH_PX = 320`
- `_PREVIEW_DEFAULT_HEIGHT_PX = 120`
- `_PREVIEW_HORIZONTAL_PADDING_PX = 24`

### Exact code path

In `signing_shell.py`:

#### `_preview_available_width`

```python
def _preview_available_width(preview, container=None):
    container_width = _widget_width(container) if container is not None else None
    if isinstance(container_width, int) and container_width > 0:
        return max(_PREVIEW_DEFAULT_WIDTH_PX, container_width - _PREVIEW_HORIZONTAL_PADDING_PX)
    if preview.signature_rect is None:
        return _PREVIEW_DEFAULT_WIDTH_PX
    return _PREVIEW_MAX_WIDTH_PX
```

What this means:

- once `self._preview_controls.container` has a width, future preview passes read that width back
- if the container width is `320`, the computed available width becomes `max(320, 320 - 24) == 320`
- so after the first fixed-width pass, the preview tends to stay pinned around `320px`

#### `_preview_body_size`

```python
scale = min(max_width_px / width_pt, _PREVIEW_MAX_HEIGHT_PX / height_pt)
width = round(width_pt * scale)
height = round(height_pt * scale)
```

This means the preview width is constrained by both:

- the available width
- the hard height cap of `180px`

For a wide, shallow rectangle, height is not the limiter, so width tends to stop at `320px` because `available_width_px` has already been pinned there.

For a tall rectangle, the height cap can shrink the width even further.

#### `_update_preview_controls`

This function then writes that computed width back into the widget tree:

```python
self._preview_controls.card_container.setFixedWidth(body_width)
self._preview_controls.single_body_container.setFixedSize(body_width, body_height)
self._preview_controls.multi_body_container.setFixedSize(body_width, body_height)

for widget in (
    self._preview_controls.container,
    self._preview_controls.title_label,
    self._preview_controls.detail_label,
    self._preview_controls.footer_label,
):
    _set_widget_width_limit(widget, body_width)
```

Important consequence:

- the outer preview group container itself is width-limited to `body_width`
- on the next refresh, `_preview_available_width()` reads that limited width back from the same container
- this creates a feedback loop where the preview constrains itself

### Real Qt evidence

Using `QT_QPA_PLATFORM=offscreen` and a real `QApplication`, with the main workspace resized to `1400x900`:

Initial state:

- scroll area width: `550`
- properties panel width: `534`
- preview group width: `320`
- preview group min/max width: `320 / 320`
- card width: `320`

After selecting a wide, shallow rectangle:

- preview group width stayed `320`
- even though the panel still had `534px` of width available

So the preview is not merely "choosing" to stay small; it is explicitly fixed to that width by code.

### Why it looks like "half the pane"

With panel width about `534px` and preview width fixed at `320px`, the preview only uses about `60%` of the panel width. In other window sizes it will look closer to half.

## Behavior 2: pane widening / horizontal scrollbar

### Main root cause found

The most direct width explosion is the validation label.

In the panel constructor:

```python
self._validation_label = bindings.q_label("")
```

Later in `refresh_preview()`:

```python
self._validation_label.setText(self._format_validation_text(preview))
```

But unlike the preview labels, the validation label is never width-limited.

In the current shell code path, it also is not configured here with `setWordWrap(True)`, so the label is free to report a very large single-line width via `sizeHint()`.

### Real Qt evidence

With the workspace at `1400x900`:

Before long error text:

- properties panel `sizeHint().width() = 525`
- validation label `sizeHint().width() = 238`
- horizontal scrollbar invisible

After manually setting the validation label to:

`ERROR visible_signature_layout_unavailable: Visible signature content does not fit inside the selected rectangle for the single_line template. Enlarge the signature box or choose a more compact appearance.`

the numbers changed to:

- properties panel `sizeHint().width() = 1173`
- validation label `sizeHint().width() = 1157`
- scroll area width still `550`
- horizontal scrollbar maximum became `639`
- horizontal scrollbar became visible

This is a direct reproduction of the pane-widening behavior from code, without any guessing.

### Why drawing a rectangle triggers it

Drawing a rectangle calls:

1. `SigningWorkspaceWidget._handle_viewer_selection(...)`
2. `SignaturePropertiesPanel.set_signature_rect(...)`
3. `SignaturePropertiesPanel.refresh_preview()`
4. `_format_validation_text(preview)`
5. `self._validation_label.setText(...)`

If the new placement causes a long validation error, the validation label asks for a huge width, which inflates the entire panel size hint and causes the horizontal scrollbar.

This is why the scrollbar can appear "as soon as" a rectangle is drawn.

## Other contributors to panel width

Even before the validation label expands, the properties panel already has a fairly large width demand.

Measured `sizeHint()` values in real Qt at `1000x700`:

- properties panel overall: `525`
- `Appearance` group: `509`
- `Preview` group: `346`
- each field row: `332`

Within the `Appearance` group:

- `Text and layout` sub-group: `450`
- `Box and stamp` sub-group: `503`

Within the `Box and stamp` group, the `"Border / Background"` row's composed widget had a `sizeHint()` of about `375`, which materially contributes to the panel's baseline width.

So there are two distinct width problems:

1. baseline panel width is already fairly large because several rows are wide
2. the validation label can suddenly push it far wider

The second one is the direct explanation for the sudden widening after placement.

## What changes these values

### Preview width-affecting values

- `preview.signature_rect.width_pt`
- `preview.signature_rect.height_pt`
- `_PREVIEW_MAX_WIDTH_PX`
- `_PREVIEW_MAX_HEIGHT_PX`
- `_PREVIEW_DEFAULT_WIDTH_PX`
- `_PREVIEW_HORIZONTAL_PADDING_PX`
- the current width already assigned to `self._preview_controls.container`

### Pane-width-affecting values

- every child widget's `sizeHint()`
- especially:
  - `Appearance` group row composition
  - field row label minimum width of `132`
  - preview group fixed width
  - validation label text length

## Most likely minimal fixes

These are not applied yet in this note; they are the smallest likely fixes implied by the trace.

### Fix for behavior 1

- stop using `self._preview_controls.container` as both:
  - the source of "available width"
  - and the target of a fixed width limit
- compute available width from the actual parent/scroll viewport instead
- do not call `_set_widget_width_limit()` on the outer preview group container
- let the preview card scale to the actual available width, still subject to a chosen max if desired

### Fix for behavior 2

- width-limit the validation label to the available panel width
- and/or enable wrapping on the label inside a width-constrained container
- and/or set an explicit size policy that prevents `sizeHint()` from expanding to the full single-line message width

Without that, any long validation message can continue to blow out the panel width.
