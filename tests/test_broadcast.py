from telegram_bot.broadcast import send_broadcast


def test_sends_to_everyone():
    sent = []

    def send(chat_id, text):
        sent.append((chat_id, text))

    result = send_broadcast("hi", ["1", "2", "3"], send)

    assert sent == [("1", "hi"), ("2", "hi"), ("3", "hi")]
    assert result.sent == ["1", "2", "3"]
    assert result.failed == []
    assert result.summary == "Broadcast sent to 3/3."


def test_one_failure_does_not_stop_the_rest():
    def send(chat_id, text):
        if chat_id == "2":
            raise RuntimeError("boom")

    result = send_broadcast("hi", ["1", "2", "3"], send)

    assert result.sent == ["1", "3"]
    assert result.failed == ["2"]
    assert result.summary == "Broadcast sent to 2/3. Failed: 2"
