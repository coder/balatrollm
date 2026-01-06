# Contributing

Guide for contributing to BalatroLLM development.

## Prerequisites

- **Balatro** (v1.0.1+) - Purchase from [Steam](https://store.steampowered.com/app/2379780/Balatro/)
- **BalatroBot** (latest) - Follow the [installation guide](https://coder.github.io/balatrobot/installation/)
- **Uv** (v0.9.21+) - Follow the [installation guide](https://docs.astral.sh/uv/)
- **LLM API access** - Obtain API key from an OpenAI-compatible provider (e.g., [OpenRouter](https://openrouter.ai/), [OpenAI](https://openai.com/))

## Development Environment Setup

### direnv (Recommended)

We use [direnv](https://direnv.net/) to automatically manage environment variables and virtual environment activation. When you `cd` into the project directory, direnv automatically loads settings from `.envrc`.

!!! warning "Contains Secrets"

    The `.envrc` file may contain API keys. **Never commit this file**.

**Example `.envrc` configuration:**

```bash
# Load the virtual environment
source .venv/bin/activate

# Python-specific variables
export PYTHONUNBUFFERED="1"
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
export PYTHONPATH="${PWD}/tests:${PYTHONPATH}"

# BALATROBOT env vars
export BALATROBOT_FAST=1
export BALATROBOT_DEBUG=1
export BALATROBOT_RENDER_ON_API=0
export BALATROBOT_HEADLESS=0

# BALATROLLM env vars
export BALATROLLM_API_KEY="sk-..."
export BALATROLLM_BASE_URL="https://openrouter.ai/api/v1"
```

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/coder/balatrollm.git
cd balatrollm
```

### 2. Install Dependencies

```bash
make install
```

### 3. Activate Virtual Environment

```bash
source .venv/bin/activate
```

## Available Make Commands

The project includes a Makefile with convenient targets for common development tasks:

```bash
make help      # Show all available commands
make install   # Install dependencies
make lint      # Run ruff linter
make format    # Format code (Python, Markdown)
make typecheck # Run type checker (ty)
make quality   # Run all code quality checks
make test      # Run all tests (unit + integration)
make all       # Run quality checks and tests
```

## Running Tests

Tests use Python + pytest to verify bot functionality. You don't need to have BalatroBot running—the tests automatically start the required Balatro instances.

!!! info "Separate Unit and Integration Test Suites"

    The unit and integration test suites are run in sequence. Unit tests run first without Balatro, followed by integration tests that spawn Balatro instances.

```bash
# Install all dependencies
make install

# Run all tests (unit + integration in sequence)
make test

# Run unit tests only (no Balatro required)
pytest tests/unit

# Run integration tests (starts Balatro instances)
# Runs with 2 workers in parallel
BALATROBOT_RENDER_ON_API=0 BALATROBOT_HEADLESS=1 pytest -n 2 tests/integration

# Run specific test file
pytest tests/unit/test_config.py -v

# Run tests with dev marker only
pytest tests/unit -m dev

# Run only integration tests
pytest tests/integration -m integration

# Run tests that do not require Balatro instance
pytest tests/unit -m "not integration"
```

**Test markers:**

- `@pytest.mark.dev`: Run only tests under development with `-m dev`
- `@pytest.mark.integration`: Tests that start Balatro (skip with `-m "not integration"`)

## Code Structure

```
src/balatrollm/
├── cli.py           # CLI entry point and argument parsing
├── bot.py           # Core game loop with LLM decision-making
├── client.py        # BalatroBot JSON-RPC client
├── llm.py           # OpenAI client wrapper with retry logic
├── strategy.py      # Strategy template management
├── config.py        # Multi-source configuration management
├── executor.py      # Parallel execution orchestration
├── collector.py     # Data collection and statistics
└── strategies/      # Strategy templates
    └── default/
        ├── manifest.json         # Strategy metadata
        ├── STRATEGY.md.jinja     # Game rules and tactics
        ├── GAMESTATE.md.jinja    # Current state template
        ├── MEMORY.md.jinja       # Action history template
        └── TOOLS.json            # Function calling tools
```

## Code Quality

Before committing, always run:

```bash
make quality  # Runs lint, typecheck, and format
```

This ensures your code meets the project's quality standards:

- **Linting**: `ruff check` for Python code style
- **Formatting**: `ruff format` for Python, `mdformat` for Markdown
- **Type checking**: `ty check` for static type analysis

## Pull Request Guidelines

1. **One feature per PR** - Keep changes focused
2. **Add tests** - New functionality needs test coverage
3. **Update docs** - Update documentation for user-facing changes
4. **Run code quality checks** - Execute `make quality` before committing
5. **Test locally** - Ensure both unit and integration tests pass
6. **Use Conventional Commits** - Follow [Conventional Commits](https://www.conventionalcommits.org/) for automated changelog generation

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment.

### Workflows

- **code-quality.yml**: Runs linting, type checking, and formatting on every PR (equivalent to `make quality`)
- **deploy-docs.yml**: Deploys documentation to GitHub Pages when changes are pushed to main
- **release-please.yml**: Automated version management and changelog generation
- **release-pypi.yml**: Publishes the package to PyPI when a release tag is created
- **commit_lint.yml**: Validates commit messages follow Conventional Commits format
- **update-balatrobot-dependency.yml**: Automatically updates BalatroBot dependency

### For Contributors

You don't need to worry about most CI/CD workflows—just ensure your PR passes the **code quality checks**:

```bash
make quality  # Run this before pushing
```

If CI fails on your PR, check the workflow logs on GitHub for details. Most issues can be fixed by running `make quality` locally.

## Contributing Strategies

See [Strategies](strategies.md) for how to create and contribute custom playing strategies.

