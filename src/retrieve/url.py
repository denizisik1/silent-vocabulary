from urllib.parse import quote


def build_entry_url(base_url: str, word: str) -> str:
    cleaned_base = base_url.strip()
    cleaned_word = word.strip()
    if not cleaned_base:
        raise ValueError("Source URL is empty.")
    if not cleaned_word:
        raise ValueError("Word input is empty.")

    if not cleaned_base.endswith("/"):
        cleaned_base = f"{cleaned_base}/"
    return f"{cleaned_base}{quote(cleaned_word)}"
