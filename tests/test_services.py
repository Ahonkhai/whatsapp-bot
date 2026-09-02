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
