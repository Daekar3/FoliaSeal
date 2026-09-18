"""Reusable Qt detail editor for one document-independent Appearance."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.reusable_signing_models import AppearanceProfile
from foliaseal.application.reusable_signing_objects import (
    ReusableObjectKind,
    ReusableObjectMutationRejected,
    ReusableObjectRef,
    ReusableSigningObjects,
    SaveAppearance,
)
from foliaseal.application.signature_image_import import (
    ManagedSignatureImageStore,
    SignatureImageImportError,
    SignatureImageOptimizationRequired,
)
from foliaseal.application.signature_properties_coordinator import (
    VisibleSignaturePlacementDraft,
    VisibleSignatureSetupDraft,
)
from foliaseal.domain.models import SignatureAppearance, SignatureFieldSource
from foliaseal.infra.config.schemas import ConfigValidationError
from foliaseal.presentation.qt.visible_signature_setup_form import QtVisibleSignatureSetupForm


@dataclass(frozen=True)
class AppearanceProfileEditorWidgetControls:
    """Public controls for the Library-owned Appearance editor."""

    container: Any
    breadcrumb_label: Any
    sample_preview_label: Any
    sample_preview_image: Any
    name_input: Any
    setup_form: QtVisibleSignatureSetupForm
    save_button: Any
    cancel_button: Any
    form_scroll_area: Any | None = None
    action_row: Any | None = None


def _compose_row(bindings: Any, *widgets: Any) -> Any:
    container = bindings.q_widget()
    layout = bindings.q_hbox_layout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    if hasattr(layout, "addStretch"):
        layout.addStretch()
    for widget in widgets:
        layout.addWidget(widget)
    return container


class AppearanceProfileEditorWidget:
    """Own an isolated Appearance draft and its explicit Save/Cancel transaction.

    The widget never mutates the catalog while controls are edited. The caller decides how to
    resolve a cancel/back request (for example, with a Save/Discard/Continue prompt) through
    ``on_cancel_requested``.
    """

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        library: ReusableSigningObjects,
        initial_ref: ReusableObjectRef | None = None,
        breadcrumb: str = "Signature Library / Appearances",
        on_saved: Callable[[], None] | None = None,
        on_cancel_requested: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        image_store: ManagedSignatureImageStore | None = None,
    ) -> None:
        self._bindings = bindings
        self._library = library
        self._initial_ref = initial_ref
        self._breadcrumb = breadcrumb
        self._on_saved = on_saved or (lambda: None)
        self._on_cancel_requested = on_cancel_requested or (lambda: None)
        self._on_error = on_error or (lambda _message: None)
        self._image_store = image_store
        self._suspend_updates = True
        self._dirty = False
        self._saved_ref: ReusableObjectRef | None = None
        self._original_name = ""
        self._original_appearance = self._initial_appearance()
        self._staged_image_paths: set[str] = set()
        self.controls = self._build_controls(parent)
        self._suspend_updates = False
        self._refresh_preview()

    @property
    def dirty(self) -> bool:
        """Whether the draft differs from the persisted child state."""

        return self._dirty

    @property
    def saved_ref(self) -> ReusableObjectRef | None:
        """Stable reference produced by the most recent successful Save."""

        return self._saved_ref

    @property
    def initial_ref(self) -> ReusableObjectRef | None:
        return self._initial_ref

    def save(self) -> bool:
        """Validate and commit the isolated draft, leaving navigation to the owner."""

        name = str(self.controls.name_input.text()).strip()
        if not name:
            self._on_error("Appearance name is required.")
            return False
        overwrite = False
        if self._initial_ref is None:
            existing = self._library.resolve_name(ReusableObjectKind.APPEARANCE, name)
            if existing is not None:
                message_box = getattr(self._bindings, "q_message_box", None)
                question = getattr(message_box, "question", None)
                yes = getattr(message_box, "Yes", None)
                if callable(question):
                    result = question(
                        self.controls.container,
                        "Replace appearance?",
                        f"Appearance '{name}' already exists. Replace it?",
                    )
                    if result == yes:
                        overwrite = True
                    else:
                        return False
                else:
                    self._on_error(f"Appearance '{name}' already exists.")
                    return False
        try:
            appearance = self.controls.setup_form.build_draft().appearance
            has_visible_content = any(
                binding.show_in_visible_appearance
                and binding.source is not SignatureFieldSource.HIDDEN
                for _field_key, binding in appearance.iter_field_bindings()
            )
            if not has_visible_content and appearance.image_stamp_path is None:
                self._on_error(
                    "An Appearance must contain visible signing text or an image."
                )
                return False
            self._library.execute(
                SaveAppearance(
                    name=name,
                    appearance=appearance,
                    appearance_profile_id=(
                        None if self._initial_ref is None else self._initial_ref.object_id
                    ),
                    overwrite=overwrite,
                )
            )
        except ReusableObjectMutationRejected:
            return False
        except (ConfigValidationError, KeyError, ValueError) as exc:
            self._on_error(str(exc))
            return False
        self._saved_ref = self._library.resolve_name(ReusableObjectKind.APPEARANCE, name)
        self._staged_image_paths.clear()
        self._dirty = False
        self._on_saved()
        return True

    def request_cancel(self) -> None:
        """Ask the owner to resolve Back/Cancel, preserving the draft until it decides."""

        self._on_cancel_requested()

    def discard_staged_images(self) -> None:
        """Delete normalized images created by this draft and not yet saved."""

        if self._image_store is None:
            self._staged_image_paths.clear()
            return
        for image_path in tuple(self._staged_image_paths):
            try:
                self._image_store.delete_managed_image(image_path)
            except SignatureImageImportError as exc:
                self._on_error(str(exc))
        self._staged_image_paths.clear()

    def _initial_appearance(self) -> SignatureAppearance:
        if self._initial_ref is None:
            return SignatureAppearance()
        resolved = self._library.resolve(self._initial_ref)
        if not isinstance(resolved, AppearanceProfile):
            raise ConfigValidationError("Select an Appearance to edit.")
        self._original_name = resolved.display_name
        return resolved.appearance

    def _build_controls(self, parent: Any) -> AppearanceProfileEditorWidgetControls:
        bindings = self._bindings
        container = bindings.q_widget(parent)
        set_minimum_size = getattr(container, "setMinimumSize", None)
        if callable(set_minimum_size):
            set_minimum_size(500, 560)
        layout = bindings.q_vbox_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        breadcrumb = bindings.q_label(self._breadcrumb)
        if hasattr(breadcrumb, "setAccessibleName"):
            breadcrumb.setAccessibleName("Appearance editor breadcrumb")
        layout.addWidget(breadcrumb)

        body = bindings.q_widget()
        body_layout = bindings.q_hbox_layout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(8)
        content_side = bindings.q_widget()
        content_layout = bindings.q_vbox_layout(content_side)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)
        preview_side = bindings.q_widget()
        preview_layout = bindings.q_vbox_layout(preview_side)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(4)
        body_layout.addWidget(content_side, 3)
        body_layout.addWidget(preview_side, 2)
        layout.addWidget(body)

        preview_heading = bindings.q_label("Sample preview (synthetic data — never saved)")
        if hasattr(preview_heading, "setWordWrap"):
            preview_heading.setWordWrap(True)
        preview_layout.addWidget(preview_heading)
        sample_preview = bindings.q_label("")
        if hasattr(sample_preview, "setWordWrap"):
            sample_preview.setWordWrap(True)
        if hasattr(sample_preview, "setMinimumHeight"):
            sample_preview.setMinimumHeight(72)
        if hasattr(sample_preview, "setStyleSheet"):
            sample_preview.setStyleSheet(
                "border: 1px solid #9ca3af; padding: 8px;"
                " background: #ffffff; color: #111827;"
            )
        preview_layout.addWidget(sample_preview)
        sample_preview_image = bindings.q_label("")
        if hasattr(sample_preview_image, "setMinimumHeight"):
            sample_preview_image.setMinimumHeight(72)
        if hasattr(sample_preview_image, "setAlignment"):
            alignment = getattr(getattr(bindings, "qt", None), "AlignCenter", None)
            if alignment is not None:
                sample_preview_image.setAlignment(alignment)
        if hasattr(sample_preview_image, "setStyleSheet"):
            sample_preview_image.setStyleSheet(
                "border: 1px solid #9ca3af; padding: 4px; background: #ffffff;"
            )
        preview_layout.addWidget(sample_preview_image)
        if hasattr(preview_layout, "addStretch"):
            preview_layout.addStretch()

        name_input = bindings.q_line_edit()
        name_input.setPlaceholderText("Appearance name")
        content_layout.addWidget(bindings.q_label("Name"))
        content_layout.addWidget(name_input)

        setup_form = QtVisibleSignatureSetupForm(
            bindings=bindings,
            on_change=self._mark_dirty,
            on_image_import=self._import_image,
            on_image_remove=self._remove_image,
            appearance_compact=True,
        )
        setup_form.load(
            VisibleSignatureSetupDraft(
                appearance=self._original_appearance,
                placement=VisibleSignaturePlacementDraft(
                    page_number=1,
                    left_pt=24.0,
                    bottom_pt=18.0,
                    width_pt=180.0,
                    height_pt=54.0,
                    enabled=False,
                ),
            )
        )
        form_container = bindings.q_widget()
        form_layout = bindings.q_vbox_layout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.addWidget(setup_form.appearance_controls.container)
        form_layout.addWidget(setup_form.visible_text_controls.container)
        scroll_factory = getattr(bindings, "q_scroll_area", None)
        scroll_area = None
        if callable(scroll_factory):
            scroll_area = scroll_factory()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(form_container)
            content_layout.addWidget(scroll_area)
        else:
            content_layout.addWidget(form_container)

        save_button = bindings.q_push_button("Save")
        cancel_button = bindings.q_push_button("Cancel")
        if hasattr(save_button, "setDefault"):
            save_button.setDefault(True)
        action_row = _compose_row(bindings, cancel_button, save_button)
        layout.addWidget(action_row)
        name_input.textChanged.connect(self._on_name_changed)  # type: ignore[attr-defined]
        save_button.clicked.connect(self.save)  # type: ignore[attr-defined]
        cancel_button.clicked.connect(self.request_cancel)  # type: ignore[attr-defined]
        if self._initial_ref is not None:
            name_input.setText(self._original_name)
        return AppearanceProfileEditorWidgetControls(
            container=container,
            breadcrumb_label=breadcrumb,
            sample_preview_label=sample_preview,
            sample_preview_image=sample_preview_image,
            name_input=name_input,
            setup_form=setup_form,
            save_button=save_button,
            cancel_button=cancel_button,
            form_scroll_area=scroll_area,
            action_row=action_row,
        )

    def _on_name_changed(self, *_args: object) -> None:
        self._mark_dirty()

    def _import_image(self) -> None:
        if self._image_store is None:
            self._on_error("Managed image storage is unavailable.")
            return
        file_dialog = getattr(self._bindings, "q_file_dialog", None)
        chooser = getattr(file_dialog, "getOpenFileName", None)
        if not callable(chooser):
            self._on_error("Image selection is unavailable in this environment.")
            return
        selected = chooser(
            self.controls.container,
            "Choose signature image",
            "",
            "Signature images (*.png *.jpg *.jpeg *.gif)",
        )
        source = selected[0] if isinstance(selected, tuple) else selected
        source_text = str(source).strip()
        if not source_text:
            return
        preserve_alpha = self.controls.setup_form.build_draft().appearance.preserve_image_alpha
        try:
            try:
                managed = self._image_store.import_asset(
                    source_text,
                    preserve_alpha=preserve_alpha,
                )
            except SignatureImageOptimizationRequired as exc:
                if not self._confirm_image_optimization(exc):
                    return
                managed = self._image_store.import_asset(
                    source_text,
                    preserve_alpha=preserve_alpha,
                    allow_optimization=True,
                )
        except SignatureImageImportError as exc:
            self._on_error(str(exc))
            return
        current_path = self.controls.setup_form.build_draft().appearance.image_stamp_path
        if current_path is not None and current_path in self._staged_image_paths:
            try:
                self._image_store.delete_managed_image(current_path)
            except SignatureImageImportError as exc:
                # The new import is already in the managed directory.  Do not leave it
                # orphaned if replacing an earlier staged image fails; retain the old draft
                # path so the caller can retry or cancel safely.
                try:
                    self._image_store.delete_managed_image(str(managed.path))
                except SignatureImageImportError:
                    pass
                self._on_error(str(exc))
                return
            self._staged_image_paths.discard(current_path)
        self.controls.setup_form.set_image_asset(str(managed.path), managed.asset)
        self._staged_image_paths.add(str(managed.path))

    def _confirm_image_optimization(self, error: SignatureImageOptimizationRequired) -> bool:
        message_box = getattr(self._bindings, "q_message_box", None)
        question = getattr(message_box, "question", None)
        yes = getattr(message_box, "Yes", None)
        if not callable(question):
            self._on_error(str(error))
            return False
        result = question(
            self.controls.container,
            "Optimize signature image?",
            "This image is larger than 2048 pixels on one edge. Optimize a managed copy?",
        )
        return result == yes

    def _remove_image(self) -> None:
        current_path = self.controls.setup_form.build_draft().appearance.image_stamp_path
        if current_path is not None and current_path in self._staged_image_paths:
            if self._image_store is not None:
                try:
                    self._image_store.delete_managed_image(current_path)
                except SignatureImageImportError as exc:
                    self._on_error(str(exc))
            self._staged_image_paths.discard(current_path)
        self.controls.setup_form.set_image_stamp_path(None)

    def _mark_dirty(self) -> None:
        if self._suspend_updates:
            return
        self._dirty = True
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        if not hasattr(self, "controls"):
            return
        appearance = self.controls.setup_form.build_draft().appearance
        signer_label = appearance.signer_label_prefix or "Digitally signed by"
        layout = appearance.layout_template.value.replace("_", " ").title()
        stamp = appearance.stamp_position.value.replace("_", " ").title()
        has_image = appearance.image_stamp_path is not None
        _set_text(
            self.controls.sample_preview_label,
            "Sample preview (synthetic data — never saved)\n"
            "Sample signer: Ada Example\n"
            f"{signer_label} Ada Example\n"
            f"Layout: {layout} · Image position: {stamp}\n"
            f"Image: {'selected' if has_image else 'none'}\n"
            "This preview uses synthetic data and is never persisted.",
        )
        self._refresh_preview_image(appearance.image_stamp_path)

    def refresh_preview_after_mount(self) -> None:
        """Apply preview visibility after the host becomes visible in the Library."""

        self._refresh_preview()

    def _refresh_preview_image(self, image_path: str | None) -> None:
        preview_image = self.controls.sample_preview_image
        if not image_path:
            set_visible = getattr(preview_image, "setVisible", None)
            if callable(set_visible):
                set_visible(False)
            return
        pixmap_factory = getattr(self._bindings, "q_pixmap", None)
        if not callable(pixmap_factory):
            return
        pixmap = pixmap_factory(image_path)
        is_null = getattr(pixmap, "isNull", None)
        if image_path and callable(is_null) and not is_null():
            scaled = getattr(pixmap, "scaled", None)
            if callable(scaled):
                qt = getattr(self._bindings, "qt", None)
                aspect = getattr(qt, "KeepAspectRatio", None)
                transform = getattr(qt, "SmoothTransformation", None)
                args = [240, 96]
                if aspect is not None:
                    args.append(aspect)
                if transform is not None:
                    args.append(transform)
                pixmap = scaled(*args)
            set_pixmap = getattr(preview_image, "setPixmap", None)
            if callable(set_pixmap):
                set_pixmap(pixmap)
            set_visible = getattr(preview_image, "setVisible", None)
            if callable(set_visible):
                set_visible(True)
            return
        set_visible = getattr(preview_image, "setVisible", None)
        if callable(set_visible):
            set_visible(False)


def _set_text(widget: Any, value: str) -> None:
    setter = getattr(widget, "setText", None)
    if callable(setter):
        setter(value)


__all__ = ["AppearanceProfileEditorWidget", "AppearanceProfileEditorWidgetControls"]
