# Implementation Plan: Discord Scraper v2

## Goals

- Proper OOP architecture with clear separation of concerns
- Scalable design — easy to add new export formats, new data sources, new commands
- Polished CLI with rich visual feedback, progress tracking, and good UX
- Full end-to-end pipeline in a single command

---

## Phase 1: Package Structure & Core Abstractions

Restructure from flat scripts into a proper Python package.

### Package layout

```
src/discord_scraper/
    __init__.py
    cli/
        __init__.py          # click group
        commands/
            __init__.py
            scrape.py        # scrape command
            download.py      # download command
            export.py        # export command
            run.py           # full pipeline command
            config_cmd.py    # config management (init, show, edit)
    core/
        __init__.py
        client.py            # DiscordClient — API wrapper
        rate_limiter.py      # RateLimiter — token bucket / retry logic
        config.py            # Config — TOML-based configuration
        models.py            # dataclasses: Message, Attachment, Channel, Guild
    services/
        __init__.py
        scraper.py           # ScraperService
        downloader.py        # DownloaderService
        exporter.py          # ExporterService (strategy pattern for formats)
    storage/
        __init__.py
        base.py              # abstract StorageBackend
        json_storage.py      # JSONStorage — read/write messages.json
    ui/
        __init__.py
        console.py           # shared Rich console + helpers
        progress.py          # progress bar / live display wrappers
        tables.py            # summary table builders
```

### Core classes

```python
class DiscordClient:
    """Wraps httpx.Client with Discord API v10 base URL, auth, and rate limiting."""
    def __init__(self, token: str, rate_limiter: RateLimiter)
    def get_channel(self, channel_id: str) -> Channel
    def get_guild(self, guild_id: str) -> Guild
    def get_messages(self, channel_id: str, before: str | None, after: str | None, limit: int) -> list[Message]

class RateLimiter:
    """Handles 429 responses with exponential backoff and per-route bucket tracking."""
    def execute(self, request_fn: Callable) -> httpx.Response

class Config:
    """Loads/saves config from config.toml. Falls back to defaults."""
    channels: list[str]
    data_dir: Path
    max_workers: int
    token: str  # resolved from config -> env -> .env file
```

### Data models

```python
@dataclass(frozen=True)
class Guild:
    id: str
    name: str
    slug: str  # computed

@dataclass(frozen=True)
class Channel:
    id: str
    name: str
    guild_id: str
    slug: str  # computed

@dataclass(frozen=True)
class Attachment:
    id: str
    url: str
    filename: str

@dataclass(frozen=True)
class Message:
    id: str
    timestamp: str
    author_id: str
    author_username: str
    author_display_name: str
    content: str
    type: int
    pinned: bool
    attachments: list[Attachment]
    embeds_count: int
    mentions: list[str]
    referenced_message_id: str | None
    raw: dict  # preserve original API response
```

### Why this structure

- **`core/`** has zero dependency on CLI or display — pure logic, testable
- **`services/`** orchestrate core objects into workflows — also testable without CLI
- **`cli/`** is a thin layer that wires services to click commands and UI
- **`storage/`** is abstracted so we could swap JSON for SQLite later without touching services
- **`ui/`** centralizes all Rich usage so services stay display-agnostic

---

## Phase 2: Configuration System

Replace hardcoded `CHANNEL_IDS` with a layered config.

### `config.toml`

```toml
[scraper]
channels = [
    "1215564428007972874",
    "1120213595469389844",
]
data_dir = "data"

[downloader]
max_workers = 8
timeout = 60

[export]
default_format = "csv"
```

### Resolution order

1. CLI flags (highest priority)
2. `config.toml` in project root
3. Environment variables (`DISCORD_TOKEN`, `DISCORD_DATA_DIR`)
4. `.env` file
5. Built-in defaults

### CLI config commands

```bash
discord-scraper config init          # create config.toml from template
discord-scraper config show          # print resolved config
discord-scraper config add-channel <ID>
discord-scraper config rm-channel <ID>
```

---

## Phase 3: CLI UX & Visuals

### Entry point

Register in `pyproject.toml`:

```toml
[project.scripts]
discord-scraper = "discord_scraper.cli:app"
```

### Command tree

```
discord-scraper
  scrape       Fetch messages from configured channels
    --channel ID       Override config, scrape specific channel(s) (repeatable)
    --full             Force full re-scrape (ignore existing data)
    --limit N          Stop after N messages per channel
  download     Download attachments from scraped data
    --workers N        Thread count (default: 8)
    --retry-failed     Re-attempt previously failed downloads
  export       Export messages to other formats
    --format csv|jsonl    (default: csv)
    --output PATH         Custom output path
  run          Full pipeline: scrape → download → export
    --skip-download
    --skip-export
  config       Manage configuration
    init | show | add-channel | rm-channel
```

### Visual design with Rich

**Scrape command — live display:**

```
╭─ Scraping ──────────────────────────────────────╮
│  Server: My Server                              │
│  Channel: #general                              │
│  Progress: ████████████░░░░░░░░  1,247 messages │
│  Rate limits hit: 2                             │
╰─────────────────────────────────────────────────╯
```

**Download command — progress with stats:**

