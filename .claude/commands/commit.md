Generate a conventional commit message for the current staged changes.

Analyze the git diff of staged files and create a commit message following conventional commits specification:

### Conventional Commits

**Format:** `<type>(<scope>): <description>`

#### Types

- feat: new feature
- fix: bug fix
- docs: documentation
- style: formatting, missing semicolons, etc.
- refactor: code change that neither fixes a bug nor adds a feature
- test: adding or correcting tests
- chore: maintenance tasks
- ci: continuous integration changes
- revert: reverts a previous commit

### Workflow

1. Run `git status` to see overall repository state. If there are are no staged changes, exit.
2. Run `git diff --staged` to analyze the actual changes
3. Run `git diff --stat --staged` for summary of changed files
4. Run `git log --oneline -10` to review recent commit patterns
5. Choose appropriate type and scope based on changes
6. Write concise description (50 chars max for first line)
7. Include body if changes are complex
8. Commit the staged changes with the generated message

### Co-authors

Here is the collection of all previous co-authors of the repo as reference (names and emails):

- claude: `Co-Authored-By: Claude <noreply@anthropic.com>`

Here is a list of the co-authors which contributed to this commit:

```
$ARGUMENTS
```

If the list is empty, do not add any co-authors

### Notes

- Do not include emojis in the commit message.
- Do not include `🤖 Generated with [Claude Code](https://claude.ai/code)` in the commit message.
