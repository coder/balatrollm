# Contributing

Welcome to **BalatroLLM**! We appreciate your interest in contributing.

This document provides guidelines and instructions for contributing to the project. Whether you're fixing bugs, improving documentation, proposing new features, or submitting new strategies, your contributions are welcome.

## How to Contribute

1. **Report Issues**: If you find bugs or have feature requests, please create an issue on GitHub.

2. **Submit Pull Requests**: For code contributions, fork the repository, make your changes, and submit a pull request.

3. **Follow Coding Standards**: We use Ruff for linting and formatting, and ty for type checking. Make sure your code passes all checks.

4. **Write Tests**: For new features or bug fixes, please include tests to validate your changes.

5. **Use Conventional Commits**: Follow the conventional commits specification for your commit messages.

6. **Submit Strategies**: Community members can contribute new playing strategies. See the [Strategies documentation](https://s1m0n38.github.io/balatrollm/strategies/) for detailed guidelines.

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
