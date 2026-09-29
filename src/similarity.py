"""
similarity.py
Pure standard-library string similarity used to detect look-alike / sound-alike
medicine name pairs. Two signals are combined:

  1. Orthographic similarity  - normalized Levenshtein edit distance (catches
     typos and visually similar spellings, e.g. "hydralazine" vs "hydroxyzine").
  2. Phonetic similarity      - a Soundex-style code comparison (catches names
     that sound alike when spoken or misheard over a phone/verbal order, even
     when spelled quite differently).

No external dependencies, so the project runs anywhere Python 3.8+ runs.
"""
from __future__ import annotations


def levenshtein_distance(a: str, b: str) -> int:
    a, b = a.lower(), b.lower()
    if a == b:
        return 0
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            cur[j] = min(
                prev[j] + 1,       # deletion
                cur[j - 1] + 1,    # insertion
                prev[j - 1] + cost # substitution
            )
        prev = cur
    return prev[-1]


def orthographic_similarity(a: str, b: str) -> float:
    """0.0 (completely different) .. 1.0 (identical)."""
    if not a or not b:
        return 0.0
    dist = levenshtein_distance(a, b)
    return 1.0 - dist / max(len(a), len(b))


_SOUNDEX_CODES = {
    "b": "1", "f": "1", "p": "1", "v": "1",
    "c": "2", "g": "2", "j": "2", "k": "2", "q": "2", "s": "2", "x": "2", "z": "2",
    "d": "3", "t": "3",
    "l": "4",
    "m": "5", "n": "5",
    "r": "6",
}


def soundex(word: str) -> str:
    """Classic Soundex phonetic code, e.g. 'Robert' and 'Rupert' -> 'R163'."""
    word = "".join(ch for ch in word.lower() if ch.isalpha())
    if not word:
        return "0000"
    first_letter = word[0].upper()
    codes = [_SOUNDEX_CODES.get(ch, "") for ch in word]
    digits = [first_letter]
    prev_code = _SOUNDEX_CODES.get(word[0], "")
    for ch, code in zip(word[1:], codes[1:]):
        if code and code != prev_code:
            digits.append(code)
        if ch not in ("h", "w"):
            prev_code = code
    result = "".join(digits)[:4]
    return (result + "000")[:4]

def double_metaphone(word: str) -> str:
    """Lightweight pharmacy-oriented Double Metaphone style code."""
    word = "".join(ch for ch in word.lower() if ch.isalpha())

    if not word:
        return ""

    replacements = [
        ("ph", "f"),
        ("ght", "t"),
        ("kn", "n"),
        ("wr", "r"),
        ("wh", "w"),
        ("ck", "k"),
        ("qu", "k"),
        ("x", "ks"),
        ("z", "s"),
        ("ch", "x"),
        ("sh", "x"),
        ("th", "t"),
    ]

    for old, new in replacements:
        word = word.replace(old, new)

    vowels = "aeiou"
    result = []

    for i, ch in enumerate(word):
        if ch in vowels:
            if i == 0:
                result.append(ch)
        elif not result or ch != result[-1]:
            result.append(ch)

    return "".join(result)[:6].upper()

def phonetic_similarity(a: str, b: str) -> float:
    """Compare Soundex and Double Metaphone phonetic similarity."""

    sa, sb = soundex(a), soundex(b)
    da, db = double_metaphone(a), double_metaphone(b)

    if sa == sb or da == db:
        return 1.0

    if sa[:3] == sb[:3] or da[:3] == db[:3]:
        return 0.5

    return 0.0

def combined_similarity(a: str, b: str, ortho_weight: float = 0.6) -> float:
    """Weighted blend of orthographic + phonetic similarity, 0.0 .. 1.0."""
    o = orthographic_similarity(a, b)
    p = phonetic_similarity(a, b)
    return round(ortho_weight * o + (1 - ortho_weight) * p, 4)