```
╭─ Downloading Attachments ───────────────────────╮
│                                                 │
│  ████████████████░░░░  342/427 files  [80%]     │
│                                                 │
│  ↓ 12.4 MB/s  ✓ 340  ⊘ 84 skipped  ✗ 2 failed │
│                                                 │
╰─────────────────────────────────────────────────╯
```

**Run command — pipeline stages:**

```
╭─ Pipeline ──────────────────────────────────────╮
│                                                 │
│  ✓ Scrape     7 channels   4,812 messages       │
│  ◐ Download   342/427 files                     │
│  ○ Export     waiting                            │
│                                                 │
╰─────────────────────────────────────────────────╯
```

**Final summary table (all commands):**

```
╭─ Summary ───────────────────────────────────────╮
│                                                 │
│  Channel            Messages  Attachments  CSV  │
│  ─────────────────  ────────  ───────────  ───  │
│  server/general        1,247          84    ✓   │
│  server/media            312         427    ✓   │
│  server/announcements    203           0    ✓   │
│  ─────────────────  ────────  ───────────  ───  │
│  Total                 1,762         511        │
│                                                 │
│  Duration: 2m 34s                               │
│                                                 │
╰─────────────────────────────────────────────────╯
```

### UX details

- **Color-coded status**: green = success, yellow = skipped/warning, red = error
- **Elapsed time** shown on all long operations
- **`--quiet`** flag suppresses all output except errors
- **`--verbose`** flag shows per-request debug info
- **`--no-color`** flag for piping / CI
- **Ctrl+C** handling: graceful shutdown, save progress, show partial results
- **Error messages** include actionable suggestions (e.g., "Token expired. Run `discord-scraper config init` to update.")

---

## Phase 4: Incremental Scraping

### How it works

1. Read existing `messages.json` if present
2. Find the newest message ID
3. Fetch only messages with `after=<newest_id>`
4. Merge new messages with existing, deduplicate by ID, sort by timestamp
5. Write back to `messages.json`

### Metadata file

Each channel directory gets a `.scrape-meta.json`:

```json
{
    "last_scraped": "2026-06-30T14:22:00Z",
    "newest_message_id": "1234567890",
    "oldest_message_id": "0987654321",
    "total_messages": 1247
}
```

This avoids reading the full JSON just to determine the latest message.

### Flags

- Default: incremental (fetch only new)
- `--full`: re-scrape everything, replace existing data
- `--limit N`: stop after N messages (useful for testing)

---

## Phase 5: Scalability & Robustness

### Storage backend abstraction

```python
class StorageBackend(ABC):
    @abstractmethod
    def load_messages(self, channel: Channel) -> list[Message]: ...
    @abstractmethod
    def save_messages(self, channel: Channel, messages: list[Message]) -> None: ...
    @abstractmethod
    def get_metadata(self, channel: Channel) -> ScrapeMeta | None: ...
```

Start with `JSONStorage`. Later can add `SQLiteStorage` for large-scale scraping without loading entire JSON files into memory.

### Async option

The current sync `httpx.Client` works fine for sequential channel scraping, but if scraping many channels, an async path with `httpx.AsyncClient` + `asyncio.gather` could scrape multiple channels concurrently. This is a future enhancement — keep the service interface async-ready but implement sync first.

### Exporter strategy pattern

```python
class Exporter(ABC):
    @abstractmethod
    def export(self, messages: list[Message], output_path: Path) -> None: ...

class CSVExporter(Exporter): ...
class JSONLExporter(Exporter): ...
# Future: MarkdownExporter, HTMLExporter, etc.
```

Adding a new format = one new class, registered in a dict. No if/else chains.

### Download resilience

- Track failed downloads in `.download-failures.json`
- `--retry-failed` flag re-attempts only failures
- Exponential backoff on transient errors
- Resume partial downloads for large files (HTTP Range header)

---

## Phase 6: Developer Experience

### Entry point & packaging

```toml
[project.scripts]
discord-scraper = "discord_scraper.cli:app"
```

After `uv sync`, the command is available as `discord-scraper` directly.

### Testing

- Add `pytest` + `pytest-httpx` for mocking API calls
- Test core classes and services independently of CLI
- Snapshot tests for CLI output formatting

### Linting

- Add `ruff` for linting and formatting
- Configure in `pyproject.toml`

---

## Implementation Order

| Step | What | Depends on |
|------|-------|-----------|
| 1 | Create package structure, move code into it | — |
| 2 | Data models (`models.py`) | — |
| 3 | `DiscordClient` + `RateLimiter` | models |
| 4 | `Config` class + `config.toml` | — |
| 5 | `JSONStorage` backend | models |
| 6 | `ScraperService` with incremental support | client, storage |
| 7 | `DownloaderService` | storage |
| 8 | `ExporterService` + CSV exporter | models, storage |
| 9 | UI module (console, progress, tables) | — |
| 10 | CLI commands wired to services + UI | everything above |
| 11 | `run` pipeline command | all commands |
| 12 | Testing setup + core tests | services |
| 13 | Linting setup | — |

Steps 2–4 and 9 can be done in parallel. Steps 6–8 can be done in parallel after step 5.
