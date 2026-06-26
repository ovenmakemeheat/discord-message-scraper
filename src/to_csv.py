import csv
import json
import os
import sys
from glob import glob

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def convert_json_to_csv(json_path: str) -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        messages = json.load(f)

    csv_path = json_path.replace(".json", ".csv")

    fieldnames = [
        "id",
        "timestamp",
        "edited_timestamp",
        "author_id",
        "author_username",
        "author_display_name",
        "content",
        "type",
        "pinned",
        "attachments",
        "embeds_count",
        "mention_everyone",
        "mentions",
        "referenced_message_id",
    ]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for msg in messages:
            author = msg.get("author", {})
            attachments = msg.get("attachments", [])
            attachment_urls = ", ".join(a.get("url", "") for a in attachments)
            mention_list = msg.get("mentions", [])
            mention_names = ", ".join(m.get("username", "") for m in mention_list)
            ref = msg.get("referenced_message")

            writer.writerow(
                {
                    "id": msg["id"],
                    "timestamp": msg["timestamp"],
                    "edited_timestamp": msg.get("edited_timestamp", ""),
                    "author_id": author.get("id", ""),
                    "author_username": author.get("username", ""),
                    "author_display_name": author.get("global_name", ""),
                    "content": msg.get("content", ""),
                    "type": msg.get("type", ""),
                    "pinned": msg.get("pinned", False),
                    "attachments": attachment_urls,
                    "embeds_count": len(msg.get("embeds", [])),
                    "mention_everyone": msg.get("mention_everyone", False),
                    "mentions": mention_names,
                    "referenced_message_id": ref["id"] if ref else "",
                }
            )

    return len(messages), csv_path


def main():
    json_files = glob(os.path.join(DATA_DIR, "**", "messages.json"), recursive=True)

    if not json_files:
        print(f"Error: No messages.json files found in {DATA_DIR}/. Run main.py first.")
        sys.exit(1)

    print(f"Found {len(json_files)} JSON file(s) to convert.\n")

    for json_path in sorted(json_files):
        count, csv_path = convert_json_to_csv(json_path)
        print(f"  {json_path} -> {csv_path} ({count} messages)")

    print("\nDone.")


if __name__ == "__main__":
    main()
