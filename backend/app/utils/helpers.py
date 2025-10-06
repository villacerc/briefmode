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
    # 1. Unicode normalize
    word = unicodedata.normalize("NFC", word)

    # 2. Casefold (Unicode-aware lowercase)
    word = word.casefold()

    # 3. Remove ASCII punctuation except apostrophe
    word = re.sub(r"[!¡¿\"#$%&()*+,\-./:;<=>?@[\\\]^_`{|}~]", "", word)

    # 4. Collapse whitespace
    word = re.sub(r"\s+", " ", word).strip()

    # 5. Strip accents
    word = ''.join(
        c for c in unicodedata.normalize('NFD', word)
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