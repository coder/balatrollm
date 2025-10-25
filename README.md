<div align="center">
  <h1>BalatroLLM</h1>
  <p align="center">
    <a href="https://github.com/coder/balatrollm/releases">
      <img alt="GitHub release" src="https://img.shields.io/github/v/release/coder/balatrollm?include_prereleases&sort=semver&style=for-the-badge&logo=github"/>
    </a>
    <a href="https://pypi.org/project/balatrollm/">
      <img alt="PyPI" src="https://img.shields.io/pypi/v/balatrollm?style=for-the-badge&logo=pypi&logoColor=white"/>
    </a>
    <a href="https://discord.gg/TPn6FYgGPv">
      <img alt="Discord" src="https://img.shields.io/badge/discord-server?style=for-the-badge&logo=discord&logoColor=%23FFFFFF&color=%235865F2"/>
    </a>
  </p>
  <div><video src="https://github.com/user-attachments/assets/777d0c4f-d66a-47dd-9eab-7efb20beaaf2" alt="BalatroLLM playing Balatro"></div>
  <p><em>A Balatro bot powered by LLMs</em></p>
</div>

---

BalatroLLM is a bot that uses Large Language Models (LLMs) to play [Balatro](https://www.playbalatro.com/), the popular roguelike poker deck-building game. The bot analyzes game states, makes strategic decisions, and executes actions through the [BalatroBot](https://github.com/coder/balatrobot) client.

The system combines multiple components to make informed decisions:

- **Strategy templates** (`STRATEGY.md.jinja`) - Define the playing style and approach
- **Game state analysis** (`GAMESTATE.md.jinja`) - Current game situation and available options
- **Memory system** (`MEMORY.md.jinja`) - Historical context from previous decisions
- **Action tools** (`TOOLS.json`) - Available game actions and their parameters

These components are processed together in a single LLM call, enabling the bot to understand the current situation and perform the optimal tool call based on its configured strategy.

---

### 📋 Requirements

- [uv](https://docs.astral.sh/uv/) package manager
- Balatro instance with [BalatroBot](https://github.com/coder/balatrobot) mod installed

> [!IMPORTANT]
> Setting up Balatro with the BalatroBot mod requires careful configuration. Please refer to the [BalatroBot](https://github.com/coder/balatrobot) documentation and follow the instructions step by step.

### 📦 Installation

1. Clone the repository

```bash
git clone https://github.com/coder/balatrollm.git
cd balatrollm
```

2. Create environment and install dependencies

```bash
uv sync --no-dev
```

3. Activate environment

```bash
source .venv/bin/activate
```

> [!TIP]
> You can use [direnv](https://direnv.net/) to automatically activate the environment when you enter the project directory. The `.envrc.example` file contains an example configuration for direnv.


### ⚙️ LLM Configuration

BalatroLLM performs single requests to an OpenAI-compatible chat/completions endpoint. You need to configure:

- `--model`: LLM model identifier
- `--base-url`: OpenAI-compatible API base URL
- `--api-key`: API key (if required)

The default configuration uses [OpenRouter](https://openrouter.ai/), which provides access to many LLMs:

- `--model openai/gpt-oss-20b`: Small, fast, and affordable model
- `--base-url https://openrouter.ai/api/v1`: OpenRouter API base URL
- `--api-key $OPENROUTER_API_KEY`: It's recommended to export the API key in the `.envrc` file.

> [!TIP]
> After configuring the base URL and API key, you can check the available models by running `balatrollm --list-models`

---

### ⚡ Usage

The typical workflow to run BalatroLLM is:

1. Start Balatro with the BalatroBot mod:

```bash
bash balatro.sh
```

2. Run the bot, typically with multiple runs using the same configuration:

```bash
balatrollm --runs-per-seed 3 --seed ABCDEFG
```

3. Generate benchmark reports from the runs:

```bash
balatrobench --models
```

> [!TIP]
> You can run `bash balatro.sh --help`, `balatrollm --help`, and `balatrobench --help` to see all available options.

---

### 📚 Documentation

https://coder.github.io/balatrollm/
