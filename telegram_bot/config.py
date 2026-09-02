"""Every environment variable the bot reads, in one place."""

import os

# Bot API
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")


def api_url() -> str:
    """Base URL for Bot API calls. Read at call time, not import time, so the
    token can be swapped in tests without reimporting the module."""
    return f"https://api.telegram.org/bot{BOT_TOKEN}"


# Secret token echoed back by Telegram in the X-Telegram-Bot-Api-Secret-Token
# header on every webhook delivery. Optional, but strongly recommended in
# production — without it anyone who finds the webhook URL can POST fake
# updates to the bot. Set the same value here and when calling setWebhook.
WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")

# Public HTTPS URL of this app, used to register the webhook with Telegram
# (e.g. https://my-bot.up.railway.app). Railway injects RAILWAY_PUBLIC_DOMAIN
# once a domain is generated, so on Railway this needs no configuring.
WEBHOOK_URL = os.environ.get("TELEGRAM_WEBHOOK_URL", "")
RAILWAY_DOMAIN = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")

# Register the webhook automatically on startup. Means the token never has to
# leave the host to get the bot running; set to "false" to manage the webhook
# by hand with set_webhook.py instead.
AUTO_SET_WEBHOOK = os.environ.get("TELEGRAM_AUTO_SET_WEBHOOK", "true").strip().lower() not in ("false", "0", "no")

PORT = int(os.environ.get("PORT", "8080"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Broadcast feature: who's allowed to trigger /broadcast, and where the
# recipient list lives. Both are opt-in — an empty admin set means nobody
# can broadcast at all. IDs are numeric Telegram user/chat IDs (see /whoami).
ADMIN_IDS = {i.strip() for i in os.environ.get("TELEGRAM_ADMIN_IDS", "").split(",") if i.strip()}
RECIPIENTS_FILE = os.environ.get("TELEGRAM_RECIPIENTS_FILE", "recipients.txt")
# Comma-separated recipients, for hosts where a committed/mounted file isn't
# convenient (e.g. pasted straight into Railway's dashboard). Takes priority
# over RECIPIENTS_FILE when set.
RECIPIENTS = os.environ.get("TELEGRAM_RECIPIENTS", "")
