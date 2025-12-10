<div style="display: flex; justify-content: center;">
  <figure style="text-align: center; margin: 0;">
    <a href="https://coder.github.io/balatrollm/">
      <img src="assets/balatrollm.svg" alt="BalatroLLM" width="170">
    </a>
    <figcaption>
      <a href="https://coder.github.io/balatrollm/">BalatroLLM</a><br>
      <small>Play Balatro with LLMs</small>
    </figcaption>
  </figure>
</div>

---

BalatroLLM is a bot that uses Large Language Models (LLMs) to play [Balatro](https://www.playbalatro.com/), the popular roguelike poker deck-building game. The bot analyzes game states, makes strategic decisions, and executes actions through the [BalatroBot](https://github.com/coder/balatrobot) client.

!!! warning "Breaking Changes"

    **BalatroLLM 1.0.0 introduces breaking changes:**

    - **Requires BalatroBot 1.x**: This version is strictly compatible only with BalatroBot 1.x versions. Ensure your BalatroBot mod is updated.

<div class="grid cards" markdown>

- :material-cog:{ .lg .middle } __Setup__

    ---

    Installation guide covering dependencies, environment setup, and API key configuration.

    [:octicons-arrow-right-24: Setup](setup.md)

- :material-play:{ .lg .middle } __Usage__

    ---

    Learn how to run the bot, configure strategies, and customize gameplay parameters.

    [:octicons-arrow-right-24: Usage](usage.md)

- :material-chart-line:{ .lg .middle } __Analysis__

    ---

    Generate benchmarks, analyze performance metrics, and integrate with BalatroBench for comprehensive statistics.

    [:octicons-arrow-right-24: Analysis](analysis.md)

- :material-strategy:{ .lg .middle } __Strategies__

    ---

    Learn how strategies work, their structure using Jinja2 templates, and how to contribute your own.

    [:octicons-arrow-right-24: Strategies](strategies.md)

- :octicons-sparkle-fill-16:{ .lg .middle } __Documentation for LLM__

    ---

    Docs in [llms.txt](https://llmstxt.org/) format. Paste the following link (or its content) into the LLM.

    [:octicons-arrow-right-24: llms-full.txt](llms-full.txt)

</div>

## Related Projects

<div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap;">
  <figure style="text-align: center; margin: 0;">
    <a href="https://coder.github.io/balatrobot/">
      <img src="assets/balatrobot.svg" alt="BalatroBot" width="92">
    </a>
    <figcaption>
      <a href="https://coder.github.io/balatrobot/">BalatroBot</a><br>
      <small>API for developing Balatro bots</small>
    </figcaption>
  </figure>
  <figure style="text-align: center; margin: 0;">
    <a href="https://coder.github.io/balatrollm/">
      <img src="assets/balatrollm.svg" alt="BalatroLLM" width="92">
    </a>
    <figcaption>
      <a href="https://coder.github.io/balatrollm/">BalatroLLM</a><br>
      <small>Play Balatro with LLMs</small>
    </figcaption>
  </figure>
  <figure style="text-align: center; margin: 0;">
    <a href="https://coder.github.io/balatrobench/">
      <img src="assets/balatrobench.svg" alt="BalatroBench" width="92">
    </a>
    <figcaption>
      <a href="https://coder.github.io/balatrobench/">BalatroBench</a><br>
      <small>Benchmark LLMs playing Balatro</small>
    </figcaption>
  </figure>
</div>
