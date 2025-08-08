# Contributing

Welcome to **template-python**! We appreciate your interest in contributing.

This document provides guidelines and instructions for contributing to the project. Whether you're fixing bugs, improving documentation, or proposing new features, your contributions are welcome.

## How to Contribute

1. **Report Issues**: If you find bugs or have feature requests, please create an issue on GitHub.

2. **Submit Pull Requests**: For code contributions, fork the repository, make your changes, and submit a pull request.

3. **Follow Coding Standards**: We use Ruff for linting and formatting, and pyright/basedpyright for type checking. Make sure your code passes all checks.

4. **Write Tests**: For new features or bug fixes, please include tests to validate your changes.

5. **Use Conventional Commits**: Follow the conventional commits specification for your commit messages.

## Environment Setup

This section describes how to set up the **recommended** development environment for this project using [uv](https://docs.astral.sh/uv/).

1. Download the repository:

```sh
git clone https://github.com/S1M0N38/template-python.git
cd template-python
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
   - Updates the version in `src/template_python/__init__.py`
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
