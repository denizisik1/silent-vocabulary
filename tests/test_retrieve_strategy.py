from retrieve import (
    DEFAULT_RETRIEVE_STRATEGY,
    STRATEGY_BASIC_FIRST,
    STRATEGY_PRIMARY_FIRST,
    normalize_retrieve_strategy,
    retrieve_attempt_order,
)

ALL_ATTEMPTS = {
    ("primary", "basic"),
    ("primary", "browser"),
    ("backup", "basic"),
    ("backup", "browser"),
}


def test_default_strategy_is_primary_first():
    assert DEFAULT_RETRIEVE_STRATEGY == STRATEGY_PRIMARY_FIRST


def test_normalize_accepts_known_strategies():
    assert normalize_retrieve_strategy(STRATEGY_BASIC_FIRST) == STRATEGY_BASIC_FIRST
    assert normalize_retrieve_strategy(STRATEGY_PRIMARY_FIRST) == STRATEGY_PRIMARY_FIRST


def test_normalize_ignores_case_and_surrounding_whitespace():
    assert normalize_retrieve_strategy("  BASIC_First  ") == STRATEGY_BASIC_FIRST


def test_normalize_falls_back_for_unusable_values():
    assert normalize_retrieve_strategy(None) == DEFAULT_RETRIEVE_STRATEGY
    assert normalize_retrieve_strategy("") == DEFAULT_RETRIEVE_STRATEGY
    assert normalize_retrieve_strategy("chaos") == DEFAULT_RETRIEVE_STRATEGY
    assert normalize_retrieve_strategy(42) == DEFAULT_RETRIEVE_STRATEGY


def test_primary_first_exhausts_primary_before_backup():
    assert retrieve_attempt_order(STRATEGY_PRIMARY_FIRST) == [
        ("primary", "basic"),
        ("primary", "browser"),
        ("backup", "basic"),
        ("backup", "browser"),
    ]


def test_basic_first_tries_both_sources_before_the_browser():
    assert retrieve_attempt_order(STRATEGY_BASIC_FIRST) == [
        ("primary", "basic"),
        ("backup", "basic"),
        ("primary", "browser"),
        ("backup", "browser"),
    ]


def test_unknown_strategy_uses_the_primary_first_order():
    assert retrieve_attempt_order("chaos") == retrieve_attempt_order(STRATEGY_PRIMARY_FIRST)


def test_every_strategy_covers_each_source_and_method_once():
    for strategy in (STRATEGY_PRIMARY_FIRST, STRATEGY_BASIC_FIRST):
        order = retrieve_attempt_order(strategy)

        assert len(order) == len(ALL_ATTEMPTS)
        assert set(order) == ALL_ATTEMPTS


def test_every_strategy_starts_with_the_cheapest_attempt():
    for strategy in (STRATEGY_PRIMARY_FIRST, STRATEGY_BASIC_FIRST):
        assert retrieve_attempt_order(strategy)[0] == ("primary", "basic")
