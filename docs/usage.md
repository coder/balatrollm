# Usage

Learn how to run BalatroLLM, configure strategies, and customize gameplay parameters.

## Simple Run

Assuming that you have followed the [setup guide](setup.md) and configured the provider, you can run BalatroLLM with the following steps:

1. Start Balatro with the BalatroBot mod using the utility script:

```bash
bash balatro.sh
```

2. Start BalatroLLM:

```bash
balatrollm --model openai/gpt-oss-20b
```

3. Watch the gameplay!

## Advanced Usage

### BalatroBot

The `BALATROBOT_*` variables are used to configure Balatro and BalatroBot. It is recommended to set the variables that you don't change often in the `.envrc`.

- `BALATROBOT_HOST`: The host to run the server on. Defaults to `127.0.0.1`.
- `BALATROBOT_PORT`: The port to run the server on. Defaults to `12346`.

- `BALATROBOT_HEADLESS`: Avoid rendering the game on the screen. Set to `1` to enable.
- `BALATROBOT_FAST`: Faster animations and gameplay. Set to `1` to enable.
- `BALATROBOT_AUDIO`: Enable audio. Set to `1` to enable.
- `BALATROBOT_RENDER_ON_API`: Render the frame only on an API call.

These are the environment variables set by `balatro.sh` using its flags. For example, to run the game in fast mode, you can run: `bash balatro.sh --fast`.

Usually, you don't need to set these variables manually.

### BalatroLLM

The `BALATROLLM_*` variables are used as defaults for the BalatroLLM CLI. It is recommended to set the variables that you don't change often in the `.envrc`.

- `BALATROLLM_BASE_URL`: The base URL to use. (required)
- `BALATROLLM_API_KEY`: The API key to use. (usually required)
- `BALATROLLM_MODEL`: The model to use. (required)

- `BALATROLLM_STRATEGY`: The strategy to use. (default: `default`)
- `BALATROLLM_RUNS_PER_SEED`: The number of runs per seed. (default: `1`)
- `BALATROLLM_SEEDS`: The seeds to use. If empty, a random seed is used. You can also use a comma-separated list of seeds.
- `BALATROLLM_NO_SCREENSHOT`: Whether to take screenshots. Screenshots are not available in headless mode. (default: `0`, i.e. take screenshots)
- `BALATROLLM_USE_DEFAULT_PATHS`: Whether to use BalatroBot's default storage paths. It's not recommended to change this. (default: `0`)

Each of these variables has a corresponding BalatroLLM CLI flag. For example, `--model` is the BalatroLLM CLI flag for `BALATROLLM_MODEL`.

### Examples

- Run on two seeds (3 runs each):

```
bash balatro.sh --fast
balatrollm \
  --model openai/gpt-oss-20b \
  --seeds AAAAAAA,BBBBBBB \
  --runs-per-seed 3
```

- Run faster across 2 Balatro instances in parallel:

```
bash balatro.sh --fast --ports 12346,12347
balatrollm \
  --model openai/gpt-oss-20b \
  --seeds AAAAAAA,BBBBBBB \
  --runs-per-seed 3 \
  --ports 12346,12347
```

- Run even faster in headless mode:

```
bash balatro.sh --headless --fast --ports 12346,12347
balatrollm \
  --model openai/gpt-oss-20b \
  --seeds AAAAAAA,BBBBBBB \
  --runs-per-seed 3 \
  --ports 12346,12347 \
  --no-screenshot
```

- Run on resource-constrained devices with screenshots:

```
bash balatro.sh --fast --render-on-api
balatrollm \
  --model openai/gpt-oss-20b \
  --seeds AAAAAAA,BBBBBBB \
  --runs-per-seed 3
```

## Models

If you have configured the provider, you should be able to see the available models by running

```bash
balatrollm --list-models
```

Before using a model, ensure that the model (exact name) is already present in the `config/models.yaml` file. This YAML file is used for model configuration. Update it accordingly to run balatrollm with the model of your choice.

The current model configuration includes some of the models supported by [OpenRouter](https://openrouter.ai/). This is the provider we are using to run balatrollm with various models.

## Strategies

Strategies define how the LLM bot approaches decision-making during gameplay. Each strategy consists of Jinja2 templates that generate the prompts sent to the language model, providing different playing styles and approaches.

BalatroLLM ships with two built-in strategies:

- **default**: Conservative, financially disciplined approach
- **aggressive**: High-risk, high-reward strategy with aggressive spending

To run balatrollm with a specific strategy, use the `--strategy` flag:

```bash
balatrollm --strategy default
```

```bash
balatrollm --strategy aggressive
```

For detailed information about how strategies work, their structure, and how to contribute your own strategies, see the [Strategies documentation](strategies.md).
