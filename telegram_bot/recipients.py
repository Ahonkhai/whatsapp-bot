"""Loads the broadcast recipient list from a plain-text file.

One Telegram chat ID per line. Blank lines and `#` comments are ignored, so
the file can be annotated:

    123456789    # Alex
    987654321    # Sam

A user has to have started a chat with the bot before it can message them —
Telegram bots cannot initiate conversations. Have people send /start, then
add the ID that /whoami reports.
"""

from pathlib import Path


def load_recipients(path: str) -> list[str]:
    file = Path(path)
    if not file.exists():
        return []

    chat_ids = []
    for line in file.read_text().splitlines():
        chat_id = line.split("#", 1)[0].strip()
        if chat_id:
            chat_ids.append(chat_id)
    return chat_ids


def resolve_recipients(file_path: str, env_value: str) -> list[str]:
    """TELEGRAM_RECIPIENTS (comma-separated) wins when set; otherwise the file."""
    if env_value.strip():
        return [c.strip() for c in env_value.split(",") if c.strip()]
    return load_recipients(file_path)
