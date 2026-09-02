"""The services the bot offers, and the inline keyboard that lists them.

This is the file to edit to make the bot your own: change `SERVICES` and the
menu, the buttons and the detail screens all follow. Each service needs a
short `id` (used as the button's callback_data, so keep it under ~30 chars
and free of spaces), a `label` for the button, and a `description` shown
when someone taps it.
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


SERVICES: tuple[Service, ...] = (
    Service(
        id="consulting",
        label="💼 Consulting",
        description="One-on-one sessions to scope your project and pick an approach.",
    ),
    Service(
        id="development",
        label="🛠 Development",
        description="Custom builds — web apps, bots, and integrations, delivered end to end.",
    ),
    Service(
        id="support",
        label="🤝 Support",
        description="Ongoing maintenance, monitoring, and fixes for something already live.",
    ),
    Service(
        id="pricing",
        label="💳 Pricing",
        description="Hourly and per-project rates, with a fixed quote after a short call.",
    ),
    Service(
        id="contact",
        label="📩 Contact",
        description="Reach a human directly — just reply here and we'll get back to you.",
    ),
)

BUTTONS_PER_ROW = 2


def find(service_id: str) -> Service | None:
    return next((s for s in SERVICES if s.id == service_id), None)


def menu_keyboard() -> dict:
    """An inline keyboard with one button per service, laid out in rows."""
    buttons = [
        {"text": service.label, "callback_data": f"{SERVICE_PREFIX}{service.id}"}
        for service in SERVICES
    ]
    rows = [
        buttons[i:i + BUTTONS_PER_ROW]
        for i in range(0, len(buttons), BUTTONS_PER_ROW)
    ]
    return {"inline_keyboard": rows}


def back_keyboard() -> dict:
    """The single 'back' button shown on a service's detail screen."""
    return {"inline_keyboard": [[{"text": "⬅️ Back to services", "callback_data": BACK_ACTION}]]}
