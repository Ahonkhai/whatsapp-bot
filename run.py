"""Entrypoint.

    TELEGRAM_BOT_TOKEN=... TELEGRAM_WEBHOOK_SECRET=... python run.py
"""

from telegram_bot import config
from telegram_bot.app import create_app
from telegram_bot.logging_setup import setup

setup()
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT)
