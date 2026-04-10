.PHONY: db-start db-stop db-reset db-status migrate runserver

CONTAINER   := cardio-trace-pg
VOLUME      := cardio-trace-pgdata
PG_IMAGE    := postgres:17
DB_NAME     := $(or $(DB_NAME),cardio_trace)
DB_USER     := $(or $(DB_USER),postgres)
DB_PASSWORD := $(or $(DB_PASSWORD),postgres)
DB_PORT     := $(or $(DB_PORT),5432)

-include .env
export

db-start: ## Start PostgreSQL in Docker
	@if docker ps --format '{{.Names}}' | grep -q '^$(CONTAINER)$$'; then \
		echo "$(CONTAINER) is already running"; \
	else \
		docker run -d --rm \
			--name $(CONTAINER) \
			-v $(VOLUME):/var/lib/postgresql/data \
			-e POSTGRES_DB=$(DB_NAME) \
			-e POSTGRES_USER=$(DB_USER) \
			-e POSTGRES_PASSWORD=$(DB_PASSWORD) \
			-p $(DB_PORT):5432 \
			$(PG_IMAGE) && \
		echo "$(CONTAINER) started on port $(DB_PORT)"; \
	fi

db-stop: ## Stop PostgreSQL container
	@docker stop $(CONTAINER) 2>/dev/null && \
		echo "$(CONTAINER) stopped" || \
		echo "$(CONTAINER) is not running"

db-reset: ## Remove PostgreSQL volume (destroys all data)
	@docker stop $(CONTAINER) 2>/dev/null || true
	@docker volume rm $(VOLUME) 2>/dev/null && \
		echo "Volume $(VOLUME) removed" || \
		echo "Volume $(VOLUME) does not exist"

db-status: ## Show container status
	@docker ps --filter name=$(CONTAINER) --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

migrate: ## Run Django migrations
	uv run python manage.py migrate

runserver: ## Start Django development server
	uv run python manage.py runserver
