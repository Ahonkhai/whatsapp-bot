"""The "Memberships and plans" store flow.

Screens, in order:
    membership status  →  Store  →  Full Membership Plans  →  a plan (checkout)
                                 →  Single Page Access      →  a page  (checkout)

The data lives in `store.json` (path via TELEGRAM_STORE_FILE) so prices and
copy can be edited without touching code. Shape:

    {
      "status_text": "You don't have an active membership.",
      "checkout_text": "To purchase, message the admin ...",
      "contact_url": "https://t.me/your_username",   # optional
      "plans": [
        {"id": "7d", "label": "7Day Membership", "price": "$1000",
         "duration": "7d", "url": ""}               # url optional: a pay link
      ],
      "single_pages": [
        {"id": "insta", "label": "Instagram page", "price": "$50", "url": ""}
      ]
    }

Note: the status line is the same for everyone — the bot has no per-user
membership store. Real "you have/don't have a membership" state would need a
database keyed by Telegram user id.
"""

import json
import logging
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

from telegram_bot import config

log = logging.getLogger(__name__)

# callback_data routes. Telegram caps callback_data at 64 bytes.
STORE_HOME = "store:home"
STORE_PLANS = "store:plans"
STORE_PAGES = "store:pages"
PLAN_PREFIX = "store:p:"
PAGE_PREFIX = "store:pg:"
# The membership-status screen is reached through the service button; its
# "Store / Buy" back-target reuses that same route.
STATUS_ACTION = "svc:plans"

DEFAULT_STATUS = "You don't have an active membership."
DEFAULT_CHECKOUT = "To purchase, message the admin with the plan name and you'll be given access."


@dataclass(frozen=True)
class Item:
    """A plan or a single-page product."""

    id: str
    label: str
    price: str = ""
    duration: str = ""
    url: str = ""

    @property
    def button_label(self) -> str:
        parts = self.label
        if self.price:
            parts += f" — {self.price}"
        if self.duration:
            parts += f" / {self.duration}"
        return parts


@dataclass(frozen=True)
class Store:
    status_text: str = DEFAULT_STATUS
    checkout_text: str = DEFAULT_CHECKOUT
    contact_url: str = ""
    plans: tuple[Item, ...] = field(default_factory=tuple)
    single_pages: tuple[Item, ...] = field(default_factory=tuple)

    def find_plan(self, item_id: str) -> Item | None:
        return next((p for p in self.plans if p.id == item_id), None)

    def find_page(self, item_id: str) -> Item | None:
        return next((p for p in self.single_pages if p.id == item_id), None)


def _valid_url(url: str) -> bool:
    return url.startswith(("https://", "http://", "tg://"))


def _parse_items(raw_items, prefix: str) -> tuple[Item, ...]:
    items: list[Item] = []
    seen: set[str] = set()
    for entry in raw_items or []:
        item_id = str(entry.get("id", "")).strip()
        label = str(entry.get("label", "")).strip()
        if not item_id or not label:
            log.warning("store.json: skipping an item with no id/label: %r", entry)
            continue
        if item_id in seen:
            log.warning("store.json: skipping duplicate item id %r", item_id)
            continue
        if len(f"{prefix}{item_id}".encode("utf-8")) > 64:
            log.warning("store.json: item id %r too long for callback_data", item_id)
            continue
        seen.add(item_id)
        url = str(entry.get("url", "")).strip()
        if url and not _valid_url(url):
            log.warning("store.json: dropping url %r on %r — not http(s)/tg", url, item_id)
            url = ""
        items.append(Item(
            item_id, label,
            str(entry.get("price", "")).strip(),
            str(entry.get("duration", "")).strip(),
            url,
        ))
    return tuple(items)


def parse_store(raw: dict) -> Store:
    return Store(
        status_text=str(raw.get("status_text", "")).strip() or DEFAULT_STATUS,
        checkout_text=str(raw.get("checkout_text", "")).strip() or DEFAULT_CHECKOUT,
        contact_url=str(raw.get("contact_url", "")).strip() if _valid_url(str(raw.get("contact_url", "")).strip()) else "",
        plans=_parse_items(raw.get("plans"), PLAN_PREFIX),
        single_pages=_parse_items(raw.get("single_pages"), PAGE_PREFIX),
    )


def load_store(path: str | None = None) -> Store:
    file = Path(path or config.STORE_FILE)
    if not file.exists():
        log.warning("store file not found at %s — using defaults", file)
        return Store()
    try:
        raw = json.loads(file.read_text())
    except (json.JSONDecodeError, OSError):
        log.exception("could not read %s — using defaults", file)
        return Store()
    return parse_store(raw)


# Loaded once at import (like the rest of the bot's config).
STORE = load_store()


# --- screens: each returns (text, keyboard) ---------------------------------

def _back(callback_data: str, label: str = "⬅️ Back") -> list[dict]:
    return [{"text": label, "callback_data": callback_data}]


def status_screen() -> tuple[str, dict]:
    text = f"💎 {escape(STORE.status_text)}"
    keyboard = {"inline_keyboard": [
        [{"text": "🛒 Store / Buy", "callback_data": STORE_HOME}],
        _back("svc:back"),
    ]}
    return text, keyboard


def store_home_screen() -> tuple[str, dict]:
    text = "🛒 <b>Store</b>\nChoose what you would like to purchase:"
    keyboard = {"inline_keyboard": [
        [{"text": "💎 Full Membership Plans", "callback_data": STORE_PLANS}],
        [{"text": "📄 Single Page Access", "callback_data": STORE_PAGES}],
        _back(STATUS_ACTION),
    ]}
    return text, keyboard


def plans_screen() -> tuple[str, dict]:
    text = "💎 <b>Choose a Membership Plan</b>"
    rows = [[{"text": plan.button_label, "callback_data": f"{PLAN_PREFIX}{plan.id}"}] for plan in STORE.plans]
    if not rows:
        text += "\n\nNo plans available yet."
    rows.append(_back(STORE_HOME))
    return text, {"inline_keyboard": rows}


def pages_screen() -> tuple[str, dict]:
    text = "📄 <b>Single Page Access</b>"
    rows = [[{"text": page.button_label, "callback_data": f"{PAGE_PREFIX}{page.id}"}] for page in STORE.single_pages]
    if not rows:
        text += "\n\nNo single pages available yet."
    rows.append(_back(STORE_HOME))
    return text, {"inline_keyboard": rows}


def _checkout_screen(item: Item, back_to: str) -> tuple[str, dict]:
    lines = [f"💎 <b>{escape(item.label)}</b>", ""]
    detail = " · ".join(p for p in (item.price, item.duration) if p)
    if detail:
        lines.append(escape(detail))
        lines.append("")
    lines.append(escape(STORE.checkout_text))
    text = "\n".join(lines)

    rows: list[list[dict]] = []
    # A per-item pay link wins; otherwise a shared contact link, if set.
    pay_url = item.url or STORE.contact_url
    if pay_url:
        rows.append([{"text": "💳 Continue", "url": pay_url}])
    rows.append(_back(back_to))
    return text, {"inline_keyboard": rows}


def plan_checkout_screen(item: Item) -> tuple[str, dict]:
    return _checkout_screen(item, STORE_PLANS)


def page_checkout_screen(item: Item) -> tuple[str, dict]:
    return _checkout_screen(item, STORE_PAGES)
