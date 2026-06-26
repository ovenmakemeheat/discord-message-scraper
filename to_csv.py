import csv
import json
import sys

INPUT_FILE = "data/messages.json"
OUTPUT_FILE = "data/messages.csv"


def main():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            messages = json.load(f)
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found. Run main.py first to scrape messages.")
        sys.exit(1)

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

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for msg in messages:
            author = msg.get("author", {})
            attachments = msg.get("attachments", [])
            attachment_urls = ", ".join(a.get("url", "") for a in attachments)
            mentions = msg.get("mentions", [])
            mention_names = ", ".join(m.get("username", "") for m in mentions)
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

    print(f"Converted {len(messages)} messages to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
