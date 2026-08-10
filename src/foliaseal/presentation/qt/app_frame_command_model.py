"""Typed top-level command definitions for the Qt application frame."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AppFrameCommandId(StrEnum):
    """Stable identifiers for commands owned by the application frame."""

    OPEN = "file.open"
    SAVE = "file.save"
    SAVE_AS = "file.save_as"
    CLOSE = "file.close"
    EXIT = "file.exit"
    PREVIOUS_PAGE = "view.previous_page"
    NEXT_PAGE = "view.next_page"


@dataclass(frozen=True)
class AppFrameCommandDefinition:
    """Presentation metadata shared by a frame command and its Qt action."""

    command_id: AppFrameCommandId
    menu: str
    text: str
    shortcut: str | None
    accessible_name: str
    mnemonic_text: str


FILE_COMMAND_DEFINITIONS: tuple[AppFrameCommandDefinition, ...] = (
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.OPEN,
        menu="File",
        text="Open",
        shortcut="Ctrl+O",
        accessible_name="Open PDF",
        mnemonic_text="&Open",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.SAVE,
        menu="File",
        text="Save",
        shortcut="Ctrl+S",
        accessible_name="Sign and save PDF",
        mnemonic_text="&Save",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.SAVE_AS,
        menu="File",
        text="Save As",
        shortcut="Ctrl+Shift+S",
        accessible_name="Save signed PDF as",
        mnemonic_text="Save &As",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.CLOSE,
        menu="File",
        text="Close",
        shortcut="Ctrl+W",
        accessible_name="Close PDF",
        mnemonic_text="&Close",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.EXIT,
        menu="File",
        text="Exit",
        shortcut="Ctrl+Q",
        accessible_name="Exit FoliaSeal",
        mnemonic_text="E&xit",
    ),
)


VIEW_COMMAND_DEFINITIONS: tuple[AppFrameCommandDefinition, ...] = (
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.PREVIOUS_PAGE,
        menu="View",
        text="Previous Page",
        shortcut="Page Up",
        accessible_name="Go to previous PDF page",
        mnemonic_text="Previous &Page",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.NEXT_PAGE,
        menu="View",
        text="Next Page",
        shortcut="Page Down",
        accessible_name="Go to next PDF page",
        mnemonic_text="Next P&age",
    ),
)


ALL_COMMAND_DEFINITIONS: tuple[AppFrameCommandDefinition, ...] = (
    *FILE_COMMAND_DEFINITIONS,
    *VIEW_COMMAND_DEFINITIONS,
)


def command_definition(command_id: AppFrameCommandId) -> AppFrameCommandDefinition:
    """Return one definition from the single frame command registry."""

    for definition in ALL_COMMAND_DEFINITIONS:
        if definition.command_id is command_id:
            return definition
    raise KeyError(command_id)
