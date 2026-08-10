import pytest

from foliaseal.application.document_safety import (
    LinkDecisionKind,
    LinkInteractionMode,
    SourceChangeAction,
    SourceChangeStatus,
    classify_link_destination,
    source_change_decision,
)


def test_internal_page_destination_is_allowed_without_external_launcher() -> None:
    decision = classify_link_destination("#page=3", internal_page_index=2)

    assert decision.kind is LinkDecisionKind.ALLOW_INTERNAL
    assert decision.page_index == 2
    assert decision.destination == "#page=3"
    assert decision.launcher is None


def test_internal_page_destination_without_raw_uri_is_allowed() -> None:
    decision = classify_link_destination(None, internal_page_index=2)

    assert decision.kind is LinkDecisionKind.ALLOW_INTERNAL
    assert decision.page_index == 2
    assert decision.destination == ""
    assert decision.launcher is None


def test_https_destination_requires_confirmation_and_has_no_launcher() -> None:
    decision = classify_link_destination(" HTTPS://example.test/review ")

    assert decision.kind is LinkDecisionKind.CONFIRM_EXTERNAL
    assert decision.destination == "HTTPS://example.test/review"
    assert decision.page_index is None
    assert decision.launcher is None


@pytest.mark.parametrize("destination", ["mailto:review@example.test", "http://example.test"])
def test_allowed_external_schemes_require_confirmation(destination: str) -> None:
    decision = classify_link_destination(destination)

    assert decision.kind is LinkDecisionKind.CONFIRM_EXTERNAL
    assert decision.reason is not None


@pytest.mark.parametrize(
    "destination",
    [
        "file:///tmp/secret.pdf",
        "javascript:alert(1)",
        "launch:program",
        "gopher://example.test",
        "",
    ],
)
def test_unsafe_unknown_and_empty_destinations_are_blocked(destination: str) -> None:
    decision = classify_link_destination(destination)

    assert decision.kind is LinkDecisionKind.BLOCK
    assert decision.page_index is None
    assert decision.launcher is None


@pytest.mark.parametrize("page_index", [-1, None])
def test_internal_destination_without_valid_page_index_is_blocked(page_index: int | None) -> None:
    decision = classify_link_destination("#page=3", internal_page_index=page_index)

    assert decision.kind is LinkDecisionKind.BLOCK


def test_unchanged_source_has_no_banner_action() -> None:
    decision = source_change_decision(
        exists=True,
        observed_fingerprint=("input.pdf", 1),
        current_fingerprint=("input.pdf", 1),
    )

    assert decision.status is SourceChangeStatus.UNCHANGED
    assert decision.action == "none"


def test_changed_source_offers_reload_or_ignore_without_auto_reload() -> None:
    decision = source_change_decision(
        exists=True,
        observed_fingerprint=("input.pdf", 1),
        current_fingerprint=("input.pdf", 2),
    )

    assert decision.status is SourceChangeStatus.CHANGED
    assert decision.action == "reload_or_ignore"


def test_missing_source_offers_locate_or_close() -> None:
    decision = source_change_decision(
        exists=False,
        observed_fingerprint=("input.pdf", 1),
        current_fingerprint=None,
    )

    assert decision.status is SourceChangeStatus.MISSING
    assert decision.action == "locate_or_close"


@pytest.mark.parametrize(
    "observed_fingerprint,current_fingerprint",
    [(None, None), (None, ("input.pdf", 1)), (("input.pdf", 1), None)],
)
def test_unmeasured_existing_source_requires_review(
    observed_fingerprint: tuple[object, ...] | None,
    current_fingerprint: tuple[object, ...] | None,
) -> None:
    decision = source_change_decision(
        exists=True,
        observed_fingerprint=observed_fingerprint,
        current_fingerprint=current_fingerprint,
    )

    assert decision.status is SourceChangeStatus.UNKNOWN
    assert decision.action is SourceChangeAction.REVIEW_REQUIRED


@pytest.mark.parametrize(
    "mode",
    [LinkInteractionMode.SELECT_TEXT, LinkInteractionMode.PLACE_SIGNATURE],
)
def test_select_and_place_modes_block_link_activation(mode: LinkInteractionMode) -> None:
    decision = classify_link_destination("#page=2", internal_page_index=1, interaction_mode=mode)

    assert decision.kind is LinkDecisionKind.BLOCK
    assert decision.reason == "Links activate only in Pan mode."


@pytest.mark.parametrize("destination", ["", "//example.test/path", "http ://example.test"])
def test_malformed_internal_destinations_are_blocked(destination: str) -> None:
    decision = classify_link_destination(destination, internal_page_index=1)

    assert decision.kind is LinkDecisionKind.BLOCK


def test_display_destination_is_bounded_and_has_no_control_characters() -> None:
    decision = classify_link_destination("https://example.test/\x00\x7f\x85" + "x" * 600)

    assert decision.kind is LinkDecisionKind.CONFIRM_EXTERNAL
    assert len(decision.destination) <= 512
    assert all(
        not (ord(character) < 32 or 0x7F <= ord(character) <= 0x9F)
        for character in decision.destination
    )
