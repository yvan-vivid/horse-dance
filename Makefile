.PHONY: all check test clean

all: check test

check: | .venv
	poetry run mypy src

test: | .venv
	poetry run pytest --cov=src --cov-report term-missing

.venv:
	poetry install

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	rm -rf .coverage .mypy_cache .pytest_cache .venv
