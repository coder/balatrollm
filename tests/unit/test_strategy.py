"""Unit tests for the StrategyManager module."""

from typing import Any

import pytest

from balatrollm.strategy import StrategyManager
from tests.unit.conftest import load_unit_fixture, load_unit_golden


def get_mock_pack_playing_card(
    overrides: dict[str, object] | None = None,
) -> dict[str, Any]:
    """Factory for a pack playing card shaped like BalatroBot gamestate."""
    base: dict[str, Any] = {
        "id": 1,
        "key": "D_6",
        "set": "ENHANCED",
        "label": "Glass Card",
        "value": {
            "rank": "6",
            "suit": "D",
            "effect": "+6 chips X2 Mult 1 in 4 chance to destroy card",
        },
        "modifier": {
            "enhancement": "GLASS",
            "edition": "FOIL",
            "seal": "RED",
        },
        "state": {},
        "cost": {"buy": 1, "sell": 1},
    }
    return {**base, **(overrides or {})}


def get_mock_pack_opened_gamestate(
    overrides: dict[str, object] | None = None,
) -> dict[str, Any]:
    """Factory for SMODS_BOOSTER_OPENED gamestate with pack playing cards."""
    base: dict[str, Any] = {
        "state": "SMODS_BOOSTER_OPENED",
        "money": 10,
        "ante_num": 1,
        "round_num": 1,
        "deck": "RED",
        "stake": "WHITE",
        "seed": "AAAAAAA",
        "won": False,
        "round": {
            "hands_left": 4,
            "discards_left": 3,
            "hands_played": 0,
            "discards_used": 0,
            "chips": 0,
            "reroll_cost": 5,
        },
        "jokers": {"count": 0, "limit": 5, "cards": []},
        "consumables": {"count": 0, "limit": 2, "cards": []},
        "hand": {"count": 0, "limit": 8, "cards": [], "highlighted_limit": 5},
        "shop": {"count": 0, "limit": 2, "cards": []},
        "packs": {"count": 0, "limit": 2, "cards": []},
        "vouchers": {"count": 0, "limit": 1, "cards": []},
        "pack": {
            "count": 1,
            "limit": 3,
            "cards": [get_mock_pack_playing_card()],
        },
        "hands": {},
        "blinds": {
            "small": {"name": "Small Blind", "score": 300, "status": "Upcoming"},
            "big": {"name": "Big Blind", "score": 450, "status": "Upcoming"},
            "boss": {"name": "The Hook", "score": 600, "status": "Upcoming"},
        },
    }
    return {**base, **(overrides or {})}


class TestStrategyManagerInit:
    """Tests for StrategyManager initialization."""

    def test_init_with_default_strategy(self) -> None:
        """Verify default strategy loads successfully."""
        sm = StrategyManager("default")
        assert sm.path.exists()

    def test_init_with_nonexistent_strategy_raises(self) -> None:
        """Verify FileNotFoundError for missing strategy."""
        with pytest.raises(FileNotFoundError, match="Strategy not found"):
            StrategyManager("nonexistent_strategy_xyz")

    def test_init_loads_tools(self) -> None:
        """Verify TOOLS.json is loaded."""
        sm = StrategyManager("default")
        assert isinstance(sm._tools, dict)
        assert "SELECTING_HAND" in sm._tools
        assert "SHOP" in sm._tools
        assert "BLIND_SELECT" in sm._tools


class TestStrategyManagerGetTools:
    """Tests for get_tools() method."""

    def test_get_tools_selecting_hand(self) -> None:
        """Verify tools for SELECTING_HAND state."""
        sm = StrategyManager("default")
        tools = sm.get_tools("SELECTING_HAND")
        assert isinstance(tools, list)
        assert len(tools) > 0
        tool_names = [t["function"]["name"] for t in tools]
        assert "play" in tool_names
        assert "discard" in tool_names
        assert "rearrange" in tool_names
        assert "sell" in tool_names
        assert "use" in tool_names

    def test_get_tools_shop(self) -> None:
        """Verify tools for SHOP state."""
        sm = StrategyManager("default")
        tools = sm.get_tools("SHOP")
        tool_names = [t["function"]["name"] for t in tools]
        assert "buy" in tool_names
        assert "reroll" in tool_names
        assert "next_round" in tool_names
        assert "sell" in tool_names
        assert "use" in tool_names
        assert "rearrange" in tool_names

    def test_get_tools_blind_select(self) -> None:
        """Verify tools for BLIND_SELECT state."""
        sm = StrategyManager("default")
        tools = sm.get_tools("BLIND_SELECT")
        tool_names = [t["function"]["name"] for t in tools]
        assert "select" in tool_names
        assert "skip" in tool_names

    def test_get_tools_unknown_state_returns_empty(self) -> None:
        """Verify empty list for unknown state."""
        sm = StrategyManager("default")
        tools = sm.get_tools("UNKNOWN_STATE")
        assert tools == []


