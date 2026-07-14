.PHONY: format tidy lint typecheck security test a b c d e f x


# ---------------------------------------------------------------------------
# When a tool below reports a problem, judge it first:
#   - If it's a real issue, fix the underlying code.
#   - If it's a false positive, or a deliberate pattern that isn't worth a
#     rewrite, suppress it - but as narrowly as possible (one rule, one
#     line) - and leave a short comment saying why.
#
# Don't reach for a broad disable (a whole rule turned off project-wide, or
# the whole tool skipped) when a single-line suppression would do. Each tool
# has its own syntax for this; see the comment above each target below.
# ---------------------------------------------------------------------------

# black: reformats code automatically, it doesn't really "complain" about
# choices you can disagree with. If one block genuinely needs to keep its
# manual layout (e.g. a hand-aligned table of numbers), wrap it in:
#   # fmt: off
#   ...code...
#   # fmt: on
# or append "# fmt: skip" to a single line. Use sparingly.
a format:
	black --line-length 100 src tests

# flake8: style/lint checker (pycodestyle + pyflakes).
# Suppress one warning on one line with:
#   some_code()  # noqa: E501
# Always name the specific code (E501, F401, ...). A bare "# noqa" silences
# every check on that line, including ones that show up later - avoid it.
# If a whole file should be exempt from a rule on purpose (e.g. an
# __init__.py that re-exports names), add it to per-file-ignores in the
# flake8 config instead of scattering noqa comments through the file.
b tidy:
	flake8 --max-line-length 100 src tests

# pylint: deeper static analysis.
# Suppress one rule on one line with:
#   some_code()  # pylint: disable=broad-except
# or on the line above with "# pylint: disable-next=broad-except".
# For a block, pair disable/enable:
#   # pylint: disable=broad-except
#   ...code...
#   # pylint: enable=broad-except
# Only add a rule to the --disable list below (or pylintrc/pyproject.toml)
# if it's wrong or noisy for the whole codebase, not just one call site.
c lint:
	PYTHONPATH=.:src pylint \
		--ignored-modules=PySide6 \
		--disable=missing-class-docstring,missing-function-docstring,missing-module-docstring,too-few-public-methods,duplicate-code,cyclic-import \
		src tests

# mypy: static type checker.
# Suppress one error on one line with:
#   some_code()  # type: ignore[attr-defined]
# Always include the bracketed error code - a bare "# type: ignore" also
# hides unrelated type errors that show up on that line later.
# If a whole module genuinely can't be typed yet (e.g. an untyped
# third-party dependency), exempt it via the ignore_errors/overrides section
# in the mypy config instead of ignoring line by line.
d typecheck:
	mypy src tests

# bandit: security linter.
# Suppress one finding on one line with:
#   some_code()  # nosec B105 -- not a real secret, this is a test fixture
# Always name the specific test ID (e.g. B105) and add a short reason so a
# reviewer can tell it was a deliberate call. B101 (assert use) is already
# excluded globally above via -s B101.
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
