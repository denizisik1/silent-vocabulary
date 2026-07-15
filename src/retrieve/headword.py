import re
import unicodedata
from dataclasses import dataclass
from typing import Any

RANK_EXACT = 0
RANK_SAME_LETTERS = 1
RANK_UNATTRIBUTED = 2

_SECTION_MARKER = re.compile(r"^(?:[IVXLC]+|\d+)\s*[.)]\s*", re.IGNORECASE)
_SYLLABLE_MARKS = ("\u00b7", "\u00ad", "\u2027", "|")

_HEADWORD_TEST = (
    "self::h1 or self::h2 or self::h3 or self::h4"
    " or contains(@class,'headword') or contains(@class,'hdwd')"
    " or contains(@class,'entry_title') or contains(@class,'orth')"
)
_ANCESTOR_HEADWORD = f"ancestor-or-self::*[{_HEADWORD_TEST}][1]"
_PRECEDING_HEADWORD = f"preceding::*[{_HEADWORD_TEST}][1]"


@dataclass(frozen=True)
class WantedIpa:
    find_by: str
    word: str | None = None


def plain_text(text: str) -> str:
    cleaned = text
    for mark in _SYLLABLE_MARKS:
        cleaned = cleaned.replace(mark, "")
    return unicodedata.normalize("NFC", " ".join(cleaned.split()))


def headword_of_heading(heading: str) -> str:
    text = plain_text(heading)
    while True:
        shortened = _SECTION_MARKER.sub("", text)
        if shortened == text:
            return text
        text = shortened


def heading_names_word(heading: str, word: str, *, ignore_case: bool) -> bool:
    text = headword_of_heading(heading)
    wanted = plain_text(word)
    if not wanted:
        return False
    if ignore_case:
        text = text.lower()
        wanted = wanted.lower()
    if not text.startswith(wanted):
        return False
    if len(text) == len(wanted):
        return True
    return not text[len(wanted)].isalpha()


def heading_near(node: Any) -> str:
    for xpath in (_ANCESTOR_HEADWORD, _PRECEDING_HEADWORD):
        found = node.xpath(xpath)
        if not found:
            continue
        heading = " ".join(found[0].text_content().split())
        if heading:
            return heading
    return ""


def headword_rank(node: Any, word: str | None) -> int | None:
    if not word or not word.strip():
        return RANK_UNATTRIBUTED

    heading = heading_near(node)
    if not heading:
        return RANK_UNATTRIBUTED
    if heading_names_word(heading, word, ignore_case=False):
        return RANK_EXACT
    if heading_names_word(heading, word, ignore_case=True):
        return RANK_SAME_LETTERS
    return None
