"""Registers this app's /webhook URL with Telegram, by hand.

The app does this for itself on startup, so you normally don't need this.
It's here for when TELEGRAM_AUTO_SET_WEBHOOK is off, or to point a bot at a
tunnel while developing locally:

    TELEGRAM_BOT_TOKEN=... TELEGRAM_WEBHOOK_URL=https://abc123.ngrok-free.app \
    TELEGRAM_WEBHOOK_SECRET=... python set_webhook.py

Pass `delete` to remove the webhook again:

    python set_webhook.py delete
"""

import sys

from telegram_bot import config, webhook
from telegram_bot.logging_setup import setup


def main() -> None:
    setup()
    if not config.BOT_TOKEN:
        sys.exit("TELEGRAM_BOT_TOKEN is not set.")

    if len(sys.argv) > 1 and sys.argv[1] == "delete":
        webhook.delete()
        return

    if not webhook.base_url():
        sys.exit("TELEGRAM_WEBHOOK_URL is not set (e.g. https://my-bot.up.railway.app).")
    if not config.WEBHOOK_SECRET:
        print("warning: TELEGRAM_WEBHOOK_SECRET is not set — the webhook will accept unverified updates.")
    webhook.register()


if __name__ == "__main__":
    main()
