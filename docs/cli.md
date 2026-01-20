# CLI Reference

Reference for the `balatrollm` command-line interface.

## Usage

```bash
balatrollm [CONFIG] [OPTIONS]
```

BalatroLLM can be configured through three methods with the following precedence (lowest to highest):

1. **Environment variables** - `BALATROLLM_*` prefixed variables
2. **Configuration file** - YAML file (see [`config/example.yaml`](https://github.com/coder/balatrollm/blob/main/config/example.yaml))
3. **CLI flags** - Command-line arguments (highest precedence)

This means CLI flags override config file values, which override environment variables.

## Arguments

| Argument | Required | Description                     |
| -------- | -------- | ------------------------------- |
| `CONFIG` | No       | Path to YAML configuration file |

## Options

| CLI Flag              | Environment Variable  | Default                        | Description                  |
| --------------------- | --------------------- | ------------------------------ | ---------------------------- |
| `--model MODEL`       | `BALATROLLM_MODEL`    | *(required)*                   | LLM model(s) to use          |
| `--seed SEED`         | `BALATROLLM_SEED`     | `AAAAAAA`                      | Game seed(s)                 |
| `--deck DECK`         | `BALATROLLM_DECK`     | `RED`                          | Deck code(s)                 |
| `--stake STAKE`       | `BALATROLLM_STAKE`    | `WHITE`                        | Stake code(s)                |
| `--strategy STRATEGY` | `BALATROLLM_STRATEGY` | `default`                      | Strategy name(s)             |
| `--parallel N`        | `BALATROLLM_PARALLEL` | `1`                            | Concurrent game instances    |
| `--host HOST`         | `BALATROLLM_HOST`     | `127.0.0.1`                    | BalatroBot host              |
| `--port PORT`         | `BALATROLLM_PORT`     | `12346`                        | Starting port                |
| `--base-url URL`      | `BALATROLLM_BASE_URL` | `https://openrouter.ai/api/v1` | LLM API base URL             |
| `--api-key KEY`       | `BALATROLLM_API_KEY`  | *None*                         | LLM API key                  |
| `--views`             | `BALATROLLM_VIEWS`    | `False`                        | Enable views HTTP server     |
| `--dry-run`           | -                     | `False`                        | Show tasks without executing |

!!! note "Multiple Values"

    Options marked with "model(s)", "seed(s)", etc. accept multiple values. When multiple values are provided, BalatroLLM generates a cartesian product of all combinations as tasks.

The following values can be provided for `deck` and `stake` options:

- **Decks:** `RED`, `BLUE`, `YELLOW`, `GREEN`, `BLACK`, `MAGIC`, `NEBULA`, `GHOST`, `ABANDONED`, `CHECKERED`, `ZODIAC`, `PAINTED`, `ANAGLYPH`, `PLASMA`, `ERRATIC`
- **Stakes:** `WHITE`, `RED`, `GREEN`, `BLACK`, `BLUE`, `PURPLE`, `ORANGE`, `GOLD`

## Examples

### Basic Usage

```bash
# Run with specific model (requires BALATROLLM_API_KEY in environment)
balatrollm --model openai/gpt-5

# Run with configuration file
balatrollm config/example.yaml

# Run with config file and override specific options
balatrollm config/example.yaml --model openai/gpt-5 --seed BBBBBBB
```

### Advanced Usage

```bash
# Multiple seeds and decks (generates cartesian product of all combinations)
balatrollm --model openai/gpt-5 --deck RED BLUE --seed AAAAAAA BBBBBBB

# Run multiple game instances concurrently
balatrollm --model openai/gpt-5 --parallel 4

# Preview tasks without executing
balatrollm config/example.yaml --dry-run

# Use a custom strategy
balatrollm --model openai/gpt-4o --strategy my_custom_strategy

# Enable views overlay on port 12345
balatrollm --model openai/gpt-4o --views
# Access views at:
#   http://localhost:12345/views/task.html
#   http://localhost:12345/views/responses.html
```

!!! note "Cartesian Product"

    When specifying multiple values for seeds, decks, stakes, etc., BalatroLLM generates all combinations as separate tasks. For example, `--deck RED BLUE --seed AAAAAAA BBBBBBB` creates 4 tasks: `(RED, AAAAAAA)`, `(RED, BBBBBBB)`, `(BLUE, AAAAAAA)`, `(BLUE, BBBBBBB)`. For complex task configurations, use a YAML configuration file.

For more information about strategies, see the [Strategies documentation](strategies.md).

## BalatroBot Configuration

BalatroBot instances spawned by BalatroLLM can be configured through `BALATROBOT_*` environment variables. These settings control how Balatro runs during automated gameplay.

| Environment Variable       | Default       | Description                                |
| -------------------------- | ------------- | ------------------------------------------ |
| `BALATROBOT_HOST`          | `127.0.0.1`   | Server hostname                            |
| `BALATROBOT_PORT`          | `12346`       | Server port                                |
| `BALATROBOT_FAST`          | `0`           | Enable fast mode (10x game speed)          |
| `BALATROBOT_HEADLESS`      | `0`           | Enable headless mode (minimal rendering)   |
| `BALATROBOT_RENDER_ON_API` | `0`           | Render only on API calls                   |
| `BALATROBOT_AUDIO`         | `0`           | Enable audio                               |
| `BALATROBOT_DEBUG`         | `0`           | Enable debug mode (requires DebugPlus mod) |
| `BALATROBOT_NO_SHADERS`    | `0`           | Disable all shaders                        |
| `BALATROBOT_BALATRO_PATH`  | auto-detected | Path to Balatro game directory             |
| `BALATROBOT_LOVELY_PATH`   | auto-detected | Path to lovely library (dll/so/dylib)      |
| `BALATROBOT_LOVE_PATH`     | auto-detected | Path to LOVE executable (native only)      |
| `BALATROBOT_PLATFORM`      | auto-detected | Platform: darwin, linux, windows, native   |
| `BALATROBOT_LOGS_PATH`     | `logs`        | Directory for log files                    |

For detailed information about platform-specific behavior and configuration, see the [BalatroBot Platform-Specific Details](https://coder.github.io/balatrobot/cli/#platform-specific-details)