class TestRenderGamestateGolden:
    """Golden tests: compare full rendered output against expected files."""

    def test_selecting_hand_golden(self) -> None:
        """Verify SELECTING_HAND gamestate matches golden output."""
        gamestate = load_unit_fixture("strategy", "state-SELECTING_HAND")
        expected = load_unit_golden("strategy", "state-SELECTING_HAND", "gamestate")
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)
        assert result == expected

    def test_shop_golden(self) -> None:
        """Verify SHOP gamestate matches golden output."""
        gamestate = load_unit_fixture("strategy", "state-SHOP")
        expected = load_unit_golden("strategy", "state-SHOP", "gamestate")
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)
        assert result == expected

    def test_blind_select_golden(self) -> None:
        """Verify BLIND_SELECT gamestate matches golden output."""
        gamestate = load_unit_fixture("strategy", "state-BLIND_SELECT")
        expected = load_unit_golden("strategy", "state-BLIND_SELECT", "gamestate")
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)
        assert result == expected


class TestRenderStrategyGolden:
    """Golden tests for strategy template."""

    def test_strategy_golden(self) -> None:
        """Verify strategy template matches golden output."""
        gamestate = load_unit_fixture("strategy", "state-SELECTING_HAND")
        expected = load_unit_golden("strategy", "state-SELECTING_HAND", "strategy")
        sm = StrategyManager("default")
        result = sm.render_strategy(gamestate)
        assert result == expected


class TestRenderMemoryGolden:
    """Golden tests for memory template."""

    def test_memory_empty_golden(self) -> None:
        """Verify memory template with empty history matches golden output."""
        expected = load_unit_golden("strategy", "state-SELECTING_HAND", "memory")
        sm = StrategyManager("default")
        result = sm.render_memory(history=[])
        assert result == expected


class TestRenderGamestateProperties:
    """Property tests: verify semantic correctness of rendered output."""

    def test_state_name_appears_in_output(self) -> None:
        """Property: the state name must appear in rendered output."""
        for state in ["SELECTING_HAND", "SHOP", "BLIND_SELECT"]:
            gamestate = load_unit_fixture("strategy", f"state-{state}")
            sm = StrategyManager("default")
            result = sm.render_gamestate(gamestate)
            assert state in result, f"State {state} not found in output"

    def test_all_hand_cards_rendered(self) -> None:
        """Property: all hand cards appear with correct indices."""
        gamestate = load_unit_fixture("strategy", "state-SELECTING_HAND")
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        for i, card in enumerate(gamestate["hand"]["cards"]):
            assert f"- {i}:" in result, f"Card index {i} not found"
            assert card["key"] in result, f"Card key {card['key']} not found"

    def test_money_appears_in_output(self) -> None:
        """Property: current money appears in rendered output."""
        gamestate = load_unit_fixture("strategy", "state-SELECTING_HAND")
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        assert f"${gamestate['money']}" in result, "Money not found in output"

    def test_round_info_appears(self) -> None:
        """Property: hands/discards left appear in SELECTING_HAND state."""
        gamestate = load_unit_fixture("strategy", "state-SELECTING_HAND")
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        hands_left = gamestate["round"]["hands_left"]
        discards_left = gamestate["round"]["discards_left"]
        assert str(hands_left) in result, "Hands left not found"
        assert str(discards_left) in result, "Discards left not found"

    def test_shop_items_rendered(self) -> None:
        """Property: shop items appear in SHOP state."""
        gamestate = load_unit_fixture("strategy", "state-SHOP")
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        for i, item in enumerate(gamestate["shop"]["cards"]):
            assert f"- {i}:" in result, f"Shop item index {i} not found"
            assert item["label"] in result, f"Shop item {item['label']} not found"

    def test_blinds_rendered_in_blind_select(self) -> None:
        """Property: all blinds appear in BLIND_SELECT state."""
        gamestate = load_unit_fixture("strategy", "state-BLIND_SELECT")
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        for blind_type in ["small", "big", "boss"]:
            blind = gamestate["blinds"][blind_type]
            assert blind["name"] in result, f"{blind_type} blind name not found"
            assert str(blind["score"]) in result, f"{blind_type} blind score not found"


class TestPackOpenSunkCostGuidance:
    """Opened packs already spent money; skip is not a refund."""

    @pytest.mark.parametrize("strategy", ["default", "conservative", "aggressive"])
    def test_strategy_teaches_pack_skip_does_not_refund(self, strategy: str) -> None:
        """Strategy text must state pack cost is sunk and skip does not refund."""
        gamestate = get_mock_pack_opened_gamestate()
        sm = StrategyManager(strategy)
        result = sm.render_strategy(gamestate)

        assert "already spent" in result.lower()
        assert "does not refund" in result.lower()

    @pytest.mark.parametrize("strategy", ["default", "conservative", "aggressive"])
    def test_pack_opened_gamestate_teaches_sunk_cost(self, strategy: str) -> None:
        """Pack-open gamestate must remind the LLM money is already spent."""
        gamestate = get_mock_pack_opened_gamestate()
        sm = StrategyManager(strategy)
        result = sm.render_gamestate(gamestate)

        assert "already spent" in result.lower()
        assert "does not refund" in result.lower()

    @pytest.mark.parametrize("strategy", ["default", "conservative", "aggressive"])
    def test_pack_tool_describes_skip_as_no_refund(self, strategy: str) -> None:
        """Pack tool description must say skipping does not refund the purchase."""
        sm = StrategyManager(strategy)
        tools = sm.get_tools("SMODS_BOOSTER_OPENED")
        pack_tool = next(t for t in tools if t["function"]["name"] == "pack")
        description = pack_tool["function"]["description"].lower()

        assert "does not refund" in description


