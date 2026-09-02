"""The services the bot offers, and the inline keyboard that lists them.

This is the file to edit to make the bot your own: change `SERVICES` and the
menu, the buttons and the detail screens all follow. Each service needs a
short `id` (used as the button's callback_data, so keep it under ~30 chars
and free of spaces), a `label` for the button, and a `description` shown
when someone taps it.

Give a service a `url` instead and its button opens that link directly
rather than showing a detail screen — the right shape for a public channel
or a support chat.
"""

from dataclasses import dataclass

# callback_data prefixes. Telegram caps callback_data at 64 bytes, so these
# stay short.
SERVICE_PREFIX = "svc:"
BACK_ACTION = "svc:back"


@dataclass(frozen=True)
class Service:
    id: str
    label: str
    description: str
    # When set, the button is a link straight to this URL and `description`
    # is never shown. Must be https:// or tg:// — Telegram rejects the
    # keyboard outright otherwise.
    url: str = ""


SERVICES: tuple[Service, ...] = (
    Service(
        id="links",
        label="🔗 Get my links",
        description="Browse the sites I've built, by category.",  # unused: svc:links opens the category menu (see links.py)
    ),
    Service(
        id="plans",
        label="💎 Memberships and plans",
        description="See membership plans and buy access.",  # unused: svc:plans opens the store (see store.py)
    ),
    Service(
        id="add_domain",
        label="➕ Add a domain",
        description="Connect a custom domain to your account and start using it for your links.",
    ),
    Service(
        id="my_domain",
        label="🌐 My domain",
        description="See the domains on your account, their status, and their DNS settings.",
    ),
    Service(
        id="referrals",
        label="🎁 Refer and earn",
        description="Share your referral link and earn a reward for everyone who signs up through it.",
    ),
    Service(
        id="help_channel",
        label="📢 Help channel",
        description="Announcements, guides, and updates.",
        # e.g. "https://t.me/your_channel" — until this is filled in the
        # button shows the description above instead of opening a link.
        url="",
    ),
    Service(
        id="support",
        label="🛟 Support",
        description="Send your question here and someone will get back to you.",
        # e.g. "https://t.me/your_support_username"
        url="",
    ),
    # --- Placeholders. Rename these (id, label, description) as you decide
    # what goes here, or delete the ones you don't end up needing. ---
    Service(
        id="placeholder_1",
        label="🧩 Placeholder 1",
        description="Not set up yet — check back soon.",
    ),
    Service(
        id="placeholder_2",
        label="🧩 Placeholder 2",
        description="Not set up yet — check back soon.",
    ),
    Service(
        id="placeholder_3",
        label="🧩 Placeholder 3",
        description="Not set up yet — check back soon.",
    ),
)

BUTTONS_PER_ROW = 2


def find(service_id: str) -> Service | None:
    return next((s for s in SERVICES if s.id == service_id), None)


def _button(service: Service) -> dict:
    if service.url:
        return {"text": service.label, "url": service.url}
    return {"text": service.label, "callback_data": f"{SERVICE_PREFIX}{service.id}"}


def menu_keyboard() -> dict:
    """An inline keyboard with one button per service, laid out in rows."""
    buttons = [_button(service) for service in SERVICES]
    rows = [
        buttons[i:i + BUTTONS_PER_ROW]
        for i in range(0, len(buttons), BUTTONS_PER_ROW)
    ]
    return {"inline_keyboard": rows}


def back_keyboard() -> dict:
    """The single 'back' button shown on a service's detail screen."""
    return {"inline_keyboard": [[{"text": "⬅️ Back to services", "callback_data": BACK_ACTION}]]}
