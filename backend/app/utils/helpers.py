import re
import regex
import unicodedata

NO_SPACE_LANGUAGES = ["ja", "zh", "th", "lo", "km", "my", "bo", "mn"]

def is_latin_script(text: str) -> bool:
    """Return True if all alphabetic characters are from the Latin script."""
    for ch in text:
        if ch.isalpha():
            try:
                if "LATIN" not in unicodedata.name(ch):
                    return False
            except ValueError:
                # Character has no Unicode name
                return False
    return True

def sanitize_word(word: str) -> str:
    word = unicodedata.normalize("NFC", word)
    word = word.casefold()

    # Remove all punctuation and symbols, except apostrophe
    word = "".join(
        c for c in word
        if (not unicodedata.category(c).startswith(("P", "S"))) or c == "'"
    )

    # Collapse whitespace
    word = re.sub(r"\s+", " ", word).strip()

    # Strip accents
    word = ''.join(
        c for c in unicodedata.normalize("NFD", word)
        if unicodedata.category(c) != 'Mn'
    )

    return word

def sanitize_phrase(phrase: str, lang: str = "en") -> str:
    # Unicode normalize + casefold
    phrase = unicodedata.normalize("NFC", phrase)
    phrase = phrase.casefold()

    # Remove punctuation except apostrophe
    phrase = re.sub(r"[!\"#$%&()*+,-./:;<=>?@[\\\]^_`{|}~]", "", phrase)

    # If language uses spaces, sanitize each word separately
    if lang not in NO_SPACE_LANGUAGES:
        words = phrase.split()
        words = [sanitize_word(w) for w in words if w]
        phrase = " ".join(words)
    else:
        # For no-space languages, sanitize the string as a whole
        phrase = sanitize_word(phrase)

    return phrase

def is_single_word(text):
    text = text.strip()

    # Contains spaces → phrase
    if " " in text:
        return False

    # Contains punctuation → phrase
    if any(unicodedata.category(c).startswith("P") for c in text):
        return False

    # Letters + numbers + combining marks only
    if not all(
        unicodedata.category(c)[0] in ("L", "M", "N")
        for c in text
    ):
        return False

    return True