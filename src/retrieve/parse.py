import re

from lxml import html  # type: ignore[import-untyped]

from retrieve.headword import RANK_EXACT, headword_rank

_IPA_CHARACTERS = "ˈˌːɑɐəɛɪɔʊʃʒŋθðç"
_IPA_WRAPPERS = (
    ("[", "]", re.compile(r"\[([^\[\]]+)\]"), False),
    ("/", "/", re.compile(r"/([^/]+)/"), False),
    ("(", ")", re.compile(r"\(([^()]+)\)"), True),
    ('"', '"', re.compile(r'"([^"]+)"'), True),
)
_TITLE_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_CHALLENGE_TITLES = ("just a moment", "attention required", "access denied")
_CHALLENGE_MARKERS = ("cf-challenge", "cf_chl_opt", "cdn-cgi/challenge-platform")


class NoPronunciationFound(ValueError):
    def __init__(self, find_by: str, page_bytes: int) -> None:
        self.find_by = find_by
        self.page_bytes = page_bytes
        super().__init__(f"No IPA found for selector: {find_by} ({page_bytes} bytes read)")


def page_title(page_html: str) -> str:
    match = _TITLE_PATTERN.search(page_html)
    if match is None:
        return ""
    return " ".join(match.group(1).split()).strip()


def looks_like_challenge(page_html: str) -> bool:
    title = page_title(page_html).lower()
    if any(marker in title for marker in _CHALLENGE_TITLES):
        return True
    lowered = page_html.lower()
    return any(marker in lowered for marker in _CHALLENGE_MARKERS)


def _looks_like_ipa(text: str) -> bool:
    return any(character in text for character in _IPA_CHARACTERS)


def _delimited_ipa(text: str) -> str | None:
    earliest_start: int | None = None
    preserved: str | None = None
    for opener, closer, pattern, inner_must_look_like_ipa in _IPA_WRAPPERS:
        match = pattern.search(text)
        if match is None:
            continue
        inner = match.group(1).strip()
        if not inner:
            continue
        if inner_must_look_like_ipa and not _looks_like_ipa(inner):
            continue
        if earliest_start is None or match.start() < earliest_start:
            earliest_start = match.start()
            preserved = f"{opener}{inner}{closer}"
    return preserved


def clean_ipa_text(text: str) -> str | None:
    stripped = " ".join(text.split()).strip()
    if not stripped:
        return None

    delimited = _delimited_ipa(stripped)
    if delimited is not None:
        return delimited
    if _looks_like_ipa(stripped):
        return f'"{stripped}"'
    return None


def _class_token_xpath(token: str) -> str:
    safe = "".join(character for character in token if character.isalnum() or character in "-_")
    if not safe:
        raise ValueError(f"Invalid find-by token: {token}")
    return (
        "//*[contains(concat(' ', normalize-space(@class), ' '), "
        f"' {safe} ') or contains(@class, '{safe}')]"
    )


def _selector_xpath(token: str) -> str:
    if token.startswith("."):
        return _class_token_xpath(token[1:])
    if token.startswith("#"):
        safe_id = "".join(
            character for character in token[1:] if character.isalnum() or character in "-_"
        )
        return f"//*[@id='{safe_id}']"
    return _class_token_xpath(token)


def extract_ipa_from_html(page_html: str, find_by: str, word: str | None = None) -> str:
    token = find_by.strip()
    if not token:
        raise ValueError("Find-by selector is empty.")

    document = html.fromstring(page_html)
    best_rank: int | None = None
    best_ipa: str | None = None

    for node in document.xpath(_selector_xpath(token)):
        cleaned = clean_ipa_text(node.text_content())
        if not cleaned:
            continue
        rank = headword_rank(node, word)
        if rank is None:
            continue
        if best_rank is None or rank < best_rank:
            best_rank = rank
            best_ipa = cleaned
        if best_rank == RANK_EXACT:
            break

    if best_ipa is None:
        raise NoPronunciationFound(token, len(page_html))
    return best_ipa
