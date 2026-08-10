"""Qt-free access to FoliaSeal's packaged offline Help topics."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

_TOPIC_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_UNSAFE_MARKUP_PATTERN = re.compile(
    r"(?:https?://|//|javascript:|data:|file:|<script\b|QWebEngine|!\[)",
    re.IGNORECASE,
)


class HelpTopicError(ValueError):
    """Raised when a packaged Help catalog or topic cannot be used safely."""


@dataclass(frozen=True)
class HelpTopic:
    """One immutable canonical Help topic."""

    topic_id: str
    title: str
    keywords: tuple[str, ...]
    related: tuple[str, ...]
    markdown: str
    path: Path | None


class HelpCatalog:
    """Load and validate the immutable Markdown Help catalog."""

    def __init__(self, *, resource_package: str, index_name: str = "index.json") -> None:
        self._resource_package = resource_package
        self._root = resources.files(resource_package)
        self._topics = self._load_topics(index_name)

    @classmethod
    def default(cls) -> HelpCatalog:
        """Return the packaged FoliaSeal Help catalog."""

        return cls(resource_package="foliaseal.resources.help")

    def list_topics(self) -> tuple[HelpTopic, ...]:
        """Return topics in the stable order declared by the index."""

        return tuple(self._topics.values())

    def topic(self, topic_id: str) -> HelpTopic:
        """Return one topic or raise a stable user-facing error."""

        try:
            return self._topics[topic_id]
        except KeyError as exc:
            raise HelpTopicError(f"Unknown help topic: {topic_id}") from exc

    def markdown(self, topic_id: str) -> str:
        """Return canonical Markdown for one topic."""

        return self.topic(topic_id).markdown

    def topic_path(self, topic_id: str) -> Path | None:
        """Return a filesystem path when the resource loader exposes one."""

        return self.topic(topic_id).path

    def _load_topics(self, index_name: str) -> dict[str, HelpTopic]:
        try:
            index_text = self._root.joinpath(index_name).read_text(encoding="utf-8")
            raw_entries = json.loads(index_text)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise HelpTopicError("Unable to read the packaged Help index") from exc
        if not isinstance(raw_entries, list) or not raw_entries:
            raise HelpTopicError("Help index must contain a non-empty list")

        entries: dict[str, HelpTopic] = {}
        for raw_entry in raw_entries:
            entry = self._validate_entry(raw_entry)
            topic_id = entry["id"]
            if topic_id in entries:
                raise HelpTopicError(f"Duplicate help topic: {topic_id}")
            topic_resource = self._root.joinpath(entry["filename"])
            try:
                markdown = topic_resource.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise HelpTopicError(f"Unable to read help topic: {topic_id}") from exc
            if not markdown.strip() or _UNSAFE_MARKUP_PATTERN.search(markdown):
                raise HelpTopicError(f"Unsafe or empty help topic: {topic_id}")
            path = Path(topic_resource) if isinstance(topic_resource, Path) else None
            entries[topic_id] = HelpTopic(
                topic_id=topic_id,
                title=entry["title"],
                keywords=tuple(entry["keywords"]),
                related=tuple(entry["related"]),
                markdown=markdown,
                path=path,
            )

        known_ids = set(entries)
        for topic in entries.values():
            missing = set(topic.related) - known_ids
            if missing:
                missing_id = sorted(missing)[0]
                raise HelpTopicError(
                    f"Help topic {topic.topic_id} links to unknown topic: {missing_id}"
                )
        return entries

    @staticmethod
    def _validate_entry(raw_entry: Any) -> dict[str, Any]:
        if not isinstance(raw_entry, dict):
            raise HelpTopicError("Help index entries must be objects")
        required = {"id", "title", "keywords", "related", "filename"}
        if set(raw_entry) != required:
            raise HelpTopicError(
                "Help index entries must contain exactly id, title, keywords, related, filename"
            )
        topic_id = raw_entry["id"]
        title = raw_entry["title"]
        filename = raw_entry["filename"]
        keywords = raw_entry["keywords"]
        related = raw_entry["related"]
        if not isinstance(topic_id, str) or not _TOPIC_ID_PATTERN.fullmatch(topic_id):
            raise HelpTopicError(f"Invalid help topic id: {topic_id!r}")
        if not isinstance(title, str) or not title.strip():
            raise HelpTopicError(f"Invalid help title: {topic_id}")
        if (
            not isinstance(filename, str)
            or not filename.endswith(".md")
            or Path(filename).name != filename
        ):
            raise HelpTopicError(f"Invalid help filename: {topic_id}")
        if not isinstance(keywords, list) or not all(
            isinstance(keyword, str) and keyword.strip() for keyword in keywords
        ):
            raise HelpTopicError(f"Invalid help keywords: {topic_id}")
        if not isinstance(related, list) or not all(
            isinstance(related_id, str) and _TOPIC_ID_PATTERN.fullmatch(related_id)
            for related_id in related
        ):
            raise HelpTopicError(f"Invalid related Help topics: {topic_id}")
        return {
            "id": topic_id,
            "title": title,
            "keywords": keywords,
            "related": related,
            "filename": filename,
        }
