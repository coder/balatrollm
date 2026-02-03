# Strategies

Learn how strategies work in BalatroLLM, including their structure, implementation using Jinja2 templates, and how to contribute your own.

## Overview

Strategies in BalatroLLM define how the LLM bot approaches decision-making during gameplay. Each strategy consists of Jinja2 templates that generate the prompts sent to the language model, along with metadata and configuration files.

The strategy system allows for different playing styles - from conservative, financially-disciplined approaches to aggressive, high-risk strategies - by modifying the context, guidance, and available tools provided to the LLM.

## Strategy Structure

Each strategy is a directory under `src/balatrollm/strategies/` containing exactly 5 **required** files:

```
src/balatrollm/strategies/{strategy_name}/
├── manifest.json          # Strategy metadata
├── STRATEGY.md.jinja      # Strategy-specific guide and approach
├── GAMESTATE.md.jinja     # Game state representation template
├── MEMORY.md.jinja        # Response history tracking template
└── TOOLS.json             # Strategy-specific function definitions
```

### Strategy Naming Requirements

Strategy names must follow these rules:

- Lowercase letters and numbers only (e.g., `aggressive`, `value_based`, `risky2`)
- Valid Python identifier (cannot start with a number)
- Underscores allowed, hyphens forbidden (e.g., `high_risk` ✓, `high-risk` ✗)
- No spaces or special characters

## manifest.json

The `manifest.json` file defines strategy metadata with **5 required fields**:

```json
{
  "name": "Default",
  "description": "Conservative, financially disciplined approach to Balatro",
  "author": "BalatroBench",
  "version": "0.1.0",
  "tags": ["conservative", "financial"]
}
```

### Required Fields

- **name** (string): Human-readable strategy name displayed to users
- **description** (string): Brief description of the strategy's approach and philosophy
- **author** (string): Author identifier or organization name
- **version** (string): Strategy version in semantic versioning format (e.g., "0.1.0")
- **tags** (array of strings): Categorization tags for filtering and organization

### Versioning

Strategy versions are **independent** from BalatroLLM versions. Increment the strategy version when making changes:

- **Patch** (0.1.0 → 0.1.1): Bug fixes, typo corrections
- **Minor** (0.1.0 → 0.2.0): New features, significant prompt improvements
- **Major** (0.1.0 → 1.0.0): Complete strategy overhaul, breaking changes

## Jinja2 Templates

