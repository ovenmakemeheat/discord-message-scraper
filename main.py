import json
import os
import sys
import time

import httpx
from dotenv import load_dotenv

BASE_URL = "https://discord.com/api/v10"
MAX_PER_PAGE = 100
OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "messages.json")


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
            print(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after + 0.5)
            continue

        if response.status_code == 401:
            print("Error: Invalid or expired token.")
            sys.exit(1)

        if response.status_code == 403:
            print("Error: No access to this channel.")
            sys.exit(1)

        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            sys.exit(1)

        batch = response.json()

        if not batch:
            break

        all_messages.extend(batch)
        before_id = batch[-1]["id"]
        print(f"Fetched {len(all_messages)} messages so far...")

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
    load_dotenv()

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print(
            "Error: DISCORD_TOKEN not set. Copy .env.example to .env and fill in your token."
        )
        sys.exit(1)

    channel_id = os.getenv("CHANNEL_ID", "1430396032738529413")

    print(f"Scraping channel {channel_id}...")

    with httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": token},
        timeout=30.0,
    ) as client:
        messages = fetch_messages(client, channel_id)

    print(f"Total messages fetched: {len(messages)}")

    save_messages(messages, OUTPUT_FILE)
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
