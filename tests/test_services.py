from telegram_bot import services


def test_every_service_id_is_unique():
    ids = [s.id for s in services.SERVICES]
    assert len(ids) == len(set(ids))


def test_callback_data_fits_telegrams_64_byte_limit():
    for service in services.SERVICES:
        data = f"{services.SERVICE_PREFIX}{service.id}"
        assert len(data.encode("utf-8")) <= 64, data


def test_find_returns_the_service_or_none():
    assert services.find(services.SERVICES[0].id) is services.SERVICES[0]
    assert services.find("nope") is None


def test_menu_rows_respect_the_row_width():
    rows = services.menu_keyboard()["inline_keyboard"]
    assert all(len(row) <= services.BUTTONS_PER_ROW for row in rows)
    assert sum(len(row) for row in rows) == len(services.SERVICES)


def test_plain_service_button_carries_callback_data():
    service = services.Service(id="thing", label="Thing", description="d")
    assert services._button(service) == {"text": "Thing", "callback_data": "svc:thing"}


def test_service_with_a_url_becomes_a_link_button():
    """A url service opens the link directly — no callback, no detail screen."""
    service = services.Service(id="chan", label="Chan", description="d", url="https://t.me/x")
    button = services._button(service)
    assert button == {"text": "Chan", "url": "https://t.me/x"}
    assert "callback_data" not in button


def test_every_configured_url_is_a_scheme_telegram_accepts():
    for service in services.SERVICES:
        if service.url:
            assert service.url.startswith(("https://", "tg://")), service.id
