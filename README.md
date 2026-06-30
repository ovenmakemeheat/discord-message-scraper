# Discord Message Scraper

A CLI tool to scrape Discord messages, download attachments, and export to CSV/JSONL. Built with Python, powered by Discord API v10.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Commands](#commands)
- [Configuration](#configuration)
- [Output Structure](#output-structure)
- [Finding Your Discord Token](#finding-your-discord-token)
- [How It Works](#how-it-works)

---

## Quick Start

**Prerequisites:** Python 3.12+ and [uv](https://docs.astral.sh/uv/)

```bash
# 1. Install dependencies
uv sync

# 2. Set up your Discord token
cp .env.example .env
# Edit .env and paste your token (see "Finding Your Discord Token" below)

# 3. Initialize config and add channels
discord-scraper config init
discord-scraper config add-channel <CHANNEL_ID>

# 4. Run the full pipeline
discord-scraper run
```

That's it. Messages are saved to `data/`, attachments downloaded, and CSV exported.

---

## Commands

### `run` — Full Pipeline

Runs all three stages in sequence: scrape, download, export.

```bash
discord-scraper run                             # full pipeline
discord-scraper run --skip-download             # scrape + export only
discord-scraper run --skip-export               # scrape + download only
discord-scraper run --full --channel 123456789  # full re-scrape of one channel
```

### `scrape` — Fetch Messages

Fetches messages from configured channels. Incremental by default — only pulls new messages since the last run.

```bash
discord-scraper scrape                          # incremental
discord-scraper scrape --full                   # full re-scrape
discord-scraper scrape --channel 123456789      # specific channel (repeatable)
discord-scraper scrape --limit 500              # cap at 500 messages per channel
```

### `download` — Download Attachments

Downloads all attachments from scraped messages. Skips files already downloaded.

```bash
discord-scraper download                        # 8 threads (default)
discord-scraper download --workers 16           # custom thread count
```

### `export` — Export to CSV/JSONL

Converts scraped JSON data into flat file formats.

```bash
discord-scraper export                          # CSV (default)
discord-scraper export --format jsonl           # JSONL
```

### `config` — Manage Configuration

```bash
discord-scraper config init                     # create config.toml
discord-scraper config show                     # display resolved config
discord-scraper config add-channel <ID>         # add a channel to scrape
discord-scraper config rm-channel <ID>          # remove a channel
```

All commands support `--quiet` to suppress output except errors.

---

## Configuration

Running `discord-scraper config init` creates a `config.toml`:

```toml
[scraper]
channels = []
data_dir = "data"

[downloader]
max_workers = 8
timeout = 60

[export]
default_format = "csv"
```

Settings are resolved in this order (first match wins):

1. CLI flags (`--channel`, `--workers`, `--format`, etc.)
2. `config.toml`
3. Environment variables (`DISCORD_TOKEN`)
4. `.env` file
5. Built-in defaults

---

## Output Structure

```
data/
  <server-name>/
    <channel-name>/
      messages.json         # raw API responses
      .scrape-meta.json     # tracks last scrape for incremental mode
      messages.csv          # exported flat data
      attachments/          # downloaded files
```

---

## Finding Your Discord Token

### Browser (Web App)

1. Open [discord.com/app](https://discord.com/app) in your browser
2. Open DevTools: `F12` or `Ctrl+Shift+I` (Windows/Linux) / `Cmd+Option+I` (macOS)
3. Go to the **Network** tab
4. Perform any action (send a message, switch channels) to trigger an API request
5. Click any request to `discord.com/api`
6. Under **Headers**, copy the value of the `Authorization` header

### Desktop App

DevTools is disabled by default in the desktop app. To enable it:

1. **Fully close Discord** (quit from the system tray, not just close the window)

2. **Open `settings.json`** in a text editor:

   | OS      | Path                                              |
   |---------|---------------------------------------------------|
   | Windows | `%appdata%\discord\settings.json`                 |
   | macOS   | `~/Library/Application Support/discord/settings.json` |
   | Linux   | `~/.config/discord/settings.json`                 |

3. **Add the DevTools flag** to the JSON object:

   ```json
   {
     "DANGEROUS_ENABLE_DEVTOOLS_ONLY_ENABLE_IF_YOU_KNOW_WHAT_YOURE_DOING": true
   }
   ```

   Your file will look something like:

   ```json
   {
     "BACKGROUND_COLOR": "#202225",
     "IS_MAXIMIZED": false,
     "DANGEROUS_ENABLE_DEVTOOLS_ONLY_ENABLE_IF_YOU_KNOW_WHAT_YOURE_DOING": true
   }
   ```

4. **Save, restart Discord**, then open DevTools:
   - Windows/Linux: `Ctrl+Shift+I`
   - macOS: `Cmd+Option+I`

5. Follow the same **Network tab** steps from the browser method above.

---

## How It Works

| Stage        | What it does                                                                                   |
|--------------|-----------------------------------------------------------------------------------------------|
| **Scrape**   | Paginates through channels (100 msgs/page), resolves server/channel names, saves raw JSON. Incremental by default — uses stored metadata to fetch only new messages. Handles rate limiting with automatic retry. |
| **Download** | Scans all `messages.json` files, downloads attachments in parallel (multi-threaded). Skips already-downloaded files. |
| **Export**   | Flattens messages into CSV or JSONL with author info, attachment URLs, mentions, and reply references. |
