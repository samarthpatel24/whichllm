"""Tests for shared utilities."""

from pathlib import Path

from whichllm.utils import _cache_dir


def test_cache_dir_defaults_to_dot_cache(monkeypatch):
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    result = _cache_dir()
    assert result == Path.home() / ".cache" / "whichllm"


def test_cache_dir_respects_xdg_cache_home(monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", "/tmp/custom-cache")
    result = _cache_dir()
    assert result == Path("/tmp/custom-cache/whichllm")


def test_cache_dir_falls_back_on_empty_xdg(monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", "")
    result = _cache_dir()
    assert result == Path.home() / ".cache" / "whichllm"


def test_cache_dir_ignores_relative_xdg(monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", "relative/path")
    result = _cache_dir()
    assert result == Path.home() / ".cache" / "whichllm"
