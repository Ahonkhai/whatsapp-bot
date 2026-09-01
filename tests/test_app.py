import hashlib
import hmac
import json

import pytest

from whatsapp_bot import config
from whatsapp_bot.app import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(config, "VERIFY_TOKEN", "verify-me")
    monkeypatch.setattr(config, "APP_SECRET", "")
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_webhook_verification_succeeds(client):
    resp = client.get(
        "/webhook",
        query_string={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-me",
            "hub.challenge": "12345",
        },
    )
    assert resp.status_code == 200
    assert resp.text == "12345"


def test_webhook_verification_wrong_token(client):
    resp = client.get(
        "/webhook",
        query_string={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong",
            "hub.challenge": "12345",
        },
    )
    assert resp.status_code == 403


def test_incoming_message_triggers_reply(client, monkeypatch):
    sent = {}

    def fake_send_text(to, body):
        sent["to"] = to
        sent["body"] = body

    monkeypatch.setattr("whatsapp_bot.app.client.send_text", fake_send_text)

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "15551234567",
                                    "type": "text",
                                    "text": {"body": "/ping"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    resp = client.post("/webhook", data=json.dumps(payload), content_type="application/json")

    assert resp.status_code == 200
    assert sent == {"to": "15551234567", "body": "pong"}


def test_incoming_rejects_bad_signature(client, monkeypatch):
    monkeypatch.setattr(config, "APP_SECRET", "shh")
    resp = client.post(
        "/webhook",
        data=b"{}",
        content_type="application/json",
        headers={"X-Hub-Signature-256": "sha256=deadbeef"},
    )
    assert resp.status_code == 403
