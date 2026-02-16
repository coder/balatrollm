---
model: sonnet
---

Analyze all modified and untracked files, group them logically, and create one or more conventional commits.

### Conventional Commits

**Format:** `<type>(<scope>): <description>`

Title must be **< 72 characters**.

#### Types

- feat: new feature
- fix: bug fix
- refactor: code change that neither fixes a bug nor adds a feature
- style: formatting, missing semicolons, etc.
- perf: performance improvement
- docs: documentation
- chore: maintenance tasks
- ci: continuous integration changes
- test: adding or correcting tests

#### Scopes

Use one of these fixed scopes. Omit the scope only when a change spans too many areas to pick one.

| Scope | Covers |
|---|---|
| `bot` | Core game loop, decision-making logic (`bot.py`) |
| `client` | BalatroBot JSON-RPC client (`client.py`) |
| `llm` | LLM client wrapper, retry logic (`llm.py`) |
| `executor` | Parallel execution orchestration (`executor.py`) |
| `collector` | Data collection, statistics (`collector.py`) |
| `strategy` | Strategy templates, rendering (`strategy.py`, `strategies/`) |
| `views` | HTTP server, HTML templates (`views.py`, `views/`) |
| `config` | Configuration management (`config.py`, YAML configs) |
| `cli` | CLI entry point, argument parsing (`cli.py`) |
| `test:unit` | Unit tests (`tests/unit/`) |
| `test:integration` | Integration tests (`tests/integration/`) |
| `test:fixtures` | Test fixtures and data (`tests/fixtures/`) |
| `docs` | All documentation (`docs/`, `*.md` files) |
| `ci` | CI/CD workflows, Makefile |
| `deps` | Dependency updates (`pyproject.toml`, `uv.lock`) |
| `release` | Version bumps, changelog updates |

#### Examples

```
feat(bot): add support for new game state
fix(client): handle JSON-RPC timeout gracefully
refactor(llm): extract retry logic into separate method
test:unit: add tests for collector statistics
docs: update installation instructions
chore(deps): bump openai to 1.0.0
```

### Workflow

1. Run `git status` to see overall repository state. If there are no changes (staged or unstaged), exit.
2. Run `git diff` and `git diff --stat` to analyze all unstaged changes.
3. Run `git diff --staged` and `git diff --stat --staged` to analyze already staged changes.
4. Run `git log --oneline -10` to review recent commit patterns.
5. Group the changed files logically by scope/purpose. If all changes belong to the same logical unit, make a single commit. If changes span multiple unrelated scopes, split them into separate commits (e.g., a dependency update and a new bot feature should be two commits).
6. For each logical group, in order:
   a. Stage only the files for that group with `git add <file1> <file2> ...`
   b. Write a concise commit message (72 chars max for first line). Include a body if the changes are complex.
   c. Create the commit.
7. After all commits, run `git log --oneline -5` to confirm the result.
