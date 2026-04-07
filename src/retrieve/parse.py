import re

from lxml import html  # type: ignore[import-untyped]

_IPA_PATTERN = re.compile(r"[/\[\()]([^/\[\]()]+)[/\]\)]")


def clean_ipa_text(text: str) -> str | None:
    stripped = " ".join(text.split()).strip()
    if not stripped:
        return None

    match = _IPA_PATTERN.search(stripped)
    if match:
        inner = match.group(1).strip()
        if inner:
            return f"[{inner}]"

    if any(character in stripped for character in "ˈˌːɑɐəɛɪɔʊʃʒŋθðç"):
        return f"[{stripped.strip('[]/() ')}]"
    return None


def _class_token_xpath(token: str) -> str:
    safe = "".join(character for character in token if character.isalnum() or character in "-_")
    if not safe:
        raise ValueError(f"Invalid find-by token: {token}")
    return (
        "//*[contains(concat(' ', normalize-space(@class), ' '), "
        f"' {safe} ') or contains(@class, '{safe}')]"
    )


def extract_ipa_from_html(page_html: str, find_by: str) -> str:
    token = find_by.strip()
    if not token:
        raise ValueError("Find-by selector is empty.")

    document = html.fromstring(page_html)
    if token.startswith("."):
        xpath = _class_token_xpath(token[1:])
    elif token.startswith("#"):
        safe_id = "".join(
            character for character in token[1:] if character.isalnum() or character in "-_"
        )
        xpath = f"//*[@id='{safe_id}']"
    else:
        xpath = _class_token_xpath(token)

    nodes = document.xpath(xpath)
    for node in nodes:
        cleaned = clean_ipa_text(node.text_content())
        if cleaned:
            return cleaned

    raise ValueError(f"No IPA found for selector: {token}")
