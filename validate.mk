.PHONY: format tidy lint typecheck security test a b c d e f x


# ---------------------------------------------------------------------------
# When a tool below reports a problem, judge it first:
#   - If it's a real issue, fix the underlying code.
#   - If it's a false positive, or a deliberate pattern that isn't worth a
#     rewrite, suppress it - but as narrowly as possible (one rule, one
#     line) - and leave a short comment saying why on that same line.
#
# Keep the suppressor and the reason on the same line as the code they
# apply to, even if that goes past the line length. Then also skip the
# formatter and the line-length check on that line:
#   some_code()  # pylint: disable=broad-except  # why  # noqa: E501  # fmt: skip
# Put "# fmt: skip" last so black still sees it. Only add E501 / fmt: skip
# when the line actually exceeds the limit. If pylint then reports
# line-too-long, add that rule to the pylint: disable list on the same line.
#
# Don't reach for a broad disable (a whole rule turned off project-wide, or
# the whole tool skipped) when a single-line suppression would do. Each tool
# has its own syntax for this; see the comment above each target below.
# ---------------------------------------------------------------------------

# black: reformats code automatically, it doesn't really "complain" about
# choices you can disagree with. If one line must keep its layout (a
# hand-aligned table, or a long suppressor comment), append:
#   # fmt: skip
# For a whole block:
#   # fmt: off
#   ...code...
#   # fmt: on
# Use sparingly.
a format:
	black --line-length 100 src tests

# flake8: style/lint checker (pycodestyle + pyflakes).
# Suppress one warning on one line with:
#   some_code()  # noqa: E501
# Always name the specific code (E501, F401, ...). A bare "# noqa" silences
# every check on that line, including ones that show up later - avoid it.
# A long suppressor comment is the usual E501 case; combine as:
#   some_code()  # pylint: disable=broad-except  # why  # noqa: E501  # fmt: skip
# If a whole file should be exempt from a rule on purpose (e.g. imports
# after an env check), add it to --per-file-ignores below rather than
# scattering noqa comments through the file.
b tidy:
	flake8 --max-line-length 100 \
		--per-file-ignores='src/init.py:E402,src/fetch_pronunciations.py:E402' \
		src tests

# pylint: deeper static analysis.
# Suppress one rule on one line with:
#   some_code()  # pylint: disable=broad-except  # why
# Prefer that over "# pylint: disable-next=broad-except" on the previous
# line, so the reason sits next to the code. For a block, pair disable/enable:
#   # pylint: disable=broad-except
#   ...code...
#   # pylint: enable=broad-except
# Only add a rule to the --disable list below if it's wrong or noisy for
# the whole codebase, not just one call site.
c lint:
	PYTHONPATH=.:src pylint \
		--ignored-modules=PySide6 \
		--disable=missing-class-docstring,missing-function-docstring,missing-module-docstring,too-few-public-methods,duplicate-code,cyclic-import \
		src tests

# mypy: static type checker.
# Suppress one error on one line with:
#   some_code()  # type: ignore[attr-defined]  # why
# Always include the bracketed error code - a bare "# type: ignore" also
# hides unrelated type errors that show up on that line later.
# An untyped third-party import is the same idea:
#   import requests  # type: ignore[import-untyped]  # no stubs
d typecheck:
	mypy src tests

# bandit: security linter.
# Suppress one finding on one line with:
#   some_code()  # not a real secret, test fixture  # nosec B105
# Always name the specific test ID (e.g. B105). Put the reason BEFORE
# "# nosec", not after it - bandit treats extra words after nosec as test
# IDs. B101 (assert use) is already excluded globally below via -s B101.
e security:
	bandit -r src tests -s B101

# pytest: test runner.
# A failing test should be fixed, not silenced - there's no legitimate
# "suppress" for a real failure. If a test can't pass yet for a known
# reason, mark it explicitly instead of skipping quietly:
#   @pytest.mark.xfail(reason="waiting on upstream fix, see ISSUE-123")
# Noisy warnings from code you don't control (e.g. a dependency's
# DeprecationWarning) can be filtered narrowly with:
#   @pytest.mark.filterwarnings("ignore::DeprecationWarning")
# on the specific test, rather than a blanket filter for the whole suite.
f test:
	PYTHONPATH=.:src pytest


x: format tidy lint typecheck security test
