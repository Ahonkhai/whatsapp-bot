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
    monkeypatch.setattr(config, "RECIPIENTS", "")
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


def _message_payload(sender: str, body: str) -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {"from": sender, "type": "text", "text": {"body": body}}
                            ]
                        }
                    }
                ]
            }
        ]
    }


def test_broadcast_fans_out_to_recipients(client, monkeypatch, tmp_path):
    recipients_file = tmp_path / "recipients.txt"
    recipients_file.write_text("15551110001\n15551110002\n")
    monkeypatch.setattr(config, "ADMIN_NUMBERS", {"15559998888"})
    monkeypatch.setattr(config, "RECIPIENTS_FILE", str(recipients_file))

    sent = []
    monkeypatch.setattr("whatsapp_bot.app.client.send_text", lambda to, body: sent.append((to, body)))

    payload = _message_payload("15559998888", "/broadcast hello everyone")
    resp = client.post("/webhook", data=json.dumps(payload), content_type="application/json")

    assert resp.status_code == 200
    assert ("15551110001", "hello everyone") in sent
    assert ("15551110002", "hello everyone") in sent
    # summary reply to the admin
    assert ("15559998888", "Broadcast sent to 2/2.") in sent


def test_broadcast_uses_env_recipients_over_file(client, monkeypatch, tmp_path):
    recipients_file = tmp_path / "recipients.txt"
    recipients_file.write_text("15559990000\n")  # should be ignored: env takes priority
    monkeypatch.setattr(config, "ADMIN_NUMBERS", {"15559998888"})
    monkeypatch.setattr(config, "RECIPIENTS_FILE", str(recipients_file))
    monkeypatch.setattr(config, "RECIPIENTS", "15551110001,15551110002")

    sent = []
    monkeypatch.setattr("whatsapp_bot.app.client.send_text", lambda to, body: sent.append((to, body)))

    payload = _message_payload("15559998888", "/broadcast from env")
    resp = client.post("/webhook", data=json.dumps(payload), content_type="application/json")

    assert resp.status_code == 200
    assert ("15551110001", "from env") in sent
    assert ("15551110002", "from env") in sent
    assert ("15559990000", "from env") not in sent


def test_broadcast_rejects_non_admin(client, monkeypatch, tmp_path):
    recipients_file = tmp_path / "recipients.txt"
    recipients_file.write_text("15551110001\n")
    monkeypatch.setattr(config, "ADMIN_NUMBERS", {"15559998888"})
    monkeypatch.setattr(config, "RECIPIENTS_FILE", str(recipients_file))

    sent = []
    monkeypatch.setattr("whatsapp_bot.app.client.send_text", lambda to, body: sent.append((to, body)))

    payload = _message_payload("15550000000", "/broadcast sneaky")
    resp = client.post("/webhook", data=json.dumps(payload), content_type="application/json")

    assert resp.status_code == 200
    assert sent == [("15550000000", "You're not authorized to broadcast.")]


def test_broadcast_requires_message_text(client, monkeypatch):
    monkeypatch.setattr(config, "ADMIN_NUMBERS", {"15559998888"})

    sent = []
    monkeypatch.setattr("whatsapp_bot.app.client.send_text", lambda to, body: sent.append((to, body)))

    payload = _message_payload("15559998888", "/broadcast")
    resp = client.post("/webhook", data=json.dumps(payload), content_type="application/json")

    assert resp.status_code == 200
    assert sent == [("15559998888", "Usage: /broadcast <message>")]
