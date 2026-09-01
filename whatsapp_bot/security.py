"""Webhook payload signature verification."""

import hashlib
import hmac


def is_valid_signature(payload: bytes, signature_header: str | None, app_secret: str) -> bool:
    """Check a request body against Meta's X-Hub-Signature-256 header.

    Meta signs the raw request body with the app secret (HMAC-SHA256) and
    sends it as `sha256=<hex digest>`. Comparison is constant-time to avoid
    leaking the expected digest through response timing.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(app_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)
