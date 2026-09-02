from telegram_bot.recipients import load_recipients, resolve_recipients


def test_missing_file_returns_empty_list(tmp_path):
    assert load_recipients(str(tmp_path / "nope.txt")) == []


def test_parses_ids_ignoring_comments_and_blanks(tmp_path):
    path = tmp_path / "recipients.txt"
    path.write_text(
        "\n".join(
            [
                "123456789    # Alex",
                "",
                "# a full-line comment",
                "  987654321  ",
            ]
        )
    )
    assert load_recipients(str(path)) == ["123456789", "987654321"]


def test_resolve_prefers_env_value_over_file(tmp_path):
    path = tmp_path / "recipients.txt"
    path.write_text("111111111\n")
    assert resolve_recipients(str(path), " 123456789, 987654321 ") == [
        "123456789",
        "987654321",
    ]


def test_resolve_falls_back_to_file_when_env_empty(tmp_path):
    path = tmp_path / "recipients.txt"
    path.write_text("111111111\n")
    assert resolve_recipients(str(path), "") == ["111111111"]
