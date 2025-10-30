# Strategies

Learn how strategies work in BalatroLLM, including their structure, implementation using Jinja2 templates, and how to contribute your own.

## Overview

Strategies in BalatroLLM define how the LLM bot approaches decision-making during gameplay. Each strategy consists of Jinja2 templates that generate the prompts sent to the language model, along with metadata and configuration files.

The strategy system allows for different playing styles - from conservative, financially-disciplined approaches to aggressive, high-risk strategies - by modifying the context, guidance, and available tools provided to the LLM.

## Strategy Structure

Each strategy is a directory under `src/balatrollm/strategies/` containing exactly **5 required files**:

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

- **Lowercase letters and numbers only** (e.g., `aggressive`, `value_based`, `risky2`)
- **Valid Python identifier** (cannot start with a number)
- **Underscores allowed, hyphens forbidden** (e.g., `high_risk` ✓, `high-risk` ✗)
- **No spaces or special characters**

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

All Jinja2 templates have access to:

- **`G`**: The complete game state dictionary containing:

    - Current hand, jokers, consumables
    - Money, remaining hands/discards
    - Blind information, ante level
    - Deck composition, played cards
    - And more...

- **`constants`**: Balatro game constants including:

    - `constants.jokers`: All joker definitions
    - `constants.consumables`: Tarot, Planet, and Spectral cards
    - `constants.vouchers`: Available vouchers
    - `constants.tags`: Tag definitions
    - `constants.editions`: Card editions (Foil, Holographic, Polychrome)
    - `constants.enhancements`: Card enhancements (Bonus, Mult, Wild, Glass, Steel, Stone, Gold, Lucky)
    - `constants.seals`: Card seals (Gold, Red, Blue, Purple)

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

Tracks previous responses and errors to provide context for decision-making. This template helps the LLM learn from mistakes and maintain consistency.

Context variables:

- `responses`: List of previous LLM responses
- `last_error_call_msg`: Last error message from failed tool calls
- `last_failed_call_msg`: Last failed tool call details

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

- **SELECTING_HAND**: During hand selection phase (playing/discarding)
- **SHOP**: During shop phase (buying, selling, using consumables)

### Common Tools

**SELECTING_HAND phase:**

- `play_hand_or_discard`: Play or discard selected cards
- `rearrange_hand`: Reorder cards in hand
- `rearrange_jokers`: Reorder jokers for optimal scoring
- `sell_joker`: Sell a joker for money
- `sell_consumable`: Sell a consumable for money
- `use_consumable`: Use a Tarot/Planet/Spectral card

**SHOP phase:**

- `shop`: Perform shop actions (next_round, reroll, buy_card, redeem_voucher)
- `sell_joker`: Sell a joker
- `sell_consumable`: Sell a consumable
- `use_consumable`: Use a Tarot/Planet/Spectral card
- `rearrange_jokers`: Reorder jokers

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

Review the built-in strategies to understand structure and best practices:

- `src/balatrollm/strategies/default/`: Conservative approach
- `src/balatrollm/strategies/aggressive/`: High-risk approach

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
4. Commit following conventional commits: `feat: add [strategy_name] strategy`
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
- **Tested**: Locally verified to work with at least one complete game

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

### Debugging

If your strategy produces errors:

1. **Check template syntax**: Ensure valid Jinja2 (matching braces, proper filters)
2. **Verify manifest.json**: All fields present, valid JSON format
3. **Test TOOLS.json**: Valid JSON, matches OpenAI function calling format
4. **Review game logs**: Check `runs/` directory for detailed error messages
5. **Compare with defaults**: See how built-in strategies handle similar situations

## Examples

### Example manifest.json

```json
{
  "name": "Aggressive",
  "description": "High-risk, high-reward strategy with aggressive spending and bold decisions",
  "author": "BalatroBench",
  "version": "0.1.0",
  "tags": ["aggressive", "high-risk", "bold"]
}
```

### Example Jinja2 Template Snippet

```jinja
## Financial Status

Current money: ${{ G.dollars }}
Interest rate: $1 per $5 saved (max $5 at $25+)

{% if G.dollars >= 25 %}
You're earning maximum interest ($5). Consider strategic spending.
{% elif G.dollars >= 20 %}
Almost at max interest! Saving ${{ 25 - G.dollars }} more will maximize returns.
{% else %}
Focus on immediate power upgrades over interest at this stage.
{% endif %}
```

### Example Tool Definition

```json
{
  "type": "function",
  "function": {
    "name": "shop",
    "description": "Perform shop actions including buying cards, rerolling, or proceeding to next round",
    "parameters": {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": ["next_round", "reroll", "buy_card", "redeem_voucher"],
          "description": "The shop action to perform"
        },
        "index": {
          "type": "integer",
          "description": "Index of card to buy (0-indexed) or voucher to redeem"
        },
        "reasoning": {
          "type": "string",
          "description": "Brief explanation of why you're taking this action"
        }
      },
      "required": ["action"]
    }
  }
}
```
