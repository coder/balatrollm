"""Unit tests for the cli module."""

from pathlib import Path

import pytest

from balatrollm.cli import BALATROLLM_CONFIG_ENV, _resolve_config_path

# ============================================================================
# Test _resolve_config_path
# ============================================================================


class TestResolveConfigPath:
    """Tests for _resolve_config_path helper function."""

    def test_cli_arg_returns_arg(self) -> None:
        """CLI argument should be returned when provided."""
        cli_path = Path("/some/config.yaml")
        result = _resolve_config_path(cli_path)
        assert result == cli_path

    def test_env_var_used_when_no_cli_arg(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """BALATROLLM_CONFIG env var should be used when CLI arg is None."""
        monkeypatch.setenv(BALATROLLM_CONFIG_ENV, "/env/config.yaml")
        result = _resolve_config_path(None)
        assert result == Path("/env/config.yaml")

    def test_cli_arg_takes_precedence_over_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CLI argument should take precedence over BALATROLLM_CONFIG env var."""
        monkeypatch.setenv(BALATROLLM_CONFIG_ENV, "/env/config.yaml")
        cli_path = Path("/cli/config.yaml")
        result = _resolve_config_path(cli_path)
        assert result == cli_path

    def test_none_when_no_cli_arg_and_no_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """None should be returned when neither CLI arg nor env var is set."""
        monkeypatch.delenv(BALATROLLM_CONFIG_ENV, raising=False)
        result = _resolve_config_path(None)
        assert result is None

    def test_empty_env_var_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty BALATROLLM_CONFIG env var should be treated as unset."""
        monkeypatch.setenv(BALATROLLM_CONFIG_ENV, "")
        result = _resolve_config_path(None)
        assert result is None
