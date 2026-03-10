.PHONY: install test clean docs

install:
	poetry install

test:
	poetry run pytest tests/

test-unit:
	poetry run pytest tests/unit

test-integration:
	poetry run pytest tests/integration

test-contract:
	poetry run python scripts/validate_contracts.py

benchmark:
	poetry run python scripts/benchmark.py

docs:
	poetry run python scripts/generate_docs.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache

doctor:
	poetry run python scripts/doctor.py

quickstart:
	./scripts/quickstart.sh