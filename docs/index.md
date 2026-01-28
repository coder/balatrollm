<style>
  .project-logos img {
    transition: transform 0.3s ease;
  }
  .project-logos img:hover {
    transform: scale(1.1);
  }
</style>

<div class="project-logos" style="display: flex; justify-content: center; align-items: flex-end; gap: 2rem; flex-wrap: wrap;">
  <figure style="text-align: center; margin: 0;">
    <a href="https://coder.github.io/balatrobot/">
      <img src="assets/balatrobot.svg" alt="BalatroBot" width="80">
    </a>
    <figcaption>
      <a href="https://coder.github.io/balatrobot/">BalatroBot</a><br>
      <small>API for developing Balatro bots</small>
    </figcaption>
  </figure>
  <figure style="text-align: center; margin: 0;">
    <a href="https://coder.github.io/balatrollm/">
      <img src="assets/balatrollm.svg" alt="BalatroLLM" width="120">
    </a>
    <figcaption>
      <a href="https://coder.github.io/balatrollm/">BalatroLLM</a><br>
      <small>Play Balatro with LLMs</small>
    </figcaption>
  </figure>
  <figure style="text-align: center; margin: 0;">
    <a href="https://balatrobench.com/">
      <img src="assets/balatrobench.svg" alt="BalatroBench" width="80">
    </a>
    <figcaption>
      <a href="https://balatrobench.com/">BalatroBench</a><br>
      <small>Benchmark LLMs playing Balatro</small>
    </figcaption>
  </figure>
</div>

---

BalatroLLM is a bot that uses Large Language Models (LLMs) to play [Balatro](https://www.playbalatro.com/), the popular roguelike poker deck-building game. The bot analyzes game states, makes strategic decisions, and executes actions through the [BalatroBot](https://github.com/coder/balatrobot) API.

<div class="grid cards" markdown>

- :material-download:{ .lg .middle } __Installation__

    ---

    Installation guide covering dependencies, environment setup, and API key configuration.

    [:octicons-arrow-right-24: Installation](installation.md)

- :material-console:{ .lg .middle } __CLI Reference__

    ---

    Reference for the `balatrollm` command-line interface, options, and usage examples.

    [:octicons-arrow-right-24: CLI Reference](cli.md)

- :material-strategy:{ .lg .middle } __Strategies__

    ---

    Learn how strategies work, their structure using Jinja2 templates, and how to contribute your own.

    [:octicons-arrow-right-24: Strategies](strategies.md)

- :octicons-people-24:{ .lg .middle } __Contributing__

    ---

    Guide for contributing to BalatroLLM development, including setup and coding standards.

    [:octicons-arrow-right-24: Contributing](contributing.md)

- :octicons-sparkle-fill-16:{ .lg .middle } __Documentation for LLM__

    ---

    Docs in [llms.txt](https://llmstxt.org/) format. Paste the following link (or its content) into the LLM.

    [:octicons-arrow-right-24: llms-full.txt](llms-full.txt)

</div>
