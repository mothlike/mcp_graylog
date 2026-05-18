.PHONY: help install dev-install test lint typecheck check clean build start docker-build docker-run docker-stop docker-logs docker-compose-up docker-compose-down docker-compose-logs

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install the package in development mode
	./venv/bin/python -m pip install -e .

dev-install: ## Install development dependencies
	./venv/bin/python -m pip install -e ".[dev]"

test: ## Run tests
	./venv/bin/python -m pytest -q

lint: ## Run ruff linting
	./venv/bin/python -m ruff check .

typecheck: ## Run mypy on package code
	./venv/bin/python -m mypy mcp_graylog

check: lint typecheck test ## Run lint, typecheck, and tests

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	./venv/bin/python -m build

start: ## Start the MCP server with stdio transport
	./start.sh

docker-build: ## Build Docker image
	docker build -t mcp-graylog .

docker-run: ## Run Docker container in explicit streamable HTTP mode
	docker run -d \
		--name mcp-graylog \
		-p 8000:8000 \
		-e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \
		-e GRAYLOG_TOKEN=your-graylog-token \
		mcp-graylog

docker-stop: ## Stop Docker container
	docker stop mcp-graylog || true
	docker rm mcp-graylog || true

docker-logs: ## Show Docker container logs
	docker logs mcp-graylog

docker-compose-up: ## Start services with docker compose
	docker compose up -d

docker-compose-down: ## Stop services with docker compose
	docker compose down

docker-compose-logs: ## Show docker compose logs
	docker compose logs -f
