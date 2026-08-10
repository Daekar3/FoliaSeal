"""Settings dialog for inspecting and managing reusable signing objects."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.reusable_signing_models import PlacementProfile
from foliaseal.application.reusable_signing_objects import (
    DeleteObject,
    DuplicateObject,
    RenameObject,
    ReusableObjectKind,
    ReusableObjectRef,
    ReusableSigningObjects,
    SetPinned,
)
from foliaseal.application.signature_library_session import (
    CertificateLibraryRef,
    LibraryCatalog,
    LibrarySort,
    SignatureLibraryRow,
    SignatureLibrarySession,
)
from foliaseal.infra.config.schemas import ConfigValidationError


def _compose_row(bindings: Any, *widgets: Any) -> Any:
    container = bindings.q_widget()
    layout = bindings.q_hbox_layout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    for widget in widgets:
        layout.addWidget(widget)
    return container


def _set_enabled(widget: Any, enabled: bool) -> None:
    setter = getattr(widget, "setEnabled", None)
    if callable(setter):
        setter(enabled)
    elif hasattr(widget, "_enabled"):
        widget._enabled = bool(enabled)


def _set_text(widget: Any, value: str) -> None:
    setter = getattr(widget, "setText", None)
    if callable(setter):
        setter(value)
    elif hasattr(widget, "_text"):
        widget._text = value
    elif hasattr(widget, "text"):
        widget.text = value


@dataclass(frozen=True)
class ReusableObjectLibraryControls:
    """Widgets exposed by the reusable-signing-object library dialog."""

    dialog: Any
    catalog_selector: Any
    search_input: Any
    sort_selector: Any
    object_selector: Any
    detail_container: Any
    details_label: Any
    name_input: Any
    rename_button: Any
    delete_button: Any
    duplicate_button: Any
    pin_button: Any
    create_button: Any
    edit_button: Any
    create_placement_button: Any
    edit_placement_button: Any
    save_button: Any
    cancel_button: Any
    close_button: Any


class ReusableObjectLibraryDialog:
    """Manage saved appearance, placement, and composed preset objects.

    The dialog delegates queries and mutations to an application boundary. A
    profile rename retains the stable component id, so presets that reference
    it remain valid; deletion is rejected by the catalog when a dependency is
    still present.
    """

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        library: ReusableSigningObjects,
        certificate_catalog: Any | None = None,
        certificate_catalog_provider: Callable[[], Any] | None = None,
        initial_catalog: str = "presets",
        library_sort: str = LibrarySort.NAME_ASCENDING.value,
        on_preferences_changed: Callable[[str, str], None] | None = None,
        on_toggle_certificate_pin: Callable[[CertificateLibraryRef, bool], bool] | None = None,
        on_rename_certificate: Callable[[CertificateLibraryRef, str], bool] | None = None,
        on_delete_certificate: Callable[[CertificateLibraryRef], bool] | None = None,
        on_configure_certificate: Callable[[CertificateLibraryRef], bool] | None = None,
        on_create_appearance: Callable[[], bool] | None = None,
        on_edit_appearance: Callable[[ReusableObjectRef], bool] | None = None,
        on_create: Callable[[], bool] | None = None,
        on_edit: Callable[[ReusableObjectRef], bool] | None = None,
        on_create_placement: Callable[[], bool] | None = None,
        on_edit_placement: Callable[[PlacementProfile], bool] | None = None,
    ) -> None:
        self._bindings = bindings
        self._library = library
        self._on_create = on_create
        self._on_edit = on_edit
        self._on_create_appearance = on_create_appearance
        self._on_edit_appearance = on_edit_appearance
        self._on_create_placement = on_create_placement
        self._on_edit_placement = on_edit_placement
        self._certificate_catalog_provider = certificate_catalog_provider
        self._on_preferences_changed = on_preferences_changed
        self._on_toggle_certificate_pin = on_toggle_certificate_pin
        self._on_rename_certificate = on_rename_certificate
        self._on_delete_certificate = on_delete_certificate
        self._on_configure_certificate = on_configure_certificate
        self._session = SignatureLibrarySession(
            library,
            certificate_catalog,
            initial_catalog=initial_catalog,
            sort=library_sort,
        )
        self._rows: tuple[SignatureLibraryRow, ...] = ()
        self.controls = self._build_controls(parent)
        self.refresh()

    def show(self) -> Any:
        """Show the modeless Library window without blocking the main frame."""
        show = getattr(self.controls.dialog, "show", None)
        if callable(show):
            show()
        raise_window = getattr(self.controls.dialog, "raise_", None)
        if callable(raise_window):
            raise_window()
        activate = getattr(self.controls.dialog, "activateWindow", None)
        if callable(activate):
            activate()
        return self

    def refresh(self) -> None:
        if self._certificate_catalog_provider is not None:
            self._session.set_certificate_catalog(self._certificate_catalog_provider())
        self._rows = self._session.refresh()
        self._render_catalog_navigation()
        self._render_master_list()
        self._render_selection()

    def rename_selected(self) -> bool:
        selected = self._selected_object()
        new_name = self._session.draft_name or self.controls.name_input.text().strip()
        if selected is None or not new_name:
            self._show_error("Select a saved object and enter a new name.")
            return False
        ref, _name = selected
        if not isinstance(ref, ReusableObjectRef):
            if self._on_rename_certificate is None:
                self._show_error("Certificate changes are managed from Settings.")
                return False
            if not self._on_rename_certificate(ref, new_name):
                return False
            self.refresh()
            self._session.select(ref)
            self._session.commit_detail()
            self._render_master_list()
            self._render_selection()
            return True
        try:
            self._library.execute(RenameObject(ref=ref, new_name=new_name))
        except (ConfigValidationError, KeyError) as exc:
            self._show_error(str(exc))
            return False
        self.refresh()
        self._set_selector_text(new_name)
        self._session.commit_detail()
        return True

    def duplicate_selected(self) -> bool:
        selected = self._selected_object()
        if selected is None or not isinstance(selected[0], ReusableObjectRef):
            self._show_error("Select a reusable object before duplicating it.")
            return False
        ref, name = selected
        duplicate_name = f"{name} Copy"
        try:
            self._library.execute(DuplicateObject(ref=ref, new_name=duplicate_name))
        except (ConfigValidationError, KeyError) as exc:
            self._show_error(str(exc))
            return False
        self.refresh()
        self._session.select(
            next((row.ref for row in self._rows if row.display_name == duplicate_name), None)
        )
        self._render_master_list()
        self._render_selection()
        return True

    def toggle_pin_selected(self) -> bool:
        selected = self._selected_object()
        if selected is None:
            self._show_error("Select an object before changing its pin.")
            return False
        ref, _name = selected
        row = self._session.selected_row()
        if row is None:
            self._session.select(ref)
            row = self._session.selected_row()
        if row is None:
            return False
        pinned = not row.pinned
        try:
            if isinstance(ref, ReusableObjectRef):
                self._library.execute(SetPinned(ref=ref, pinned=pinned))
            elif self._on_toggle_certificate_pin is None or not self._on_toggle_certificate_pin(
                ref, pinned
            ):
                return False
        except (ConfigValidationError, KeyError) as exc:
            self._show_error(str(exc))
            return False
        self.refresh()
        self._session.select(ref)
        self._render_master_list()
        self._render_selection()
        return True

    def cancel_detail(self) -> bool:
        """Discard the current detail selection without changing the catalog."""

        self._session.cancel_detail()
        self._render_master_list()
        self._render_selection()
        return True

    def save_detail(self) -> bool:
        """Commit the current detail transaction through the typed rename boundary."""

        return self.rename_selected()

    def delete_selected(self) -> bool:
        selected = self._selected_object()
        if selected is None:
            self._show_error("Select a saved object before deleting it.")
            return False
        ref, _name = selected
        if not self._confirm_delete(_name):
            return False
        if not isinstance(ref, ReusableObjectRef):
            if self._on_delete_certificate is None or not self._on_delete_certificate(ref):
                return False
            self.refresh()
            return True
        try:
            self._library.execute(DeleteObject(ref=ref))
        except (ConfigValidationError, KeyError) as exc:
            self._show_error(str(exc))
            return False
        self.refresh()
        return True

    def _build_controls(self, parent: Any) -> ReusableObjectLibraryControls:
        dialog = self._bindings.q_dialog(parent)
        set_title = getattr(dialog, "setWindowTitle", None)
        if callable(set_title):
            set_title("Manage reusable signing objects")
        layout = self._bindings.q_hbox_layout(dialog)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        navigation = (
            self._bindings.q_list_widget()
            if self._has_list_widget()
            else self._bindings.q_combo_box()
        )
        if hasattr(navigation, "setMinimumWidth"):
            navigation.setMinimumWidth(130)
        search = self._bindings.q_line_edit()
        search.setPlaceholderText("Search saved objects")
        sort_selector = self._bindings.q_combo_box()
        for label, value in (
            ("Name A–Z", LibrarySort.NAME_ASCENDING.value),
            ("Name Z–A", LibrarySort.NAME_DESCENDING.value),
            ("Expiration soonest", LibrarySort.EXPIRATION_SOONEST.value),
        ):
            try:
                sort_selector.addItem(label, value)
            except TypeError:
                sort_selector.addItem(label)
        available_sorts = (
            LibrarySort.NAME_ASCENDING,
            LibrarySort.NAME_DESCENDING,
            LibrarySort.EXPIRATION_SOONEST,
        )
        available_sort_index = {
            value: index for index, value in enumerate(available_sorts)
        }.get(self._session.sort, 0)
        sort_selector.setCurrentIndex(available_sort_index)
        selector = (
            self._bindings.q_list_widget()
            if self._has_list_widget()
            else self._bindings.q_combo_box()
        )
        details = self._bindings.q_label("")
        name_input = self._bindings.q_line_edit()
        name_input.setPlaceholderText("New name")
        rename = self._bindings.q_push_button("Rename")
        delete = self._bindings.q_push_button("Delete")
        duplicate = self._bindings.q_push_button("Duplicate")
        pin = self._bindings.q_push_button("Pin")
        create = self._bindings.q_push_button("Create")
        edit = self._bindings.q_push_button("Edit")
        create_placement = self._bindings.q_push_button("Create placement")
        edit_placement = self._bindings.q_push_button("Edit selected placement")
        save = self._bindings.q_push_button("Save")
        cancel = self._bindings.q_push_button("Cancel")
        close = self._bindings.q_push_button("Close")

        navigation.addItems([catalog.value for catalog in LibraryCatalog])
        navigation_column = self._bindings.q_widget()
        navigation_layout = self._bindings.q_vbox_layout(navigation_column)
        navigation_layout.setContentsMargins(0, 0, 0, 0)
        navigation_layout.addWidget(self._bindings.q_label("Catalog"))
        navigation_layout.addWidget(navigation)

        master_column = self._bindings.q_widget()
        master_layout = self._bindings.q_vbox_layout(master_column)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.addWidget(self._bindings.q_label("Saved objects"))
        master_layout.addWidget(search)
        master_layout.addWidget(sort_selector)
        master_layout.addWidget(selector)

        detail = self._bindings.q_widget()
        detail_layout = self._bindings.q_vbox_layout(detail)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.addWidget(self._bindings.q_label("Details"))
        detail_layout.addWidget(details)
        detail_layout.addWidget(self._bindings.q_label("Name"))
        detail_layout.addWidget(name_input)
        detail_layout.addWidget(_compose_row(self._bindings, rename, duplicate, delete, pin))
        detail_layout.addWidget(_compose_row(self._bindings, create, edit))
        detail_layout.addWidget(_compose_row(self._bindings, create_placement, edit_placement))
        add_stretch = getattr(detail_layout, "addStretch", None)
        if callable(add_stretch):
            add_stretch()
        detail_layout.addWidget(_compose_row(self._bindings, save, cancel))
        detail_layout.addWidget(close)

        splitter_cls = getattr(self._bindings, "q_splitter", None)
        if splitter_cls is not None:
            splitter = splitter_cls()
            orientation = getattr(getattr(self._bindings, "qt", None), "Horizontal", None)
            if orientation is not None and hasattr(splitter, "setOrientation"):
                splitter.setOrientation(orientation)
            splitter.addWidget(navigation_column)
            splitter.addWidget(master_column)
            splitter.addWidget(detail)
            if hasattr(splitter, "setStretchFactor"):
                splitter.setStretchFactor(2, 1)
            layout.addWidget(splitter)
        else:
            layout.addWidget(navigation_column)
            layout.addWidget(master_column)
            layout.addWidget(detail)

        if hasattr(navigation, "currentRowChanged"):
            navigation.currentRowChanged.connect(self._handle_catalog_row_changed)
        else:
            navigation.currentTextChanged.connect(self._handle_catalog_text_changed)
        search.textChanged.connect(lambda value: self._handle_search_changed(str(value)))
        sort_selector.currentIndexChanged.connect(self._handle_sort_changed)
        name_input.textChanged.connect(lambda value: self._session.set_draft_name(str(value)))
        if hasattr(selector, "currentRowChanged"):
            selector.currentRowChanged.connect(lambda _row: self._handle_master_row_changed())
        else:
            selector.currentTextChanged.connect(lambda _value: self._handle_master_row_changed())
        rename.clicked.connect(self.rename_selected)
        duplicate.clicked.connect(self.duplicate_selected)
        pin.clicked.connect(self.toggle_pin_selected)
        delete.clicked.connect(self.delete_selected)
        save.clicked.connect(self.save_detail)
        cancel.clicked.connect(self.cancel_detail)
        create.clicked.connect(self._create_selected_object)
        edit.clicked.connect(self._edit_selected_object)
        if self._on_create_placement is not None:
            create_placement.clicked.connect(self._on_create_placement)
        else:
            create_placement.setEnabled(False)
        if self._on_edit_placement is not None:
            edit_placement.clicked.connect(self._edit_selected_placement)
        else:
            edit_placement.setEnabled(False)
        reject = getattr(dialog, "reject", None)
        if callable(reject):
            close.clicked.connect(reject)
        return ReusableObjectLibraryControls(
            dialog=dialog,
            catalog_selector=navigation,
            search_input=search,
            sort_selector=sort_selector,
            object_selector=selector,
            detail_container=detail,
            details_label=details,
            name_input=name_input,
            rename_button=rename,
            delete_button=delete,
            duplicate_button=duplicate,
            pin_button=pin,
            create_button=create,
            edit_button=edit,
            create_placement_button=create_placement,
            edit_placement_button=edit_placement,
            save_button=save,
            cancel_button=cancel,
            close_button=close,
        )

    def _edit_selected_placement(self) -> bool:
        selected = self._selected_object()
        if selected is None:
            self._show_error("Select a saved placement before editing it.")
            return False
        ref, _name = selected
        if not isinstance(ref, ReusableObjectRef):
            self._show_error("Select a placement to open the placement editor.")
            return False
        try:
            profile = self._library.resolve(ref)
        except ConfigValidationError as exc:
            self._show_error(str(exc))
            return False
        if not isinstance(profile, PlacementProfile):
            self._show_error("Select a placement to open the placement editor.")
            return False
        assert self._on_edit_placement is not None
        return self._on_edit_placement(profile)

    def _edit_selected_preset(self) -> bool:
        selected = self._selected_object()
        if selected is None or not isinstance(selected[0], ReusableObjectRef):
            self._show_error("Select a signature preset before editing it.")
            return False
        ref, _name = selected
        if ref.kind is not ReusableObjectKind.PRESET:
            self._show_error("Select a signature preset before editing it.")
            return False
        assert self._on_edit is not None
        return self._on_edit(ref)

    def _create_selected_object(self) -> bool:
        callback = (
            self._on_create_appearance
            if self._session.catalog is LibraryCatalog.APPEARANCES
            else self._on_create
            if self._session.catalog is LibraryCatalog.PRESETS
            else None
        )
        if callback is None:
            self._show_error("Create is not available for this catalog.")
            return False
        return callback()

    def _edit_selected_object(self) -> bool:
        selected = self._selected_object()
        if selected is None:
            self._show_error("Select a reusable object before editing it.")
            return False
        ref, _name = selected
        if isinstance(ref, CertificateLibraryRef):
            row = self._session.selected_row()
            if (
                row is not None
                and not row.configured
                and ref.configuration_id is None
                and self._on_configure_certificate is not None
            ):
                configured = self._on_configure_certificate(ref)
                if configured:
                    self.refresh()
                    refreshed_ref = next(
                        (
                            candidate.ref
                            for candidate in self._rows
                            if isinstance(candidate.ref, CertificateLibraryRef)
                            and candidate.ref.object_id == ref.object_id
                        ),
                        None,
                    )
                    self._session.select(refreshed_ref)
                    self._render_master_list()
                    self._render_selection()
                return configured
            self._show_error("Select a retained certificate file to configure it.")
            return False
        if not isinstance(ref, ReusableObjectRef):
            self._show_error("Select a reusable object before editing it.")
            return False
        if ref.kind is ReusableObjectKind.APPEARANCE:
            if self._on_edit_appearance is None:
                self._show_error("Appearance editing is not available.")
                return False
            return self._on_edit_appearance(ref)
        if ref.kind is ReusableObjectKind.PRESET:
            if self._on_edit is None:
                self._show_error("Preset editing is not available.")
                return False
            return self._on_edit(ref)
        self._show_error("Select an appearance or preset to edit it.")
        return False

    def _has_list_widget(self) -> bool:
        return callable(getattr(self._bindings, "q_list_widget", None))

    def _render_catalog_navigation(self) -> None:
        navigation = self.controls.catalog_selector
        if hasattr(navigation, "setCurrentRow"):
            navigation.setCurrentRow(list(LibraryCatalog).index(self._session.catalog))
        else:
            setter = getattr(navigation, "setCurrentText", None)
            if callable(setter):
                setter(self._session.catalog.value)
            else:
                index = getattr(navigation, "findText", lambda _value: -1)(
                    self._session.catalog.value
                )
                if index >= 0 and hasattr(navigation, "setCurrentIndex"):
                    navigation.setCurrentIndex(index)

    def _render_master_list(self) -> None:
        selector = self.controls.object_selector
        clear = getattr(selector, "clear", None)
        if callable(clear):
            clear()
        names = [row.display_name for row in self._rows]
        if hasattr(selector, "addItems"):
            selector.addItems(names)
        else:
            for name in names:
                selector.addItem(name)
        if hasattr(selector, "setItemData"):
            for index, row in enumerate(self._rows):
                selector.setItemData(index, row.ref)
        selected = self._session.selected_ref
        if selected is not None:
            selected_index = next(
                (index for index, row in enumerate(self._rows) if row.ref == selected),
                -1,
            )
            if hasattr(selector, "setCurrentRow"):
                selector.setCurrentRow(selected_index)
            elif selected_index >= 0:
                selector.setCurrentIndex(selected_index)

    def _handle_catalog_row_changed(self, index: int) -> None:
        catalogs = list(LibraryCatalog)
        if 0 <= int(index) < len(catalogs):
            self._session.select_catalog(catalogs[int(index)])
            if self._on_preferences_changed is not None:
                self._on_preferences_changed(
                    self._session.catalog.value, self._session.sort.value
                )
            self._rows = self._session.rows()
            self._render_master_list()
            self._render_selection()

    def _handle_catalog_text_changed(self, value: str) -> None:
        try:
            catalog = next(item for item in LibraryCatalog if item.value == value)
        except StopIteration:
            return
        self._session.select_catalog(catalog)
        if self._on_preferences_changed is not None:
            self._on_preferences_changed(self._session.catalog.value, self._session.sort.value)
        self._rows = self._session.rows()
        self._render_master_list()
        self._render_selection()

    def _handle_search_changed(self, value: str) -> None:
        self._rows = self._session.set_search(value)
        self._render_master_list()
        self._render_selection()

    def _handle_sort_changed(self, index: int | None = None) -> None:
        if not hasattr(self, "controls"):
            return
        selector = self.controls.sort_selector
        if index is None:
            index = int(getattr(selector, "currentIndex", lambda: 0)())
        data_getter = getattr(selector, "itemData", None)
        value = (
            data_getter(index)
            if callable(data_getter)
            else (
                LibrarySort.NAME_ASCENDING,
                LibrarySort.NAME_DESCENDING,
                LibrarySort.EXPIRATION_SOONEST,
            )[index].value
            if 0 <= index < 3
            else LibrarySort.NAME_ASCENDING.value
        )
        self._rows = self._session.set_sort(str(value))
        if self._on_preferences_changed is not None:
            self._on_preferences_changed(self._session.catalog.value, self._session.sort.value)
        self._render_master_list()
        self._render_selection()

    def _handle_master_row_changed(self) -> None:
        selected = self._selected_object()
        self._session.select(None if selected is None else selected[0])
        self._render_selection()

    def _render_selection(self) -> None:
        if self._session.catalog is LibraryCatalog.APPEARANCES:
            _set_text(self.controls.create_button, "Create appearance")
        elif self._session.catalog is LibraryCatalog.PRESETS:
            _set_text(self.controls.create_button, "Create preset")
        else:
            _set_text(self.controls.create_button, "Create")
        _set_enabled(
            self.controls.create_button,
            (
                self._session.catalog is LibraryCatalog.APPEARANCES
                and self._on_create_appearance is not None
            )
            or (
                self._session.catalog is LibraryCatalog.PRESETS
                and self._on_create is not None
            ),
        )
        selected = self._session.selected_row()
        if selected is None:
            if self._session.catalog is LibraryCatalog.CERTIFICATES:
                message = "Certificate management is available from Settings."
            elif self._rows:
                message = "Select an object to inspect its saved references."
            else:
                message = "No saved objects match this catalog or search."
            self.controls.details_label.setText(message)
            _set_enabled(self.controls.duplicate_button, False)
            _set_enabled(self.controls.pin_button, False)
            _set_enabled(self.controls.edit_button, False)
            _set_enabled(self.controls.edit_placement_button, False)
            return
        self.controls.details_label.setText(selected.details)
        self.controls.name_input.setText(self._session.draft_name or selected.display_name)
        _set_text(self.controls.pin_button, "Unpin" if selected.pinned else "Pin")
        is_reusable = isinstance(selected.ref, ReusableObjectRef)
        _set_enabled(self.controls.duplicate_button, is_reusable)
        _set_enabled(
            self.controls.pin_button,
            is_reusable or self._on_toggle_certificate_pin is not None,
        )
        _set_enabled(
            self.controls.edit_placement_button,
            isinstance(selected.ref, ReusableObjectRef)
            and selected.ref.kind is ReusableObjectKind.PLACEMENT,
        )
        _set_enabled(
            self.controls.edit_button,
            (
                is_reusable
                and (
                (selected.ref.kind is ReusableObjectKind.PRESET and self._on_edit is not None)
                or (
                    selected.ref.kind is ReusableObjectKind.APPEARANCE
                    and self._on_edit_appearance is not None
                )
                )
            ),
        )
        if isinstance(selected.ref, ReusableObjectRef):
            if selected.ref.kind is ReusableObjectKind.APPEARANCE:
                _set_text(self.controls.edit_button, "Edit appearance")
            elif selected.ref.kind is ReusableObjectKind.PRESET:
                _set_text(self.controls.edit_button, "Edit preset")
        elif (
            isinstance(selected.ref, CertificateLibraryRef)
            and not selected.configured
            and selected.ref.configuration_id is None
        ):
            _set_text(self.controls.edit_button, "Configure certificate")
            _set_enabled(
                self.controls.edit_button,
                self._on_configure_certificate is not None,
            )

    def _selected_object(
        self,
    ) -> tuple[ReusableObjectRef | CertificateLibraryRef, str] | None:
        selector = self.controls.object_selector
        if hasattr(selector, "currentRow"):
            index = selector.currentRow()
        else:
            index_getter = getattr(selector, "currentIndex", None)
            if callable(index_getter):
                index = index_getter()
            else:
                value = str(getattr(selector, "currentText", lambda: "")()).strip()
                index = next(
                    (index for index, row in enumerate(self._rows) if row.display_name == value),
                    -1,
                )
        if not isinstance(index, int) or not 0 <= index < len(self._rows):
            return None
        row = self._rows[index]
        return row.ref, row.display_name

    def _set_selector_text(self, value: str) -> None:
        selector = self.controls.object_selector
        index = next(
            (index for index, row in enumerate(self._rows) if row.display_name == value),
            -1,
        )
        if hasattr(selector, "setCurrentRow"):
            selector.setCurrentRow(index)
        else:
            setter = getattr(selector, "setCurrentText", None)
            if callable(setter):
                setter(value)

    def _show_error(self, message: str) -> None:
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.controls.dialog, "Reusable signing object error", message)

    def _confirm_delete(self, display_name: str) -> bool:
        """Require an explicit Yes before any catalog deletion is dispatched."""

        message_box = getattr(self._bindings, "q_message_box", None)
        question = getattr(message_box, "question", None)
        yes = getattr(message_box, "Yes", None)
        if yes is None:
            standard_button = getattr(message_box, "StandardButton", None)
            yes = getattr(standard_button, "Yes", None)
        if not callable(question) or yes is None:
            self._show_error("Deletion confirmation is unavailable; nothing was deleted.")
            return False
        result = question(
            self.controls.dialog,
            "Delete saved object?",
            f"Delete saved object '{display_name}'?",
        )
        return result == yes
