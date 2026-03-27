from pdf_signer.infra.render import RenderCacheKey, RenderCachePolicy, RenderPageResult


def _sample_result(seed: int) -> RenderPageResult:
    return RenderPageResult(width_px=10 + seed, height_px=20 + seed, rgba_bytes=b"x" * 4)


def test_render_cache_returns_stored_result_and_updates_lru_order() -> None:
    cache = RenderCachePolicy(max_entries=2)
    key_a = RenderCacheKey(document_path="a.pdf", page_index=0, zoom=1.0)
    key_b = RenderCacheKey(document_path="a.pdf", page_index=1, zoom=1.0)

    cache.put(key_a, _sample_result(1))
    cache.put(key_b, _sample_result(2))

    hit = cache.get(key_a)

    assert hit == _sample_result(1)
    assert cache.size == 2


def test_render_cache_evicts_least_recently_used_entry() -> None:
    cache = RenderCachePolicy(max_entries=2)
    key_a = RenderCacheKey(document_path="a.pdf", page_index=0, zoom=1.0)
    key_b = RenderCacheKey(document_path="a.pdf", page_index=1, zoom=1.0)
    key_c = RenderCacheKey(document_path="a.pdf", page_index=2, zoom=1.0)

    cache.put(key_a, _sample_result(1))
    cache.put(key_b, _sample_result(2))
    _ = cache.get(key_a)
    cache.put(key_c, _sample_result(3))

    assert cache.get(key_b) is None
    assert cache.get(key_a) == _sample_result(1)
    assert cache.get(key_c) == _sample_result(3)


def test_render_cache_can_clear_single_document_or_all_entries() -> None:
    cache = RenderCachePolicy(max_entries=4)
    cache.put(RenderCacheKey(document_path="a.pdf", page_index=0, zoom=1.0), _sample_result(1))
    cache.put(RenderCacheKey(document_path="b.pdf", page_index=0, zoom=1.0), _sample_result(2))

    cache.clear_document("a.pdf")

    assert cache.get(RenderCacheKey(document_path="a.pdf", page_index=0, zoom=1.0)) is None
    assert cache.get(
        RenderCacheKey(document_path="b.pdf", page_index=0, zoom=1.0)
    ) == _sample_result(2)

    cache.clear()

    assert cache.size == 0


def test_rejects_non_positive_cache_size() -> None:
    try:
        RenderCachePolicy(max_entries=0)
    except ValueError as exc:
        assert "max_entries" in str(exc)
    else:
        raise AssertionError("Expected ValueError for zero max_entries")
