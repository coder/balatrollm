Initialize a new Python project from this template repository.

Transform this generic template into a personalized starting point for your Python project by:

### Workflow

1. **Collect Project Information**
   - Get current git remote URL to extract owner and repository name
   - Prompt user for project name if different from repository name
   - Validate project name follows Python package naming conventions

2. **Update Project Structure**
   - Rename `src/template_python/` directory to `src/{project_name}/`
   - Update all file references from `template_python` to `{project_name}`
   - Replace `template-python` with `{project-name}` in hyphenated contexts

3. **Update Configuration Files**
   - Update `pyproject.toml`:
     - Change project name from "template-python" to "{project-name}"
     - Update description placeholder
     - Update author information from git config
     - Update repository URLs to match new project
     - Update script entry points
   - Update `README.md`:
     - Replace title from "Python Project Template" to "{Project Name}"
     - Update repository URLs and clone commands
     - Update package import examples
     - Remove template-specific content

4. **Update Source Code**
   - Update `src/{project_name}/__init__.py`
   - Update any import statements in test files
   - Update entry point script references

5. **Git Operations**
   - Stage all changes
   - Create initial commit: "feat: initialize project from template"
   - Optionally set up remote origin if not already configured

6. **Environment Setup and Validation**
   - Check for `uv` command availability (exit with error if not found)
   - Run `uv sync --all-extras` to install all dependencies including dev dependencies
   - Activate virtual environment with `source .venv/bin/activate`

7. **Quality Checks**
   - Run `pytest` to execute test suite
   - Run `ruff check` for linting validation
   - Run `ruff format` for code formatting
   - Run `basedpyright` for type checking
   - Report success only if all commands pass (exit code 0)

### Validation

- Ensure project name is valid Python package name (lowercase, underscores only)
- Verify all file references have been updated correctly
- Validate pyproject.toml syntax
- Check `uv` command is available on system
- Ensure virtual environment is created and activated successfully
- Validate all dependencies install without errors
- Verify tests pass (pytest exit code 0)
- Ensure code passes linting (ruff check exit code 0)
- Verify code formatting is correct (ruff format exit code 0)
- Confirm type checking passes (basedpyright exit code 0)

### Notes

- The command should be run immediately after cloning the template
- It assumes the current directory is the root of the template repository
- Git repository should already be initialized
- User should have git configured with name and email
- Requires `uv` package manager to be installed (https://docs.astral.sh/uv/)
- The command will create a virtual environment and install all dependencies
- All quality checks must pass for the command to report success
- Use `--skip-install` flag to skip environment setup if only doing file transformations

### Arguments

```
$ARGUMENTS
```

Optional arguments:
- `--project-name`: Override project name (default: use git repository name)
- `--author-name`: Override author name (default: use git config user.name)  
- `--author-email`: Override author email (default: use git config user.email)
- `--description`: Set project description
- `--skip-git`: Don't create initial commit
- `--skip-install`: Skip environment setup and quality checks (steps 6-7)
