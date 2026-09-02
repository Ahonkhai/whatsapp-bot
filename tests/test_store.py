import json

import pytest

from telegram_bot import store


def _store(tmp_path, data):
    path = tmp_path / "store.json"
    path.write_text(json.dumps(data))
    return store.load_store(str(path))


def test_missing_file_uses_defaults(tmp_path):
    s = store.load_store(str(tmp_path / "nope.json"))
    assert s.status_text == store.DEFAULT_STATUS
    assert s.plans == ()


def test_broken_json_uses_defaults(tmp_path):
    path = tmp_path / "store.json"
    path.write_text("{oops")
    assert store.load_store(str(path)).plans == ()


def test_plan_button_label_matches_the_reference(tmp_path):
    s = _store(tmp_path, {"plans": [
        {"id": "7d", "label": "7Day Membership", "price": "$1000", "duration": "7d"},
    ]})
    assert s.plans[0].button_label == "7Day Membership — $1000 / 7d"


def test_label_without_price_or_duration(tmp_path):
    s = _store(tmp_path, {"plans": [{"id": "x", "label": "Just a label"}]})
    assert s.plans[0].button_label == "Just a label"


def test_duplicate_and_invalid_items_are_dropped(tmp_path):
    s = _store(tmp_path, {"plans": [
        {"id": "a", "label": "First"},
        {"id": "a", "label": "Dup"},
        {"label": "no id"},
    ]})
    assert [p.id for p in s.plans] == ["a"]
    assert s.find_plan("a").label == "First"


def test_bad_item_url_is_dropped_but_item_kept(tmp_path):
    s = _store(tmp_path, {"plans": [
        {"id": "a", "label": "A", "url": "javascript:evil"},
    ]})
    assert s.plans[0].url == ""


def test_bad_contact_url_is_ignored(tmp_path):
    s = _store(tmp_path, {"contact_url": "ftp://nope", "plans": []})
    assert s.contact_url == ""


def _kb(pair):
    return pair[1]["inline_keyboard"]


def test_status_screen_offers_the_store_and_back(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE", _store(tmp_path, {"status_text": "nope"}))
    text, kb = store.status_screen()
    assert "nope" in text
    rows = kb["inline_keyboard"]
    assert rows[0][0]["callback_data"] == store.STORE_HOME
    assert rows[-1][0]["callback_data"] == "svc:back"


def test_store_home_has_both_sections(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE", _store(tmp_path, {}))
    rows = _kb(store.store_home_screen())
    datas = [b["callback_data"] for row in rows for b in row]
    assert store.STORE_PLANS in datas
    assert store.STORE_PAGES in datas
    assert store.STATUS_ACTION in datas  # back to status


def test_plans_screen_has_a_button_per_plan(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE", _store(tmp_path, {"plans": [
        {"id": "1h", "label": "1Hour Trial", "price": "$49", "duration": "0d"},
        {"id": "1d", "label": "1Day Trial", "price": "$200", "duration": "1d"},
    ]}))
    rows = _kb(store.plans_screen())
    assert rows[0][0]["callback_data"] == "store:p:1h"
    assert rows[-1][0]["callback_data"] == store.STORE_HOME


def test_empty_pages_screen_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE", _store(tmp_path, {"single_pages": []}))
    text, kb = store.pages_screen()
    assert "No single pages" in text
    assert kb["inline_keyboard"][-1][0]["callback_data"] == store.STORE_HOME


def test_checkout_uses_per_item_pay_link(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE", _store(tmp_path, {
        "contact_url": "https://t.me/admin",
        "plans": [{"id": "7d", "label": "7Day", "price": "$1000", "url": "https://pay.me/7d"}],
    }))
    _, kb = store.plan_checkout_screen(store.STORE.find_plan("7d"))
    pay = kb["inline_keyboard"][0][0]
    assert pay["url"] == "https://pay.me/7d"  # per-item wins over contact_url


def test_checkout_falls_back_to_contact_url(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE", _store(tmp_path, {
        "contact_url": "https://t.me/admin",
        "plans": [{"id": "7d", "label": "7Day", "price": "$1000"}],
    }))
    _, kb = store.plan_checkout_screen(store.STORE.find_plan("7d"))
    assert kb["inline_keyboard"][0][0]["url"] == "https://t.me/admin"


def test_checkout_without_any_link_is_just_a_back_button(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE", _store(tmp_path, {
        "plans": [{"id": "7d", "label": "7Day", "price": "$1000"}],
    }))
    _, kb = store.plan_checkout_screen(store.STORE.find_plan("7d"))
    assert len(kb["inline_keyboard"]) == 1
    assert kb["inline_keyboard"][0][0]["callback_data"] == store.STORE_PLANS


def test_shipped_store_json_is_valid():
    s = store.load_store("store.json")
    assert len(s.plans) == 6
    assert s.find_plan("60d").button_label == "60Day Membership — $4850 / 60d"


# routing through commands.handle_callback
from telegram_bot.commands import handle_callback


def test_plans_service_button_opens_the_status_screen():
    reply = handle_callback("svc:plans")
    assert "membership" in reply.text.lower()
    assert reply.reply_markup["inline_keyboard"][0][0]["callback_data"] == store.STORE_HOME


def test_full_store_navigation():
    assert "Store" in handle_callback("store:home").text
    assert "Membership Plan" in handle_callback("store:plans").text
    assert "7Day Membership" in handle_callback("store:p:7d").text
    assert handle_callback("store:p:nope") is None
