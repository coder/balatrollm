# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

BalatroLLM is an LLM-powered bot that plays Balatro using the BalatroBot JSON-RPC API. It communicates with the game via HTTP/JSON-RPC 2.0 and uses OpenAI-compatible APIs (OpenAI, OpenRouter, etc.) for strategic decision making.


## Architecture

### Core Components

1.  **Client** (`src/balatrollm/client.py`):
    -   JSON-RPC 2.0 over HTTP client using `httpx`.
    -   Communicates with BalatroBot (Lua) on port 12346 request/response.
    -   Handles `BalatroError` exceptions.

2.  **Bot** (`src/balatrollm/bot.py`):
    -   Main game loop implementation.
    -   Flow: Fetch state -> Render Strategy -> Query LLM -> Execute Action.
    -   Manages game lifecycle (start, play, game over).

3.  **Strategies** (`src/balatrollm/strategies/`):
    -   Template-based prompt generation system.
    -   `GAMESTATE.md.jinja`: Renders current game state for LLM.
    -   `STRATEGY.md.jinja`: High-level strategic guidance.
    -   `TOOLS.json`: JSON-RPC tool definitions exposed to the LLM.

### JSON-RPC Protocol

-   **Transport**: HTTP POST to `http://127.0.0.1:12346`
-   **Format**: `{"jsonrpc": "2.0", "method": "...", "params": {...}, "id": 1}`
-   **Key Endpoints**:
    -   `start`: Start a new run (params: `deck`, `stake`, `seed`).
    -   `gamestate`: specific get state call.
    -   `play` / `discard`: Action on selected cards.
    -   `buy` / `sell` / `use`: Shop and consumable actions.
    -   `select` / `skip`: Blind interactions.

## Key Changes in V1

-   **State Enum**: Game states are now string enums (e.g., `SELECTING_HAND`, `SHOP`, `GAME_OVER`) instead of integers.
-   **Card Structure**: 0-based indexing. Structure is flattened with short codes (e.g., Suit "H", Rank "A", Edition "FOIL").
-   **Split Actions**: Complex actions are split (e.g., `shop` -> `buy`, `reroll`, `next_round`).

## Key Files

-   `src/balatrollm/client.py`: JSON-RPC client implementation.
-   `src/balatrollm/bot.py`: Main bot logic.
-   `src/balatrollm/data_collection.py`: Run logging and stats.
-   `balatro.sh`: Helper script to manage Balatro game instances.
-   `runs/`: Directory where game execution logs and artifacts are stored.
