.PHONY: format tidy lint typecheck security test a b c d e f x closing install


a format:
	black --line-length 100 src tests

b tidy:
	flake8 --max-line-length 100 src tests

c lint:
	pylint --disable=missing-class-docstring,missing-function-docstring,missing-module-docstring,too-few-public-methods src tests

d typecheck:
	mypy src tests

e security:
	bandit -r src tests

f test:
	pytest


x: format tidy lint typecheck security test


closing:
	pip freeze > requirements.txt

install:
	pip install -r requirements.txt
	playwright install