class TestRenderPackPlayingCardModifiers:
    """Pack playing cards must render modifier fields from card.modifier."""

    @pytest.mark.parametrize("strategy", ["default", "conservative", "aggressive"])
    def test_pack_card_renders_enhancement_edition_and_seal(
        self, strategy: str
    ) -> None:
        """Opened Standard pack cards expose enhancement/edition/seal to the LLM."""
        gamestate = get_mock_pack_opened_gamestate()
        sm = StrategyManager(strategy)
        result = sm.render_gamestate(gamestate)

        assert "**GLASS Enhancement**" in result
        assert "**FOIL Edition**" in result
        assert "**RED Seal**" in result

    @pytest.mark.parametrize("strategy", ["default", "conservative", "aggressive"])
    def test_pack_hand_targeting_renders_enhancement(self, strategy: str) -> None:
        """Hand cards shown during pack targeting include enhancement."""
        hand_card = get_mock_pack_playing_card(
            {
                "id": 2,
                "key": "H_A",
                "set": "ENHANCED",
                "label": "Steel Card",
                "value": {"rank": "A", "suit": "H", "effect": "X1.5 Mult"},
                "modifier": {"enhancement": "STEEL"},
            }
        )
        gamestate = get_mock_pack_opened_gamestate(
            {
                "hand": {
                    "count": 1,
                    "limit": 8,
                    "cards": [hand_card],
                    "highlighted_limit": 5,
                }
            }
        )
        sm = StrategyManager(strategy)
        result = sm.render_gamestate(gamestate)

        assert "Your Hand (for targeting)" in result
        assert "(STEEL)" in result


class TestRenderMemoryProperties:
    """Property tests for memory template."""

    def test_history_actions_appear(self) -> None:
        """Property: all history actions appear in memory output."""
        sm = StrategyManager("default")
        history: list[dict[str, str | dict[str, list[int]]]] = [
            {"method": "play", "params": {"cards": [0, 1]}, "reasoning": "Test play"},
            {
                "method": "discard",
                "params": {"cards": [2]},
                "reasoning": "Test discard",
            },
        ]
        result = sm.render_memory(history=history)

        for entry in history:
            method = str(entry["method"])
            reasoning = str(entry["reasoning"])
            assert method in result
            assert reasoning in result

    def test_error_message_appears(self) -> None:
        """Property: error message appears when provided."""
        sm = StrategyManager("default")
        result = sm.render_memory(history=[], last_error="Test error message")
        assert "Test error message" in result

    def test_failure_message_appears(self) -> None:
        """Property: failure message appears when provided."""
        sm = StrategyManager("default")
        result = sm.render_memory(history=[], last_failure="Test failure message")
        assert "Test failure message" in result


class TestToolDefinitionStructure:
    """Tests for tool definition structure compliance."""

    def test_tools_have_openai_structure(self) -> None:
        """Verify tool definitions have OpenAI function calling structure."""
        sm = StrategyManager("default")

        for state in ["SELECTING_HAND", "SHOP", "BLIND_SELECT"]:
            tools = sm.get_tools(state)
            for tool in tools:
                assert tool["type"] == "function"
                assert "function" in tool
                assert "name" in tool["function"]
                assert "description" in tool["function"]
                assert "parameters" in tool["function"]
                assert tool["function"]["parameters"]["type"] == "object"

    def test_play_tool_has_required_params(self) -> None:
        """Verify play tool has cards and reasoning parameters."""
        sm = StrategyManager("default")
        tools = sm.get_tools("SELECTING_HAND")

        play_tool = next(t for t in tools if t["function"]["name"] == "play")
        params = play_tool["function"]["parameters"]["properties"]
        required = play_tool["function"]["parameters"]["required"]

        assert "cards" in params
        assert params["cards"]["type"] == "array"
        assert "reasoning" in params
        assert "cards" in required
        assert "reasoning" in required

    def test_buy_tool_has_optional_params(self) -> None:
        """Verify buy tool has card/voucher/pack as optional parameters."""
        sm = StrategyManager("default")
        tools = sm.get_tools("SHOP")

        buy_tool = next(t for t in tools if t["function"]["name"] == "buy")
        params = buy_tool["function"]["parameters"]["properties"]
        required = buy_tool["function"]["parameters"]["required"]

        assert "card" in params or "voucher" in params or "pack" in params
        assert "reasoning" in required
        assert "card" not in required
        assert "voucher" not in required
        assert "pack" not in required
