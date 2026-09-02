"""Thin client for the Telegram Bot API."""

import logging
from typing import Any

import requests

from telegram_bot import config

log = logging.getLogger(__name__)


def _call(method: str, payload: dict[str, Any]) -> None:
    response = requests.post(f"{config.api_url()}/{method}", json=payload, timeout=10)
    if not response.ok:
        log.error("%s failed (%s): %s", method, response.status_code, response.text)
    response.raise_for_status()


def send_message(
    chat_id: int | str,
    text: str,
    reply_markup: dict | None = None,
    parse_mode: str | None = None,
) -> None:
    """Send a message to a chat, optionally with an inline keyboard."""
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode
    _call("sendMessage", payload)


def edit_message_text(
    chat_id: int | str,
    message_id: int,
    text: str,
    reply_markup: dict | None = None,
    parse_mode: str | None = None,
) -> None:
    """Replace the text (and keyboard) of a message the bot already sent.

    Used for the services menu so tapping a button updates the message in
    place instead of pushing a new one into the chat.
    """
    payload: dict[str, Any] = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode
    _call("editMessageText", payload)


def answer_callback_query(callback_query_id: str, text: str | None = None) -> None:
    """Acknowledge a button tap so the client stops showing a spinner."""
    payload: dict[str, Any] = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    _call("answerCallbackQuery", payload)
