# Setup

This guide will help you install and configure BalatroLLM.

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)**: for managing Python environment and dependencies
- **[Balatro Game](https://www.playbalatro.com/)**: You need a copy of Balatro installed
- **[BalatroBot](https://github.com/coder/balatrobot)**: The underlying framework for Balatro automation
- **Access to LLM model**: exposing an OpenAI-compatible chat/completion API

!!! warning "BalatroBot Setup"

    Setting up Balatro with the BalatroBot mod requires careful configuration. Please refer to the [BalatroBot](https://github.com/coder/balatrobot) documentation and follow the instructions step by step.
    Ensure that BalatroBot is installed and running before proceeding with the BalatroLLM installation.

## Installation

- Clone the repository

```bash
git clone --depth 1 https://github.com/coder/balatrollm.git
cd balatrollm
```

- Create environment and install dependencies

```bash
uv sync --no-dev
```

When running `uv sync`, `uv` automatically downloads the required Python version, creates a new environment at `.venv`, and installs the project dependencies.

- Activate environment

```bash
source .venv/bin/activate
```

- Test that the new commands are available

```bash
balatrollm --help
balatrobench --help
```

!!! tip "Auto venv activation & Environment Variables"

    You can use [direnv](https://direnv.net/) to automatically activate the environment when you enter the project directory. The `.envrc.example` file contains an example configuration for direnv.

## Provider Configuration

You need to configure your chosen provider. We recommend configuring the provider through environment variables using `.envrc` (see `.envrc.example`)

- `BALATROLLM_BASE_URL`: API base URL
- `BALATROLLM_API_KEY`: API key for LLM provider

Now you should be able to run

```bash
balatrollm --list-models
```

to see the available models. You can now set the model environment variable:

- `BALATROLLM_MODEL`: Model to use

!!! note "CLI precedence"

    All `BALATROLLM_*` environment variables have a corresponding CLI argument. The environment variables are used as defaults when running `balatrollm`. CLI arguments take precedence over the corresponding environment variable. For example, you can set a default model with `BALATROLLM_MODEL` but use another one: `balatrollm --model "..."`.
