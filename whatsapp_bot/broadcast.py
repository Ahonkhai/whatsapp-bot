"""Fans a message out to a list of recipients, one at a time.

Takes the send function as a parameter (rather than importing
`whatsapp_bot.client` directly) so it can be tested without any network
calls or WhatsApp credentials.
"""

import logging
from dataclasses import dataclass, field
from typing import Callable

log = logging.getLogger(__name__)


@dataclass
class BroadcastResult:
    sent: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        total = len(self.sent) + len(self.failed)
        text = f"Broadcast sent to {len(self.sent)}/{total}."
        if self.failed:
            text += f" Failed: {', '.join(self.failed)}"
        return text


def send_broadcast(text: str, recipients: list[str], send: Callable[[str, str], None]) -> BroadcastResult:
    result = BroadcastResult()
    for number in recipients:
        try:
            send(number, text)
        except Exception:
            log.exception("broadcast failed for %s", number)
            result.failed.append(number)
        else:
            result.sent.append(number)
    return result
