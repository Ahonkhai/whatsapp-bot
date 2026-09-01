"""Entrypoint.

    WHATSAPP_ACCESS_TOKEN=... WHATSAPP_PHONE_NUMBER_ID=... WHATSAPP_VERIFY_TOKEN=... python run.py
"""

from whatsapp_bot import config
from whatsapp_bot.app import create_app
from whatsapp_bot.logging_setup import setup

setup()
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT)
