"""Loads the broadcast recipient list from a plain-text file.

One phone number per line (E.164, no leading '+'). Blank lines and `#`
comments are ignored, so the file can be annotated:

    15551234567   # Alex
    15559876543   # Sam
"""

from pathlib import Path


def load_recipients(path: str) -> list[str]:
    file = Path(path)
    if not file.exists():
        return []

    numbers = []
    for line in file.read_text().splitlines():
        number = line.split("#", 1)[0].strip()
        if number:
            numbers.append(number)
    return numbers
