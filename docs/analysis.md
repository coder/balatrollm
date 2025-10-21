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

[BalatroBench](https://coder.github.io/balatrobench/) is a web-based dashboard for visualizing and comparing LLM performance in Balatro. It provides interactive charts, leaderboards, and detailed analytics.

### Integrating with BalatroBench

To use BalatroBench as a local dashboard for visualizing your benchmark results:

```bash
# Step 1: Generate runs with custom output directory
balatrollm --runs-dir example-runs --runs 20

# Step 2: Generate benchmark analysis
balatrollm benchmark --runs-dir example-runs --output-dir example-benchmark

# Step 3: Clone BalatroBench repository
git clone https://github.com/coder/balatrobench.git /path/to/balatrobench

# Step 4: Move benchmark data to BalatroBench (or create symbolic link)
mv example-benchmark/benchmarks /path/to/balatrobench/data/benchmarks
# OR create a symbolic link:
# ln -s $(pwd)/example-benchmark/benchmarks /path/to/balatrobench/data/benchmarks

# Step 5: Host BalatroBench locally
cd /path/to/balatrobench
python3 -m http.server 8001
# Then visit http://localhost:8001
```

## BalatroBench Dashboard Views

BalatroBench provides three primary views for analyzing LLM performance in Balatro, each offering different levels of detail and insights into model behavior and strategic decision-making.

### 1. Main Leaderboard and Performance Overview

The main dashboard presents a comprehensive comparison of all evaluated models, combining visual and tabular representations of performance metrics.

![Main Leaderboard - Light Theme](assets/balatrobench-light-1.png#only-light)
![Main Leaderboard - Dark Theme](assets/balatrobench-dark-1.png#only-dark)

**Visual Performance Comparison**

The top section features an interactive bar chart displaying average performance across models, with each bar representing the mean number of rounds achieved. Error bars indicate the standard deviation, providing insight into performance consistency. Models are color-coded for easy identification, with higher-performing models typically shown in more prominent colors (purple for top performers, progressing through gray, green, and blue for lower performers).

**Detailed Leaderboard Table**

Below the chart, a comprehensive table provides granular performance metrics for each model:

- **Model & Vendor**: Lists the specific model name and its provider (x-ai, openai, google, deepseek)

- **Round Performance**: Shows average rounds achieved with standard deviation, indicating both performance level and consistency

- **Success Rate Indicators**: Three color-coded percentage columns:

    - **Green (✓)**: Successful round completions
    - **Yellow (⚠)**: Partial completions or warnings
    - **Red (✗)**: Failed attempts or errors

- **Financial Metrics**:

    - **In $/¥**: Input token costs with standard deviation
    - **Out $/¥**: Output token costs with standard deviation

- **Performance Timing**:

    - **Duration**: Average time per decision with variability measures
    - **Total Cost**: Comprehensive cost analysis including standard deviations

This view enables researchers to quickly identify top-performing models, understand cost-performance trade-offs, and assess model reliability through consistency metrics.

### 2. Model Details and Analytics

Clicking on any model in the leaderboard expands to reveal detailed analytics and run breakdowns for that specific model.

![Model Details - Light Theme](assets/balatrobench-light-2.png#only-light)
![Model Details - Dark Theme](assets/balatrobench-dark-2.png#only-dark)

**Performance Distribution Analysis**

The expanded view includes three key analytical components:

**Rounds Distribution Histogram**: A bar chart showing the frequency distribution of rounds achieved across all runs for the selected model. This reveals whether the model's performance is consistent or highly variable, with patterns indicating:

- Consistent performers show narrow, tall distributions
- Variable performers show wide, scattered distributions
- Multi-modal distributions may indicate different strategic approaches

**Provider Breakdown**: A donut chart visualizing the proportion of runs from different API providers, useful for understanding data source diversity and potential provider-specific performance variations.

**Aggregated Statistics Panel**: A summary box displaying key totals:

- **Input/Output Token Counts**: Total tokens processed across all runs
- **Financial Totals**: Cumulative costs in dollars
- **Total Processing Time**: Aggregate time spent on decision-making

**Individual Run Analysis Table**

The bottom section provides a detailed breakdown of individual game runs, with each row representing a complete Balatro session:

- **Round-by-Round Results**: Shows progression through different game rounds with success/warning/failure indicators
- **Performance Metrics**: Input/output costs and timing for each individual run
- **Success Patterns**: Color-coded indicators help identify at which stages models typically succeed or fail

This view helps researchers understand model behavior patterns, identify optimal performance conditions, and analyze the relationship between different performance factors.

### 3. Individual Run Analysis

The most detailed view opens when clicking on a specific run, providing a step-by-step analysis of the LLM's decision-making process throughout a complete Balatro game session.

![Run Details - Light Theme](assets/balatrobench-light-3.png#only-light)
![Run Details - Dark Theme](assets/balatrobench-dark-3.png#only-dark)

**Game State Visualization**

The left panel displays an actual screenshot of the Balatro game state at the moment of decision, showing:

- **Current Game Phase**: Whether in shop, hand selection, or other game modes
- **Available Options**: Cards, jokers, and other game elements visible to the LLM
- **Resource Status**: Money, joker slots, and other strategic resources
- **Visual Context**: The exact visual information the LLM uses for decision-making

**Strategic Analysis Panel**

The right panel provides comprehensive insight into the LLM's reasoning process:

**Contextual Situation Analysis**: A detailed text description explaining:

- Current game state and available options
- Strategic considerations and constraints
- Resource management situation
- Previous game history and context

**LLM Reasoning Process**: The model's internal reasoning, showing:

- Strategic analysis of available options
- Cost-benefit calculations
- Risk assessment considerations
- Long-term planning thoughts
- Decision rationale and justification

**Function Call Details**: Technical information about the executed action:

- **Function Name**: The specific game action taken (e.g., "shop", "select_hand")
- **Parameters**: Exact arguments passed to the game engine
- **Action Description**: Human-readable explanation of what the model decided to do
- **Strategic Reasoning**: Why this particular action was chosen

**Navigation and Analysis Tools**

- **Step Navigation**: Arrow controls allow researchers to move through the chronological sequence of decisions within a single game run
- **Request Numbering**: Clear labeling of each decision point for reference and analysis
- **Modal Interface**: Clean overlay design that allows easy comparison with the main dashboard

This detailed view enables researchers to:

- Understand exactly how LLMs interpret visual game states
- Analyze the quality and depth of strategic reasoning
- Identify decision-making patterns and potential improvements
- Debug specific failure modes or suboptimal choices
- Study the relationship between reasoning quality and performance outcomes

The combination of visual game state, strategic reasoning, and technical execution details provides a complete picture of LLM behavior in complex, multi-step decision-making scenarios.
