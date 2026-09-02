"""Webhook authenticity check."""

import hmac


def is_valid_secret_token(header_value: str | None, expected: str) -> bool:
    """Check the X-Telegram-Bot-Api-Secret-Token header on an incoming update.

    Telegram echoes back verbatim whatever `secret_token` was passed to
    setWebhook, so this is a plain equality check rather than a signature —
    done in constant time so a wrong value can't be brute-forced by
    measuring response timing.
    """
    if not header_value:
        return False
    return hmac.compare_digest(header_value, expected)
