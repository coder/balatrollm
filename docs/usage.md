# Usage

Learn how to run BalatroLLM, configure strategies, and customize gameplay parameters.

## Basic Usage

### Simple Bot Run

Start a basic bot session with default settings:

```bash
# Run once with default model and strategy
balatrollm

# Run with a specific model
balatrollm --model openai/gpt-oss-120b

# Run multiple times for consistency testing
balatrollm --runs 5
```

### Model Selection

List and choose from available models:

```bash
# See all available models
balatrollm --list-models

# Popular models for different use cases
balatrollm --model openai/gpt-oss-20b        # Default, good balance
balatrollm --model openai/gpt-oss-120b       # More powerful
balatrollm --model qwen/qwen3-235b-a22b-2507 # Alternative provider
balatrollm --model x-ai/grok-code-fast-1     # Fast responses
```

## Strategy Configuration

### Built-in Strategies

BalatroLLM includes pre-configured strategies:

```bash
# Conservative, financially disciplined approach (default)
balatrollm --strategy default

# High-risk, high-reward approach
balatrollm --strategy aggressive
```

### Strategy Behavior

Each strategy has different characteristics:

- **Default Strategy**: Conservative play, careful resource management, long-term planning
- **Aggressive Strategy**: Bold plays, higher spending, risk-taking for bigger rewards

## Advanced Configuration

### Custom API Providers

Use different LLM providers:

```bash
# OpenRouter (default)
balatrollm --base-url https://openrouter.ai/api/v1 --api-key $OPENROUTER_API_KEY

# Custom OpenAI-compatible API
balatrollm --base-url https://api.example.com/v1 --api-key your-key

# Local LLM server
balatrollm --base-url http://localhost:1234/v1 --api-key local
```

### Port Configuration

Run on different ports for parallel execution:

```bash
# Single instance on custom port
balatrollm --port 12347

# Multiple ports for parallel runs
balatrollm --port 12346 --port 12347 --runs 10
```

### Data Organization

Control where run data is stored:

```bash
# Custom runs directory
balatrollm --runs-dir ./my-experiments

# Load configuration from previous run
balatrollm --config ./runs/v0.10.0/default/openrouter/gpt-oss-20b/20240922_red_deck_12345/config.json
```

### Storage and Output Options

Control screenshot and file output behavior:

```bash
# Disable screenshots (ideal for headless mode)
balatrollm --no-screenshot

# Use BalatroBot's default paths (ideal for distributed systems)
balatrollm --use-default-paths

# Combine both for optimized distributed/headless setups
balatrollm --no-screenshot --use-default-paths
```

## Parallel Execution

### Multiple Instances

Run multiple bot instances simultaneously:

```bash
# Start multiple Balatro instances
./balatro.sh -p 12346 -p 12347 -p 12348

# Run bots in parallel
balatrollm --port 12346 --port 12347 --port 12348 --runs 15
```

### Distributed Systems

Run balatrollm and BalatroBot on different systems:

```bash
# Docker containers and remote deployments
balatrollm --use-default-paths

# Containerized environments (no GUI, optimized storage)
balatrollm --no-screenshot --use-default-paths

# High-volume distributed testing
balatrollm --use-default-paths --runs 100 --model x-ai/grok-code-fast-1
```

### Performance Optimization

For faster execution:

```bash
# Use headless mode
./balatro.sh --headless --fast

# Choose faster models
balatrollm --model x-ai/grok-code-fast-1

# Optimize for automated/headless environments
balatrollm --no-screenshot --model x-ai/grok-code-fast-1

# Combine multiple optimizations
./balatro.sh --headless --fast -p 12346 -p 12347
balatrollm --model x-ai/grok-code-fast-1 --no-screenshot --port 12346 --port 12347 --runs 20
```

## Configuration Files

### Loading Previous Configurations

Reuse successful configurations:

```bash
# Load exact configuration from previous run
balatrollm --config path/to/config.json

# Override specific parameters
balatrollm --config path/to/config.json --model different/model --runs 10
```

### Environment Variables

Set defaults in your environment:

```bash
# In .envrc or shell profile
export OPENROUTER_API_KEY="your-key"
export BALATROLLM_MODEL="openai/gpt-oss-120b"
export BALATROLLM_STRATEGY="aggressive"
export BALATROLLM_RUNS_DIR="./experiments"

# Use environment defaults
balatrollm
```

## Game Management

### Balatro Instance Control

Manage Balatro game instances:

```bash
# Start single instance
./balatro.sh

# Start multiple instances
./balatro.sh -p 12346 -p 12347 -p 12348

# Check running instances
./balatro.sh --status

# Kill all instances
./balatro.sh --kill

# Start with performance optimizations
./balatro.sh --headless --fast --audio
```

### Monitoring Runs

Track bot progress:

```bash
# Run with verbose output
balatrollm --runs 10 | tee bot_output.log

# Monitor multiple parallel runs
balatrollm --port 12346 --port 12347 --runs 20 &
balatrollm --port 12348 --port 12349 --runs 20 &
wait
```

## Troubleshooting

### Common Issues

**Bot won't connect:**

```bash
# Check Balatro is running
./balatro.sh --status

# Verify port availability
netstat -an | grep 12346

# Test with different port
balatrollm --port 12347
```

**API errors:**

```bash
# Test API connectivity
balatrollm --list-models

# Try different model
balatrollm --model openai/gpt-oss-20b

# Check API key
echo $OPENROUTER_API_KEY
```

**Performance issues:**

```bash
# Use faster model
balatrollm --model x-ai/grok-code-fast-1

# Enable optimizations
./balatro.sh --headless --fast

# Reduce parallel instances
balatrollm --port 12346 --runs 5
```
