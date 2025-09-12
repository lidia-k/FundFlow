.PHONY: help dev build test lint clean setup

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development
dev: ## Start development environment with Docker
	docker-compose up --build

dev-local: ## Start development environment locally (requires setup)
	concurrently "npm run dev:backend" "npm run dev:frontend"

# Setup
setup: ## Set up the development environment
	@echo "Setting up FundFlow development environment..."
	npm install
	npm run setup
	@echo "✅ Setup complete! Run 'make dev' to start developing"

setup-hooks: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install

# Building
build: ## Build the application
	npm run build

# Testing
test: ## Run all tests
	npm run test

test-backend: ## Run backend tests only
	npm run test:backend

test-frontend: ## Run frontend tests only
	npm run test:frontend

# Linting and formatting
lint: ## Run linters
	npm run lint

lint-fix: ## Fix linting issues
	npm run lint:fix

type-check: ## Check TypeScript types
	npm run type-check

# Database
db-migrate: ## Run database migrations
	npm run migration:upgrade

db-seed: ## Seed the database with sample data
	npm run db:seed

# Docker
docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start Docker containers in background
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

# Cleanup
clean: ## Clean up Docker containers and images
	npm run clean

# Utilities
logs: ## View application logs
	tail -f logs/*.log

check: ## Run all checks (lint, type-check, test)
	make lint
	make type-check
	make test