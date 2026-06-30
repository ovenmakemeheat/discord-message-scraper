# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Discord message scraper that fetches messages from configured channels via the Discord API v10, saves them as JSON, and provides utilities to download attachments and convert to CSV. Python 3.12+, managed with `uv`.

## Commands

```bash
# Setup
uv sync                          # install dependencies into .venv
cp .env.example .env              # then fill in DISCORD_TOKEN

# Run scripts
uv run python src/scrape.py               # scrape messages from configured channels
uv run python src/download_attachments.py  # download attachments from scraped messages
uv run python src/to_csv.py               # convert messages.json files to CSV
```

No test suite or linter is configured.

## Architecture

Three standalone scripts in `src/`, each with a `main()` entry point:

- **`scrape.py`** — Fetches messages from hardcoded `CHANNEL_IDS` using a user token. Resolves channel/guild names, paginates through messages (100/page), saves to `data/<guild-slug>/<channel-slug>/messages.json`. Handles rate limiting with retry.
- **`download_attachments.py`** — Scans all `data/**/messages.json` files, downloads attachment files into sibling `attachments/` directories using 8 threads. Uses `rich` for display and `tqdm` for progress.
- **`to_csv.py`** — Converts all `data/**/messages.json` files to `messages.csv` with flattened fields (author info, attachment URLs, mention names, referenced message ID).

Data flows: `scrape.py` → JSON files → `download_attachments.py` / `to_csv.py`

## Key details

- Auth token goes in `.env` as `DISCORD_TOKEN` (loaded via `python-dotenv`)
- Channel IDs to scrape are hardcoded in `scrape.py:CHANNEL_IDS`
- Output directory: `data/` (gitignored)
- Dependencies: `httpx`, `python-dotenv`, `tqdm`, `rich`

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues on `ovenmakemeheat/discord-message-scraper` via the `gh` CLI. External PRs are not a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary (needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix). See `docs/agents/triage-labels.md`.

### Domain docs

Multi-context layout — `CONTEXT-MAP.md` at the root points to per-context `CONTEXT.md` files. See `docs/agents/domain.md`.
