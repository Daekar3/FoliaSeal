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
    COPY = "edit.copy"
    PREVIOUS_PAGE = "view.previous_page"
    NEXT_PAGE = "view.next_page"
    SELECT_TEXT = "view.select_text"
    FIT_PAGE = "view.fit_page"
    FIT_WIDTH = "view.fit_width"
    FIND = "view.find"
    DOCUMENT_SIGNATURES = "view.document_signatures"
    APPLICATION_SETTINGS = "settings.application"
    MANAGE_REUSABLE_OBJECTS = "settings.manage_reusable_objects"
    CREATE_CERTIFICATE = "settings.create_certificate"
    IMPORT_CERTIFICATE = "settings.import_certificate"
    MANAGE_CERTIFICATE_CONFIGURATIONS = "settings.manage_certificate_configurations"


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


EDIT_COMMAND_DEFINITIONS: tuple[AppFrameCommandDefinition, ...] = (
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.COPY,
        menu="Edit",
        text="Copy",
        shortcut="Ctrl+C",
        accessible_name="Copy selected document text",
        mnemonic_text="&Copy",
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
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.SELECT_TEXT,
        menu="View",
        text="Select Text",
        shortcut=None,
        accessible_name="Select document text",
        mnemonic_text="&Select Text",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.FIT_PAGE,
        menu="View",
        text="Fit Page",
        shortcut="Ctrl+0",
        accessible_name="Fit PDF page in viewer",
        mnemonic_text="Fit &Page",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.FIT_WIDTH,
        menu="View",
        text="Fit Width",
        shortcut="Ctrl+Shift+0",
        accessible_name="Fit PDF page width in viewer",
        mnemonic_text="Fit &Width",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.FIND,
        menu="View",
        text="Find",
        shortcut="Ctrl+F",
        accessible_name="Find text in the current PDF",
        mnemonic_text="&Find",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.DOCUMENT_SIGNATURES,
        menu="View",
        text="Document Signatures",
        shortcut=None,
        accessible_name="Review document signatures",
        mnemonic_text="Document &Signatures",
    ),
)


SETTINGS_COMMAND_DEFINITIONS: tuple[AppFrameCommandDefinition, ...] = (
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.APPLICATION_SETTINGS,
        menu="Settings",
        text="Application settings",
        shortcut=None,
        accessible_name="Open application settings",
        mnemonic_text="&Application settings",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.MANAGE_REUSABLE_OBJECTS,
        menu="Settings",
        text="Manage reusable signing objects...",
        shortcut=None,
        accessible_name="Manage reusable signing objects",
        mnemonic_text="&Manage reusable signing objects...",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.CREATE_CERTIFICATE,
        menu="Settings",
        text="Create certificate...",
        shortcut=None,
        accessible_name="Create certificate",
        mnemonic_text="Create certi&ficate...",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.IMPORT_CERTIFICATE,
        menu="Settings",
        text="Import certificate...",
        shortcut=None,
        accessible_name="Import certificate",
        mnemonic_text="&Import certificate...",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.MANAGE_CERTIFICATE_CONFIGURATIONS,
        menu="Settings",
        text="Manage certificate configurations...",
        shortcut=None,
        accessible_name="Manage certificate configurations",
        mnemonic_text="Manage certificate &configurations...",
    ),
)


ALL_COMMAND_DEFINITIONS: tuple[AppFrameCommandDefinition, ...] = (
    *FILE_COMMAND_DEFINITIONS,
    *EDIT_COMMAND_DEFINITIONS,
    *VIEW_COMMAND_DEFINITIONS,
    *SETTINGS_COMMAND_DEFINITIONS,
)


def command_definition(command_id: AppFrameCommandId) -> AppFrameCommandDefinition:
    """Return one definition from the single frame command registry."""

    for definition in ALL_COMMAND_DEFINITIONS:
        if definition.command_id is command_id:
            return definition
    raise KeyError(command_id)
