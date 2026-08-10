"""Small modeless, keyboard-accessible product support dialogs."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from foliaseal.application.support_diagnostics import SupportLocations
from foliaseal.presentation.qt.app_frame_command_model import ALL_COMMAND_DEFINITIONS


class SupportDialog:
    """Common implementation for local support text surfaces."""

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        title: str,
        text: str,
        object_name: str,
        on_closed: Callable[[], None] | None = None,
    ) -> None:
        self._on_closed = on_closed
        self.dialog = bindings.q_dialog(parent)
        self.dialog.setObjectName(object_name)
        self.dialog.setWindowTitle(title)
        set_modal = getattr(self.dialog, "setModal", None)
        if callable(set_modal):
            set_modal(False)
        layout = bindings.q_vbox_layout(self.dialog)
        editor_type = bindings.q_text_browser or bindings.q_text_edit
        self.content = editor_type(self.dialog)
        if hasattr(self.content, "setReadOnly"):
            self.content.setReadOnly(True)
        self.content.setAccessibleName(f"{title} content")
        if hasattr(self.content, "setPlainText"):
            self.content.setPlainText(text)
        else:
            self.content.setMarkdown(text)
        layout.addWidget(self.content)
        self.close_button = bindings.q_push_button("Close", self.dialog)
        self.close_button.setObjectName(f"{object_name}_close")
        self.close_button.setAccessibleName(f"Close {title}")
        layout.addWidget(self.close_button)
        self.close_button.clicked.connect(self.dialog.close)
        finished = getattr(self.dialog, "finished", None)
        if finished is not None and hasattr(finished, "connect"):
            finished.connect(self._closed)

    def show(self) -> None:
        self.dialog.show()
        raise_window = getattr(self.dialog, "raise_", None)
        if callable(raise_window):
            raise_window()
        activate = getattr(self.dialog, "activateWindow", None)
        if callable(activate):
            activate()
        self.close_button.setFocus()

    def close(self) -> None:
        self.dialog.close()

    def _closed(self, *_args: Any) -> None:
        if self._on_closed is not None:
            self._on_closed()


def shortcut_text() -> str:
    lines = ["FoliaSeal keyboard shortcuts", ""]
    for definition in ALL_COMMAND_DEFINITIONS:
        if definition.shortcut:
            lines.append(f"{definition.text}: {definition.shortcut}")
    return "\n".join(lines)


class KeyboardShortcutsDialog(SupportDialog):
    def __init__(
        self, *, bindings: Any, parent: Any, on_closed: Callable[[], None] | None = None
    ) -> None:
        super().__init__(
            bindings=bindings,
            parent=parent,
            title="Keyboard Shortcuts",
            text=shortcut_text(),
            object_name="keyboard_shortcuts_dialog",
            on_closed=on_closed,
        )


class DataLocationsDialog(SupportDialog):
    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        locations: SupportLocations | None = None,
        on_closed: Callable[[], None] | None = None,
    ) -> None:
        paths = locations or SupportLocations.for_environment()
        text = (
            f"Configuration: {paths.config_dir}\n"
            f"Managed data: {paths.data_dir}\n"
            f"Diagnostic logs: {paths.logs_dir}"
        )
        super().__init__(
            bindings=bindings,
            parent=parent,
            title="Data Locations",
            text=text,
            object_name="data_locations_dialog",
            on_closed=on_closed,
        )


class AboutDialog(SupportDialog):
    def __init__(
        self, *, bindings: Any, parent: Any, on_closed: Callable[[], None] | None = None
    ) -> None:
        super().__init__(
            bindings=bindings,
            parent=parent,
            title="About FoliaSeal",
            text="FoliaSeal\nDevelopment checkout",
            object_name="about_dialog",
            on_closed=on_closed,
        )
