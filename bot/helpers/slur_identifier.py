import re
from pathlib import Path

# Load once when the module is imported
SLUR_FILE = Path(__file__).parent / "slurs.txt"

with open(SLUR_FILE, encoding="utf-8") as f:
    SLURS = {
        line.strip().lower()
        for line in f
        if line.strip() and not line.startswith("#")
    }


def normalize(text: str) -> str:
    text = text.lower()

    # Replace common leetspeak
    replacements = {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "@": "a",
        "$": "s",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove punctuation
    text = re.sub(r"[^a-z\s]", " ", text)

    # Collapse repeated letters (e.g. niiiiice -> niice)
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)

    return text


def identify_slurs(text: str):
    """
    Returns:
        {
            "found": bool,
            "matches": list[str],
            "count": int
        }
    """

    normalized = normalize(text)

    words = normalized.split()

    matches = sorted({
        word
        for word in words
        if word in SLURS
    })

    return {
        "found": len(matches) > 0,
        "matches": matches,
        "count": len(matches)
    }