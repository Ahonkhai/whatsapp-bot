"""Thin client for sending messages through the WhatsApp Cloud API."""

import logging

import requests

from whatsapp_bot import config

log = logging.getLogger(__name__)


def send_text(to: str, body: str) -> None:
    """Send a plain-text WhatsApp message to `to` (E.164, no leading '+')."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    headers = {"Authorization": f"Bearer {config.ACCESS_TOKEN}"}

    response = requests.post(config.GRAPH_API_URL, json=payload, headers=headers, timeout=10)
    if not response.ok:
        log.error("send_text failed (%s): %s", response.status_code, response.text)
    response.raise_for_status()
