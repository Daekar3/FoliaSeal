"""Modeless, local-only Qt presentation for the packaged Help catalog."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from foliaseal.application.help_catalog import HelpCatalog, HelpTopicError


class HelpViewerDialog:
    """A searchable, keyboard-accessible Help window backed by one catalog."""

    MAX_HISTORY = 64

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        catalog: HelpCatalog | None = None,
        initial_topic_id: str = "getting-started",
        on_closed: Callable[[], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._catalog = catalog or HelpCatalog.default()
        self._on_closed = on_closed
        self._history: list[str] = []
        self._history_index = -1
        self._filtered_topic_ids: list[str] = []
        self._current_topic_id: str | None = None

        if bindings.q_text_browser is None or bindings.q_list_widget is None:
            raise RuntimeError("The Qt Help viewer requires QTextBrowser and QListWidget bindings.")

        self.dialog = bindings.q_dialog(parent)
        self.dialog.setWindowTitle("FoliaSeal Help")
        set_modal = getattr(self.dialog, "setModal", None)
        if callable(set_modal):
            set_modal(False)
        set_minimum_size = getattr(self.dialog, "setMinimumSize", None)
        if callable(set_minimum_size):
            set_minimum_size(760, 520)

        layout = bindings.q_vbox_layout(self.dialog)
        search_label = bindings.q_label("Search Help", self.dialog)
        self.search_input = bindings.q_line_edit(self.dialog)
        self.search_input.setPlaceholderText("Search topics")
        self.search_input.setAccessibleName("Search Help topics")
        search_label.setBuddy(self.search_input)
        layout.addWidget(search_label)
        layout.addWidget(self.search_input)

        splitter = bindings.q_splitter(self.dialog)
        topic_panel = bindings.q_widget(self.dialog)
        topic_layout = bindings.q_vbox_layout(topic_panel)
        topic_label = bindings.q_label("Topics", topic_panel)
        self.topic_list = bindings.q_list_widget(topic_panel)
        self.topic_list.setAccessibleName("Help topics")
        topic_layout.addWidget(topic_label)
        topic_layout.addWidget(self.topic_list)
        content_panel = bindings.q_widget(self.dialog)
        content_layout = bindings.q_vbox_layout(content_panel)
        self.content_browser = bindings.q_text_browser(content_panel)
        self.content_browser.setReadOnly(True)
        self.content_browser.setOpenExternalLinks(False)
        self.content_browser.setOpenLinks(False)
        self.content_browser.setAccessibleName("Help topic content")
        content_layout.addWidget(self.content_browser)
        splitter.addWidget(topic_panel)
        splitter.addWidget(content_panel)
        layout.addWidget(splitter)

        navigation = bindings.q_hbox_layout()
        self.back_button = bindings.q_push_button("Back", self.dialog)
        self.forward_button = bindings.q_push_button("Forward", self.dialog)
        self.close_button = bindings.q_push_button("Close", self.dialog)
        self.back_button.setAccessibleName("Go back in Help history")
        self.forward_button.setAccessibleName("Go forward in Help history")
        self.close_button.setAccessibleName("Close Help")
        navigation.addWidget(self.back_button)
        navigation.addWidget(self.forward_button)
        navigation.addStretch()
        navigation.addWidget(self.close_button)
        layout.addLayout(navigation)

        self.search_input.textChanged.connect(self._filter_topics)
        self.topic_list.currentRowChanged.connect(self._topic_row_changed)
        self.content_browser.anchorClicked.connect(self._handle_anchor)
        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)
        self.close_button.clicked.connect(self.dialog.close)
        finished = getattr(self.dialog, "finished", None)
        if finished is not None and hasattr(finished, "connect"):
            finished.connect(self._closed)
        set_tab_order = getattr(self.dialog, "setTabOrder", None)
        if callable(set_tab_order):
            set_tab_order(self.search_input, self.topic_list)
            set_tab_order(self.topic_list, self.content_browser)
            set_tab_order(self.content_browser, self.back_button)
            set_tab_order(self.back_button, self.forward_button)
            set_tab_order(self.forward_button, self.close_button)

        self._filter_topics("")
        self.show_topic(initial_topic_id, record=True)

    @property
    def current_topic_id(self) -> str | None:
        """Return the currently displayed stable topic id."""

        return self._current_topic_id

    def show(self) -> None:
        """Show and focus the modeless window."""

        self.dialog.show()
        raise_window = getattr(self.dialog, "raise_", None)
        if callable(raise_window):
            raise_window()
        activate = getattr(self.dialog, "activateWindow", None)
        if callable(activate):
            activate()
        self.search_input.setFocus()

    def show_topic(self, topic_id: str, *, record: bool = True) -> None:
        """Display one topic and optionally append it to local history."""

        topic = self._catalog.topic(topic_id)
        if record:
            self._record_history(topic_id)
        self._current_topic_id = topic_id
        self.content_browser.setMarkdown(topic.markdown)
        self._select_filtered_topic(topic_id)
        self._sync_navigation()

    def go_back(self) -> None:
        """Navigate to the previous topic in this window's local history."""

        if self._history_index <= 0:
            return
        self._history_index -= 1
        self.show_topic(self._history[self._history_index], record=False)

    def go_forward(self) -> None:
        """Navigate to the next topic in this window's local history."""

        if self._history_index >= len(self._history) - 1:
            return
        self._history_index += 1
        self.show_topic(self._history[self._history_index], record=False)

    def close(self) -> None:
        """Close the owned modeless dialog."""

        self.dialog.close()

    def _filter_topics(self, query: str) -> None:
        normalized = query.strip().casefold()
        topics = self._catalog.list_topics()
        self._filtered_topic_ids = [
            topic.topic_id
            for topic in topics
            if not normalized
            or normalized in topic.topic_id.casefold()
            or normalized in topic.title.casefold()
            or any(normalized in keyword.casefold() for keyword in topic.keywords)
        ]
        block_signals = getattr(self.topic_list, "blockSignals", None)
        if callable(block_signals):
            block_signals(True)
        self.topic_list.clear()
        for topic_id in self._filtered_topic_ids:
            self.topic_list.addItem(self._catalog.topic(topic_id).title)
        if self._filtered_topic_ids:
            current_id = self._current_topic_id
            row = (
                self._filtered_topic_ids.index(current_id)
                if current_id in self._filtered_topic_ids
                else 0
            )
            self.topic_list.setCurrentRow(row)
        if callable(block_signals):
            block_signals(False)
        if self._filtered_topic_ids and self._current_topic_id not in self._filtered_topic_ids:
            self.show_topic(self._filtered_topic_ids[0], record=True)

    def _topic_row_changed(self, row: int) -> None:
        if 0 <= row < len(self._filtered_topic_ids):
            topic_id = self._filtered_topic_ids[row]
            if topic_id != self._current_topic_id:
                self.show_topic(topic_id, record=True)

    def _select_filtered_topic(self, topic_id: str) -> None:
        if topic_id not in self._filtered_topic_ids:
            return
        row = self._filtered_topic_ids.index(topic_id)
        block_signals = getattr(self.topic_list, "blockSignals", None)
        if callable(block_signals):
            block_signals(True)
        self.topic_list.setCurrentRow(row)
        if callable(block_signals):
            block_signals(False)

    def _record_history(self, topic_id: str) -> None:
        if self._history_index >= 0 and self._history[self._history_index] == topic_id:
            return
        if self._history_index < len(self._history) - 1:
            self._history = self._history[: self._history_index + 1]
        self._history.append(topic_id)
        if len(self._history) > self.MAX_HISTORY:
            self._history.pop(0)
        self._history_index = len(self._history) - 1

    def _sync_navigation(self) -> None:
        self.back_button.setEnabled(self._history_index > 0)
        self.forward_button.setEnabled(self._history_index < len(self._history) - 1)

    def _handle_anchor(self, url: Any) -> None:
        scheme = getattr(url, "scheme", lambda: "")()
        if scheme != "help":
            return
        topic_id = getattr(url, "path", lambda: "")().lstrip("/")
        if not topic_id:
            topic_id = getattr(url, "toString", lambda: "")().removeprefix("help:")
        try:
            self.show_topic(topic_id)
        except HelpTopicError:
            return

    def _closed(self) -> None:
        if self._on_closed is not None:
            self._on_closed()
