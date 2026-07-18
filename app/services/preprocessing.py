import hashlib
import re
import unicodedata

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE,
)
HTML_PATTERN = re.compile(r"<[^>]+>")
SPECIAL_PATTERN = re.compile(r"[^\w\s.,!?'\-%/]")
WHITESPACE_PATTERN = re.compile(r"\s+")


def clean_text(text: str | None) -> str:
    if not text:
        return ""
    value = unicodedata.normalize("NFKC", text)
    value = HTML_PATTERN.sub(" ", value)
    value = EMOJI_PATTERN.sub(" ", value)
    value = SPECIAL_PATTERN.sub(" ", value)
    value = WHITESPACE_PATTERN.sub(" ", value)
    return value.strip()


def normalize_for_dedup(text: str) -> str:
    return clean_text(text).lower()


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_for_dedup(text).encode("utf-8")).hexdigest()
