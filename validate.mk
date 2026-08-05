.PHONY: format tidy lint typecheck security test a b c d e f x


a format:
	black --line-length 100 src tests

b tidy:
	flake8 --max-line-length 100 src tests

c lint:
	PYTHONPATH=.:src pylint \
		--ignored-modules=PySide6 \
		--disable=missing-class-docstring,missing-function-docstring,missing-module-docstring,too-few-public-methods,duplicate-code,cyclic-import \
		src tests

d typecheck:
	mypy src tests

e security:
	bandit -r src tests -s B101

f test:
	PYTHONPATH=.:src pytest


x: format tidy lint typecheck security test
