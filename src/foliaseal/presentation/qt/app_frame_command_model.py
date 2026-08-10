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
    BACK = "view.back"
    FORWARD = "view.forward"
    SELECT_TEXT = "view.select_text"
    ZOOM_IN = "view.zoom_in"
    ZOOM_OUT = "view.zoom_out"
    RESET_ZOOM = "view.reset_zoom"
    FIT_PAGE = "view.fit_page"
    FIT_WIDTH = "view.fit_width"
    FIND = "view.find"
    DOCUMENT_SIGNATURES = "view.document_signatures"
    APPLICATION_SETTINGS = "settings.application"
    MANAGE_REUSABLE_OBJECTS = "settings.manage_reusable_objects"
    CREATE_CERTIFICATE = "settings.create_certificate"
    IMPORT_CERTIFICATE = "settings.import_certificate"
    MANAGE_CERTIFICATE_CONFIGURATIONS = "settings.manage_certificate_configurations"
    SIGNATURE_LIBRARY = "signing.signature_library"
    SIGN_AND_SAVE = "signing.sign_and_save"
    PLACE_SIGNATURE = "signing.place_signature"
    ADJUST_PLACEMENT = "signing.adjust_placement"
    REMOVE_PLACEMENT = "signing.remove_placement"


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
        command_id=AppFrameCommandId.BACK,
        menu="View",
        text="Back",
        shortcut="Alt+Left",
        accessible_name="Go back to the previous internal document destination",
        mnemonic_text="&Back",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.FORWARD,
        menu="View",
        text="Forward",
        shortcut="Alt+Right",
        accessible_name="Go forward to the next internal document destination",
        mnemonic_text="&Forward",
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
        command_id=AppFrameCommandId.ZOOM_IN,
        menu="View",
        text="Zoom In",
        shortcut="Ctrl++",
        accessible_name="Zoom in the PDF viewer",
        mnemonic_text="Zoom &In",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.ZOOM_OUT,
        menu="View",
        text="Zoom Out",
        shortcut="Ctrl+-",
        accessible_name="Zoom out the PDF viewer",
        mnemonic_text="Zoom &Out",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.RESET_ZOOM,
        menu="View",
        text="Reset Zoom",
        shortcut=None,
        accessible_name="Reset PDF viewer zoom",
        mnemonic_text="Reset &Zoom",
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


SIGNING_COMMAND_DEFINITIONS: tuple[AppFrameCommandDefinition, ...] = (
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.SIGNATURE_LIBRARY,
        menu="Signing",
        text="Signature Library",
        shortcut=None,
        accessible_name="Open Signature Library",
        mnemonic_text="&Signature Library",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.PLACE_SIGNATURE,
        menu="Signing",
        text="Place Signature",
        shortcut=None,
        accessible_name="Enter signature placement mode",
        mnemonic_text="&Place Signature",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.ADJUST_PLACEMENT,
        menu="Signing",
        text="Adjust Placement",
        shortcut=None,
        accessible_name="Adjust visible signature placement",
        mnemonic_text="Ad&just Placement",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.REMOVE_PLACEMENT,
        menu="Signing",
        text="Remove Placement",
        shortcut=None,
        accessible_name="Remove visible signature placement",
        mnemonic_text="&Remove Placement",
    ),
    AppFrameCommandDefinition(
        command_id=AppFrameCommandId.SIGN_AND_SAVE,
        menu="Signing",
        text="Sign and save",
        shortcut=None,
        accessible_name="Sign and save PDF",
        mnemonic_text="Sign and sa&ve",
    ),
)


ALL_COMMAND_DEFINITIONS: tuple[AppFrameCommandDefinition, ...] = (
    *FILE_COMMAND_DEFINITIONS,
    *EDIT_COMMAND_DEFINITIONS,
    *VIEW_COMMAND_DEFINITIONS,
    *SIGNING_COMMAND_DEFINITIONS,
    *SETTINGS_COMMAND_DEFINITIONS,
)


def command_definition(command_id: AppFrameCommandId) -> AppFrameCommandDefinition:
    """Return one definition from the single frame command registry."""

    for definition in ALL_COMMAND_DEFINITIONS:
        if definition.command_id is command_id:
            return definition
    raise KeyError(command_id)
