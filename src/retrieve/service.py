from dataclasses import dataclass

from retrieve.fetch import fetch_html, fetch_html_with_method, probe_url
from retrieve.parse import extract_ipa_from_html
from retrieve.strategy import FETCH_METHOD_BASIC, retrieve_attempt_order
from retrieve.url import build_entry_url


@dataclass(frozen=True)
class RetrieveResult:
    word: str
    url: str
    pronunciation: str
    source_label: str
    fetch_method: str = FETCH_METHOD_BASIC


@dataclass(frozen=True)
class CapabilityReport:
    source_label: str
    base_url: str
    sample_url: str
    reachable: bool
    detail: str
    ipa_found: bool
    sample_ipa: str | None = None


@dataclass(frozen=True)
class SourceEndpoint:
    label: str
    base_url: str
    find_by: str


def retrieve_ipa(
    *,
    base_url: str,
    find_by: str,
    word: str,
    source_label: str,
    fetch_method: str = FETCH_METHOD_BASIC,
) -> RetrieveResult:
    url = build_entry_url(base_url, word)
    page_html = fetch_html_with_method(url, fetch_method)
    pronunciation = extract_ipa_from_html(page_html, find_by)
    return RetrieveResult(
        word=word.strip(),
        url=url,
        pronunciation=pronunciation,
        source_label=source_label,
        fetch_method=fetch_method,
    )


def retrieve_ipa_with_strategy(
    *,
    word: str,
    primary: SourceEndpoint,
    backup: SourceEndpoint,
    strategy: str,
) -> RetrieveResult:
    endpoints = {
        primary.label: primary,
        backup.label: backup,
    }
    errors: list[str] = []
    for source_label, fetch_method in retrieve_attempt_order(strategy):
        endpoint = endpoints[source_label]
        try:
            return retrieve_ipa(
                base_url=endpoint.base_url,
                find_by=endpoint.find_by,
                word=word,
                source_label=source_label,
                fetch_method=fetch_method,
            )
        except (ValueError, RuntimeError, OSError) as error:
            errors.append(f"{source_label}/{fetch_method}: {error}")

    raise RuntimeError(" | ".join(errors) if errors else "Retrieve failed")


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
