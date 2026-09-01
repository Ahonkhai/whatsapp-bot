"""Flask app: webhook verification + incoming message handling."""

import logging

from flask import Flask, request

from whatsapp_bot import client, config
from whatsapp_bot.broadcast import send_broadcast
from whatsapp_bot.commands import handle_message
from whatsapp_bot.recipients import resolve_recipients
from whatsapp_bot.security import is_valid_signature

log = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/webhook")
    def verify():
        """Meta's one-time handshake when you set the webhook URL."""
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge", "")

        if mode == "subscribe" and token == config.VERIFY_TOKEN:
            return challenge, 200
        return "verification failed", 403

    @app.post("/webhook")
    def incoming():
        if config.APP_SECRET:
            signature = request.headers.get("X-Hub-Signature-256")
            if not is_valid_signature(request.get_data(), signature, config.APP_SECRET):
                log.warning("rejected webhook with invalid signature")
                return "invalid signature", 403
        else:
            log.warning("WHATSAPP_APP_SECRET not set — skipping signature verification")

        payload = request.get_json(silent=True) or {}
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    _handle_message(message)

        # Always 200: Meta retries (and eventually disables) a webhook that
        # doesn't ack quickly, regardless of what the message contained.
        return "ok", 200

    @app.get("/health")
    def health():
        return "ok", 200

    return app


def _handle_message(message: dict) -> None:
    sender = message.get("from")
    if not sender or message.get("type") != "text":
        return

    body = message.get("text", {}).get("body", "").strip()

    if body.lower().startswith("/broadcast"):
        _handle_broadcast(sender, body)
        return

    reply = handle_message(body)
    client.send_text(sender, reply)


def _handle_broadcast(sender: str, body: str) -> None:
    if sender not in config.ADMIN_NUMBERS:
        client.send_text(sender, "You're not authorized to broadcast.")
        return

    text = body[len("/broadcast"):].strip()
    if not text:
        client.send_text(sender, "Usage: /broadcast <message>")
        return

    recipients = [n for n in resolve_recipients(config.RECIPIENTS_FILE, config.RECIPIENTS) if n != sender]
    if not recipients:
        client.send_text(sender, "No recipients configured.")
        return

    result = send_broadcast(text, recipients, client.send_text)
    client.send_text(sender, result.summary)
