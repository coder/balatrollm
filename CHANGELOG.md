# Changelog

## [0.8.1](https://github.com/S1M0N38/balatrollm/compare/v0.8.0...v0.8.1) (2025-09-08)


### Bug Fixes

* add pyyaml missing dependency ([dbd91cd](https://github.com/S1M0N38/balatrollm/commit/dbd91cdd8581e9ad6ba98d057a38d815fc733492))
* update completed gamestate ([#13](https://github.com/S1M0N38/balatrollm/issues/13)) ([a2463b6](https://github.com/S1M0N38/balatrollm/commit/a2463b67d60a2156dc7165d686769726ae391195))


### Documentation

* remove release process form CONTRIBUTING.md ([3763cec](https://github.com/S1M0N38/balatrollm/commit/3763cecc33b6949b056865f2d6a1647a86839048))

## [0.8.0](https://github.com/S1M0N38/balatrollm/compare/v0.7.0...v0.8.0) (2025-09-06)


### Features

* add model-specific config loading ([15d71d9](https://github.com/S1M0N38/balatrollm/commit/15d71d9926ee91b110f6e1515bb80ec8278eb7d7))
* **bot:** improve error handling and LLM integration ([310799c](https://github.com/S1M0N38/balatrollm/commit/310799c5cd5761b571c8a39ad72579ff74922668))
* move to openrouter ([6a0f4fa](https://github.com/S1M0N38/balatrollm/commit/6a0f4fad2408bf3296a209a0cb1aaa4f90591318))
* remove litellm dependency ([28fb425](https://github.com/S1M0N38/balatrollm/commit/28fb425b7f0b9ebe748248b13fab1fef31fb76df))
* replace litellm config with models.yaml ([446d981](https://github.com/S1M0N38/balatrollm/commit/446d981fe6465b7668dce878b5851348ba14a644))
* use model config for model parameters ([3576fd5](https://github.com/S1M0N38/balatrollm/commit/3576fd522738e64c7cf83f45c471463f0548723a))


### Documentation

* add strategy submission guidelines ([03cc82d](https://github.com/S1M0N38/balatrollm/commit/03cc82dae171b64ec3621bf109a309c353b8e01d))
* update CLI and documentation for direct OpenRouter integration ([00a061d](https://github.com/S1M0N38/balatrollm/commit/00a061d793f4f70a00186b9f95c33974e50ba3d6))

## [0.7.0](https://github.com/S1M0N38/balatrollm/compare/v0.6.0...v0.7.0) (2025-09-03)


### Features

* add configurable port for balatrobot client ([3a5cb23](https://github.com/S1M0N38/balatrollm/commit/3a5cb23cc8ff62c324a258540bf9584f192e0d5f))
* add extra_headers to requests for App identification ([65436cb](https://github.com/S1M0N38/balatrollm/commit/65436cb2ba2e7abca1a0db523b91caec7e7711dd))
* add extra_headers to requests for App identification ([2ed4a1e](https://github.com/S1M0N38/balatrollm/commit/2ed4a1e5b9a538d15b4b5ff50ff7ed45f493c1d5))
* add fields provided by OpenRouter to stats.json ([af97295](https://github.com/S1M0N38/balatrollm/commit/af97295327c9afea8338feb0a279bc5ebe00b321))
* add fields provided by OpenRouter to stats.json ([f4cd7fb](https://github.com/S1M0N38/balatrollm/commit/f4cd7fb9aaebe6dbc05b490bbdd05736afd20571))
* make balatro instance configurable in Makefile ([1f7ad4b](https://github.com/S1M0N38/balatrollm/commit/1f7ad4b6fe1736b6644ec3fe60c99d47b7d7bee3))
* parallelize runs over multiple ports ([75286fa](https://github.com/S1M0N38/balatrollm/commit/75286faac2c448601711360ae05683e430cb4d20))
* parallelize runs with multiple ports ([7169a24](https://github.com/S1M0N38/balatrollm/commit/7169a2493e119dd30ba1802a4e6b4864bce1cdc6))
* stop game on 3 consecutive failed/error calls ([3e25508](https://github.com/S1M0N38/balatrollm/commit/3e2550895d41c358ecf95345a8413faea7e7ee05))
* update benchmark with new openrouter fields ([0c4c8a5](https://github.com/S1M0N38/balatrollm/commit/0c4c8a5eec5718dd5fa08b76526c29c5f11f444d))
* update default model to openai/gpt-oss-20b ([c6b7cdc](https://github.com/S1M0N38/balatrollm/commit/c6b7cdca043ee8d7874c4f109fc6bbc0531f713e))
* update default model to openai/gpt-oss-20b ([70bffc7](https://github.com/S1M0N38/balatrollm/commit/70bffc778a4e34db4059d38ef507dff459cd2d72))
* use openrouter in litellm config ([6a42fe0](https://github.com/S1M0N38/balatrollm/commit/6a42fe0331477eea2f10dc5da2f497974caa1c21))
* use openrouter in litellm config ([85e9d22](https://github.com/S1M0N38/balatrollm/commit/85e9d22e25d4daff4ca26a901f4c6bff50986ca6))


### Bug Fixes

* update balatrobench command to new models ([de5222d](https://github.com/S1M0N38/balatrollm/commit/de5222dab820be4d740fe10bdf82eb8a65edda1b))
* update balatrobench command to new models ([5042746](https://github.com/S1M0N38/balatrollm/commit/50427462b61ec57e6d86cf4adafbd11f19789b65))
* use invalid_responses instead of error_calls ([9a09569](https://github.com/S1M0N38/balatrollm/commit/9a095691dffd850d8b3c5ef72d402748a5c0550e))


### Documentation

* update help for balatrollm ([6b4a515](https://github.com/S1M0N38/balatrollm/commit/6b4a5155f5feba19dc7682fe1516afb85f804d86))

## [0.6.0](https://github.com/S1M0N38/balatrollm/compare/v0.5.0...v0.6.0) (2025-09-02)


### Features

* add last_response_is_invalid and last_tool_called_failed to LLMBot ([7ae6d4a](https://github.com/S1M0N38/balatrollm/commit/7ae6d4aed596929e02165e703546a0ec719aa6d8))
* make use of error messages in memory ([1c8bc14](https://github.com/S1M0N38/balatrollm/commit/1c8bc14c3292df19d810948c0e14cf1d9b63978e))
* update data collection to include invalid responses ([18e7341](https://github.com/S1M0N38/balatrollm/commit/18e73412459af15e7cb3caea1eb0f49f7869240b))
* update default MEMORY strategy with previous errors ([c02a9b0](https://github.com/S1M0N38/balatrollm/commit/c02a9b0d59c398af206de7cbaac64a5f2a6cdf0f))


### Bug Fixes

* comment BotError to BalatroError ([4b42402](https://github.com/S1M0N38/balatrollm/commit/4b4240299c97a355d8c839896f0c8b6d5b157cf2))
* remove reasoning effort from qwen-3-32b config ([17265db](https://github.com/S1M0N38/balatrollm/commit/17265dbd3cc873768526e307a8694f52bf3708d3))
* typos in data_collection.py ([17e0542](https://github.com/S1M0N38/balatrollm/commit/17e054256f9f397f54d860a7c4694c0e1d4860b4))
* use logger instead of logging in bot.py ([d69ba00](https://github.com/S1M0N38/balatrollm/commit/d69ba00865c9d6cd3679376e36e05895dc58ca9d))

## [0.5.0](https://github.com/S1M0N38/balatrollm/compare/v0.4.0...v0.5.0) (2025-09-01)


### Features

* add benchmark command in Makefile ([dcf0c56](https://github.com/S1M0N38/balatrollm/commit/dcf0c56384c10f8124bfa5097ba35261999b2162))
* add multi-run support and improve CLI argument handling ([fd9219a](https://github.com/S1M0N38/balatrollm/commit/fd9219a75011a2bac33764b38ee11c8014551047))
* enhance bot architecture with comprehensive docstrings ([02bfa5b](https://github.com/S1M0N38/balatrollm/commit/02bfa5b2557fbd500533a828d855c72c4664c88d))
* make base_dir configurable ([c285c10](https://github.com/S1M0N38/balatrollm/commit/c285c1010db084d005c019a7b041654bde19daae))
* make number of runs configurable in Makefile ([c47d373](https://github.com/S1M0N38/balatrollm/commit/c47d373a81ed393b4aca78fdd456121afbd84606))
* report averaged stats in leaderboard ([be5e381](https://github.com/S1M0N38/balatrollm/commit/be5e3819540e66310fd15e4197eafab9676004d8))
* update MEMORY.md.jinja with raw tool_calls ([4493674](https://github.com/S1M0N38/balatrollm/commit/4493674f38cde8a7a5d1619c46c2839127dac1fd))


### Bug Fixes

* add game state 4 to completed ([c6df03d](https://github.com/S1M0N38/balatrollm/commit/c6df03de1206d1281e0412da4f3b96caaa927fb2))


### Documentation

* add balatrobench command to README and CLAUDE ([6e1e9d5](https://github.com/S1M0N38/balatrollm/commit/6e1e9d595ea8c0192583813c805750f4368d7e5d))
* add comprehensive documentation to benchmark system ([e93dcf7](https://github.com/S1M0N38/balatrollm/commit/e93dcf79365820a8ae5707885bdb212282f1208d))
* add comprehensive documentation to Config class ([34308c2](https://github.com/S1M0N38/balatrollm/commit/34308c2c59fc34c9424b0706766262319620dd24))
* add comprehensive documentation to data collection system ([48e7cdf](https://github.com/S1M0N38/balatrollm/commit/48e7cdf71159a99afb615238afed661e1408a979))
* add comprehensive documentation to strategy system ([4e61cb7](https://github.com/S1M0N38/balatrollm/commit/4e61cb7fb3b43c85b04a21149b71550e19290208))
* update CLI documentation with new options ([69cd0d0](https://github.com/S1M0N38/balatrollm/commit/69cd0d05224af3a50a876d24f0b7dd37f7576200))

## [0.4.0](https://github.com/S1M0N38/balatrollm/compare/v0.3.0...v0.4.0) (2025-08-29)


### Features

* add new models and update old ones to new format ([c99cb0a](https://github.com/S1M0N38/balatrollm/commit/c99cb0a2588a97282364bf9faffd39b125afd7e4))
* add setup and teardown targets ([e18a048](https://github.com/S1M0N38/balatrollm/commit/e18a04896256035a8a6f3941243b4ebbe56d7bfd))
* **config:** add metadata fields and simplify structure ([aae7d16](https://github.com/S1M0N38/balatrollm/commit/aae7d1680345180ab6cb0e7d57c157ab8bc1d907))
* remove support for env vars update flags ([fe93936](https://github.com/S1M0N38/balatrollm/commit/fe93936aed3473a39c2ae1f28ddf60e432dae940))
* update benchmark and data collection to new dir structure ([1d21cbe](https://github.com/S1M0N38/balatrollm/commit/1d21cbebf3e9460d81a55b64bfb2746ad939a9ea))


### Documentation

* remove the footer form the readme ([db5d4c2](https://github.com/S1M0N38/balatrollm/commit/db5d4c22ab060074db8367fc2c07d99ca03c955a))
* update CLAUDE.md with help text from commands ([f3b78af](https://github.com/S1M0N38/balatrollm/commit/f3b78afe1341fabf95bd1098274c3f14e8322272))
* update documentation to reflect architecture changes ([181b4be](https://github.com/S1M0N38/balatrollm/commit/181b4bed5f8d75bf00bbf3899972a2a00bac0835))
* update README.md ([da45438](https://github.com/S1M0N38/balatrollm/commit/da45438c1ec6fbdb515e80a80cf1ed6e6489e12e))

## [0.3.0](https://github.com/S1M0N38/balatrollm/compare/v0.2.0...v0.3.0) (2025-08-25)


### Features

* add additional fields to config.json for community metadata ([68d011b](https://github.com/S1M0N38/balatrollm/commit/68d011b16393e2bfda2bee9d9180df0c6e67fb05))
* add audio support to balatro.sh ([91e0d69](https://github.com/S1M0N38/balatrollm/commit/91e0d690f561ad86bb7380db0942d45d1f3e425d))
* add benchmark subcommand to CLI ([745b61f](https://github.com/S1M0N38/balatrollm/commit/745b61fe5d8e36edcd6cd825885c7d5ea994cba3))
* add comprehensive benchmark analysis system ([87f190b](https://github.com/S1M0N38/balatrollm/commit/87f190b9ea9f6d37508dbc143f97a116d1273bd9))
* enhance CLI with strategy system support ([849a027](https://github.com/S1M0N38/balatrollm/commit/849a0279d187e5c006a369064600f96e82e7154f))
* enhance configuration system with version validation and CLI overrides ([5400f64](https://github.com/S1M0N38/balatrollm/commit/5400f6407e209c6db5668be589b21ccf710b7dfe))
* improve data collection and logging ([c2685a9](https://github.com/S1M0N38/balatrollm/commit/c2685a9c5d26c84170f590c2a8ce34312c2f0c54))
* re-work templates into four standard files ([8410f0a](https://github.com/S1M0N38/balatrollm/commit/8410f0ad04f96f18b21c33d8a193966c9db82bd9))
* update Bot to use new template system ([f1937a4](https://github.com/S1M0N38/balatrollm/commit/f1937a4da432a7545a794bfc961d230f6013bcda))
* update core classes to use strategy system ([296233c](https://github.com/S1M0N38/balatrollm/commit/296233ca8511f6152f9f2a0f8686b538d27b42a8))
* update environment configuration for strategy system ([94fa214](https://github.com/S1M0N38/balatrollm/commit/94fa214a31078ca5a25c596db6aba066e17df681))


### Bug Fixes

* change the default template to `default` ([4a84cc8](https://github.com/S1M0N38/balatrollm/commit/4a84cc86695eeed3a7b01d7dc56e1c89b1878637))
* update config field references for consistency ([ea4dc0b](https://github.com/S1M0N38/balatrollm/commit/ea4dc0be46d307a1fca431cd154e3b65225b4d4f))


### Documentation

* add modern type hints guidelines to development documentation ([374b365](https://github.com/S1M0N38/balatrollm/commit/374b365ea35e128475c94a4c33cca70942aca7c1))
* update CLAUDE.md ([756171b](https://github.com/S1M0N38/balatrollm/commit/756171b9621dbcecab2aaf27294fc5022f994b19))
* update CLAUDE.md ([487f8b6](https://github.com/S1M0N38/balatrollm/commit/487f8b6a792c18d02b7b6a332386899447446888))
* update CLAUDE.md for strategy system ([1157c7e](https://github.com/S1M0N38/balatrollm/commit/1157c7e9c6922c2ae56ab9558e2d44b83a689263))
* update README.md ([ca19807](https://github.com/S1M0N38/balatrollm/commit/ca19807621a53ae3d15da9e2844c240c3213a33a))

## [0.2.0](https://github.com/S1M0N38/balatrollm/compare/v0.1.0...v0.2.0) (2025-08-21)


### Features

* add new tools and agentic capabilities ([80e9d9a](https://github.com/S1M0N38/balatrollm/commit/80e9d9a34d33a8a662d4bf6da189085e0f2e6c4d))
* add qwen3 to proxy config ([b4a3da1](https://github.com/S1M0N38/balatrollm/commit/b4a3da164ba5f8d833954f551f1a529a17c5bab6))
* **build:** add game automation and enhanced testing support ([9805c40](https://github.com/S1M0N38/balatrollm/commit/9805c407bf27fd96dfcb042adc6b8f62ad591c5b))
* change default model to cerebras-qwen3-235b ([f354789](https://github.com/S1M0N38/balatrollm/commit/f354789706d4442ac7d42d777b53115880bdba35))
* **core:** refactor LLMBot with Config dataclass and improved architecture ([f38d93d](https://github.com/S1M0N38/balatrollm/commit/f38d93da65339099113065fff502fe5124052a2a))
* **deployment:** add Balatro automation script ([d5fdbcf](https://github.com/S1M0N38/balatrollm/commit/d5fdbcffd585a2521969a186d4467e6a9c11f6ce))
* drastically simplify the templates ([ef817f1](https://github.com/S1M0N38/balatrollm/commit/ef817f1995ccde50b35a5ad2c350d93301b08fa6))
* **templates:** add aggressive strategy template system ([6c092b7](https://github.com/S1M0N38/balatrollm/commit/6c092b7eecd1efb5d05028664396bf3cccb35990))

## 0.1.0 (2025-08-08)


### Features

* add Makefile ([30018ea](https://github.com/S1M0N38/balatrollm/commit/30018ea6c25288fabe85c10f6b068c926597cc58))
* **bot:** add templates and tools configuration ([e78933f](https://github.com/S1M0N38/balatrollm/commit/e78933fba078dfa12f0e0cc4d20a3e02944a6e82))
* **bot:** implement LLM-powered Balatro bot ([cffdf87](https://github.com/S1M0N38/balatrollm/commit/cffdf873f80e4464a9574cdb717393e16cfa9f46))
* initialize project from template ([d0acef1](https://github.com/S1M0N38/balatrollm/commit/d0acef17f570e7b61c9bb51baebe404f794b8d58))
* update package exports and environment configuration ([ca1c85c](https://github.com/S1M0N38/balatrollm/commit/ca1c85c7cc34f30756206def89020399bbcc4dc3))


### Documentation

* add CLAUDE.md ([c9be87a](https://github.com/S1M0N38/balatrollm/commit/c9be87a0e337be9222029b6a22eabee6c2b7f6d0))
* update README with LLM bot usage and setup ([5ec3075](https://github.com/S1M0N38/balatrollm/commit/5ec30758e30c8ea4d3b9f6ec3981380418bc032b))
