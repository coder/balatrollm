"""Integration tests for StrategyManager card rendering edge cases.

These tests focus on card modifiers (editions, enhancements, seals) that require
real game state manipulation via the BalatroBot API.

Unit tests cover golden file comparisons and basic properties.
Integration tests cover dynamic card modifier rendering.
"""

import httpx
import pytest

from balatrollm.strategy import StrategyManager
from tests.conftest import api
from tests.integration.conftest import load_integration_fixture

# =============================================================================
# Playing Card Modifier Tests
# =============================================================================

EDITIONS = ["FOIL", "HOLO", "POLYCHROME", "NEGATIVE"]
ENHANCEMENTS = ["BONUS", "MULT", "WILD", "GLASS", "STEEL", "STONE", "GOLD", "LUCKY"]
SEALS = ["RED", "BLUE", "GOLD", "PURPLE"]


class TestPlayingCardModifiers:
    """Test playing card modifier rendering on hand cards."""

    @pytest.mark.parametrize("edition", EDITIONS)
    def test_render_hand_card_edition(self, client: httpx.Client, edition: str) -> None:
        """Verify edition is rendered on hand cards."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(client, "add", {"key": "H_A", "edition": edition})

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        assert f"**{edition} Edition**" in result

    @pytest.mark.parametrize("enhancement", ENHANCEMENTS)
    def test_render_hand_card_enhancement(
        self, client: httpx.Client, enhancement: str
    ) -> None:
        """Verify enhancement is rendered on hand cards."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(client, "add", {"key": "H_A", "enhancement": enhancement})

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        # STONE cards are rendered specially without Enhancement text
        if enhancement == "STONE":
            assert "this is a stone card" in result
        else:
            assert f"**{enhancement} Enhancement**" in result

    @pytest.mark.parametrize("seal", SEALS)
    def test_render_hand_card_seal(self, client: httpx.Client, seal: str) -> None:
        """Verify seal is rendered on hand cards."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(client, "add", {"key": "H_A", "seal": seal})

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        assert f"**{seal} Seal**" in result

    def test_render_edition_and_enhancement(self, client: httpx.Client) -> None:
        """Verify edition and enhancement render together on hand cards."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(client, "add", {"key": "H_A", "edition": "FOIL", "enhancement": "BONUS"})

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        assert "**FOIL Edition**" in result
        assert "**BONUS Enhancement**" in result

    def test_render_edition_and_seal(self, client: httpx.Client) -> None:
        """Verify edition and seal render together on hand cards."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(client, "add", {"key": "H_A", "edition": "HOLO", "seal": "RED"})

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        assert "**HOLO Edition**" in result
        assert "**RED Seal**" in result

    def test_render_all_modifiers_on_hand_card(self, client: httpx.Client) -> None:
        """Verify edition, enhancement, and seal all render together on hand cards."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(
            client,
            "add",
            {
                "key": "H_A",
                "edition": "POLYCHROME",
                "enhancement": "GLASS",
                "seal": "GOLD",
            },
        )

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        assert "**POLYCHROME Edition**" in result
        assert "**GLASS Enhancement**" in result
        assert "**GOLD Seal**" in result

    def test_render_multiple_modified_cards(self, client: httpx.Client) -> None:
        """Verify multiple cards with different modifiers render correctly."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(client, "add", {"key": "H_A", "edition": "FOIL"})
        api(client, "add", {"key": "D_K", "enhancement": "MULT"})
        api(client, "add", {"key": "S_Q", "seal": "BLUE"})

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        assert "**FOIL Edition**" in result
        assert "**MULT Enhancement**" in result
        assert "**BLUE Seal**" in result


# =============================================================================
# Joker Modifiers
# =============================================================================


class TestJokerModifiers:
    """Test joker special modifiers (eternal, perishable, rental)."""

    @pytest.mark.parametrize("edition", EDITIONS)
    def test_render_joker_edition(self, client: httpx.Client, edition: str) -> None:
        """Verify edition is rendered on jokers."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(client, "add", {"key": "j_joker", "edition": edition})

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        # Verify in jokers section
        assert f"**{edition} Edition**" in result
        assert "Joker" in result

    def test_render_eternal_joker(self, client: httpx.Client) -> None:
        """Verify Eternal modifier is rendered on jokers."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(client, "add", {"key": "j_joker", "eternal": True})

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        assert "**Eternal**" in result

    def test_render_perishable_joker(self, client: httpx.Client) -> None:
        """Verify Perishable modifier is rendered with rounds remaining."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(client, "add", {"key": "j_joker", "perishable": 5})

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        assert "**Perishable**" in result
        assert "5 rounds remaining" in result

    def test_render_rental_joker(self, client: httpx.Client) -> None:
        """Verify Rental modifier is rendered on jokers."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(client, "add", {"key": "j_joker", "rental": True})

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        assert "**Rental**" in result

    def test_render_joker_with_multiple_modifiers(self, client: httpx.Client) -> None:
        """Verify joker with edition and eternal renders both."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(client, "add", {"key": "j_joker", "edition": "FOIL", "eternal": True})

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        assert "**FOIL Edition**" in result
        assert "**Eternal**" in result


# =============================================================================
# Consumable Editions
# =============================================================================


class TestConsumableEditions:
    """Test consumable card edition rendering.

    Note: In Balatro, consumables can only have NEGATIVE edition.
    FOIL, HOLO, and POLYCHROME are not valid for consumables.
    """

    @pytest.mark.dev
    def test_render_consumable_negative(self, client: httpx.Client) -> None:
        """Verify NEGATIVE edition is rendered on consumables."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(client, "add", {"key": "c_fool", "edition": "NEGATIVE"})

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        # NEGATIVE is the only valid edition for consumables in Balatro
        assert "**NEGATIVE Edition**" in result
        assert "The Fool" in result

    @pytest.mark.dev
    def test_render_consumable_without_edition(self, client: httpx.Client) -> None:
        """Verify consumable renders correctly without edition."""
        load_integration_fixture(client, "strategy", "state-SELECTING_HAND")
        api(client, "add", {"key": "c_fool"})

        gamestate = api(client, "gamestate", {})["result"]
        sm = StrategyManager("default")
        result = sm.render_gamestate(gamestate)

        # Should appear in consumables section
        assert "Consumables count is 1/2" in result
        assert "The Fool" in result
