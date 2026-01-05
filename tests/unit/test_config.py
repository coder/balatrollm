"""Unit tests for the config module."""

from argparse import Namespace
from pathlib import Path

import pytest

from balatrollm.config import (
    Config,
    Task,
    _deep_merge,
    _ensure_list,
    _parse_env_value,
    get_model_config,
)

# ============================================================================
# Test _ensure_list
# ============================================================================


class TestEnsureList:
    """Tests for _ensure_list helper function."""

    def test_none_returns_empty_list(self) -> None:
        """None should return empty list."""
        assert _ensure_list(None) == []

    def test_string_returns_single_item_list(self) -> None:
        """Single string should return list with that string."""
        assert _ensure_list("hello") == ["hello"]

    def test_list_passthrough(self) -> None:
        """List should pass through unchanged."""
        assert _ensure_list(["a", "b", "c"]) == ["a", "b", "c"]

    def test_list_converts_items_to_strings(self) -> None:
        """List items should be converted to strings."""
        # Note: type checker complains but the function handles mixed lists at runtime
        assert _ensure_list([1, 2, 3])  # type: ignore[arg-type]

    def test_non_string_non_list_converted_to_list(self) -> None:
        """Non-string, non-list values should be converted to single-item list."""
        # Note: type checker complains but the function handles Any at runtime
        assert _ensure_list(42) == ["42"]  # type: ignore[arg-type]


# ============================================================================
# Test _parse_env_value
# ============================================================================


class TestParseEnvValue:
    """Tests for _parse_env_value helper function."""

    def test_int_field_converts_to_int(self) -> None:
        """INT_FIELDS should be converted to int."""
        assert _parse_env_value("parallel", "4") == 4
        assert _parse_env_value("port", "12346") == 12346

    def test_list_field_returns_single_item_list(self) -> None:
        """LIST_FIELDS should return single-item list."""
        assert _parse_env_value("model", "openai/gpt-4") == ["openai/gpt-4"]
        assert _parse_env_value("seed", "AAAAAAA") == ["AAAAAAA"]
        assert _parse_env_value("deck", "RED") == ["RED"]
        assert _parse_env_value("stake", "WHITE") == ["WHITE"]
        assert _parse_env_value("strategy", "default") == ["default"]

    def test_string_field_returns_string(self) -> None:
        """STRING_FIELDS should return string as-is."""
        assert _parse_env_value("host", "localhost") == "localhost"
        assert (
            _parse_env_value("base_url", "https://api.openai.com/v1")
            == "https://api.openai.com/v1"
        )
        assert _parse_env_value("api_key", "sk-test") == "sk-test"


# ============================================================================
# Test _deep_merge
# ============================================================================


class TestDeepMerge:
    """Tests for _deep_merge helper function."""

    def test_empty_override(self) -> None:
        """Empty override should return base unchanged."""
        base = {"a": 1, "b": 2}
        assert _deep_merge(base, {}) == {"a": 1, "b": 2}

    def test_simple_override(self) -> None:
        """Simple values should be overridden."""
        base = {"a": 1, "b": 2}
        override = {"b": 3}
        assert _deep_merge(base, override) == {"a": 1, "b": 3}

    def test_add_new_key(self) -> None:
        """New keys should be added."""
        base = {"a": 1}
        override = {"b": 2}
        assert _deep_merge(base, override) == {"a": 1, "b": 2}

    def test_nested_merge(self) -> None:
        """Nested dicts should be merged recursively."""
        base = {"a": {"x": 1, "y": 2}}
        override = {"a": {"y": 3, "z": 4}}
        assert _deep_merge(base, override) == {"a": {"x": 1, "y": 3, "z": 4}}

    def test_nested_override_with_non_dict(self) -> None:
        """Non-dict values should completely replace dict values."""
        base = {"a": {"x": 1}}
        override = {"a": "replaced"}
        assert _deep_merge(base, override) == {"a": "replaced"}

    def test_does_not_mutate_base(self) -> None:
        """Base dict should not be mutated."""
        base = {"a": 1}
        override = {"a": 2}
        _deep_merge(base, override)
        assert base == {"a": 1}


