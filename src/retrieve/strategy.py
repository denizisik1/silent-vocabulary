FETCH_METHOD_BASIC = "basic"
FETCH_METHOD_STEALTH = "stealth"

STRATEGY_PRIMARY_FIRST = "primary_first"
STRATEGY_BASIC_FIRST = "basic_first"

DEFAULT_RETRIEVE_STRATEGY = STRATEGY_PRIMARY_FIRST
RETRIEVE_STRATEGIES = frozenset(
    {
        STRATEGY_PRIMARY_FIRST,
        STRATEGY_BASIC_FIRST,
    }
)

STRATEGY_LABELS = {
    STRATEGY_PRIMARY_FIRST: "Primary first",
    STRATEGY_BASIC_FIRST: "Basic first",
}


def normalize_retrieve_strategy(value: str | None) -> str:
    if not isinstance(value, str):
        return DEFAULT_RETRIEVE_STRATEGY
    cleaned = value.strip().lower()
    if cleaned in RETRIEVE_STRATEGIES:
        return cleaned
    return DEFAULT_RETRIEVE_STRATEGY


def retrieve_attempt_order(strategy: str) -> list[tuple[str, str]]:
    primary_basic = ("primary", FETCH_METHOD_BASIC)
    primary_stealth = ("primary", FETCH_METHOD_STEALTH)
    backup_basic = ("backup", FETCH_METHOD_BASIC)
    backup_stealth = ("backup", FETCH_METHOD_STEALTH)

    normalized = normalize_retrieve_strategy(strategy)
    if normalized == STRATEGY_BASIC_FIRST:
        return [
            primary_basic,
            backup_basic,
            primary_stealth,
            backup_stealth,
        ]
    return [
        primary_basic,
        primary_stealth,
        backup_basic,
        backup_stealth,
    ]
