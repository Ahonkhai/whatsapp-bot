import json

import pytest

from telegram_bot import links


def _catalog(tmp_path, data):
    path = tmp_path / "links.json"
    path.write_text(json.dumps(data))
    return links.load_catalog(str(path))


def test_missing_file_gives_an_empty_catalog(tmp_path):
    cat = links.load_catalog(str(tmp_path / "nope.json"))
    assert cat.categories == ()
    assert cat.title == links.DEFAULT_TITLE


def test_broken_json_gives_an_empty_catalog(tmp_path):
    path = tmp_path / "links.json"
    path.write_text("{not valid")
    assert links.load_catalog(str(path)).categories == ()


def test_counts_come_from_the_link_list(tmp_path):
    cat = _catalog(tmp_path, {"categories": [
        {"id": "s", "name": "Social", "links": [
            {"title": "A", "url": "https://a.com"},
            {"title": "B", "url": "https://b.com"},
        ]},
    ]})
    social = cat.find("s")
    assert social.count == 2
    assert "(2)" in social.button_label


def test_emoji_is_optional_in_the_label(tmp_path):
    cat = _catalog(tmp_path, {"categories": [
        {"id": "u", "name": "Uncategorized", "links": []},
        {"id": "g", "name": "Gaming", "emoji": "🎧", "links": []},
    ]})
    assert cat.find("u").button_label == "📁 Uncategorized (0)"
    assert cat.find("g").button_label == "📁 🎧 Gaming (0)"


def test_duplicate_ids_are_dropped(tmp_path):
    cat = _catalog(tmp_path, {"categories": [
        {"id": "x", "name": "First", "links": []},
        {"id": "x", "name": "Second", "links": []},
    ]})
    assert len(cat.categories) == 1
    assert cat.find("x").name == "First"


def test_same_name_different_id_both_kept(tmp_path):
    """Banking 🇺🇸 and Banking 🇬🇧 in the screenshot share a name, not an id."""
    cat = _catalog(tmp_path, {"categories": [
        {"id": "bank_us", "name": "Banking", "emoji": "🇺🇸", "links": []},
        {"id": "bank_uk", "name": "Banking", "emoji": "🇬🇧", "links": []},
    ]})
    assert [c.id for c in cat.categories] == ["bank_us", "bank_uk"]


def test_non_http_link_is_skipped(tmp_path):
    cat = _catalog(tmp_path, {"categories": [
        {"id": "s", "name": "S", "links": [
            {"title": "good", "url": "https://ok.com"},
            {"title": "bad", "url": "javascript:alert(1)"},
        ]},
    ]})
    titles = [l.title for l in cat.find("s").links]
    assert titles == ["good"]


def test_link_without_url_is_skipped(tmp_path):
    cat = _catalog(tmp_path, {"categories": [
        {"id": "s", "name": "S", "links": [{"title": "no url"}]},
    ]})
    assert cat.find("s").links == ()


def test_category_without_id_or_name_is_skipped(tmp_path):
    cat = _catalog(tmp_path, {"categories": [
        {"name": "no id", "links": []},
        {"id": "ok", "name": "Fine", "links": []},
    ]})
    assert [c.id for c in cat.categories] == ["ok"]


def test_home_keyboard_has_a_button_per_category_plus_back(tmp_path, monkeypatch):
    cat = _catalog(tmp_path, {"categories": [
        {"id": "a", "name": "A", "links": []},
        {"id": "b", "name": "B", "links": []},
    ]})
    monkeypatch.setattr(links, "CATALOG", cat)
    rows = links.home_keyboard()["inline_keyboard"]
    assert len(rows) == 3  # two categories + back
    assert rows[-1][0]["callback_data"] == "svc:back"
    assert rows[0][0]["callback_data"] == "lnk:c:a"


def test_category_keyboard_links_open_urls_and_has_a_back(tmp_path):
    cat = _catalog(tmp_path, {"categories": [
        {"id": "s", "name": "S", "links": [{"title": "Site", "url": "https://s.com"}]},
    ]})
    rows = links.category_keyboard(cat.find("s"))["inline_keyboard"]
    assert rows[0][0] == {"text": "Site", "url": "https://s.com"}
    assert rows[-1][0]["callback_data"] == links.LINKS_HOME


def test_shipped_links_json_is_valid():
    """The file committed to the repo must load cleanly."""
    cat = links.load_catalog("links.json")
    assert len(cat.categories) >= 1
    assert cat.find("social") is not None