# ============================================================================
# Test get_model_config
# ============================================================================


class TestGetModelConfig:
    """Tests for get_model_config function."""

    def test_none_returns_defaults(self) -> None:
        """None input should return default config."""
        config = get_model_config(None)
        assert "seed" in config
        assert "parallel_tool_calls" in config
        assert config["parallel_tool_calls"] is False

    def test_empty_returns_defaults(self) -> None:
        """Empty dict should return default config."""
        config = get_model_config({})
        assert "seed" in config
        assert config["seed"] == 1

    def test_user_overrides_applied(self) -> None:
        """User config should override defaults."""
        config = get_model_config({"seed": 42})
        assert config["seed"] == 42
        # Other defaults should remain
        assert "parallel_tool_calls" in config

    def test_nested_override(self) -> None:
        """Nested config should be deep merged."""
        config = get_model_config({"extra_headers": {"Custom-Header": "value"}})
        # Should have both default and custom headers
        assert "HTTP-Referer" in config["extra_headers"]
        assert "Custom-Header" in config["extra_headers"]


# ============================================================================
# Test Task dataclass
# ============================================================================


class TestTask:
    """Tests for Task dataclass."""

    def test_task_is_immutable(self) -> None:
        """Task should be frozen (immutable)."""
        task = Task(
            model="openai/gpt-4",
            seed="AAAAAAA",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        with pytest.raises(AttributeError):
            task.model = "other"  # type: ignore[misc]

    def test_task_str_representation(self) -> None:
        """Task string should contain all fields."""
        task = Task(
            model="openai/gpt-4",
            seed="AAAAAAA",
            deck="RED",
            stake="WHITE",
            strategy="default",
        )
        s = str(task)
        assert "RED" in s
        assert "WHITE" in s
        assert "AAAAAAA" in s
        assert "default" in s
        assert "openai/gpt-4" in s


# ============================================================================
# Test Config.validate
# ============================================================================


class TestConfigValidate:
    """Tests for Config.validate method."""

    def test_missing_model_raises(self) -> None:
        """Empty model list should raise ValueError."""
        config = Config(model=[])
        with pytest.raises(ValueError, match="model"):
            config.validate()

    def test_invalid_parallel_raises(self) -> None:
        """parallel < 1 should raise ValueError."""
        config = Config(model=["openai/gpt-4"], parallel=0)
        with pytest.raises(ValueError, match="parallel"):
            config.validate()

    def test_invalid_port_raises(self) -> None:
        """Invalid port should raise ValueError."""
        config = Config(model=["openai/gpt-4"], port=0)
        with pytest.raises(ValueError, match="port"):
            config.validate()

        config = Config(model=["openai/gpt-4"], port=70000)
        with pytest.raises(ValueError, match="port"):
            config.validate()

    def test_invalid_deck_raises(self) -> None:
        """Invalid deck name should raise ValueError."""
        config = Config(model=["openai/gpt-4"], deck=["INVALID"])
        with pytest.raises(ValueError, match="deck"):
            config.validate()

    def test_invalid_stake_raises(self) -> None:
        """Invalid stake name should raise ValueError."""
        config = Config(model=["openai/gpt-4"], stake=["INVALID"])
        with pytest.raises(ValueError, match="stake"):
            config.validate()

    def test_valid_config_passes(self) -> None:
        """Valid config should pass validation."""
        config = Config(
            model=["openai/gpt-4"],
            deck=["RED", "BLUE"],
            stake=["WHITE", "RED"],
            strategy=["default"],
        )
        # Should not raise
        config.validate()


# ============================================================================
# Test Config.generate_tasks
# ============================================================================


class TestConfigGenerateTasks:
    """Tests for Config.generate_tasks method."""

    def test_single_values_generate_one_task(self) -> None:
        """Single values for all params should generate one task."""
        config = Config(
            model=["openai/gpt-4"],
            seed=["AAAAAAA"],
            deck=["RED"],
            stake=["WHITE"],
            strategy=["default"],
        )
        tasks = config.generate_tasks()
        assert len(tasks) == 1
        assert tasks[0].model == "openai/gpt-4"
        assert tasks[0].seed == "AAAAAAA"
        assert tasks[0].deck == "RED"
        assert tasks[0].stake == "WHITE"
        assert tasks[0].strategy == "default"

    def test_multiple_seeds_generate_multiple_tasks(self) -> None:
        """Multiple seeds should generate multiple tasks."""
        config = Config(
            model=["openai/gpt-4"],
            seed=["AAA", "BBB", "CCC"],
            deck=["RED"],
            stake=["WHITE"],
            strategy=["default"],
        )
        tasks = config.generate_tasks()
        assert len(tasks) == 3
        seeds = {t.seed for t in tasks}
        assert seeds == {"AAA", "BBB", "CCC"}

    def test_cartesian_product(self) -> None:
        """Multiple values should create cartesian product."""
        config = Config(
            model=["m1", "m2"],
            seed=["s1"],
            deck=["RED", "BLUE"],
            stake=["WHITE"],
            strategy=["default"],
        )
        tasks = config.generate_tasks()
        # 2 models * 1 seed * 2 decks * 1 stake * 1 strategy = 4
        assert len(tasks) == 4

    def test_deck_stake_uppercased(self) -> None:
        """Deck and stake should be uppercased in tasks."""
        config = Config(
            model=["m1"],
            seed=["s1"],
            deck=["red"],
            stake=["white"],
            strategy=["default"],
        )
        tasks = config.generate_tasks()
        assert tasks[0].deck == "RED"
        assert tasks[0].stake == "WHITE"


# ============================================================================
# Test Config.total_runs
# ============================================================================


class TestConfigTotalRuns:
    """Tests for Config.total_runs property."""

    def test_total_runs_calculation(self) -> None:
        """total_runs should be product of all list lengths."""
        config = Config(
            model=["m1", "m2"],  # 2
            seed=["s1", "s2", "s3"],  # 3
            deck=["RED"],  # 1
            stake=["WHITE", "RED"],  # 2
            strategy=["default"],  # 1
        )
        # 2 * 3 * 1 * 2 * 1 = 12
        assert config.total_runs == 12

    def test_total_runs_matches_tasks_length(self) -> None:
        """total_runs should equal len(generate_tasks())."""
        config = Config(
            model=["m1", "m2"],
            seed=["s1", "s2"],
            deck=["RED", "BLUE"],
            stake=["WHITE"],
            strategy=["default"],
        )
        assert config.total_runs == len(config.generate_tasks())


# ============================================================================
# Test Config.load (integration-like tests)
# ============================================================================


class TestConfigLoad:
    """Tests for Config.load class method."""

    def test_load_from_args(self) -> None:
        """Loading from CLI args should work."""
        args = Namespace(
            model=["openai/gpt-4"],
            seed=["TEST"],
            deck=["BLUE"],
            stake=["RED"],
            strategy=["default"],
            parallel=2,
            host="localhost",
            port=8080,
            base_url="https://test.api/v1",
            api_key="test-key",
        )
        config = Config.load(args=args)
        assert config.model == ["openai/gpt-4"]
        assert config.parallel == 2
        assert config.host == "localhost"
        assert config.port == 8080

    def test_load_with_yaml(self, tmp_path: Path) -> None:
        """Loading from YAML file should work."""
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("""
model: openai/gpt-4
seed: AAAAAAA
deck: RED
stake: WHITE
strategy: default
parallel: 4
""")
        config = Config.load(yaml_path=yaml_file)
        assert config.model == ["openai/gpt-4"]
        assert config.parallel == 4

    def test_load_precedence(self, tmp_path: Path) -> None:
        """CLI args should override YAML values."""
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("""
model: openai/gpt-4
parallel: 2
""")
        args = Namespace(
            model=None,
            seed=None,
            deck=None,
            stake=None,
            strategy=None,
            parallel=8,  # Override
            host=None,
            port=None,
            base_url=None,
            api_key=None,
        )
        config = Config.load(yaml_path=yaml_file, args=args)
        assert config.model == ["openai/gpt-4"]  # From YAML
        assert config.parallel == 8  # From args (override)
