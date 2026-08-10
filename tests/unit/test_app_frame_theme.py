from foliaseal.infra.config.app_settings_ui import AppearanceMode
from foliaseal.presentation.qt.app_frame_theme import apply_appearance_mode


class _FakeColor:
    def __init__(self, value):
        self.value = value


class _FakePalette:
    Window = "window"
    WindowText = "window_text"
    Base = "base"
    Text = "text"
    Button = "button"
    ButtonText = "button_text"
    Highlight = "highlight"
    HighlightedText = "highlighted_text"

    def __init__(self, existing=None):
        self.colors = dict(getattr(existing, "colors", {}))

    def setColor(self, role, color):  # noqa: N802
        self.colors[role] = color.value


class _FakeStyle:
    def __init__(self):
        self.standard_palette = object()

    def standardPalette(self):  # noqa: N802
        return self.standard_palette


class _FakeApplication:
    def __init__(self):
        self.current_palette = _FakePalette()
        self._style = _FakeStyle()

    def style(self):
        return self._style

    def setPalette(self, palette):  # noqa: N802
        self.current_palette = palette

    def palette(self):
        return self.current_palette


class _FakeApplicationType:
    application = _FakeApplication()

    @classmethod
    def instance(cls):
        return cls.application


def test_dark_mode_applies_only_the_declared_ui_palette_roles() -> None:
    apply_appearance_mode(
        mode=AppearanceMode.DARK,
        q_application=_FakeApplicationType,
        q_palette=_FakePalette,
        q_color=_FakeColor,
    )

    assert _FakeApplicationType.application.current_palette.colors == {
        "window": "#202124",
        "window_text": "#f1f3f4",
        "base": "#292a2d",
        "text": "#f1f3f4",
        "button": "#303134",
        "button_text": "#f1f3f4",
    }


def test_system_mode_restores_the_platform_standard_palette() -> None:
    application = _FakeApplicationType.application
    apply_appearance_mode(
        mode=AppearanceMode.SYSTEM,
        q_application=_FakeApplicationType,
    )

    assert application.current_palette is application._style.standard_palette
