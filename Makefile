.PHONY: help install test lint format clean build docker-build docker-run start test-entrypoint install-deps

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install the package in development mode
	pip install -e .

test: ## Run tests
	pytest tests/ -v

lint: ## Run linting checks
	black --check .
	isort --check-only .
	mypy .

format: ## Format code
	black .
	isort .

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	python -m build

docker-build: ## Build Docker image
	docker build -t mcp-graylog .

docker-run: ## Run Docker container
	docker run -d \
		--name mcp-graylog \
		-p 8000:8000 \
		-e GRAYLOG_ENDPOINT=https://your-graylog-server:9000 \
		-e GRAYLOG_USERNAME=your-username \
		-e GRAYLOG_PASSWORD=your-password \
		mcp-graylog

docker-stop: ## Stop Docker container
	docker stop mcp-graylog || true
	docker rm mcp-graylog || true

docker-logs: ## Show Docker container logs
	docker logs mcp-graylog

dev-install: ## Install development dependencies
	pip install -e ".[dev]"

check: format lint test ## Run all checks (format, lint, test)

publish: ## Publish to PyPI (requires twine)
	python -m build
	twine upload dist/*

start: ## Start the server using the startup script
	./start.sh

test-entrypoint: ## Test the entrypoint configuration
	./test_entrypoint.sh

test-pydantic: ## Test the Pydantic fix
	python3 test_pydantic_fix.py

test-fixes: ## Test the Pydantic and FastMCP fixes
	python3 test_fixes.py

install-deps: ## Install dependencies using the installation script
	./install_deps.sh

docker-compose-up: ## Start services with docker-compose
	docker-compose up -d

docker-compose-down: ## Stop services with docker-compose
	docker-compose down

docker-compose-logs: ## Show docker-compose logs
	docker-compose logs -f 