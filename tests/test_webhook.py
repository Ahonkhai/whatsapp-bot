import pytest

from telegram_bot import config, webhook


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.setattr(config, "BOT_TOKEN", "123:ABC")
    monkeypatch.setattr(config, "WEBHOOK_URL", "")
    monkeypatch.setattr(config, "RAILWAY_DOMAIN", "")
    monkeypatch.setattr(config, "WEBHOOK_SECRET", "")
    monkeypatch.setattr(config, "AUTO_SET_WEBHOOK", True)


def test_explicit_url_wins_over_railway(monkeypatch):
    monkeypatch.setattr(config, "WEBHOOK_URL", "https://explicit.example")
    monkeypatch.setattr(config, "RAILWAY_DOMAIN", "ignored.up.railway.app")
    assert webhook.base_url() == "https://explicit.example"


def test_railway_domain_is_used_when_no_explicit_url(monkeypatch):
    monkeypatch.setattr(config, "RAILWAY_DOMAIN", "my-bot.up.railway.app")
    assert webhook.base_url() == "https://my-bot.up.railway.app"


def test_trailing_slash_does_not_double_up(monkeypatch):
    monkeypatch.setattr(config, "WEBHOOK_URL", "https://example.com/")
    assert webhook.webhook_payload()["url"] == "https://example.com/webhook"


def test_no_url_configured():
    assert webhook.base_url() == ""


def test_payload_requests_callback_queries(monkeypatch):
    """Without callback_query Telegram never delivers button taps."""
    monkeypatch.setattr(config, "WEBHOOK_URL", "https://example.com")
    assert "callback_query" in webhook.webhook_payload()["allowed_updates"]


def test_payload_includes_the_secret_when_set(monkeypatch):
    monkeypatch.setattr(config, "WEBHOOK_URL", "https://example.com")
    monkeypatch.setattr(config, "WEBHOOK_SECRET", "shh")
    assert webhook.webhook_payload()["secret_token"] == "shh"


def test_payload_omits_the_secret_when_unset(monkeypatch):
    monkeypatch.setattr(config, "WEBHOOK_URL", "https://example.com")
    assert "secret_token" not in webhook.webhook_payload()


def test_api_url_reads_the_current_token(monkeypatch):
    monkeypatch.setattr(config, "BOT_TOKEN", "999:XYZ")
    assert config.api_url() == "https://api.telegram.org/bot999:XYZ"


def _no_register(monkeypatch):
    called = []
    monkeypatch.setattr(webhook, "register", lambda: called.append(True))
    return called


def test_startup_registers_when_configured(monkeypatch):
    monkeypatch.setattr(config, "WEBHOOK_URL", "https://example.com")
    called = _no_register(monkeypatch)
    webhook.register_on_startup()
    assert called == [True]


def test_startup_skips_when_auto_is_off(monkeypatch):
    monkeypatch.setattr(config, "WEBHOOK_URL", "https://example.com")
    monkeypatch.setattr(config, "AUTO_SET_WEBHOOK", False)
    called = _no_register(monkeypatch)
    webhook.register_on_startup()
    assert called == []


def test_startup_skips_without_a_token(monkeypatch):
    monkeypatch.setattr(config, "WEBHOOK_URL", "https://example.com")
    monkeypatch.setattr(config, "BOT_TOKEN", "")
    called = _no_register(monkeypatch)
    webhook.register_on_startup()
    assert called == []


def test_startup_skips_without_a_url(monkeypatch):
    called = _no_register(monkeypatch)
    webhook.register_on_startup()
    assert called == []


def test_startup_survives_telegram_being_down(monkeypatch):
    """A failed registration must not stop the app from booting."""
    monkeypatch.setattr(config, "WEBHOOK_URL", "https://example.com")

    def boom():
        raise RuntimeError("connection refused")

    monkeypatch.setattr(webhook, "register", boom)
    webhook.register_on_startup()  # must not raise
