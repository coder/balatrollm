# Installation

This guide will help you install and configure BalatroLLM.

## Prerequisites

- **Balatro** (v1.0.1+) - Purchase from [Steam](https://store.steampowered.com/app/2379780/Balatro/)
- **BalatroBot** (latest) - Follow the [installation guide](https://coder.github.io/balatrobot/installation/)
- **Uv** (v0.9.21+) - Follow the [installation guide](https://docs.astral.sh/uv/)
- **LLM API access** - Obtain API key from an OpenAI-compatible provider (e.g., [OpenRouter](https://openrouter.ai/), [OpenAI](https://openai.com/))

!!! warning "BalatroBot Setup Required"

    Setting up Balatro with the BalatroBot mod requires careful configuration. Please follow the [BalatroBot Installation Guide](https://coder.github.io/balatrobot/installation/) step by step.

    Ensure BalatroBot is installed and working before proceeding with BalatroLLM installation.

## Installation

### 1. Clone the Repository

```bash
git clone --depth 1 https://github.com/coder/balatrollm.git
cd balatrollm
```

### 2. Create Environment and Install Dependencies

```bash
uv sync --no-dev
```

When running `uv sync`, uv automatically downloads the required Python version, creates a new environment at `.venv`, and installs the project dependencies.

### 3. Activate Environment

```bash
source .venv/bin/activate
```

### 4. Verify Installation

```bash
balatrollm --help
```

!!! tip "Auto venv activation"

    You can use [direnv](https://direnv.net/) to automatically activate the environment when you enter the project directory. See the `.envrc.example` file for an example configuration.

## Provider Configuration

Configure your LLM provider through environment variables. We recommend using `.envrc` (see `.envrc.example`):

```bash
export BALATROLLM_BASE_URL="https://openrouter.ai/api/v1"
export BALATROLLM_API_KEY="sk-..."
```

| Variable              | Description                             |
| --------------------- | --------------------------------------- |
| `BALATROLLM_BASE_URL` | API base URL (e.g., OpenRouter, OpenAI) |
| `BALATROLLM_API_KEY`  | API key for your LLM provider           |

For full CLI reference, see [CLI Reference](cli.md).
