.PHONY: help db-start db-stop db-reset db-status migrate runserver login build-image tag-image push-image

IMAGE_NAME    := cardio-trace-backend-api
IMAGE_TAG     := $(or $(IMAGE_TAG),dev)
VOLUME        := cardio-trace-pgdata
COMPOSE_FILE  := docker-compose.dev.yml
DB_SERVICE    := db
AWS_ACCOUNT_ID := 719030484884
AWS_REGION := eu-north-1

.DEFAULT_GOAL := help

-include .env
export

help: ## Show available targets
	@echo "Targets:"
	@grep -E '^[a-zA-Z0-9_.-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  %-22s %s\n", $$1, $$2}'
	@echo ""

login: ## Login to ECR for Docker image push/pull
	@echo "Initiating ECR login..."
	aws ecr get-login-password --region $(AWS_REGION) \
		| docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

db-start: ## Start PostgreSQL via docker compose
	@docker compose -f $(COMPOSE_FILE) up -d $(DB_SERVICE)

db-stop: ## Stop PostgreSQL container
	@docker compose -f $(COMPOSE_FILE) stop $(DB_SERVICE)

db-reset: ## Remove PostgreSQL volume (destroys all data)
	@docker compose -f $(COMPOSE_FILE) stop $(DB_SERVICE) >/dev/null 2>&1 || true
	@docker volume rm $(VOLUME) 2>/dev/null && \
		echo "Volume $(VOLUME) removed" || \
		echo "Volume $(VOLUME) does not exist"

db-status: ## Show PostgreSQL container status
	@docker compose -f $(COMPOSE_FILE) ps $(DB_SERVICE)

migrate: ## Run Django migrations
	uv run python manage.py migrate

runserver: ## Start Django development server
	uv run python manage.py runserver

build-image: ## Build backend API Docker image
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

tag-image: ## Tag backend API Docker image for ECR
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(IMAGE_NAME):$(IMAGE_TAG)

push-image: ## Push backend API Docker image to ECR
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/$(IMAGE_NAME):$(IMAGE_TAG)