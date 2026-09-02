"""Turns an incoming message (or button tap) into a reply.

Kept free of any Flask/HTTP/Telegram-client concerns so it can be tested
with plain values in, plain values out.
"""

from dataclasses import dataclass
from html import escape

from telegram_bot import links, services, store

HELP_TEXT = (
    "Available commands:\n"
    "/start - welcome message and the services menu\n"
    "/services - show the services menu again\n"
    "/help - show this message\n"
    "/ping - check the bot is alive\n"
    "/whoami - show your Telegram user ID\n"
    "/broadcast <message> - (admins only) send a message to everyone on the recipient list\n"
    "Anything else is echoed back."
)

WELCOME_TEXT = (
    "👋 <b>Welcome!</b>\n\n"
    "I'm here to help you find what you need. "
    "Pick one of the services below to learn more."
)

MENU_TEXT = "Here's what I can help with — pick a service:"


@dataclass
class Reply:
    """What to send back: text, plus an optional keyboard and parse mode."""

    text: str
    reply_markup: dict | None = None
    parse_mode: str | None = None


def _command_of(text: str) -> str:
    """First word, lowercased, with any @BotName suffix stripped.

    In groups Telegram delivers commands as `/start@MyBot`, so the suffix has
    to come off before matching.
    """
    if not text:
        return ""
    first = text.split()[0].lower()
    return first.split("@", 1)[0]


def welcome_reply() -> Reply:
    return Reply(WELCOME_TEXT, services.menu_keyboard(), parse_mode="HTML")


def menu_reply() -> Reply:
    return Reply(MENU_TEXT, services.menu_keyboard())


def handle_message(body: str, user_id: int | str | None = None) -> Reply:
    text = body.strip()
    command = _command_of(text)

    if command == "/start":
        return welcome_reply()
    if command in ("/services", "/menu"):
        return menu_reply()
    if command == "/help":
        return Reply(HELP_TEXT)
    if command == "/ping":
        return Reply("pong")
    if command == "/whoami":
        return Reply(f"Your Telegram ID is {user_id}." if user_id is not None else "Unknown ID.")
    if not text:
        return Reply("(empty message)")
    return Reply(text)


def links_home_reply() -> Reply:
    """The 'Get my links' category list."""
    return Reply(links.home_text(), links.home_keyboard(), parse_mode="HTML")


def _screen(pair) -> Reply:
    text, keyboard = pair
    return Reply(text, keyboard, parse_mode="HTML")


def _handle_store(data: str) -> Reply | None:
    """Routes for the memberships/plans store, or None if `data` isn't one."""
    if data == store.STATUS_ACTION or data == f"{services.SERVICE_PREFIX}plans":
        return _screen(store.status_screen())
    if data == store.STORE_HOME:
        return _screen(store.store_home_screen())
    if data == store.STORE_PLANS:
        return _screen(store.plans_screen())
    if data == store.STORE_PAGES:
        return _screen(store.pages_screen())
    if data.startswith(store.PLAN_PREFIX):
        item = store.STORE.find_plan(data[len(store.PLAN_PREFIX):])
        return _screen(store.plan_checkout_screen(item)) if item else None
    if data.startswith(store.PAGE_PREFIX):
        item = store.STORE.find_page(data[len(store.PAGE_PREFIX):])
        return _screen(store.page_checkout_screen(item)) if item else None
    return None


def handle_callback(data: str) -> Reply | None:
    """Turn a button's callback_data into a reply, or None if unrecognised."""
    if data == services.BACK_ACTION:
        return menu_reply()

    # The "Get my links" service opens the categories instead of a text screen.
    if data == links.LINKS_HOME or data == f"{services.SERVICE_PREFIX}links":
        return links_home_reply()

    if data.startswith(links.CATEGORY_PREFIX):
        category = links.CATALOG.find(data[len(links.CATEGORY_PREFIX):])
        if category is None:
            return None
        return Reply(links.category_text(category), links.category_keyboard(category), parse_mode="HTML")

    # The "Memberships and plans" store flow.
    store_reply = _handle_store(data)
    if store_reply is not None:
        return store_reply

    if data.startswith(services.SERVICE_PREFIX):
        service = services.find(data[len(services.SERVICE_PREFIX):])
        if service is None:
            return None
        text = f"<b>{escape(service.label)}</b>\n\n{escape(service.description)}"
        return Reply(text, services.back_keyboard(), parse_mode="HTML")

    return None
