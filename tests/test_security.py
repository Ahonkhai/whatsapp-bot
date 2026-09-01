import hashlib
import hmac

from whatsapp_bot.security import is_valid_signature

SECRET = "test-secret"


def _sign(payload: bytes, secret: str = SECRET) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_valid_signature():
    payload = b'{"hello":"world"}'
    assert is_valid_signature(payload, _sign(payload), SECRET)


def test_invalid_signature():
    payload = b'{"hello":"world"}'
    assert not is_valid_signature(payload, _sign(payload, secret="wrong"), SECRET)


def test_tampered_payload():
    payload = b'{"hello":"world"}'
    signature = _sign(payload)
    assert not is_valid_signature(b'{"hello":"mallory"}', signature, SECRET)


def test_missing_header():
    assert not is_valid_signature(b"{}", None, SECRET)


def test_malformed_header():
    assert not is_valid_signature(b"{}", "not-a-real-signature", SECRET)
