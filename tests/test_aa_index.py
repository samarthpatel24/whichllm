"""Tests for Artificial Analysis Intelligence Index extraction."""

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from whichllm.models.benchmark_sources.aa_index import (
    _extract_rsc_pairs,
    fetch_aa_index_scores,
    get_aa_curated_fallback,
)
from whichllm.models.benchmark_sources.types import ExtractionFailed


def _make_rsc_html(*entries: tuple[str, str, float | None]) -> str:
    """Build minimal HTML with RSC push payloads wrapping a ``"models"`` array."""
    objs = []
    for name, slug, score in entries:
        score_val = "null" if score is None else str(score)
        objs.append(
            f'{{\\"name\\":\\"{name}\\",'
            f'\\"slug\\":\\"{slug}\\",'
            f'\\"intelligenceIndex\\":{score_val}}}'
        )
    deprecated_obj = (
        '{\\"name\\":\\"Old Model\\",'
        '\\"slug\\":\\"old-model\\",'
        '\\"deprecated\\":true,'
        '\\"intelligenceIndex\\":15.0}'
    )
    all_objs = ",".join([*objs, deprecated_obj])
    models = f'{{\\"models\\":[{all_objs}]}}'
    return f'<html><script>self.__next_f.push([1,"{models}"])</script></html>'


def test_rsc_format_extracts_scores():
    html = _make_rsc_html(
        ("Kimi K2", "kimi-k2", 47.0),
        ("DeepSeek V3", "deepseek-v3", 38.0),
    )
    pairs = _extract_rsc_pairs(html)
    names = {name for name, _ in pairs}
    assert "Kimi K2" in names
    assert "DeepSeek V3" in names
    scores = {name: score for name, score in pairs}
    assert scores["Kimi K2"] == 47.0
    assert scores["DeepSeek V3"] == 38.0


def test_rsc_no_pushes_returns_empty():
    html = "<html><body>nothing here</body></html>"
    assert _extract_rsc_pairs(html) == []


def test_deprecated_models_included():
    html = _make_rsc_html(("Active Model", "active", 40.0))
    pairs = _extract_rsc_pairs(html)
    names = {name for name, _ in pairs}
    assert "Old Model" in names


def test_null_score_not_borrowed_from_next_model():
    html = _make_rsc_html(
        ("Null Model", "null-model", None),
        ("Real Model", "real-model", 42.0),
    )
    pairs = _extract_rsc_pairs(html)
    scores = {name: score for name, score in pairs}
    assert "Null Model" not in scores
    assert scores["Real Model"] == 42.0


def test_missing_both_formats_raises():
    mock_resp = AsyncMock(spec=httpx.Response)
    mock_resp.text = "<html><body>no data</body></html>"
    mock_resp.raise_for_status = lambda: None

    client = AsyncMock(spec=httpx.AsyncClient)

    async def run():
        with patch(
            "whichllm.models.benchmark_sources.aa_index.get_with_retries",
            return_value=mock_resp,
        ):
            await fetch_aa_index_scores(client)

    with pytest.raises(ExtractionFailed, match="neither RSC.*nor __NEXT_DATA__"):
        asyncio.run(run())


def test_fallback_returns_normalized_scores():
    fallback = get_aa_curated_fallback()
    assert len(fallback) > 0
    for hf_id, score in fallback.items():
        assert 0.0 < score <= 100.0, f"{hf_id} score {score} out of range"
