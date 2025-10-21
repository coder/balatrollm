# Setup

This guide will help you install and configure BalatroLLM for running LLM-powered Balatro bots.

## Prerequisites

- **Python 3.13+**: BalatroLLM requires Python 3.13 or later
- **Balatro Game**: You need a copy of Balatro installed
- **BalatroBot**: The underlying framework for Balatro automation
- **API Access**: An API key for LLM providers (OpenRouter recommended)

## Installation

### 1. Install BalatroLLM

```bash
# Clone the repository
git clone https://github.com/coder/balatrollm.git
cd balatrollm

# Install with uv (recommended)
uv sync --all-extras --group dev

# Or install with pip
pip install -e .
```

### 2. Set up BalatroBot

BalatroLLM depends on BalatroBot for game communication. Follow the [BalatroBot installation guide](https://coder.github.io/balatrobot/installation/) to:

1. Install the BalatroBot Steamodded mod
2. Configure Balatro for bot communication
3. Verify the setup works

### 3. Configure Environment Variables

Create a `.envrc` file in the project root:

```bash
# Copy the example file
cp .envrc.example .envrc

# Edit with your API key
export OPENROUTER_API_KEY="your-api-key-here"

# Load the environment
source .envrc
```

### 4. Verify Installation

Test that everything is working:

```bash
# Check available models
balatrollm --list-models

# Test bot connectivity (requires Balatro running)
balatrollm --help
```

## API Key Setup

### OpenRouter (Recommended)

OpenRouter provides access to multiple LLM providers through a single API:

1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Generate an API key
3. Add to your `.envrc` file as `OPENROUTER_API_KEY`

### Other Providers

BalatroLLM supports any OpenAI-compatible API:

```bash
# Use custom provider
balatrollm --base-url https://api.your-provider.com/v1 --api-key your-key
```

## Game Setup

### Start Balatro

Use the provided script to launch Balatro with bot support:

```bash
# Start single instance on default port 12346
./balatro.sh

# Start with custom port
./balatro.sh -p 12347

# Start multiple instances for parallel runs
./balatro.sh -p 12346 -p 12347

# Start in headless mode for servers
./balatro.sh --headless --fast
```

### Verify Connection

Check that BalatroLLM can connect to the game:

```bash
# Run a quick test (will exit after connection)
balatrollm --runs 1
```

## Troubleshooting

### Connection Issues

If the bot can't connect to Balatro:

1. Ensure Balatro is running with the BalatroBot mod
2. Check that the port matches (default: 12346)
3. Verify firewall settings allow local connections

### API Issues

If you get API errors:

1. Verify your API key is correct
2. Check your account balance/credits
3. Test with a different model using `--model`

### Performance Issues

For better performance:

1. Use `--fast` mode in the Balatro script
2. Run multiple instances in parallel
3. Choose faster models for initial testing
