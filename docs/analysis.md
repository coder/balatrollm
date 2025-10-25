# Analysis

Analyze run data, generate performance benchmarks, and visualize results with BalatroBench.

## Run Data Collection

When you run BalatroLLM, all game data is automatically collected and organized in the `runs` directory. Each run is stored in a hierarchical structure that makes it easy to compare different models, strategies, and game sessions.

```
runs/
└── v0.13.2/                          # Version
    └── default/                      # Strategy
        └── openai/                   # Vendor
            └── gpt-oss-20b/          # Model
                └── 20251024_120206_331_RedDeck_s1__AAAAAAA/  # Run directory
                    ├── config.json           # Model configuration and API settings
                    ├── strategy.json         # Strategy template used
                    ├── stats.json            # Aggregated performance metrics
                    ├── gamestates.jsonl      # Game state at each decision point
                    ├── requests.jsonl        # Prompts sent to the LLM
                    ├── responses.jsonl       # Model responses and actions
                    ├── run.log               # Complete text log
                    └── screenshots/          # PNG images of game states
```

Each run directory contains several files that capture different aspects of the game session. The configuration and strategy files record the setup used for the run. The stats file contains aggregated performance metrics like total rounds completed, token usage, and costs. The three JSONL files log every step of the game, recording game states, LLM prompts, and model responses. The run log provides a complete text record, and the screenshots directory contains PNG images of the game state at each step (when screenshot mode is enabled).

## Benchmark Analysis

The `balatrobench` CLI tool processes run data to generate comprehensive benchmark statistics and leaderboards. Benchmarks can be generated in two different modes depending on what you want to analyze.

### Models

Use the models mode when you want to compare how different models perform within the same strategy. This mode is useful for answering questions like "Which model plays the default strategy best?" or "How do different vendors' models compare on the aggressive strategy?"

```bash
balatrobench --models
```

The results are organized with leaderboards for each strategy, making it easy to identify the top-performing models:

```
benchmarks/models/
├── manifest.json
└── v0.13.2/                          # Version
    └── default/                      # Strategy
        ├── leaderboard.json          # Models ranked for this strategy
        └── openai/                   # Vendor
            ├── gpt-oss-20b/          # Model
            │   └── 20251024_120206_331_RedDeck_s1__AAAAAAA/  # Run
            │       └── request-00001/         # Individual request
            │           ├── request.md         # Full LLM prompt
            │           ├── reasoning.md       # Model reasoning
            │           ├── tool_call.json     # Action taken
            │           └── screenshot.png     # Game state
            └── gpt-oss-20b.json      # Aggregated model statistics
```

### Strategies

Use the strategies mode when you want to compare how different strategies perform for the same model. This mode helps answer questions like "Does the aggressive strategy work better than the default for GPT-4?" or "Which strategy should I use with Claude?"

```bash
balatrobench --strategies
```

The strategies mode generates leaderboards organized by model, with statistics for each strategy:

```
benchmarks/strategies/
├── manifest.json
└── v0.13.2/                          # Version
    └── openai/                       # Vendor
        └── gpt-oss-20b/              # Model
            ├── leaderboard.json      # Strategies ranked for this model
            ├── default/              # Strategy
            │   ├── stats.json        # Aggregated statistics
            │   └── gpt-oss-20b/      # Run details
            │       └── 20251024_120206_331_RedDeck_s1__AAAAAAA/  # Run
            │           └── request-00001/         # Individual request
            │               ├── request.md         # Full LLM prompt
            │               ├── reasoning.md       # Model reasoning
            │               ├── tool_call.json     # Action taken
            │               └── screenshot.png     # Game state
            └── aggressive/           # Other strategies
                └── [similar structure]
```

Both modes preserve detailed request-level data including the full LLM prompts, reasoning output, tool calls, and screenshots for in-depth analysis.

## BalatroBench Integration

[BalatroBench](https://coder.github.io/balatrobench/) is a web-based dashboard for visualizing benchmark results. You can run it locally to explore your data through interactive charts and leaderboards.

First, clone the BalatroBench repository:

```bash
git clone https://github.com/coder/balatrobench.git
```

Next, copy or symlink your benchmark data into the BalatroBench data directory. You can move the benchmarks directly:

```bash
mv benchmarks /path/to/balatrobench/data/benchmarks
```

Or create a symbolic link to keep the data in your BalatroLLM directory:

```bash
ln -s $(pwd)/benchmarks /path/to/balatrobench/data/benchmarks
```

Finally, start a local web server to view the dashboard:

```bash
cd /path/to/balatrobench
python3 -m http.server 8001
```

Open your browser to `http://localhost:8001` to explore the interactive visualization of your benchmark results.
