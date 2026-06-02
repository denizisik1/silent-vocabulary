from ui_retrieve_log import RESULT_SEPARATOR, RetrieveResultsLog


def test_append_separates_sessions() -> None:
    log = RetrieveResultsLog()
    log.append("first session", begin_session=True)
    log.append("more in first")
    log.append("second session", begin_session=True)
    assert log.display_text() == (
        f"first session\nmore in first\n{RESULT_SEPARATOR}\nsecond session"
    )


def test_clear_hides_and_show_restores() -> None:
    log = RetrieveResultsLog()
    log.append("one", begin_session=True)
    log.clear()
    assert log.display_text() == ""
    assert log.has_archive()
    assert not log.showing_archive()

    log.append("two", begin_session=True)
    assert log.display_text() == "two"

    assert log.toggle_show_cleared()
    assert log.showing_archive()
    assert log.display_text() == f"one\n{RESULT_SEPARATOR}\ntwo"
    assert log.toggle_show_cleared() is False
    assert log.display_text() == "two"


def test_clear_stacks_archive() -> None:
    log = RetrieveResultsLog()
    log.append("a", begin_session=True)
    log.clear()
    log.append("b", begin_session=True)
    log.clear()
    log.toggle_show_cleared()
    assert log.display_text() == f"a\n{RESULT_SEPARATOR}\nb"
