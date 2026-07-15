from collections.abc import Sequence
from dataclasses import dataclass

from retrieve.fetch import fetch_html, fetch_html_with_method, probe_url
from retrieve.headword import WantedIpa
from retrieve.parse import NoPronunciationFound, extract_ipa_from_html
from retrieve.progress import KIND_BAD, KIND_GOOD, KIND_NOTE, report_progress
from retrieve.strategy import FETCH_METHOD_BASIC, FETCH_METHOD_BROWSER, retrieve_attempt_order
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
    wanted = WantedIpa(find_by=find_by, word=word.strip())
    page_html = fetch_html_with_method(url, fetch_method, wanted=wanted)
    pronunciation = extract_ipa_from_html(page_html, find_by, wanted.word)
    return RetrieveResult(
        word=word.strip(),
        url=url,
        pronunciation=pronunciation,
        source_label=source_label,
        fetch_method=fetch_method,
    )


def retrieve_ipa_with_attempts(
    *,
    word: str,
    primary: SourceEndpoint,
    backup: SourceEndpoint,
    attempts: Sequence[tuple[str, str]],
) -> RetrieveResult:
    endpoints = {
        primary.label: primary,
        backup.label: backup,
    }
    errors: list[str] = []
    read_without_ipa: set[str] = set()

    for source_label, fetch_method in attempts:
        attempt = f"{source_label}/{fetch_method}"
        endpoint = endpoints[source_label]
        if fetch_method == FETCH_METHOD_BROWSER and source_label in read_without_ipa:
            report_progress(
                f"{attempt} skipped, the page was read already and holds no IPA",
                KIND_NOTE,
            )
            continue

        try:
            result = retrieve_ipa(
                base_url=endpoint.base_url,
                find_by=endpoint.find_by,
                word=word,
                source_label=source_label,
                fetch_method=fetch_method,
            )
        except NoPronunciationFound as error:
            read_without_ipa.add(source_label)
            errors.append(f"{attempt}: {error}")
            report_progress(
                f"{attempt} read the page but it holds no {endpoint.find_by}",
                KIND_BAD,
            )
        except (ValueError, RuntimeError, OSError) as error:
            errors.append(f"{attempt}: {error}")
            report_progress(f"{attempt} failed: {error}", KIND_BAD)
        else:
            report_progress(f"{attempt} found {result.pronunciation}", KIND_GOOD)
            return result

    raise RuntimeError(" | ".join(errors) if errors else "Retrieve failed")


def retrieve_ipa_with_strategy(
    *,
    word: str,
    primary: SourceEndpoint,
    backup: SourceEndpoint,
    strategy: str,
) -> RetrieveResult:
    return retrieve_ipa_with_attempts(
        word=word,
        primary=primary,
        backup=backup,
        attempts=retrieve_attempt_order(strategy),
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
        page_html = fetch_html(sample_url, wanted=WantedIpa(find_by=find_by, word=sample_word))
        pronunciation = extract_ipa_from_html(page_html, find_by, sample_word)
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
