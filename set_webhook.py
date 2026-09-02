"""Registers this app's /webhook URL with Telegram.

Telegram has no dashboard for this — the webhook is set by calling the Bot
API once, which is what this script does. Run it after deploying, and again
whenever the public URL changes:

    TELEGRAM_BOT_TOKEN=... TELEGRAM_WEBHOOK_URL=https://my-bot.up.railway.app \
    TELEGRAM_WEBHOOK_SECRET=... python set_webhook.py

Pass `delete` to remove the webhook again (e.g. to fall back to polling):

    python set_webhook.py delete
"""

import sys

import requests

from telegram_bot import config


def set_webhook() -> None:
    if not config.BOT_TOKEN:
        sys.exit("TELEGRAM_BOT_TOKEN is not set.")
    if not config.WEBHOOK_URL:
        sys.exit("TELEGRAM_WEBHOOK_URL is not set (e.g. https://my-bot.up.railway.app).")
    if not config.WEBHOOK_SECRET:
        print("warning: TELEGRAM_WEBHOOK_SECRET is not set — the webhook will accept unverified updates.")

    payload = {
        "url": f"{config.WEBHOOK_URL.rstrip('/')}/webhook",
        # Without this the bot is not delivered button taps at all.
        "allowed_updates": ["message", "edited_message", "callback_query"],
    }
    if config.WEBHOOK_SECRET:
        payload["secret_token"] = config.WEBHOOK_SECRET

    response = requests.post(f"{config.API_URL}/setWebhook", json=payload, timeout=10)
    print(response.status_code, response.text)
    response.raise_for_status()


def delete_webhook() -> None:
    if not config.BOT_TOKEN:
        sys.exit("TELEGRAM_BOT_TOKEN is not set.")
    response = requests.post(f"{config.API_URL}/deleteWebhook", timeout=10)
    print(response.status_code, response.text)
    response.raise_for_status()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "delete":
        delete_webhook()
    else:
        set_webhook()
