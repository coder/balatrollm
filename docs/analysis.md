# Analysis

Generate comprehensive benchmarks, analyze performance metrics, and integrate with BalatroBench for detailed statistics visualization.

## Benchmark Generation

Run benchmarks to evaluate model performance:

```bash
balatrollm benchmark
```

## Benchmark Results

Benchmarks are organized hierarchically:

```
benchmarks/
├── v0.10.0/                    # Version
│   ├── default/                # Strategy
│   │   ├── leaderboard.json    # Strategy summary with aggregated stats
│   │   └── openai/             # Provider
│   │       ├── gpt-oss-20b.json        # Model performance summary
│   │       ├── gpt-oss-120b.json       # Model performance summary
│   │       ├── gpt-oss-20b/            # Individual runs for model
│   │       │   ├── 20250922_124308_887_RedDeck_s1__OOOO155/
│   │       │   │   ├── request-00001/  # Individual LLM request
│   │       │   │   │   ├── reasoning.md    # LLM reasoning process
│   │       │   │   │   ├── request.md      # Full request sent to LLM
│   │       │   │   │   ├── screenshot.png  # Game state screenshot
│   │       │   │   │   └── tool_call.json  # Function call details
│   │       │   │   ├── request-00002/
│   │       │   │   └── ...
│   │       │   └── [other runs]
│   │       └── gpt-oss-120b/           # Individual runs for model
│   │           └── [similar structure]
│   └── aggressive/             # Other strategies
│       └── [similar structure]
```

## BalatroBench Integration

### Overview

[BalatroBench](https://s1m0n38.github.io/balatrobench/) is a web-based dashboard for visualizing and comparing LLM performance in Balatro. It provides interactive charts, leaderboards, and detailed analytics.

### Integrating with BalatroBench

To use BalatroBench as a local dashboard for visualizing your benchmark results:

```bash
# Step 1: Generate runs with custom output directory
balatrollm --runs-dir example-runs --runs 20

# Step 2: Generate benchmark analysis
balatrollm benchmark --runs-dir example-runs --output-dir example-benchmark

# Step 3: Clone BalatroBench repository
git clone https://github.com/S1M0N38/balatrobench.git /path/to/balatrobench

# Step 4: Move benchmark data to BalatroBench (or create symbolic link)
mv example-benchmark/benchmarks /path/to/balatrobench/data/benchmarks
# OR create a symbolic link:
# ln -s $(pwd)/example-benchmark/benchmarks /path/to/balatrobench/data/benchmarks

# Step 5: Host BalatroBench locally
cd /path/to/balatrobench
python3 -m http.server 8001
# Then visit http://localhost:8001
```
