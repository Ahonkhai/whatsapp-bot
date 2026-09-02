"""Every environment variable the bot reads, in one place."""

import os

# Bot API
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Secret token echoed back by Telegram in the X-Telegram-Bot-Api-Secret-Token
# header on every webhook delivery. Optional, but strongly recommended in
# production — without it anyone who finds the webhook URL can POST fake
# updates to the bot. Set the same value here and when calling setWebhook.
WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")

# Public HTTPS URL of this app, used by set_webhook.py to register the
# webhook with Telegram (e.g. https://my-bot.up.railway.app).
WEBHOOK_URL = os.environ.get("TELEGRAM_WEBHOOK_URL", "")

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
