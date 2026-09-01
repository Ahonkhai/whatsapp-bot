from whatsapp_bot.recipients import load_recipients


def test_missing_file_returns_empty_list(tmp_path):
    assert load_recipients(str(tmp_path / "nope.txt")) == []


def test_parses_numbers_ignoring_comments_and_blanks(tmp_path):
    path = tmp_path / "recipients.txt"
    path.write_text(
        "\n".join(
            [
                "15551234567   # Alex",
                "",
                "# a full-line comment",
                "  15559876543  ",
            ]
        )
    )
    assert load_recipients(str(path)) == ["15551234567", "15559876543"]
