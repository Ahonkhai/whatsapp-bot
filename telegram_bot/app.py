"""Flask app: receives Telegram webhook updates and replies."""

import logging

from flask import Flask, request

from telegram_bot import client, config
from telegram_bot.broadcast import send_broadcast
from telegram_bot.commands import handle_callback, handle_message
from telegram_bot.recipients import resolve_recipients
from telegram_bot.security import is_valid_secret_token

log = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.post("/webhook")
    def incoming():
        if config.WEBHOOK_SECRET:
            header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if not is_valid_secret_token(header, config.WEBHOOK_SECRET):
                log.warning("rejected webhook with invalid secret token")
                return "invalid secret token", 403
        else:
            log.warning("TELEGRAM_WEBHOOK_SECRET not set — accepting unverified updates")

        _handle_update(request.get_json(silent=True) or {})

        # Always 200: Telegram retries an update the webhook doesn't ack, and
        # backs the webhook off entirely after repeated errors, regardless of
        # what the update contained.
        return "ok", 200

    @app.get("/health")
    def health():
        return "ok", 200

    return app


def _handle_update(update: dict) -> None:
    if "callback_query" in update:
        _handle_button(update["callback_query"])
        return

    message = update.get("message") or update.get("edited_message")
    if message:
        _handle_text(message)


def _handle_text(message: dict) -> None:
    chat_id = message.get("chat", {}).get("id")
    body = message.get("text")
    if chat_id is None or not isinstance(body, str):
        return

    user_id = message.get("from", {}).get("id")

    if body.strip().lower().startswith("/broadcast"):
        _handle_broadcast(chat_id, user_id, body.strip())
        return

    reply = handle_message(body, user_id)
    client.send_message(chat_id, reply.text, reply.reply_markup, reply.parse_mode)


def _handle_button(callback: dict) -> None:
    """Handle a services-menu button tap."""
    query_id = callback.get("id")
    if query_id:
        # Acknowledge first so the button stops spinning even if the edit
        # below fails — a failure here shouldn't cost the user their reply.
        try:
            client.answer_callback_query(query_id)
        except Exception:
            log.exception("answerCallbackQuery failed")

    reply = handle_callback(callback.get("data") or "")
    if reply is None:
        return

    message = callback.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    if chat_id is None:
        return

    # Update the menu in place when we can, so tapping through services
    # doesn't fill the chat with copies of the menu.
    if message_id is not None:
        client.edit_message_text(chat_id, message_id, reply.text, reply.reply_markup, reply.parse_mode)
    else:
        client.send_message(chat_id, reply.text, reply.reply_markup, reply.parse_mode)


def _handle_broadcast(chat_id: int, user_id: int | None, body: str) -> None:
    if user_id is None or str(user_id) not in config.ADMIN_IDS:
        client.send_message(chat_id, "You're not authorized to broadcast.")
        return

    # In groups the command arrives as `/broadcast@MyBot hello`, so drop the
    # @BotName suffix along with the command itself.
    text = body[len("/broadcast"):]
    if text.startswith("@"):
        _, _, text = text.partition(" ")
    text = text.strip()
    if not text:
        client.send_message(chat_id, "Usage: /broadcast <message>")
        return

    recipients = [
        r for r in resolve_recipients(config.RECIPIENTS_FILE, config.RECIPIENTS)
        if r != str(chat_id)
    ]
    if not recipients:
        client.send_message(chat_id, "No recipients configured.")
        return

    result = send_broadcast(text, recipients, client.send_message)
    client.send_message(chat_id, result.summary)
