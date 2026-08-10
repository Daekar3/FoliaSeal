from pathlib import Path

import pytest

from foliaseal.application.help_catalog import HelpCatalog, HelpTopicError


def test_default_help_catalog_lists_stable_topics_and_exact_markdown() -> None:
    catalog = HelpCatalog.default()

    assert [topic.topic_id for topic in catalog.list_topics()] == [
        "getting-started",
        "signing-basics",
        "certificates",
        "privacy",
        "troubleshooting",
    ]
    markdown = catalog.markdown("signing-basics")
    assert markdown == catalog.topic("signing-basics").markdown
    assert "# Signing basics" in markdown
    assert catalog.topic("signing-basics").related == ("certificates", "troubleshooting")


def test_help_catalog_rejects_unknown_topic() -> None:
    catalog = HelpCatalog.default()

    with pytest.raises(HelpTopicError, match="Unknown help topic: missing"):
        catalog.topic("missing")


def test_help_catalog_exposes_packaged_topic_path() -> None:
    path = HelpCatalog.default().topic_path("getting-started")

    assert isinstance(path, Path)
    assert path.is_file()
