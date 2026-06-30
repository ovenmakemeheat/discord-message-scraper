# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Discord message scraper CLI that fetches messages from configured channels via the Discord API v10, saves as JSON, downloads attachments, and exports to CSV/JSONL. Python 3.12+, managed with `uv`, packaged with `hatchling`.

## Commands

```bash
# Setup
uv sync                                        # install deps + build package
cp .env.example .env                            # then fill in DISCORD_TOKEN
discord-scraper config init                     # create config.toml

# CLI (installed as entry point after uv sync)
discord-scraper run                             # full pipeline: scrape -> download -> export
discord-scraper scrape                          # scrape only (incremental by default)
discord-scraper scrape --full                   # force full re-scrape
discord-scraper download                        # download attachments
discord-scraper export --format csv             # export (csv or jsonl)
discord-scraper config show                     # show resolved config
discord-scraper config add-channel <ID>         # add channel to config.toml
```

No test suite or linter is configured.

## Architecture

Layered package at `src/discord_scraper/` with strict dependency direction: `cli` -> `services` -> `core`/`storage`. The `ui` layer is used only by `cli`.

### `core/` — Pure logic, no I/O display

- **`models.py`** — Frozen dataclasses: `Guild`, `Channel`, `Attachment`, `Message`, `ScrapeMeta`. Each has a `from_api(dict)` classmethod to parse Discord API responses. `Message.raw` preserves the original dict for storage/export.
- **`client.py`** — `DiscordClient` context manager wrapping `httpx.Client` with rate limiting. Methods: `get_channel`, `get_guild`, `get_messages`. Raises `AuthenticationError`, `AccessDeniedError`, `APIError`.
- **`rate_limiter.py`** — `RateLimiter` handles 429 responses with retry. Tracks stats (hits, total wait).
- **`config.py`** — `Config` dataclass loaded from layered sources: CLI flags > `config.toml` > env vars > `.env` > defaults. Channels are configured in `config.toml` (not hardcoded).

### `storage/` — Abstract backend

- **`base.py`** — `StorageBackend` ABC defining `load_messages`, `save_messages`, `get_metadata`, etc.
- **`json_storage.py`** — `JSONStorage` implementation. Saves to `data/<guild-slug>/<channel-slug>/messages.json`. Tracks incremental scrape state in `.scrape-meta.json`.

### `services/` — Business logic orchestration

- **`scraper.py`** — `ScraperService` handles incremental/full scraping, pagination, message merging/dedup. Returns `ChannelResult` dataclass.
- **`downloader.py`** — `DownloaderService` with multi-threaded attachment downloads. Collects tasks from `messages.json` files, reports `DownloadStats`.
- **`exporter.py`** — Strategy pattern: `Exporter` ABC with `CSVExporter` and `JSONLExporter`. `get_exporter(format)` factory. Add new formats by subclassing `Exporter` and registering in `EXPORTERS` dict.

### `ui/` — Rich console output

- **`console.py`** — Shared `Console` instance + `error()`, `warn()`, `success()`, `info()` helpers.
- **`tables.py`** — Summary table builders for scrape/download/export results.
- **`progress.py`** — Rich progress bar factories.

### `cli/` — Click commands

- **`__init__.py`** — Click group `app` as the entry point (`discord_scraper.cli:app`).
- **`commands/`** — `scrape`, `download`, `export`, `run` (full pipeline), `config_cmd` (init/show/add-channel/rm-channel).

## Key details

- **Auth token: `.env` as `DISCORD_TOKEN`** (loaded via `python-dotenv`). This is a **user token** (not a bot token). Treat it like a password — never log it, commit it, or include it in error messages. Leaking it gives full access to the user's Discord account. `.env` and `config.toml` are gitignored for this reason.
- Channel config: `config.toml` (gitignored), managed via `discord-scraper config` commands
- Output directory: `data/` (gitignored)
- Dependencies: `click`, `httpx`, `python-dotenv`, `tqdm`, `rich`
- Build system: `hatchling`
- Data flow: `scrape` -> `messages.json` -> `download` / `export`

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues on `ovenmakemeheat/discord-message-scraper` via the `gh` CLI. External PRs are not a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary (needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix). See `docs/agents/triage-labels.md`.

### Domain docs

Multi-context layout — `CONTEXT-MAP.md` at the root points to per-context `CONTEXT.md` files. See `docs/agents/domain.md`.
