"""Turns an incoming message body into a reply.

Kept free of any Flask/HTTP/WhatsApp-client concerns so it can be tested
with plain strings in, plain strings out.
"""

HELP_TEXT = (
    "Available commands:\n"
    "/help - show this message\n"
    "/ping - check the bot is alive\n"
    "/broadcast <message> - (admins only) send a message to everyone on the recipient list\n"
    "Anything else is echoed back."
)


def handle_message(body: str) -> str:
    text = body.strip()
    command = text.split()[0].lower() if text else ""

    if command == "/help":
        return HELP_TEXT
    if command == "/ping":
        return "pong"
    if not text:
        return "(empty message)"
    return text
