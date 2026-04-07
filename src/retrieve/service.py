from dataclasses import dataclass

from retrieve.fetch import fetch_html, probe_url
from retrieve.parse import extract_ipa_from_html
from retrieve.url import build_entry_url


@dataclass(frozen=True)
class RetrieveResult:
    word: str
    url: str
    pronunciation: str
    source_label: str


@dataclass(frozen=True)
class CapabilityReport:
    source_label: str
    base_url: str
    sample_url: str
    reachable: bool
    detail: str
    ipa_found: bool
    sample_ipa: str | None = None


def retrieve_ipa(
    *,
    base_url: str,
    find_by: str,
    word: str,
    source_label: str,
) -> RetrieveResult:
    url = build_entry_url(base_url, word)
    page_html = fetch_html(url)
    pronunciation = extract_ipa_from_html(page_html, find_by)
    return RetrieveResult(
        word=word.strip(),
        url=url,
        pronunciation=pronunciation,
        source_label=source_label,
    )


def check_source_capabilities(
    *,
    base_url: str,
    find_by: str,
    sample_word: str,
    source_label: str,
) -> CapabilityReport:
    sample_url = build_entry_url(base_url, sample_word)
    reachable, detail = probe_url(sample_url)
    if not reachable:
        return CapabilityReport(
            source_label=source_label,
            base_url=base_url,
            sample_url=sample_url,
            reachable=False,
            detail=detail,
            ipa_found=False,
        )

    try:
        page_html = fetch_html(sample_url)
        pronunciation = extract_ipa_from_html(page_html, find_by)
    except (ValueError, RuntimeError, OSError) as error:
        return CapabilityReport(
            source_label=source_label,
            base_url=base_url,
            sample_url=sample_url,
            reachable=True,
            detail=str(error),
            ipa_found=False,
        )

    return CapabilityReport(
        source_label=source_label,
        base_url=base_url,
        sample_url=sample_url,
        reachable=True,
        detail="ok",
        ipa_found=True,
        sample_ipa=pronunciation,
    )
