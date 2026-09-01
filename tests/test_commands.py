from whatsapp_bot.commands import HELP_TEXT, handle_message


def test_ping():
    assert handle_message("/ping") == "pong"


def test_ping_case_insensitive():
    assert handle_message("/PING") == "pong"


def test_help():
    assert handle_message("/help") == HELP_TEXT
    assert "/broadcast" in HELP_TEXT


def test_echo():
    assert handle_message("hello there") == "hello there"


def test_echo_strips_whitespace():
    assert handle_message("  hi  ") == "hi"


def test_empty_message():
    assert handle_message("") == "(empty message)"
    assert handle_message("   ") == "(empty message)"
