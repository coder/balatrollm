# Analysis

Generate comprehensive benchmarks, analyze performance metrics, and integrate with BalatroBench for detailed statistics visualization.

## Benchmark Generation

### Basic Benchmarking

Run benchmarks to evaluate model performance:

```bash
# Benchmark current configuration
balatrollm benchmark

# Benchmark specific model across strategies
balatrollm --model openai/gpt-oss-120b benchmark

# Benchmark with multiple runs for statistical significance
balatrollm --runs 20 benchmark
```

### Comprehensive Benchmarking

Generate benchmarks across multiple dimensions:

```bash
# Benchmark all models with default strategy
make balatrobench

# Benchmark specific strategy across models
balatrollm --strategy aggressive --runs 15 benchmark

# Benchmark multiple strategies and models
for strategy in default aggressive; do
  for model in openai/gpt-oss-20b openai/gpt-oss-120b qwen/qwen3-235b-a22b-2507; do
    balatrollm --strategy $strategy --model $model --runs 10 benchmark
  done
done
```

## Benchmark Results

### Result Structure

Benchmarks are organized hierarchically:

```
benchmarks/
├── v0.10.0/                    # Version
│   ├── default/                # Strategy
│   │   ├── openrouter/         # Provider
│   │   │   ├── gpt-oss-20b.json
│   │   │   └── gpt-oss-120b.json
│   │   └── leaderboard.json    # Strategy summary
│   └── aggressive/
│       ├── openrouter/
│       └── leaderboard.json
```

### Understanding Metrics

Key performance indicators in benchmark results:

- **Win Rate**: Percentage of games won
- **Average Score**: Mean final score across runs
- **Consistency**: Standard deviation of scores
- **Efficiency**: Score per ante progression
- **Strategy Adherence**: How well the bot follows strategy guidelines

## BalatroBench Integration

### Overview

[BalatroBench](https://s1m0n38.github.io/balatrobench/) is a web-based dashboard for visualizing and comparing LLM performance in Balatro. It provides interactive charts, leaderboards, and detailed analytics.

*[Screenshot placeholder: BalatroBench dashboard showing model comparison]*

### Uploading Results

Integrate your local benchmark results with BalatroBench:

```bash
# Generate benchmarks locally
balatrollm --runs 20 benchmark

# Upload to BalatroBench (coming soon)
balatrollm benchmark --upload

# Or manually copy results to BalatroBench format
cp benchmarks/v0.10.0/default/leaderboard.json /path/to/balatrobench/data/
```

### Viewing Results

Access comprehensive analytics through the web interface:

1. **Model Comparison**: Side-by-side performance metrics
2. **Strategy Analysis**: How different strategies perform across models
3. **Trend Analysis**: Performance changes over time
4. **Detailed Breakdowns**: Ante-by-ante progression analysis

*[Screenshot placeholder: Model comparison view in BalatroBench]*

## Local Analysis

### Command-Line Analysis

Analyze results directly from the command line:

```bash
# View latest benchmark summary
cat benchmarks/v0.10.0/default/leaderboard.json | jq

# Compare models
jq '.models[] | {name: .model, win_rate: .metrics.win_rate, avg_score: .metrics.avg_score}' \
  benchmarks/v0.10.0/default/leaderboard.json

# Find top performer
jq '.models | sort_by(.metrics.avg_score) | reverse | .[0]' \
  benchmarks/v0.10.0/default/leaderboard.json
```

### Custom Analysis Scripts

Create custom analysis for specific insights:

```bash
# Calculate model efficiency (score per run)
find benchmarks -name "*.json" -not -name "leaderboard.json" | \
  xargs jq -r '[.model, (.total_score / .total_runs)] | @csv'

# Compare strategies for same model
diff <(jq '.models[] | select(.model=="gpt-oss-20b") | .metrics' \
       benchmarks/v0.10.0/default/leaderboard.json) \
     <(jq '.models[] | select(.model=="gpt-oss-20b") | .metrics' \
       benchmarks/v0.10.0/aggressive/leaderboard.json)
```

## Performance Tracking

### Continuous Monitoring

Set up automated benchmarking:

```bash
# Daily benchmark script
#!/bin/bash
DATE=$(date +%Y%m%d)
balatrollm --runs 5 --runs-dir "daily_benchmarks/$DATE" benchmark
```

### Regression Testing

Monitor performance across versions:

```bash
# Compare current version to previous
jq '.models[] | {model, current: .metrics.avg_score}' \
  benchmarks/v0.10.0/default/leaderboard.json > current.json

jq '.models[] | {model, previous: .metrics.avg_score}' \
  benchmarks/v0.9.0/default/leaderboard.json > previous.json

# Join and compare
jq -s 'add | group_by(.model) | map(add)' current.json previous.json
```

## Interpreting Results

### Statistical Significance

Ensure reliable results:

```bash
# Run sufficient samples for confidence
balatrollm --runs 30 benchmark  # Minimum recommended

# Check variance in results
jq '.detailed_runs[] | .final_score' benchmarks/latest/model.json | \
  awk '{sum+=$1; sumsq+=$1*$1} END {print "Mean:", sum/NR, "StdDev:", sqrt((sumsq-sum*sum/NR)/NR)}'
```

### Model Selection Criteria

Choose models based on your priorities:

- **Consistency**: Low standard deviation in scores
- **Peak Performance**: Highest maximum scores achieved
- **Win Rate**: Reliability in completing games successfully
- **Speed**: Faster response times for real-time applications

### Strategy Optimization

Use results to refine strategies:

```bash
# Identify successful patterns
jq '.detailed_runs[] | select(.final_score > 8000) | .strategy_decisions' \
  benchmarks/v0.10.0/aggressive/openrouter/gpt-oss-120b.json

# Find failure modes
jq '.detailed_runs[] | select(.final_score < 2000) | .failure_reason' \
  benchmarks/v0.10.0/default/openrouter/gpt-oss-20b.json
```
