# service-clients/idp-client/Makefile
#
# Quick reference:
#   make install        Install runtime + dev deps via uv.
#   make format         Auto-format with ruff (excludes _generated/).
#   make lint           ruff format then ruff check --fix.
#   make typecheck      mypy --strict on src/idp_client/.
#   make test           pytest -m unit (default).
#   make coverage       pytest with coverage report.
#   make regen          Regenerate src/idp_client/_generated/ from openapi/openapi.json.
#   make regen-spec     Pull openapi.json from a running api-lib.

# Pin uv to 3.12 to match api-lib's interpreter.
export UV_PYTHON := 3.12

OPENAPI_SNAPSHOT := openapi/openapi.json
OPENAPI_CONFIG   := openapi-config.yaml
GENERATED_DIR    := src/idp_client/_generated
IDP_OPENAPI_URL  ?= http://localhost:8000/openapi.json

.PHONY: install format format-check lint lint-check typecheck test test-live coverage regen regen-spec clean

install:
	uv sync

format:
	uv run ruff format src/ tests/

format-check:
	uv run ruff format --check src/ tests/

lint: format
	uv run ruff check --fix src/ tests/

lint-check:
	uv run ruff check src/ tests/

typecheck:
	uv run mypy

test:
	uv run pytest

test-live:
	uv run pytest -m live

coverage:
	uv run pytest --cov=src/idp_client --cov-report=term-missing

# openapi-python-client refuses to run with a populated --output-path unless we
# remove it first. The generator writes a self-contained tree.
regen:
	rm -rf $(GENERATED_DIR)
	uv run openapi-python-client generate \
		--path $(OPENAPI_SNAPSHOT) \
		--config $(OPENAPI_CONFIG) \
		--output-path $(GENERATED_DIR) \
		--meta none \
		--overwrite

regen-spec:
	curl -fsSL $(IDP_OPENAPI_URL) -o $(OPENAPI_SNAPSHOT)
	@echo "Wrote $(OPENAPI_SNAPSHOT) from $(IDP_OPENAPI_URL). Run 'make regen' to refresh _generated/."

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