Strategies use [Jinja2](https://jinja.palletsprojects.com/) templating to dynamically generate prompts based on the current game state. Templates are compiled at runtime when the bot makes decisions.

### Available Context Variables

Each template receives different context variables:

`STRATEGY.md.jinja` and `GAMESTATE.md.jinja`:

| Variable | Type   | Description                                   |
| -------- | ------ | --------------------------------------------- |
| `G`      | `dict` | Full gamestate dictionary from BalatroBot API |

The `G` dictionary contains all game state information including:

- Current hand, jokers, consumables
- Money, remaining hands/discards
- Blind information, ante level
- Deck composition, played cards
- Shop contents (when in SHOP state)
- And more...

The `G` dictionary is the Game State returned by the [BalatroBot API](https://coder.github.io/balatrobot/api/#gamestate-schema).

`MEMORY.md.jinja`:

| Variable               | Type          | Description                                          |
| ---------------------- | ------------- | ---------------------------------------------------- |
| `history`              | `list[dict]`  | Last 10 actions with `method`, `params`, `reasoning` |
| `last_error_call_msg`  | `str \| None` | Error message from invalid LLM response              |
| `last_failed_call_msg` | `str \| None` | Error message from failed API call                   |

### Custom Filters

The template environment includes a custom `from_json` filter for parsing JSON strings within templates:

```jinja
{{ some_json_string | from_json }}
```

### Template Files

#### STRATEGY.md.jinja

Defines the strategy's core philosophy and decision-making approach. This template provides high-level guidance to the LLM about how to play the game.

Example structure:

```jinja
You are an expert Balatro player. Analyze the game state and make strategic decisions...

# Strategy Philosophy

Your approach is [conservative/aggressive/balanced]...

# Decision-Making Priorities

1. [Priority 1]
2. [Priority 2]
...
```

#### GAMESTATE.md.jinja

Presents the current game state in a format optimized for LLM comprehension. This template formats all relevant game information.

Example access patterns:

```jinja
## Current Situation

- Money: ${{ G.dollars }}
- Hands remaining: {{ G.hands }}
- Current score: {{ G.chips }} / {{ G.blind.chips }}

## Your Hand

{% for card in G.hand %}
- {{ card.rank }} of {{ card.suit }}
{% endfor %}
```

#### MEMORY.md.jinja

Tracks previous actions and errors to provide context for decision-making. This template helps the LLM learn from mistakes and maintain consistency.

Context variables (see [Available Context Variables](#available-context-variables) for details):

- `history`: List of previous actions (last 10)
- `last_error_call_msg`: Error from invalid LLM response
- `last_failed_call_msg`: Error from failed API call

## TOOLS.json

Defines the function calls available to the LLM during different game phases. The structure maps game states to available tools:

```json
{
  "SELECTING_HAND": [
    {
      "type": "function",
      "function": {
        "name": "play_hand_or_discard",
        "description": "Play cards as a poker hand or discard them",
        "parameters": {
          "type": "object",
          "properties": {
            "action": {
              "type": "string",
              "enum": ["play_hand", "discard"]
            },
            "cards": {
              "type": "array",
              "items": {"type": "integer"}
            }
          },
          "required": ["action", "cards"]
        }
      }
    }
  ],
  "SHOP": [...]
}
```

### Available Game States

Tools are organized by game state. The `TOOLS.json` file maps each state to its available tools.

| Game State             | Description           | Available Tools                                           |
| ---------------------- | --------------------- | --------------------------------------------------------- |
| `SELECTING_HAND`       | Hand selection phase  | `play`, `discard`, `rearrange`, `sell`, `use`             |
| `SHOP`                 | Shop phase            | `buy`, `reroll`, `next_round`, `sell`, `use`, `rearrange` |
| `BLIND_SELECT`         | Blind selection phase | `select`, `skip`                                          |
| `SMODS_BOOSTER_OPENED` | Pack opening phase    | `pack` (select cards or skip)                             |

!!! note "BLIND_SELECT and ROUND_EVAL Behavior"

    The current `balatrollm` bot loop does not delegate `BLIND_SELECT` or `ROUND_EVAL` to the LLM (see `src/balatrollm/bot.py`).

    - `ROUND_EVAL` always calls `cash_out`
    - `BLIND_SELECT` always calls `select` (never `skip`) because Tags are not supported yet by `balatrobot`; skipping blinds would collect Tags the bot can't use

    This "always play the blind" policy is a reasonable baseline for `RED` deck on `WHITE` stake.

### Common Tools

**SELECTING_HAND phase:**

- `play`: Play selected cards as a poker hand
- `discard`: Discard selected cards
- `rearrange`: Reorder cards in hand or jokers
- `sell`: Sell a joker or consumable for money
- `use`: Use a Tarot/Planet/Spectral card

**SHOP phase:**

- `buy`: Purchase a card, joker, or pack
- `reroll`: Reroll the shop
- `next_round`: Proceed to next round
- `sell`: Sell a joker or consumable
- `use`: Use a consumable
- `rearrange`: Reorder jokers

**BLIND_SELECT phase:**

- `select`: Select a blind to play
- `skip`: Skip the current blind (if allowed). *(Currently not used by `balatrollm`; Tag handling isn’t supported yet.)*

## Strategy Validation

BalatroLLM performs **two-stage validation** when loading strategies:

1. **Template Validation** (via `StrategyManager`):

    - Verifies all 4 template files exist (STRATEGY.md.jinja, GAMESTATE.md.jinja, MEMORY.md.jinja, TOOLS.json)
    - Raises `FileNotFoundError` if any template file is missing

2. **Metadata Validation** (via `StrategyManifest`):

    - Verifies manifest.json exists
    - Validates all 5 required fields are present
    - Raises `FileNotFoundError` if manifest.json is missing
    - Raises `ValueError` if required fields are missing

Validation occurs at runtime when a strategy is selected.

## Contributing Your Own Strategy

### 1. Study Existing Strategies

Review the built-in default strategy (`src/balatrollm/strategies/default/`) to understand structure and best practices.

### 2. Create Strategy Directory

```bash
mkdir src/balatrollm/strategies/your_strategy_name
```

### 3. Create Required Files

Create all 5 required files using existing strategies as templates:

1. **manifest.json**: Define metadata
2. **STRATEGY.md.jinja**: Define strategy philosophy and approach
3. **GAMESTATE.md.jinja**: Format game state presentation
4. **MEMORY.md.jinja**: Format response history
5. **TOOLS.json**: Define available functions (usually copied from existing strategies)

### 4. Test Locally

Test your strategy to ensure it works correctly:

```bash
balatrollm --strategy your_strategy_name
```

Common issues:

- Jinja2 syntax errors in templates
- Missing required fields in manifest.json
- Invalid JSON in TOOLS.json
- File naming mismatches

### 5. Submit Pull Request

1. Fork the BalatroLLM repository
2. Create a feature branch: `git checkout -b feat/add-strategy-your_strategy_name`
3. Add your strategy directory with all required files
4. Commit following conventional commits: `feat(strategy): add [strategy_name] strategy`
5. Open a pull request with:
    - Clear title describing your strategy
    - Brief description of the strategy's approach
    - Any notable differences from existing strategies

### Quality Standards

Submissions must meet these standards:

- **Complete**: All 5 files present and functional
- **Valid**: Templates compile without errors, JSON is well-formed
- **Documented**: Clear strategy philosophy and decision-making approach
- **Unique**: Offers meaningfully different gameplay from existing strategies
- **Tested**: Locally verified to work

### Review Process

Strategy contributions are reviewed for:

- Compliance with naming and structure requirements
- Template functionality and Jinja2 compatibility
- Manifest.json completeness and validity
- Strategy uniqueness and gameplay value
- Code quality and documentation clarity

Once approved, your strategy will be available to all BalatroLLM users via the `--strategy` flag.

## Best Practices

### Template Design

- **Be concise**: LLMs work better with clear, focused prompts
- **Provide context**: Include relevant game information without overwhelming
- **Use formatting**: Headers, lists, and emphasis help LLM comprehension
- **Test iteratively**: Run games and refine based on bot behavior

### Strategy Philosophy

- **Define clear priorities**: What matters most? (economy, joker synergies, risk management)
- **Explain trade-offs**: Help the LLM understand when to break rules
- **Provide examples**: Concrete scenarios guide decision-making
- **Stay consistent**: Maintain the same approach throughout templates
