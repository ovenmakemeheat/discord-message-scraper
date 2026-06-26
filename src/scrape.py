import json
import os
import re
import sys
import time

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://discord.com/api/v10"
MAX_PER_PAGE = 100
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

CHANNEL_IDS = [
    "1215564428007972874",
    "1120213595469389844",
    "1211961995692220417",
    "1192732570446745630",
    "1394153042034688131",
    "1111635331117223986",
    "1430396032738529413",
]


def slugify(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_-]+", "-", name)
    return name


def fetch_channel_info(client: httpx.Client, channel_id: str) -> dict:
    response = client.get(f"/channels/{channel_id}")

    if response.status_code == 429:
        retry_after = response.json().get("retry_after", 5)
        time.sleep(retry_after + 0.5)
        return fetch_channel_info(client, channel_id)

    if response.status_code != 200:
        return {"id": channel_id, "name": channel_id, "guild_id": "unknown"}

    return response.json()


def fetch_guild_info(client: httpx.Client, guild_id: str) -> dict:
    response = client.get(f"/guilds/{guild_id}")

    if response.status_code == 429:
        retry_after = response.json().get("retry_after", 5)
        time.sleep(retry_after + 0.5)
        return fetch_guild_info(client, guild_id)

    if response.status_code != 200:
        return {"id": guild_id, "name": guild_id}

    return response.json()


def fetch_messages(client: httpx.Client, channel_id: str) -> list[dict]:
    all_messages = []
    before_id = None

    while True:
        params = {"limit": MAX_PER_PAGE}
        if before_id:
            params["before"] = before_id

        response = client.get(f"/channels/{channel_id}/messages", params=params)

        if response.status_code == 429:
            retry_after = response.json().get("retry_after", 5)
            print(f"  Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after + 0.5)
            continue

        if response.status_code == 401:
            print("Error: Invalid or expired token.")
            sys.exit(1)

        if response.status_code == 403:
            print(f"  Warning: No access to channel {channel_id}, skipping.")
            return []

        if response.status_code != 200:
            print(f"  Error: HTTP {response.status_code}")
            print(f"  {response.text}")
            return []

        batch = response.json()

        if not batch:
            break

        all_messages.extend(batch)
        before_id = batch[-1]["id"]
        print(f"  Fetched {len(all_messages)} messages so far...")

        if len(batch) < MAX_PER_PAGE:
            break

        time.sleep(0.5)

    return all_messages


def save_messages(messages: list[dict], filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    messages.sort(key=lambda m: m["timestamp"])
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)


def main():
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print(
            "Error: DISCORD_TOKEN not set. Copy .env.example to .env and fill in your token."
        )
        sys.exit(1)

    with httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": token},
        timeout=30.0,
    ) as client:
        guild_names: dict[str, str] = {}

        for channel_id in CHANNEL_IDS:
            print(f"\n--- Channel {channel_id} ---")

            channel_info = fetch_channel_info(client, channel_id)
            channel_name = channel_info.get("name", channel_id)
            guild_id = channel_info.get("guild_id", "unknown")

            if guild_id not in guild_names:
                guild_info = fetch_guild_info(client, guild_id)
                guild_names[guild_id] = guild_info.get("name", guild_id)

            guild_name = guild_names[guild_id]
            guild_slug = slugify(guild_name)
            channel_slug = slugify(channel_name)

            print(f"  Server: {guild_name}")
            print(f"  Channel: #{channel_name}")

            messages = fetch_messages(client, channel_id)

            if not messages:
                print("  No messages found, skipping.")
                continue

            output_dir = os.path.join(DATA_DIR, guild_slug, channel_slug)
            output_file = os.path.join(output_dir, "messages.json")
            save_messages(messages, output_file)
            print(f"  Saved {len(messages)} messages to {output_file}")

    print("\nDone.")


if __name__ == "__main__":
    main()
