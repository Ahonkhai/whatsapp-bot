"""Entrypoint.

    TELEGRAM_BOT_TOKEN=... TELEGRAM_WEBHOOK_SECRET=... python run.py
"""

from telegram_bot import config, webhook
from telegram_bot.app import create_app
from telegram_bot.logging_setup import setup

setup()
app = create_app()

# Point Telegram at this deployment as it comes up. Under gunicorn each
# worker runs this, but setWebhook is idempotent so the repeat is harmless.
webhook.register_on_startup()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT)
