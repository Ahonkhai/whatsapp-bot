"""The "Get my links" showcase: categories, and the sites in each.

The data lives in `links.json` (path via TELEGRAM_LINKS_FILE) so it can be
edited without touching code — that's the file to change to add a site.
Shape:

    {
      "title": "🔗 Your links",
      "categories": [
        {"id": "social", "name": "Social Media", "emoji": "👥",
         "links": [{"title": "My Instagram clone", "url": "https://..."}]}
      ]
    }

Each category needs a unique `id` (used in callback_data, so keep it short
and free of spaces); `emoji` is optional. Every link needs a `title` and an
https:// (or tg://) `url`. Category counts are computed from the list, so
there's nothing to keep in sync.
"""

import json
import logging
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

from telegram_bot import config

log = logging.getLogger(__name__)

# callback_data routes. Telegram caps callback_data at 64 bytes.
LINKS_HOME = "lnk:home"
CATEGORY_PREFIX = "lnk:c:"

DEFAULT_TITLE = "🔗 Your links"


@dataclass(frozen=True)
class Link:
    title: str
    url: str


@dataclass(frozen=True)
class Category:
    id: str
    name: str
    emoji: str = ""
    links: tuple[Link, ...] = field(default_factory=tuple)

    @property
    def count(self) -> int:
        return len(self.links)

    @property
    def button_label(self) -> str:
        emoji = f"{self.emoji} " if self.emoji else ""
        return f"📁 {emoji}{self.name} ({self.count})"

    @property
    def heading(self) -> str:
        emoji = f"{self.emoji} " if self.emoji else ""
        return f"{emoji}{self.name}"


@dataclass(frozen=True)
class Catalog:
    title: str = DEFAULT_TITLE
    categories: tuple[Category, ...] = field(default_factory=tuple)

    def find(self, category_id: str) -> Category | None:
        return next((c for c in self.categories if c.id == category_id), None)


def _valid_url(url: str) -> bool:
    # Telegram rejects a whole keyboard if a button URL isn't one of these.
    return url.startswith(("https://", "http://", "tg://"))


def parse_catalog(raw: dict) -> Catalog:
    """Turn parsed JSON into a Catalog, skipping malformed entries loudly."""
    categories: list[Category] = []
    seen_ids: set[str] = set()

    for entry in raw.get("categories", []):
        cat_id = str(entry.get("id", "")).strip()
        name = str(entry.get("name", "")).strip()
        if not cat_id or not name:
            log.warning("links.json: skipping a category with no id/name: %r", entry)
            continue
        if cat_id in seen_ids:
            log.warning("links.json: skipping duplicate category id %r", cat_id)
            continue
        if len(f"{CATEGORY_PREFIX}{cat_id}".encode("utf-8")) > 64:
            log.warning("links.json: category id %r is too long for callback_data", cat_id)
            continue
        seen_ids.add(cat_id)

        links: list[Link] = []
        for item in entry.get("links", []):
            title = str(item.get("title", "")).strip()
            url = str(item.get("url", "")).strip()
            if not title or not url:
                log.warning("links.json: skipping a link with no title/url in %r", cat_id)
                continue
            if not _valid_url(url):
                log.warning("links.json: skipping %r — url %r is not http(s)/tg", title, url)
                continue
            links.append(Link(title, url))

        categories.append(Category(cat_id, name, str(entry.get("emoji", "")).strip(), tuple(links)))

    title = str(raw.get("title", "")).strip() or DEFAULT_TITLE
    return Catalog(title, tuple(categories))


def load_catalog(path: str | None = None) -> Catalog:
    """Load links.json. A missing or broken file yields an empty catalog and a
    log line, rather than taking the whole bot down."""
    file = Path(path or config.LINKS_FILE)
    if not file.exists():
        log.warning("links file not found at %s — the links menu will be empty", file)
        return Catalog()
    try:
        raw = json.loads(file.read_text())
    except (json.JSONDecodeError, OSError):
        log.exception("could not read %s — the links menu will be empty", file)
        return Catalog()
    return parse_catalog(raw)


# Loaded once at import. Editing links.json means a redeploy/restart, which is
# how the rest of the bot's config works too.
CATALOG = load_catalog()


def home_text() -> str:
    return f"<b>{escape(CATALOG.title)}</b>\nPick a category:"


def home_keyboard() -> dict:
    """One button per category (with its count), then a back-to-services row."""
    rows = [
        [{"text": category.button_label, "callback_data": f"{CATEGORY_PREFIX}{category.id}"}]
        for category in CATALOG.categories
    ]
    # Falls back to the services menu — see commands.handle_callback.
    rows.append([{"text": "⬅️ Back", "callback_data": "svc:back"}])
    return {"inline_keyboard": rows}


def category_text(category: Category) -> str:
    if not category.links:
        return f"<b>{escape(category.heading)}</b>\n\nNo links here yet."
    return f"<b>{escape(category.heading)}</b>\n\nTap a site to open it:"


def category_keyboard(category: Category) -> dict:
    """One link-button per site (opens the URL), then back to the category list."""
    rows = [[{"text": link.title, "url": link.url}] for link in category.links]
    rows.append([{"text": "⬅️ Back to categories", "callback_data": LINKS_HOME}])
    return {"inline_keyboard": rows}
