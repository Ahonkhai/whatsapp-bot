"""Registering (and removing) this app's webhook with Telegram.

Telegram has no dashboard for this — the webhook is set by one Bot API call.
Shared by `set_webhook.py` (run it by hand) and app startup (which does it
for you), so the token never has to leave the host.
"""

import logging

import requests

from telegram_bot import config

log = logging.getLogger(__name__)

# Without callback_query the bot is never delivered button taps, so the
# services menu would look dead.
ALLOWED_UPDATES = ["message", "edited_message", "callback_query"]


def base_url() -> str:
    """The app's public HTTPS base URL, explicit config first, then Railway's."""
    if config.WEBHOOK_URL:
        return config.WEBHOOK_URL.rstrip("/")
    if config.RAILWAY_DOMAIN:
        return f"https://{config.RAILWAY_DOMAIN.rstrip('/')}"
    return ""


def webhook_payload() -> dict:
    payload = {"url": f"{base_url()}/webhook", "allowed_updates": ALLOWED_UPDATES}
    if config.WEBHOOK_SECRET:
        payload["secret_token"] = config.WEBHOOK_SECRET
    return payload


def register() -> None:
    """Point Telegram at this app. Raises on any failure."""
    response = requests.post(f"{config.api_url()}/setWebhook", json=webhook_payload(), timeout=10)
    if not response.ok:
        log.error("setWebhook failed (%s): %s", response.status_code, response.text)
    response.raise_for_status()
    log.info("webhook registered at %s/webhook", base_url())


def delete() -> None:
    response = requests.post(f"{config.api_url()}/deleteWebhook", timeout=10)
    response.raise_for_status()
    log.info("webhook deleted")


def register_on_startup() -> None:
    """Best-effort webhook registration when the app boots.

    Never raises: a bot that can't reach Telegram right now should still come
    up and pass its health check, so the host doesn't crash-loop it while the
    logs explain what's wrong.
    """
    if not config.AUTO_SET_WEBHOOK:
        log.info("TELEGRAM_AUTO_SET_WEBHOOK is off — not touching the webhook")
        return
    if not config.BOT_TOKEN:
        log.error("TELEGRAM_BOT_TOKEN is not set — the bot cannot send or receive anything")
        return
    if not base_url():
        log.warning(
            "no public URL known (set TELEGRAM_WEBHOOK_URL, or generate a Railway domain) "
            "— skipping webhook registration"
        )
        return

    try:
        register()
    except Exception:
        log.exception("could not register the webhook on startup")
