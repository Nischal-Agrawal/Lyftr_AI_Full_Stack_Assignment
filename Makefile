# ==========================================
# Makefile for Lyftr AI Full-Stack Chatbot
# ==========================================

.PHONY: up down logs test verify help

help:
	@echo "Usage:"
	@echo "  make up       - Build and run the entire stack via Docker Compose"
	@echo "  make down     - Stop and remove containers and networks"
	@echo "  make logs     - View and tail container logs"
	@echo "  make test     - Run backend pytest suite and frontend typecheck"
	@echo "  make verify   - Run automated live contract verification against backend"

up:
	@echo "Starting full stack with Docker Compose..."
	docker compose up --build -d
	@echo "Backend listening on:  http://localhost:8000"
	@echo "Frontend listening on: http://localhost:3000"
	@echo "Health check endpoint: http://localhost:8000/health"

down:
	@echo "Stopping Docker Compose containers..."
	docker compose down

logs:
	docker compose logs -f

test:
	@echo "Running backend pytest..."
	pytest backend/tests -v
	@echo "Running frontend typecheck & build..."
	cd frontend && npm run build

verify:
	@echo "Running live contract verification script..."
	python scripts/verify_contract.py --base-url http://localhost:8000
