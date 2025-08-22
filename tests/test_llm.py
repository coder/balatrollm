"""Tests for LLM bot functionality."""

import os
from unittest.mock import Mock, patch

import pytest

from balatrollm.llm import Config, LLMBot


class TestConfig:
    """Tests for Config dataclass."""

    def test_config_creation(self):
        """Test basic config creation."""
        config = Config(model="test-model")
        assert config.model == "test-model"
        assert config.proxy_url == "http://localhost:4000"
        assert config.api_key == "sk-balatrollm-proxy-key"
        assert config.template == "default"

    def test_config_from_environment(self):
        """Test config creation from environment variables."""
        with patch.dict(
            os.environ,
            {
                "LITELLM_MODEL": "env-model",
                "LITELLM_PROXY_URL": "http://env:5000",
                "LITELLM_API_KEY": "env-key",
                "BALATROLLM_TEMPLATE": "aggressive",
            },
        ):
            config = Config.from_environment()
            assert config.model == "env-model"
            assert config.proxy_url == "http://env:5000"
            assert config.api_key == "env-key"
            assert config.template == "aggressive"

    def test_config_from_environment_defaults(self):
        """Test config uses defaults when environment variables not set."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config.from_environment()
            assert config.model == "cerebras-gpt-oss-120b"
            assert config.proxy_url == "http://localhost:4000"
            assert config.api_key == "sk-balatrollm-proxy-key"
            assert config.template == "default"


class TestLLMBot:
    """Tests for LLMBot class."""

    @pytest.fixture
    def config(self):
        """Test configuration."""
        return Config(model="test-model")

    @pytest.fixture
    def mock_balatro_client(self):
        """Mock BalatroClient."""
        with patch("balatrollm.llm.BalatroClient") as mock:
            yield mock.return_value

    @pytest.fixture
    def bot(self, config, mock_balatro_client):
        """Test bot instance."""
        with patch("balatrollm.llm.AsyncOpenAI"):
            return LLMBot(config)

    def test_bot_initialization(self, config):
        """Test bot initializes correctly."""
        with (
            patch("balatrollm.llm.AsyncOpenAI") as mock_openai,
            patch("balatrollm.llm.BalatroClient") as mock_client,
        ):
            bot = LLMBot(config)

            assert bot.config == config
            mock_openai.assert_called_once_with(
                api_key=config.api_key, base_url=f"{config.proxy_url}/v1"
            )
            mock_client.assert_called_once()

    def test_generate_save_path(self, bot):
        """Test save path generation."""
        with patch.object(bot, "project_version", "1.0.0"):
            path = bot._generate_save_path("Red Deck", 1, "TEST123")

            assert "v1.0.0" in str(path)
            assert "test-model" in str(path)
            assert "default" in str(path)
            assert "RedDeck" in str(path)
            assert "s1" in str(path)
            assert "TEST123" in str(path)
            assert path.suffix == ".jsonl"

    def test_get_tools_for_state(self, bot):
        """Test tools selection for different states."""
        from balatrobot.enums import State

        # Mock tools data
        test_tools = {
            "BLIND_SELECT": [{"type": "function", "function": {"name": "test_tool"}}],
            "SELECTING_HAND": [
                {"type": "function", "function": {"name": "test_tool2"}}
            ],
        }
        bot.tools = test_tools

        blind_tools = bot._get_tools_for_state(State.BLIND_SELECT)
        assert blind_tools == test_tools["BLIND_SELECT"]

        hand_tools = bot._get_tools_for_state(State.SELECTING_HAND)
        assert hand_tools == test_tools["SELECTING_HAND"]

    def test_get_tools_for_invalid_state(self, bot):
        """Test error handling for invalid state."""
        from balatrobot.enums import State

        bot.tools = {}

        with pytest.raises(ValueError, match="No tools defined for state"):
            bot._get_tools_for_state(State.BLIND_SELECT)

    @pytest.mark.asyncio
    async def test_validate_proxy_connection_success(self, bot):
        """Test successful proxy connection validation."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await bot.validate_proxy_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_proxy_connection_failure(self, bot):
        """Test failed proxy connection validation."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await bot.validate_proxy_connection()
            assert result is False

    def test_execute_tool_call(self, bot, mock_balatro_client):
        """Test tool call execution."""
        # Mock tool call
        mock_tool_call = Mock()
        mock_function = Mock()
        mock_function.name = "test_action"
        mock_function.arguments = '{"param": "value"}'
        mock_tool_call.function = mock_function

        # Mock balatro client response
        expected_result = {"state": "new_state"}
        mock_balatro_client.send_message.return_value = expected_result

        result = bot.execute_tool_call(mock_tool_call)

        assert result == expected_result
        mock_balatro_client.send_message.assert_called_once_with(
            "test_action", {"param": "value"}
        )

    def test_execute_tool_call_invalid_json(self, bot):
        """Test tool call execution with invalid JSON."""
        mock_tool_call = Mock()
        mock_function = Mock()
        mock_function.name = "test_action"
        mock_function.arguments = "invalid json"
        mock_tool_call.function = mock_function

        with pytest.raises(ValueError, match="Invalid JSON in tool call arguments"):
            bot.execute_tool_call(mock_tool_call)
