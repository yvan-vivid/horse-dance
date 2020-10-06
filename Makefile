.PHONY: all check test

all: check test clean

check:
	poetry run mypy src

test:
	poetry run pytest --cov=src --cov-report term-missing

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	rm -rf .coverage .mypy_cache .pytest_cache .venv
