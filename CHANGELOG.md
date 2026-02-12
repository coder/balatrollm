# Changelog

## [1.1.1](https://github.com/coder/balatrollm/compare/v1.1.0...v1.1.1) (2026-02-12)


### Bug Fixes

* **bot:** add cache_control to strategy message ([068ff87](https://github.com/coder/balatrollm/commit/068ff87dc2e44359ec6a500f2f99bbb05ff1d6e0))
* improve game resilience and error diagnostics ([2c7b48f](https://github.com/coder/balatrollm/commit/2c7b48f68b93df38d7bba8a90b565ee77b4ae280))
* **llm:** catch JSONDecodeError in LLM retry loop ([0a17bfa](https://github.com/coder/balatrollm/commit/0a17bfa17332c07734d5b230fa39ed579f07997c))


### Dependencies

* update balatrobot to 1.4.1 ([a05daa6](https://github.com/coder/balatrollm/commit/a05daa6f1ec8bf7c8bb8471b4faee1e314d010bb))


### Documentation

* **cli:** add note about tasks vs workers and seed regex ([ebfe844](https://github.com/coder/balatrollm/commit/ebfe8446bcf6357fcb3453c46cc343b4c6163095))
* **envrc:** add .envrc.example ([ca44aef](https://github.com/coder/balatrollm/commit/ca44aef52b0edbd0e67bcad60271728c27bf1969))
* improve docs and fix inconsistencies ([60363e3](https://github.com/coder/balatrollm/commit/60363e3dd622aeda982337ef0e81837e46530259)), closes [#62](https://github.com/coder/balatrollm/issues/62)
* **index:** update logos to have same size and add underline ([a127565](https://github.com/coder/balatrollm/commit/a127565385adc0857d568968f3c291aeaa761977))
* **installation:** add tool use warning ([4b8acf9](https://github.com/coder/balatrollm/commit/4b8acf94190d5b9edd8144045c621a94f439882a))
* **mkdocs:** change accent color to shades of orange ([06d85b7](https://github.com/coder/balatrollm/commit/06d85b74aca9bc5639235ca2d6c75842f08ba537))
* **readme:** add screenshots ([2d7280c](https://github.com/coder/balatrollm/commit/2d7280c1b1c5d0ac2c0e028d0bf687e4ba27d048))

## [1.1.0](https://github.com/coder/balatrollm/compare/v1.0.9...v1.1.0) (2026-02-02)


### Features

* **balatrollm:** add views server ([e1ccc05](https://github.com/coder/balatrollm/commit/e1ccc05cfa949126b123adbfd94862d10a587ab0))
* **cli:** add BALATROLLM_CONFIG env var support ([2fc5f36](https://github.com/coder/balatrollm/commit/2fc5f3641bf59713fdb08b4d9309afe360e07696)), closes [#57](https://github.com/coder/balatrollm/issues/57)
* **collector:** add support model name without `/` ([cd30b65](https://github.com/coder/balatrollm/commit/cd30b651e5676b39fc751cf64805fd34db2fb6aa))
* **strategies:** add conservative strategy ([0ae6aae](https://github.com/coder/balatrollm/commit/0ae6aae8573a9c3aa1e243405d3e96627252ad8b))
* **strategy:** add aggressive multiplier-focused strategy ([fc958ce](https://github.com/coder/balatrollm/commit/fc958cec986e0f6e3c1846983eaaec8526e9b2b6))
* **views:** add task and responses views - WIP ([446c388](https://github.com/coder/balatrollm/commit/446c3883b3c46e51fed2d3ff707806b50e539ad5))


### Bug Fixes

* **balatrollm:** remove hard-coded usage in the DEFAULT_MODEL_CONFIG ([9f23461](https://github.com/coder/balatrollm/commit/9f23461370b3334a477bddc8c5c33dea8ce32f60))
* **config:** add usage include to config/example.yaml ([bce4c92](https://github.com/coder/balatrollm/commit/bce4c926312c3a5c902183e57f89fb9e38416c84))


### Performance Improvements

* **views:** reduce memory usage by only parsing the last 10 responses ([3c8481e](https://github.com/coder/balatrollm/commit/3c8481ec75d404543a4ea6045fce05e94bf74ca5))


### Documentation

* **CLAUDE:** add views flag in CLAUDE.md ([428b07f](https://github.com/coder/balatrollm/commit/428b07f6fa5d68c6f1c096126e86da7ad257169c))
* **cli:** add --views flag ([686d9b3](https://github.com/coder/balatrollm/commit/686d9b35cd96e45fa3eb914bfd67e632ab6aae29))
* **index:** add BalatroBench link ([3aff5db](https://github.com/coder/balatrollm/commit/3aff5dbf04ca6affc4a20f5c916ff8ba6d2a9aae))

## [1.0.9](https://github.com/coder/balatrollm/compare/v1.0.8...v1.0.9) (2026-01-18)


### Bug Fixes

* **strategies:** set strict to false for all tools schemas ([a313210](https://github.com/coder/balatrollm/commit/a3132102da2cc96a251d519c6448ad8708f6726b))

## [1.0.8](https://github.com/coder/balatrollm/compare/v1.0.7...v1.0.8) (2026-01-14)


### Bug Fixes

* **executor:** revert session_id change ([7419cfc](https://github.com/coder/balatrollm/commit/7419cfc2934f69d958f8be53b2f4537e296474cf))

## [1.0.7](https://github.com/coder/balatrollm/compare/v1.0.6...v1.0.7) (2026-01-14)


### Bug Fixes

* **executor:** remove reset client in finally block ([c525272](https://github.com/coder/balatrollm/commit/c5252722a57a3d931278b202b8446696833f4542))

## [1.0.6](https://github.com/coder/balatrollm/compare/v1.0.5...v1.0.6) (2026-01-13)


### Dependencies

* update balatrobot to 1.3.4 ([5f1f031](https://github.com/coder/balatrollm/commit/5f1f03168401fabae7a46011c3d5ca7a8d9ff071))

## [1.0.5](https://github.com/coder/balatrollm/compare/v1.0.4...v1.0.5) (2026-01-13)


### Bug Fixes

* **executor:** reset game to menu state before returning port to pool ([05a468c](https://github.com/coder/balatrollm/commit/05a468cb71dc5dbe67ada1e174286d78f893a4b4))

## [1.0.4](https://github.com/coder/balatrollm/compare/v1.0.3...v1.0.4) (2026-01-12)


### Dependencies

* update balatrobot to 1.3.3 ([af9ae33](https://github.com/coder/balatrollm/commit/af9ae332e90e4cf17d63548b3ec53469d2ecf85f))

## [1.0.3](https://github.com/coder/balatrollm/compare/v1.0.2...v1.0.3) (2026-01-11)


### Bug Fixes

* **pyproject.toml:** update balatrobot to 1.3.1 ([a02e363](https://github.com/coder/balatrollm/commit/a02e36384857cafe81f823f1fe55151615807006))

## [1.0.2](https://github.com/coder/balatrollm/compare/v1.0.1...v1.0.2) (2026-01-11)


### Dependencies

* update balatrobot to 1.3.0 ([b354476](https://github.com/coder/balatrollm/commit/b35447634f353c4011d94723c7726b61c1cf3675))

## [1.0.1](https://github.com/coder/balatrollm/compare/v1.0.0...v1.0.1) (2026-01-09)


### Bug Fixes

* **strategies:** unify pack tools into a single function ([6fb0ba0](https://github.com/coder/balatrollm/commit/6fb0ba0d75bf5255b3ee52d09f737eda28a8fefc))

## [1.0.0](https://github.com/coder/balatrollm/compare/v0.16.0...v1.0.0) (2026-01-06)


### Features

* add __init__.py to src/balatrollm ([c8d350a](https://github.com/coder/balatrollm/commit/c8d350acc25c135eac80232e9cca7289fc84434e))
* add executor to start/stop balatro instances and tasks ([3f80e3f](https://github.com/coder/balatrollm/commit/3f80e3f7b6467f312a03d2141e4b230cf41b889c))
* add llm client ([2c35963](https://github.com/coder/balatrollm/commit/2c359634cc2e567f96c2376e06017719cd78094a))
* add new config/task structure ([10ab612](https://github.com/coder/balatrollm/commit/10ab612a7e0e520c5f981bb5ef289cde3e4e9b8d))
* add strategy manifest class to strategy.py ([fb91793](https://github.com/coder/balatrollm/commit/fb91793abcfe5aa7852eafb50ba765f96c5e910c))
* **cli:** add new CLI entry point for `balatrollm`` ([f87ea11](https://github.com/coder/balatrollm/commit/f87ea11f73e58b01eb20a7b5942ebb8be793cb7d))
* **client:** add BalatroClient and BalatroError classes ([a3500cb](https://github.com/coder/balatrollm/commit/a3500cbc7773f69b1da729c3a661096cc7d4e5d0))
* **collector:** flatten the structure of the stats ([2540725](https://github.com/coder/balatrollm/commit/254072565bc27153d62a551a01d7c8867ae2135c))
* **config:** change default model to gpt-oss-120b in example.yaml ([8d94917](https://github.com/coder/balatrollm/commit/8d94917dd604d0fd806576f6d410d9596559ba83))
* **config:** remove legacy config and add example config ([76f0e37](https://github.com/coder/balatrollm/commit/76f0e375b61d1653213c16071d885430f089e251))
* **executor:** add error message if the task fails ([f9ad726](https://github.com/coder/balatrollm/commit/f9ad726ffb80538225b120eab389b250f0333f3e))
* **executor:** add log path to executor output ([d10e026](https://github.com/coder/balatrollm/commit/d10e026a8677fe95e2e8d06cd806494b6cbc3fb9))
* **executor:** spawn instances in parallel ([49b03b9](https://github.com/coder/balatrollm/commit/49b03b91816f07fcd997f94403d0070bcee44bc8))
* **scripts:** add balatro launchers for linux, macos, and windows ([4b770eb](https://github.com/coder/balatrollm/commit/4b770eb26497299ab8500e883e85dea6917e34b1))
* **strategies:** add `pack` endpoint support ([3b3c487](https://github.com/coder/balatrollm/commit/3b3c4879b5447adf0713f61f68176985063c8cbb))
* **strategies:** add schema to manifest.json ([36ca7bb](https://github.com/coder/balatrollm/commit/36ca7bb461a50c23f3b84863cf942ef5674141c1))
* **strategy:** add default strategy ([0a8fb96](https://github.com/coder/balatrollm/commit/0a8fb963c10ef8eff36a619e2df3804989987428))
* **strategy:** add strategy manager class ([16bcc64](https://github.com/coder/balatrollm/commit/16bcc6496e81cc382c046d3b4d5cd13a79b4b709))


### Bug Fixes

* **scripts:** wait for port to be ready in launch script ([3e4fc73](https://github.com/coder/balatrollm/commit/3e4fc7318d21c684c54a2c433950b65dae5bd805))
* **strategy:** remove booster packs references ([069a2a1](https://github.com/coder/balatrollm/commit/069a2a1760f0b89282c710d5d0edda735fa56527))
* test target in the Makefile ([a95e78e](https://github.com/coder/balatrollm/commit/a95e78e54c91783e633f1790c097292de86bcb6b))


### Documentation

* add comments to collector.py about various ids ([16b3cdb](https://github.com/coder/balatrollm/commit/16b3cdb2704963b40136fb3744802aa4bce52216))
* **assets:** add balatrollm-white.svg ([a1a80c5](https://github.com/coder/balatrollm/commit/a1a80c59d4643dc62e7e8dfe69b9134211d2db4d))
* move CONTRIBUTING.md to docs/contributing.md ([bc037b9](https://github.com/coder/balatrollm/commit/bc037b9f86cb684b283018ed828d8e12ae59f3e8))
* remove order list and use bullets instead ([928712b](https://github.com/coder/balatrollm/commit/928712bf7ccf634baab69df356d75f804bf0137a))
* update CLAUDE.md to reflect current state of the project ([9bb83f8](https://github.com/coder/balatrollm/commit/9bb83f835478a2f5a5d72a244ed046c07688a60a))
* update docs index with repos assets ([78e0127](https://github.com/coder/balatrollm/commit/78e01273e561bba213f2511018980969ed5d9e87))
* update mkdocs.yml following mkdocs from balatrobot ([89eb755](https://github.com/coder/balatrollm/commit/89eb755d6d46da086e9c7dd233257599bf5379c4))
* update pages in the docs ([26c8d3f](https://github.com/coder/balatrollm/commit/26c8d3f48d2b257a5f89386b2d2495cee2af83db))
* update repo link in CLAUDE.md ([7301d78](https://github.com/coder/balatrollm/commit/7301d7869d27582f0265aaea734d7e8ffebbac69))
* update the README following the balatrobot README ([9caa373](https://github.com/coder/balatrollm/commit/9caa37342a2297f1be068e8d41acec9ec60ec0b8))


### Miscellaneous Chores

* release balatrollm v1 ([ec2fcb3](https://github.com/coder/balatrollm/commit/ec2fcb3d16a30e46e89adf1f86e313767948bb20))

## [0.16.0](https://github.com/coder/balatrollm/compare/v0.15.1...v0.16.0) (2025-11-03)


### Features

* finer metrics generation by balatrobench ([0d684aa](https://github.com/coder/balatrollm/commit/0d684aa6301c4733da1bbd16d0dca0f76bd83f35))

## [0.15.1](https://github.com/coder/balatrollm/compare/v0.15.0...v0.15.1) (2025-10-30)


### Dependencies

* update balatrobot to 0.7.5 ([3ae6b1a](https://github.com/coder/balatrollm/commit/3ae6b1ad86620c0b658373b5ea31e01aed795a7d))

## [0.15.0](https://github.com/coder/balatrollm/compare/v0.14.1...v0.15.0) (2025-10-30)


### Features

* add webp conversion to balatrobench cli ([8afe67c](https://github.com/coder/balatrollm/commit/8afe67c2e076173dcb930f522532bf2bde27c3e6))


### Documentation

* add better documentation for strategies ([1af7822](https://github.com/coder/balatrollm/commit/1af782267cc947c1b4cf4dd048e7cd807dfeab78))

## [0.14.1](https://github.com/coder/balatrollm/compare/v0.14.0...v0.14.1) (2025-10-28)


### Bug Fixes

* add keepalive get_game_state to keep TCP connection alive ([992faf3](https://github.com/coder/balatrollm/commit/992faf367b9454e7513969eff07df8e03eaf5372))

## [0.14.0](https://github.com/coder/balatrollm/compare/v0.13.2...v0.14.0) (2025-10-25)


### Features

* add logic to load/save strategy manifest ([e55b885](https://github.com/coder/balatrollm/commit/e55b885051b1f2f0206835c2eaa5ab0b42cb547e))
* add manifest.json files for strategies ([14978aa](https://github.com/coder/balatrollm/commit/14978aa57dc48627116e90093079fe9d31f10445))
* add strategy metadata to benchmark ([88ebc44](https://github.com/coder/balatrollm/commit/88ebc44b4aada5a581a480990e6c906464241d99))
* configure balatrollm via env vars ([03c0fd0](https://github.com/coder/balatrollm/commit/03c0fd07a1f2bba1f44cf855f72732d4400f7903))
* new cli for balatrobench ([973bc3e](https://github.com/coder/balatrollm/commit/973bc3e0285eb0117348f6c7d5c810219cd068f3))
* new separate command for benchmarking ([b9a1284](https://github.com/coder/balatrollm/commit/b9a12841111bc651688983140a63189b922e9951))
* update the aggressive strategy ([e51b9ca](https://github.com/coder/balatrollm/commit/e51b9ca2c76c499c6e6bbbafe632a166a791771f))


### Bug Fixes

* decrease timeout for llm client ([e7f2c91](https://github.com/coder/balatrollm/commit/e7f2c9138fec93237a8c686f1e085121f535dd9c))
* use comma-separated ports in balatro.sh ([404b748](https://github.com/coder/balatrollm/commit/404b74860ac6a8add0a8d62f4470b2b726e008c4))


### Documentation

* add video in the readme ([328d9bc](https://github.com/coder/balatrollm/commit/328d9bc1e285ee8b29d72244632737d5b1916e7c))
* fix list rendering using sane_lists ([a52decb](https://github.com/coder/balatrollm/commit/a52decbcf3f81eaf6d92332d3273f85717307d18))
* remove old screenshots assets ([ef831a0](https://github.com/coder/balatrollm/commit/ef831a094886754f385df96c7cbc0f46c1d1e28b))
* rewrite docs from scratch ([8c78a9b](https://github.com/coder/balatrollm/commit/8c78a9b3efa0838d639c0f5ef51bd1d9d2cda57b))
* update .envrc.example with all the env vars ([8852bc5](https://github.com/coder/balatrollm/commit/8852bc5a0911c2762e7359c3664045c4d29fcd22))
* update desc for llms-txt and set index.md as home ([dbe4a95](https://github.com/coder/balatrollm/commit/dbe4a95d75579e812ed27c360e8a3715a4fe2e03))
* update README.md ([8ab0aa8](https://github.com/coder/balatrollm/commit/8ab0aa8fc1c6a8834d8c0ce1e29955c52afc1bec))
* update titles in the README ([27006f5](https://github.com/coder/balatrollm/commit/27006f519335fc7a9cc67263c2ac6046afa6abd4))

## [0.13.2](https://github.com/coder/balatrollm/compare/v0.13.1...v0.13.2) (2025-10-24)


### Documentation

* add pypi badge ([94b4fbf](https://github.com/coder/balatrollm/commit/94b4fbf17044f398548bf3a903288139d46200e5))

## [0.13.1](https://github.com/coder/balatrollm/compare/v0.13.0...v0.13.1) (2025-10-23)


### Bug Fixes

* extract reasoning from tool calls if not available in response ([0422061](https://github.com/coder/balatrollm/commit/042206116e2932f1c8661dc0525073f840fb4ce0))
* update benchmark.py to handle multimodal content ([97b5b04](https://github.com/coder/balatrollm/commit/97b5b04545f6ba93c38d2371c1f42082db633e30))


### Performance Improvements

* improve conversion to AVIF ([2e3be75](https://github.com/coder/balatrollm/commit/2e3be75d70c0824dd8661275828531bf6045407e))

## [0.13.0](https://github.com/coder/balatrollm/compare/v0.12.0...v0.13.0) (2025-10-23)


### Features

* use cards descriptions instead of hard-coded strings ([7b2fab5](https://github.com/coder/balatrollm/commit/7b2fab5d2e95d50b359f7447f59770a2fbd68639)), closes [#18](https://github.com/coder/balatrollm/issues/18)

## [0.12.0](https://github.com/coder/balatrollm/compare/v0.11.0...v0.12.0) (2025-10-22)


### Features

* add --no-screenshot flag to balatrollm ([d15f087](https://github.com/coder/balatrollm/commit/d15f0876e2930feec0aed8d31a97287a92116ec7))
* add --use-default-paths flag to use balatrobot's default storage paths ([0d47320](https://github.com/coder/balatrollm/commit/0d473203a118082974697fd5b499321145a9bd6c))
* add rearrnge jokers tool to default strategy ([64016d9](https://github.com/coder/balatrollm/commit/64016d9e778dda89c8648fc15beffb649752380e))
* use prompt caching ([2315919](https://github.com/coder/balatrollm/commit/23159197a5975c93d9c538532e7426b1abdb7f31))
* use throughput instead of price for sorting ([63d4b01](https://github.com/coder/balatrollm/commit/63d4b01f53066e24d94f48aed248510cde29703e))


### Bug Fixes

* add log_path back again ([bc0c87c](https://github.com/coder/balatrollm/commit/bc0c87c5d5fc52a365329c7a5cca59a054af694c))
* update grok-4-fast model slug ([02e2a9f](https://github.com/coder/balatrollm/commit/02e2a9f58f99ee1f62112d43d8b2fcb2e997f8d9))


### Performance Improvements

* send message get_game_state to trigger frame rendering ([8e89521](https://github.com/coder/balatrollm/commit/8e89521accdafa05c2577ca2232453f3c97f21e3))


### Documentation

* explain --no-screenshot --use-default-paths flags ([27a8585](https://github.com/coder/balatrollm/commit/27a8585e5947a66e49ec427601aa9e22149648ec))
* update links from S1M0N38 to coder ([9681cf5](https://github.com/coder/balatrollm/commit/9681cf5c37a5ba438fbd63bb7059e2838ebbf3b1))

## [0.11.0](https://github.com/S1M0N38/balatrollm/compare/v0.10.0...v0.11.0) (2025-10-03)


### Features

* add support for multiple seeds ([a598e8e](https://github.com/S1M0N38/balatrollm/commit/a598e8eca76a863fefb45cadd915e84ce5e08330))
* default to cerebras provider if available ([18b58ec](https://github.com/S1M0N38/balatrollm/commit/18b58ec38dec03110546d4fc22f431a708e9eedb))
* **models:** add deepseek v3.1 ([561ac82](https://github.com/S1M0N38/balatrollm/commit/561ac8221a576e5bbe311f7f2c6cb7e11b2e10c5))
* **models:** add google/gemini-2.5-flash ([7807fbe](https://github.com/S1M0N38/balatrollm/commit/7807fbe1bb3d7ee00d31a54346c85a5856a40389))
* **models:** add grok-4-fast ([85ebb9c](https://github.com/S1M0N38/balatrollm/commit/85ebb9c1051b05aa4baa13b7cf5f2af6a0aa1499))
* move seed into stats to support multi-seed runs ([54775a7](https://github.com/S1M0N38/balatrollm/commit/54775a7d67fc6b586b0af65c933257184908a619))
* remove blind select and cash_out phases from default strategy ([bf8e0f2](https://github.com/S1M0N38/balatrollm/commit/bf8e0f271d743e1ee8f6883327ca67dd49e3835b))


### Bug Fixes

* add cards param to use_consumable in TOOLS.json ([0faa085](https://github.com/S1M0N38/balatrollm/commit/0faa085e461f4cfc21ddbe3af42ee54503058946))
* add fallback for reasoning not available ([fa530c5](https://github.com/S1M0N38/balatrollm/commit/fa530c54a37f7cd45054eda48b33904ab3cdbe0b))
* add small sleeps in round eval and blind select ([38fd254](https://github.com/S1M0N38/balatrollm/commit/38fd254004fe7bccc8564db643908f0ec08230f3))
* include gamestate (SELECTING_HAND and SHOP) in GAMESTATE.md.jinja ([7b2fcec](https://github.com/S1M0N38/balatrollm/commit/7b2fcecfe1e9cea54e6644e9f22f4e909d6db88c))
* set seed to positive integer ([b4c753a](https://github.com/S1M0N38/balatrollm/commit/b4c753af4ad0dad80f581118083ef0cd75383d19))
* typo and ensure benchmarks dir creation ([cead758](https://github.com/S1M0N38/balatrollm/commit/cead75816800712a7dac519541ea4ff77873b3b3))


### Documentation

* add balatrobench images ([8db3017](https://github.com/S1M0N38/balatrollm/commit/8db30170d5d881677fafb8a199ca718273e0f777))
* add first version of the docs (WIP) ([74aa38f](https://github.com/S1M0N38/balatrollm/commit/74aa38f94372c5e319bd9f6864b775f566fbc7f7))
* add mkdocs.yml for generating documentation with mkdocs ([72701ea](https://github.com/S1M0N38/balatrollm/commit/72701ea3183509b1433c551f08dfb091759ead52))
* update analysis.md ([903f4ab](https://github.com/S1M0N38/balatrollm/commit/903f4ab28aedb6949495b152e9cd086a5ac7d2f2))
* update analysis.md (WIP) ([b7ad0af](https://github.com/S1M0N38/balatrollm/commit/b7ad0af8d876244cc1a3de2d926a7fd9dca99a07))

## [0.10.0](https://github.com/S1M0N38/balatrollm/compare/v0.9.0...v0.10.0) (2025-09-22)


### Features

* add cli option to convert pngs to avif ([3e8a655](https://github.com/S1M0N38/balatrollm/commit/3e8a65547fcbe67d42407fb8eab8707f5ab56b97))
* change stats runs from int to list of str ([7560acf](https://github.com/S1M0N38/balatrollm/commit/7560acfddc9776b6cc6d22c04559f3cd93b767c7))
* make use of balatrobot enums ([8f7185b](https://github.com/S1M0N38/balatrollm/commit/8f7185b50f1e7364c6e4023da9d04d769fc164cf))

## [0.9.0](https://github.com/S1M0N38/balatrollm/compare/v0.8.2...v0.9.0) (2025-09-19)


### Features

* add avoiding the sell-buy trap in STRATEGY.md.jinja ([8d163b1](https://github.com/S1M0N38/balatrollm/commit/8d163b1972b1a9b2c6504ba5e233420d1fda9780))
* add claude-sonnet-4 and gpt-5 to models ([c2065bb](https://github.com/S1M0N38/balatrollm/commit/c2065bb0f7aed148256916b46dd3c1a8faed19bd))
* add current score and target score to gamestate ([ae45b4d](https://github.com/S1M0N38/balatrollm/commit/ae45b4dc39144ac3570a32ae6b780025b26da143))
* add gemini-2.5-pro to models ([e93e70d](https://github.com/S1M0N38/balatrollm/commit/e93e70d3bdcf952c1ce5b01951ee8926fe33e44d))
* add screenshot dir in data collection ([ba8ee53](https://github.com/S1M0N38/balatrollm/commit/ba8ee53f3632f277eeb7bcece8835ccddc312caa))
* add shop, vouchers to GAMESTATE.md.jinja ([760e5cb](https://github.com/S1M0N38/balatrollm/commit/760e5cbc16339f210a5d8212323ab2cf5f6c6366))
* add strategic discarding and suggestion about buy-sell ([cfc2066](https://github.com/S1M0N38/balatrollm/commit/cfc20661bfd7f1468715cc8fda8ace89148d0f2f))
* create details dir for each run in benchmark ([30a4c8c](https://github.com/S1M0N38/balatrollm/commit/30a4c8c04d23eac1ab747cca6f7a7a8563610b89))
* default actions for round_eval and blind_select ([a273823](https://github.com/S1M0N38/balatrollm/commit/a2738239d95d4ee51c14577650ae583df2d20eda))
* take screenshot on each request ([4b25a07](https://github.com/S1M0N38/balatrollm/commit/4b25a0739bc92f951827a2926484f4b3fb6c79e9))


### Bug Fixes

* computation of pooled variance in benchmark ([ba2d522](https://github.com/S1M0N38/balatrollm/commit/ba2d5225f50d68f288e5fe8cea82abfcf28b6715))
* consumables and tags representation in GAMESTATE.md.jinja ([5930523](https://github.com/S1M0N38/balatrollm/commit/5930523b99a594dff1852f0ddabdf9e485737b0f))
* make the highlighted limit more explicit in default strategy ([7dcaa59](https://github.com/S1M0N38/balatrollm/commit/7dcaa5985d0aaf333e9adee989e5f3f7fe96f483))
* regex for model name add dot ([3aff39f](https://github.com/S1M0N38/balatrollm/commit/3aff39febcc18c6dfca48ca2ea6daaedcf8468f8))
* set "order of operations" section to h3 ([172e90c](https://github.com/S1M0N38/balatrollm/commit/172e90cc9e742c1bbdfc142b5802aa2ef1ef6fb8))
* sort poker hands by order ([2a5589a](https://github.com/S1M0N38/balatrollm/commit/2a5589a2ced848d9f6d703b0dbb6b180cc3ed33b))
* update the BALATRO_CONSTANTS with proper values ([e9a037f](https://github.com/S1M0N38/balatrollm/commit/e9a037fdcc15f470462e27510113c0b7c57dd897))
* use ante instead of computation of ante from round ([72a0110](https://github.com/S1M0N38/balatrollm/commit/72a011066c87a4aab4de0353080b397294ea21b9))
* use state["game"]["round_resets"]["ante"] ([5955982](https://github.com/S1M0N38/balatrollm/commit/5955982bfed647896e2998da4884fd11ae8f2530))
* whitespaces in GAMESTATE.md.jinja template ([76067af](https://github.com/S1M0N38/balatrollm/commit/76067af76d984a51ce6fdbb64b8073fddbc396b6))

## [0.8.2](https://github.com/S1M0N38/balatrollm/compare/v0.8.1...v0.8.2) (2025-09-09)


### Bug Fixes

* add milliseconds to timestamp ([8b271a8](https://github.com/S1M0N38/balatrollm/commit/8b271a87a6d669535b3b760461b48f9260f53a22))

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
