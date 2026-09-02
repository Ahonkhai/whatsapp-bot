from telegram_bot.security import is_valid_secret_token

SECRET = "test-secret"


def test_matching_token():
    assert is_valid_secret_token(SECRET, SECRET)


def test_wrong_token():
    assert not is_valid_secret_token("nope", SECRET)


def test_missing_header():
    assert not is_valid_secret_token(None, SECRET)


def test_empty_header():
    assert not is_valid_secret_token("", SECRET)
