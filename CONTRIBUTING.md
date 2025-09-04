# Contributing

Welcome to **BalatroLLM**! We appreciate your interest in contributing.

This document provides guidelines and instructions for contributing to the project. Whether you're fixing bugs, improving documentation, proposing new features, or submitting new strategies, your contributions are welcome.

## How to Contribute

1. **Report Issues**: If you find bugs or have feature requests, please create an issue on GitHub.

2. **Submit Pull Requests**: For code contributions, fork the repository, make your changes, and submit a pull request.

3. **Follow Coding Standards**: We use Ruff for linting and formatting, and pyright/basedpyright for type checking. Make sure your code passes all checks.

4. **Write Tests**: For new features or bug fixes, please include tests to validate your changes.

5. **Use Conventional Commits**: Follow the conventional commits specification for your commit messages.

6. **Submit Strategies**: Community members can contribute new playing strategies by following the strategy submission guidelines below.

## Environment Setup

This section describes how to set up the **recommended** development environment for this project using [uv](https://docs.astral.sh/uv/).

1. Download the repository:

```sh
git clone https://github.com/S1M0N38/balatrollm.git
cd balatrollm
```

2. Create environment:

```sh
uv sync --all-extras
```

3. Set up environment variables (if your project uses them):

```sh
cp .envrc.example .envrc
# And modify the .envrc file with your settings
```

The environment setup is now ready to use. Every time you are working on the project, you can activate the environment by running:

```sh
source .envrc
```

> You can use [direnv](https://github.com/direnv/direnv) to automatically activate the environment when you enter the project directory.

## Release Cycle

The project follows an automated release process using GitHub Actions:

1. **Conventional Commits**: All commits should follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

2. **Release Please PR**: The [Release Please](https://github.com/googleapis/release-please) GitHub Action automatically maintains a release PR that:

   - Updates the version in `pyproject.toml`
   - Updates the version in `src/balatrollm/__init__.py`
   - Updates the `CHANGELOG.md` based on conventional commits
   - The PR is continuously updated as new commits are added to the main branch

   **Important**: Never manually modify `uv.lock`, `CHANGELOG.md`, or version numbers in `pyproject.toml` or your package's `__init__.py`. These are automatically maintained by the release pipeline.

3. **Version Release**: When ready for a new release, the repository owner merges the Release Please PR, which:

   - Triggers the creation of a new Git tag (e.g., `v0.5.1`)
   - Creates a GitHub Release with release notes

4. **PyPI Publication**: When a new version tag is pushed, the Release PyPI workflow:

   - Builds the Python package
   - Publishes it to PyPI using trusted publishing

5. **Lock File Update**: After a release is created, an additional workflow:

   - Checks out the repository
   - Updates the `uv.lock` file with `uv lock`
   - Commits and pushes the updated lock file with the message "chore(deps): update uv.lock for version X.Y.Z"
   - This ensures dependencies are properly locked for the new version

This automated process ensures consistent versioning, comprehensive changelogs, reliable package distribution, and up-to-date dependency locks with minimal manual intervention.

## Contributing Strategies

Community members can contribute new playing strategies to enhance BalatroLLM's gameplay variety. Strategies define how the bot approaches decision-making during different game phases.

### Strategy Structure

Each strategy must be organized as a directory under `src/balatrollm/strategies/` containing exactly four files:

```
src/balatrollm/strategies/your_strategy_name/
├── STRATEGY.md.jinja      # Strategy-specific guide and approach
├── GAMESTATE.md.jinja     # Game state representation template
├── MEMORY.md.jinja        # Response history tracking template
└── TOOLS.json             # Strategy-specific function definitions
```

### Strategy Naming Requirements

Strategy names must follow these rules:

- **Lowercase letters and numbers only** (e.g., `aggressive`, `value_based`, `risky2`)
- **Valid Python identifier** (cannot start with a number)
- **Underscores allowed, hyphens forbidden** (e.g., `high_risk` allowed, `high-risk` forbidden)
- **No spaces or special characters**

### Creating Your Strategy

1. **Study Existing Strategies**: Review `src/balatrollm/strategies/default/` and `src/balatrollm/strategies/aggressive/` to understand the template structure and content expectations.

2. **Create Strategy Directory**: Create a new directory following the naming requirements:

   ```bash
   mkdir src/balatrollm/strategies/your_strategy_name
   ```

3. **Required Files**: Create all four required files using the existing strategies as templates:

   - **STRATEGY.md.jinja**: Define your strategy's core philosophy, decision-making approach, and gameplay priorities
   - **GAMESTATE.md.jinja**: Template for how game state information should be presented to the LLM
   - **MEMORY.md.jinja**: Template for tracking and presenting response history
   - **TOOLS.json**: Function definitions available to the LLM during gameplay

4. **Template Compatibility**: Ensure your templates work with the Jinja2 templating system and provide all necessary context for LLM decision-making.

### Submission Process

1. **Fork the Repository**: Fork the BalatroLLM repository to your GitHub account

2. **Create Feature Branch**: Create a new branch for your strategy:

   ```bash
   git checkout -b feat/add-strategy-your_strategy_name
   ```

3. **Implement Strategy**: Add your strategy directory with all required files

4. **Test Your Strategy**: Run your strategy locally to ensure it works:

   ```bash
   balatrollm --strategy your_strategy_name
   ```

5. **Submit Pull Request**: Open a PR containing only your new strategy directory. The PR should:

   - Have a clear title: `feat: add [strategy_name] strategy`
   - Include a brief description of your strategy's approach and philosophy
   - Follow conventional commit standards

### Quality Standards

- **Complete Implementation**: All four files must be present and functional
- **Clear Documentation**: Strategy philosophy and approach should be well-documented
- **Template Validation**: Ensure Jinja2 templates render correctly with game data
- **Unique Approach**: Strategy should offer a meaningfully different gameplay style from existing strategies

### Review Process

Submitted strategies will be reviewed for:

- Compliance with naming and structure requirements
- Template functionality and Jinja2 compatibility
- Strategy uniqueness and gameplay value
- Code quality and documentation standards

Once approved, your strategy will be available to all BalatroLLM users via the `--strategy` flag.
