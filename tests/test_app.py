import json

import pytest

from telegram_bot import config, services
from telegram_bot.app import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(config, "WEBHOOK_SECRET", "")
    monkeypatch.setattr(config, "RECIPIENTS", "")
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture
def sent(monkeypatch):
    """Captures every sendMessage the app makes."""
    calls = []
    monkeypatch.setattr(
        "telegram_bot.app.client.send_message",
        lambda chat_id, text, reply_markup=None, parse_mode=None: calls.append((chat_id, text, reply_markup)),
    )
    return calls


def _message_update(text: str, chat_id: int = 111, user_id: int | None = None) -> dict:
    return {
        "message": {
            "chat": {"id": chat_id},
            "from": {"id": user_id if user_id is not None else chat_id},
            "text": text,
        }
    }


def _callback_update(data: str, chat_id: int = 111, message_id: int | None = 7) -> dict:
    message = {"chat": {"id": chat_id}}
    if message_id is not None:
        message["message_id"] = message_id
    return {"callback_query": {"id": "cb1", "data": data, "message": message}}


def _post(client, update: dict):
    return client.post("/webhook", data=json.dumps(update), content_type="application/json")


def test_health(client):
    assert client.get("/health").status_code == 200


def test_incoming_message_triggers_reply(client, sent):
    resp = _post(client, _message_update("/ping"))

    assert resp.status_code == 200
    assert sent == [(111, "pong", None)]


def test_start_replies_with_the_services_keyboard(client, sent):
    resp = _post(client, _message_update("/start"))

    assert resp.status_code == 200
    chat_id, text, markup = sent[0]
    assert chat_id == 111
    assert "Welcome" in text
    assert markup == services.menu_keyboard()


def test_button_tap_is_acknowledged_and_edits_the_message(client, monkeypatch):
    answered = []
    edited = []
    monkeypatch.setattr("telegram_bot.app.client.answer_callback_query", lambda qid, text=None: answered.append(qid))
    monkeypatch.setattr(
        "telegram_bot.app.client.edit_message_text",
        lambda chat_id, message_id, text, reply_markup=None, parse_mode=None: edited.append((chat_id, message_id, text)),
    )

    service = services.SERVICES[0]
    resp = _post(client, _callback_update(f"{services.SERVICE_PREFIX}{service.id}"))

    assert resp.status_code == 200
    assert answered == ["cb1"]
    assert edited == [(111, 7, f"<b>{service.label}</b>\n\n{service.description}")]


def test_unknown_button_data_sends_nothing(client, sent, monkeypatch):
    monkeypatch.setattr("telegram_bot.app.client.answer_callback_query", lambda qid, text=None: None)
    edited = []
    monkeypatch.setattr(
        "telegram_bot.app.client.edit_message_text",
        lambda *a, **k: edited.append(a),
    )

    resp = _post(client, _callback_update("svc:does-not-exist"))

    assert resp.status_code == 200
    assert sent == []
    assert edited == []


def test_non_text_message_is_ignored(client, sent):
    resp = _post(client, {"message": {"chat": {"id": 111}, "photo": [{"file_id": "x"}]}})

    assert resp.status_code == 200
    assert sent == []


def test_webhook_rejects_wrong_secret_token(client, monkeypatch):
    monkeypatch.setattr(config, "WEBHOOK_SECRET", "shh")
    resp = client.post(
        "/webhook",
        data=b"{}",
        content_type="application/json",
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
    )
    assert resp.status_code == 403


def test_webhook_accepts_correct_secret_token(client, monkeypatch, sent):
    monkeypatch.setattr(config, "WEBHOOK_SECRET", "shh")
    resp = client.post(
        "/webhook",
        data=json.dumps(_message_update("/ping")),
        content_type="application/json",
        headers={"X-Telegram-Bot-Api-Secret-Token": "shh"},
    )
    assert resp.status_code == 200
    assert sent == [(111, "pong", None)]


def test_broadcast_fans_out_to_recipients(client, monkeypatch, sent, tmp_path):
    recipients_file = tmp_path / "recipients.txt"
    recipients_file.write_text("222222222\n333333333\n")
    monkeypatch.setattr(config, "ADMIN_IDS", {"999"})
    monkeypatch.setattr(config, "RECIPIENTS_FILE", str(recipients_file))

    resp = _post(client, _message_update("/broadcast hello everyone", chat_id=999))

    assert resp.status_code == 200
    bodies = [(chat_id, text) for chat_id, text, _ in sent]
    assert ("222222222", "hello everyone") in bodies
    assert ("333333333", "hello everyone") in bodies
    assert (999, "Broadcast sent to 2/2.") in bodies


def test_broadcast_uses_env_recipients_over_file(client, monkeypatch, sent, tmp_path):
    recipients_file = tmp_path / "recipients.txt"
    recipients_file.write_text("111111111\n")  # should be ignored: env takes priority
    monkeypatch.setattr(config, "ADMIN_IDS", {"999"})
    monkeypatch.setattr(config, "RECIPIENTS_FILE", str(recipients_file))
    monkeypatch.setattr(config, "RECIPIENTS", "222222222,333333333")

    resp = _post(client, _message_update("/broadcast from env", chat_id=999))

    assert resp.status_code == 200
    bodies = [(chat_id, text) for chat_id, text, _ in sent]
    assert ("222222222", "from env") in bodies
    assert ("111111111", "from env") not in bodies


def test_broadcast_rejects_non_admin(client, monkeypatch, sent, tmp_path):
    recipients_file = tmp_path / "recipients.txt"
    recipients_file.write_text("222222222\n")
    monkeypatch.setattr(config, "ADMIN_IDS", {"999"})
    monkeypatch.setattr(config, "RECIPIENTS_FILE", str(recipients_file))

    resp = _post(client, _message_update("/broadcast sneaky", chat_id=555))

    assert resp.status_code == 200
    assert sent == [(555, "You're not authorized to broadcast.", None)]


def test_broadcast_requires_message_text(client, monkeypatch, sent):
    monkeypatch.setattr(config, "ADMIN_IDS", {"999"})

    resp = _post(client, _message_update("/broadcast", chat_id=999))

    assert resp.status_code == 200
    assert sent == [(999, "Usage: /broadcast <message>", None)]


def test_broadcast_with_bot_suffix_still_parses_the_text(client, monkeypatch, sent):
    monkeypatch.setattr(config, "ADMIN_IDS", {"999"})
    monkeypatch.setattr(config, "RECIPIENTS", "222222222")

    resp = _post(client, _message_update("/broadcast@MyBot hi all", chat_id=999))

    assert resp.status_code == 200
    assert ("222222222", "hi all") in [(c, t) for c, t, _ in sent]
