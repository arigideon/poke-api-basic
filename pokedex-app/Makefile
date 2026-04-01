.PHONY: up down build logs restart shell-auth shell-backend shell-frontend

up: ## Start all services in detached mode
	docker compose up -d

down: ## Stop and remove all containers
	docker compose down

build: ## Rebuild all images
	docker compose build

logs: ## Tail logs from all services
	docker compose logs -f

restart: ## Restart all services
	docker compose restart

shell-auth: ## Open shell in auth-service container
	docker compose exec auth-service sh

shell-backend: ## Open shell in backend container
	docker compose exec backend sh

shell-frontend: ## Open shell in frontend container
	docker compose exec frontend sh

setup: ## First-time setup: copy env file
	cp .env.example .env
	@echo "Edit .env with your values, then run: make build && make up"

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
