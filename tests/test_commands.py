from telegram_bot import services
from telegram_bot.commands import HELP_TEXT, handle_callback, handle_message


def test_start_welcomes_and_shows_services():
    reply = handle_message("/start")
    assert "Welcome" in reply.text
    labels = [b["text"] for row in reply.reply_markup["inline_keyboard"] for b in row]
    assert labels == [s.label for s in services.SERVICES]


def test_start_with_bot_suffix_still_matches():
    """In groups Telegram delivers `/start@MyBot`."""
    assert handle_message("/start@MyBot").reply_markup is not None


def test_services_command_shows_the_menu():
    assert handle_message("/services").reply_markup == services.menu_keyboard()


def test_ping():
    assert handle_message("/ping").text == "pong"


def test_ping_case_insensitive():
    assert handle_message("/PING").text == "pong"


def test_help():
    assert handle_message("/help").text == HELP_TEXT
    assert "/start" in HELP_TEXT
    assert "/broadcast" in HELP_TEXT


def test_whoami_reports_the_user_id():
    assert "4242" in handle_message("/whoami", user_id=4242).text


def test_echo():
    assert handle_message("hello there").text == "hello there"


def test_echo_strips_whitespace():
    assert handle_message("  hi  ").text == "hi"


def test_echo_has_no_parse_mode():
    """User text is sent verbatim, so '<' in a message can't break the send."""
    assert handle_message("a < b").parse_mode is None


def test_empty_message():
    assert handle_message("").text == "(empty message)"
    assert handle_message("   ").text == "(empty message)"


def test_button_shows_service_details_and_a_back_button():
    service = services.find("plans")  # a normal detail-screen service
    reply = handle_callback(f"{services.SERVICE_PREFIX}{service.id}")
    assert service.description in reply.text
    assert reply.reply_markup == services.back_keyboard()


def test_back_button_returns_to_the_menu():
    reply = handle_callback(services.BACK_ACTION)
    assert reply.reply_markup == services.menu_keyboard()


def test_unknown_callback_data_is_ignored():
    assert handle_callback("svc:does-not-exist") is None
    assert handle_callback("garbage") is None
    assert handle_callback("") is None


def test_get_my_links_button_opens_the_category_list():
    reply = handle_callback("svc:links")
    assert reply is not None
    labels = [b["text"] for row in reply.reply_markup["inline_keyboard"] for b in row]
    assert any("Social Media" in l for l in labels)
    assert labels[-1] == "⬅️ Back"


def test_links_home_route_also_opens_the_category_list():
    assert handle_callback("lnk:home").reply_markup == handle_callback("svc:links").reply_markup


def test_category_button_shows_that_category():
    reply = handle_callback("lnk:c:social")
    assert reply is not None
    assert "Social Media" in reply.text


def test_unknown_category_is_ignored():
    assert handle_callback("lnk:c:does-not-exist") is None
