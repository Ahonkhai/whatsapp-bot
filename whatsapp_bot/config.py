"""Every environment variable the bot reads, in one place."""

import os

# WhatsApp Cloud API
ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
API_VERSION = os.environ.get("WHATSAPP_API_VERSION", "v21.0")
GRAPH_API_URL = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"

# Webhook verification (the value you type into the Meta dashboard)
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")

# App secret, used to verify the X-Hub-Signature-256 header on incoming
# webhooks. Optional, but strongly recommended in production — without it
# anyone who finds the webhook URL can POST fake messages to the bot.
APP_SECRET = os.environ.get("WHATSAPP_APP_SECRET", "")

PORT = int(os.environ.get("PORT", "8080"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Broadcast feature: who's allowed to trigger /broadcast, and where the
# recipient list lives. Both are opt-in — an empty admin set means nobody
# can broadcast at all.
ADMIN_NUMBERS = {n.strip() for n in os.environ.get("WHATSAPP_ADMIN_NUMBERS", "").split(",") if n.strip()}
RECIPIENTS_FILE = os.environ.get("WHATSAPP_RECIPIENTS_FILE", "recipients.txt")
