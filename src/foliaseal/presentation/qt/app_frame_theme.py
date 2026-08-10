"""Qt application-chrome theme application kept outside the frame composition root."""

from __future__ import annotations

from typing import Any

from foliaseal.infra.config.app_settings_ui import AppearanceMode


def apply_appearance_mode(
    *,
    mode: AppearanceMode,
    q_application: Any,
    q_palette: Any | None = None,
    q_color: Any | None = None,
) -> None:
    """Apply an application palette without touching rendered document content."""

    instance_factory = getattr(q_application, "instance", None)
    application = instance_factory() if callable(instance_factory) else None
    if application is None:
        return
    if mode is AppearanceMode.SYSTEM:
        style = getattr(application, "style", None)
        standard_palette = getattr(style(), "standardPalette", None) if callable(style) else None
        set_palette = getattr(application, "setPalette", None)
        if callable(standard_palette) and callable(set_palette):
            set_palette(standard_palette())
        return
    if q_palette is None or q_color is None:
        return
    current_palette = getattr(application, "palette", None)
    current_palette = current_palette() if callable(current_palette) else None
    palette = q_palette(current_palette) if current_palette is not None else q_palette()
    color = q_color
    if mode is AppearanceMode.DARK:
        values = {
            "Window": "#202124",
            "WindowText": "#f1f3f4",
            "Base": "#292a2d",
            "Text": "#f1f3f4",
            "Button": "#303134",
            "ButtonText": "#f1f3f4",
        }
    else:
        values = {
            "Window": "#f7f7f8",
            "WindowText": "#202124",
            "Base": "#ffffff",
            "Text": "#202124",
            "Button": "#f0f0f1",
            "ButtonText": "#202124",
        }
    for role_name, value in values.items():
        role = getattr(q_palette, role_name, None)
        set_color = getattr(palette, "setColor", None)
        if role is not None and callable(set_color):
            set_color(role, color(value))
    set_palette = getattr(application, "setPalette", None)
    if callable(set_palette):
        set_palette(palette)
