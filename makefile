# Anime Roast Generator - Makefile
# Usage: make <command>
# Example: make prod-deploy

# =============================================================================
# Variables
# =============================================================================
COMPOSE_DEV = docker-compose.yml
COMPOSE_PROD = docker-compose.prod.yml
BACKEND_SERVICE = backend
FRONTEND_SERVICE = frontend
REDIS_SERVICE = redis
CADDY_SERVICE = caddy

# =============================================================================
# Development Commands
# =============================================================================

.PHONY: dev-up
dev-up: ## Start development environment
	docker-compose -f $(COMPOSE_DEV) up -d --build

.PHONY: dev-down
dev-down: ## Stop development environment
	docker-compose -f $(COMPOSE_DEV) down

.PHONY: dev-logs
dev-logs: ## View development logs
	docker-compose -f $(COMPOSE_DEV) logs -f

.PHONY: dev-backend-logs
dev-backend-logs: ## View backend logs only
	docker-compose -f $(COMPOSE_DEV) logs -f $(BACKEND_SERVICE)

.PHONY: dev-restart
dev-restart: ## Restart development services
	docker-compose -f $(COMPOSE_DEV) restart

# =============================================================================
# Production Commands
# =============================================================================

.PHONY: prod-deploy
prod-deploy: ## Full production deployment (backup, pull, build, deploy)
	@echo "🚀 Starting production deployment..."
	@make pre-deploy-backup
	git pull origin main
	make prod-build
	make prod-up
	@echo "✅ Production deployment complete!"
	@echo "🌐 Check your domain to verify it's working"

.PHONY: prod-up
prod-up: ## Start production services
	docker-compose -f $(COMPOSE_PROD) up -d

.PHONY: prod-down
prod-down: ## Stop production services
	docker-compose -f $(COMPOSE_PROD) down

.PHONY: prod-build
prod-build: ## Build production images (uses cache)
	docker-compose -f $(COMPOSE_PROD) build

.PHONY: prod-build-no-cache
prod-build-no-cache: ## Build production images (no cache, fresh build)
	docker-compose -f $(COMPOSE_PROD) build --no-cache

.PHONY: prod-rebuild
prod-rebuild: prod-build-no-cache prod-up ## Full rebuild and restart (no cache)

.PHONY: prod-update
prod-update: ## Quick update - pull latest and restart with build
	git pull origin main
	docker-compose -f $(COMPOSE_PROD) up -d --build

# =============================================================================
# Service-Specific Production Commands
# =============================================================================

.PHONY: prod-backend-rebuild
prod-backend-rebuild: ## Rebuild only backend service
	docker-compose -f $(COMPOSE_PROD) build --no-cache $(BACKEND_SERVICE)
	docker-compose -f $(COMPOSE_PROD) up -d $(BACKEND_SERVICE)

.PHONY: prod-frontend-rebuild
prod-frontend-rebuild: ## Rebuild only frontend service
	docker-compose -f $(COMPOSE_PROD) build --no-cache $(FRONTEND_SERVICE)
	docker-compose -f $(COMPOSE_PROD) up -d $(FRONTEND_SERVICE)

.PHONY: prod-redis-restart
prod-redis-restart: ## Restart Redis service
	docker-compose -f $(COMPOSE_PROD) restart $(REDIS_SERVICE)

.PHONY: prod-caddy-restart
prod-caddy-restart: ## Restart Caddy (useful for SSL/cert issues)
	docker-compose -f $(COMPOSE_PROD) restart $(CADDY_SERVICE)

# =============================================================================
# Log Commands
# =============================================================================

.PHONY: logs
logs: ## View all production logs
	docker-compose -f $(COMPOSE_PROD) logs -f

.PHONY: logs-backend
logs-backend: ## View backend logs
	docker-compose -f $(COMPOSE_PROD) logs -f $(BACKEND_SERVICE)

.PHONY: logs-frontend
logs-frontend: ## View frontend logs
	docker-compose -f $(COMPOSE_PROD) logs -f $(FRONTEND_SERVICE)

.PHONY: logs-redis
logs-redis: ## View Redis logs
	docker-compose -f $(COMPOSE_PROD) logs -f $(REDIS_SERVICE)

.PHONY: logs-caddy
logs-caddy: ## View Caddy logs
	docker-compose -f $(COMPOSE_PROD) logs -f $(CADDY_SERVICE)

.PHONY: logs-tail
logs-tail: ## View last 100 lines of all logs
	docker-compose -f $(COMPOSE_PROD) logs --tail=100

.PHONY: logs-error
logs-error: ## View error logs only
	docker-compose -f $(COMPOSE_PROD) logs -f | grep -i error

# =============================================================================
# Monitoring & Health Commands
# =============================================================================

.PHONY: status
status: ## Check container status
	docker-compose -f $(COMPOSE_PROD) ps

.PHONY: health
health: ## Check health of all services
	@echo "🔍 Checking service health..."
	@docker-compose -f $(COMPOSE_PROD) ps
	@echo ""
	@echo "🩺 Health check endpoints:"
	@curl -s http://localhost:8000/health || echo "❌ Backend health check failed"

.PHONY: stats
stats: ## Show resource usage statistics
	docker stats --no-stream

.PHONY: top
show-top: ## Show running processes in containers
	docker-compose -f $(COMPOSE_PROD) top

# =============================================================================
# Maintenance Commands
# =============================================================================

.PHONY: clean
clean: ## Clean up unused Docker resources (dangling images, volumes)
	@echo "🧹 Cleaning up Docker resources..."
	docker system prune -f
	docker volume prune -f
	@echo "✅ Cleanup complete"

.PHONY: clean-all
clean-all: ## WARNING: Remove all containers, images, and volumes for this project
	@echo "⚠️  WARNING: This will remove all containers, images, and volumes!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose -f $(COMPOSE_PROD) down -v --rmi all; \
		docker system prune -f; \
		echo "✅ All resources cleaned"; \
	else \
		echo "❌ Cancelled"; \
	fi

.PHONY: redis-flush
redis-flush: ## Flush all Redis data (clears rate limiting cache)
	@echo "🔄 Flushing Redis cache..."
	@docker-compose -f $(COMPOSE_PROD) exec $(REDIS_SERVICE) redis-cli FLUSHALL
	@echo "✅ Redis cache flushed"

.PHONY: redis-info
redis-info: ## Show Redis info
	@docker-compose -f $(COMPOSE_PROD) exec $(REDIS_SERVICE) redis-cli INFO

.PHONY: backup
backup: ## Create backup of Redis data (if persisted) - DEPRECATED: use backup-all
	@echo "⚠️  This command is deprecated. Use 'make backup-all' instead."
	@make backup-all

# =============================================================================
# SQLite Backup & Restore Commands
# =============================================================================

BACKUP_DIR := backups
SQLITE_DB := /app/data/comments.db
MAX_BACKUPS := 30

.PHONY: backup-sqlite
backup-sqlite: ## Create backup of SQLite database (comments)
	@echo "💾 Creating SQLite backup..."
	@mkdir -p $(BACKUP_DIR)
	@BACKUP_FILE="$(BACKUP_DIR)/comments_$$(date +%Y%m%d_%H%M%S).db.gz"; \
	docker-compose -f $(COMPOSE_PROD) exec -T $(BACKEND_SERVICE) sh -c 'sqlite3 $(SQLITE_DB) ".backup /tmp/comments_backup.db" && cat /tmp/comments_backup.db' | gzip > $$BACKUP_FILE; \
	if [ $$? -eq 0 ]; then \
		echo "✅ Backup created: $$BACKUP_FILE"; \
		ls -lh $$BACKUP_FILE; \
	else \
		echo "❌ Backup failed"; \
		exit 1; \
	fi
	@make backup-rotate

.PHONY: backup-sqlite-hot
backup-sqlite-hot: ## Create hot backup of SQLite (while running, uses WAL checkpoint)
	@echo "💾 Creating hot SQLite backup..."
	@mkdir -p $(BACKUP_DIR)
	@BACKUP_FILE="$(BACKUP_DIR)/comments_hot_$$(date +%Y%m%d_%H%M%S).db.gz"; \
	docker-compose -f $(COMPOSE_PROD) exec -T $(BACKEND_SERVICE) sh -c 'sqlite3 $(SQLITE_DB) "PRAGMA wal_checkpoint(TRUNCATE);" && sqlite3 $(SQLITE_DB) ".backup /tmp/comments_backup.db" && cat /tmp/comments_backup.db' | gzip > $$BACKUP_FILE; \
	if [ $$? -eq 0 ]; then \
		echo "✅ Hot backup created: $$BACKUP_FILE"; \
		ls -lh $$BACKUP_FILE; \
	else \
		echo "❌ Hot backup failed"; \
		exit 1; \
	fi
	@make backup-rotate

.PHONY: backup-redis
backup-redis: ## Create backup of Redis data
	@echo "💾 Creating Redis backup..."
	@mkdir -p $(BACKUP_DIR)
	@docker-compose -f $(COMPOSE_PROD) exec $(REDIS_SERVICE) redis-cli BGSAVE
	@sleep 2
	@docker run --rm -v anime-roast-generator_redis_data:/data -v $(PWD)/$(BACKUP_DIR):/backup alpine tar czf /backup/redis_$$(date +%Y%m%d_%H%M%S).tar.gz -C /data . 2>/dev/null
	@echo "✅ Redis backup created"

.PHONY: backup-all
backup-all: backup-sqlite backup-redis ## Create backups of both SQLite and Redis
	@echo "✅ All backups completed"

.PHONY: backup-list
backup-list: ## List all available backups
	@echo "📋 Available backups:"
	@echo ""
	@echo "SQLite Backups:"
	@if [ -d $(BACKUP_DIR) ] && [ "$$(ls -A $(BACKUP_DIR)/comments_*.db.gz 2>/dev/null)" ]; then \
		ls -lh $(BACKUP_DIR)/comments_*.db.gz 2>/dev/null | awk '{printf "  %-20s %s\n", $$9, $$5}'; \
	else \
		echo "  (none)"; \
	fi
	@echo ""
	@echo "Redis Backups:"
	@if [ -d $(BACKUP_DIR) ] && [ "$$(ls -A $(BACKUP_DIR)/redis_*.tar.gz 2>/dev/null)" ]; then \
		ls -lh $(BACKUP_DIR)/redis_*.tar.gz 2>/dev/null | awk '{printf "  %-20s %s\n", $$9, $$5}'; \
	else \
		echo "  (none)"; \
	fi

.PHONY: backup-rotate
backup-rotate: ## Remove old backups (keeps last $(MAX_BACKUPS))
	@echo "🔄 Rotating backups (keeping last $(MAX_BACKUPS))..."
	@ls -t $(BACKUP_DIR)/comments_*.db.gz 2>/dev/null | tail -n +$$(( $(MAX_BACKUPS) + 1 )) | xargs -r rm -f
	@ls -t $(BACKUP_DIR)/redis_*.tar.gz 2>/dev/null | tail -n +$$(( $(MAX_BACKUPS) + 1 )) | xargs -r rm -f
	@echo "✅ Old backups cleaned up"

.PHONY: restore-sqlite
restore-sqlite: ## Restore SQLite from backup (interactive)
	@echo "📋 Available SQLite backups:"
	@ls -1t $(BACKUP_DIR)/comments_*.db.gz 2>/dev/null | head -10 | nl
	@echo ""
	@read -p "Enter number of backup to restore (or 'c' to cancel): " choice; \
	if [ "$$choice" = "c" ] || [ "$$choice" = "C" ]; then \
		echo "❌ Restore cancelled"; \
		exit 0; \
	fi; \
	BACKUP_FILE=$$(ls -1t $(BACKUP_DIR)/comments_*.db.gz 2>/dev/null | sed -n "$${choice}p"); \
	if [ -z "$$BACKUP_FILE" ]; then \
		echo "❌ Invalid selection"; \
		exit 1; \
	fi; \
	echo "⚠️  WARNING: This will replace the current database!"; \
	read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "🔄 Stopping backend service..."; \
		docker-compose -f $(COMPOSE_PROD) stop $(BACKEND_SERVICE); \
		echo "🔄 Restoring from $$BACKUP_FILE..."; \
		zcat $$BACKUP_FILE | docker-compose -f $(COMPOSE_PROD) exec -T $(BACKEND_SERVICE) sh -c 'cat > $(SQLITE_DB).tmp && mv $(SQLITE_DB).tmp $(SQLITE_DB)'; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Database restored successfully"; \
		else \
			echo "❌ Restore failed"; \
		fi; \
		echo "🔄 Starting backend service..."; \
		docker-compose -f $(COMPOSE_PROD) start $(BACKEND_SERVICE); \
	else \
		echo "❌ Restore cancelled"; \
	fi

.PHONY: restore-redis
restore-redis: ## Restore Redis from backup (interactive)
	@echo "📋 Available Redis backups:"
	@ls -1t $(BACKUP_DIR)/redis_*.tar.gz 2>/dev/null | head -10 | nl
	@echo ""
	@read -p "Enter number of backup to restore (or 'c' to cancel): " choice; \
	if [ "$$choice" = "c" ] || [ "$$choice" = "C" ]; then \
		echo "❌ Restore cancelled"; \
		exit 0; \
	fi; \
	BACKUP_FILE=$$(ls -1t $(BACKUP_DIR)/redis_*.tar.gz 2>/dev/null | sed -n "$${choice}p"); \
	if [ -z "$$BACKUP_FILE" ]; then \
		echo "❌ Invalid selection"; \
		exit 1; \
	fi; \
	echo "⚠️  WARNING: This will replace the current Redis data!"; \
	read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "🔄 Stopping Redis service..."; \
		docker-compose -f $(COMPOSE_PROD) stop $(REDIS_SERVICE); \
		echo "🔄 Restoring from $$BACKUP_FILE..."; \
		docker run --rm -v anime-roast-generator_redis_data:/data -v $(PWD)/$$BACKUP_FILE:/backup.tar.gz alpine sh -c 'rm -rf /data/* && tar xzf /backup.tar.gz -C /data'; \
		if [ $$? -eq 0 ]; then \
			echo "✅ Redis data restored successfully"; \
		else \
			echo "❌ Restore failed"; \
		fi; \
		echo "🔄 Starting Redis service..."; \
		docker-compose -f $(COMPOSE_PROD) start $(REDIS_SERVICE); \
	else \
		echo "❌ Restore cancelled"; \
	fi

.PHONY: backup-verify
backup-verify: ## Verify integrity of latest SQLite backup
	@echo "🔍 Verifying latest SQLite backup..."
	@LATEST_BACKUP=$$(ls -t $(BACKUP_DIR)/comments_*.db.gz 2>/dev/null | head -1); \
	if [ -z "$$LATEST_BACKUP" ]; then \
		echo "❌ No backups found"; \
		exit 1; \
	fi; \
	echo "Checking: $$LATEST_BACKUP"; \
	zcat $$LATEST_BACKUP | docker run --rm -i alpine sh -c 'cat > /tmp/test.db && sqlite3 /tmp/test.db "PRAGMA integrity_check;"' | grep -q "ok"; \
	if [ $$? -eq 0 ]; then \
		echo "✅ Backup integrity verified"; \
	else \
		echo "❌ Backup integrity check failed"; \
		exit 1; \
	fi

# =============================================================================
# Pre-deployment Backup Hook
# =============================================================================

.PHONY: pre-deploy-backup
pre-deploy-backup: ## Create backup before deployment (called automatically by prod-deploy)
	@echo "💾 Creating pre-deployment backup..."
	@mkdir -p $(BACKUP_DIR)
	@BACKUP_FILE="$(BACKUP_DIR)/comments_pre_deploy_$$(date +%Y%m%d_%H%M%S).db.gz"; \
	docker-compose -f $(COMPOSE_PROD) exec -T $(BACKEND_SERVICE) sh -c 'sqlite3 $(SQLITE_DB) ".backup /tmp/comments_backup.db" && cat /tmp/comments_backup.db' | gzip > $$BACKUP_FILE; \
	if [ $$? -eq 0 ]; then \
		echo "✅ Pre-deployment backup created: $$BACKUP_FILE"; \
	else \
		echo "⚠️  Pre-deployment backup failed, but continuing with deployment..."; \
	fi
	@make backup-rotate

# =============================================================================
# SSL/Certificate Commands
# =============================================================================

.PHONY: ssl-renew
ssl-renew: ## Force SSL certificate renewal (Caddy)
	@echo "🔒 Forcing SSL certificate renewal..."
	@docker-compose -f $(COMPOSE_PROD) exec $(CADDY_SERVICE) caddy reload --config /etc/caddy/Caddyfile
	@echo "✅ Caddy configuration reloaded"

.PHONY: ssl-status
ssl-status: ## Check SSL certificate status
	@echo "📜 SSL Certificate Status:"
	@docker-compose -f $(COMPOSE_PROD) exec $(CADDY_SERVICE) caddy list-modules | grep -i tls || echo "Caddy TLS module info"

# =============================================================================
# Development Utilities
# =============================================================================

.PHONY: shell-backend
shell-backend: ## Open shell in backend container
	docker-compose -f $(COMPOSE_PROD) exec $(BACKEND_SERVICE) /bin/sh

.PHONY: shell-redis
shell-redis: ## Open Redis CLI
	docker-compose -f $(COMPOSE_PROD) exec $(REDIS_SERVICE) redis-cli

.PHONY: test-api
test-api: ## Test API endpoints
	@echo "🧪 Testing API endpoints..."
	@echo "Health check:"
	@curl -s http://localhost:8000/health | jq . || echo "Health check failed"
	@echo ""
	@echo "Search test:"
	@curl -s "http://localhost:8000/api/search-anime?q=Naruto" | jq '.results | length' || echo "Search failed"
	@echo ""
	@echo "✅ API tests complete"

.PHONY: env-check
env-check: ## Check environment variables
	@echo "🔧 Checking environment configuration..."
	@test -f .env && echo "✅ .env file exists" || echo "❌ .env file missing"
	@test -f .env.prod && echo "✅ .env.prod file exists" || echo "⚠️  .env.prod file missing (for production)"
	@echo ""
	@echo "Docker Compose version:"
	@docker-compose version
	@echo ""
	@echo "Docker version:"
	@docker version --format '{{.Server.Version}}'

# =============================================================================
# Help
# =============================================================================

.PHONY: help
help: ## Show this help message
	@echo "🎌 Anime Roast Generator - Makefile Commands"
	@echo ""
	@echo "Production Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep "prod-" | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Development Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep "dev-" | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Log Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep "logs" | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Maintenance Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(clean|backup|redis|restore)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick Start:"
	@echo "  make prod-deploy          # Full production deployment"
	@echo "  make logs-backend         # Watch backend logs"
	@echo "  make test-api             # Test API endpoints"
	@echo ""

.DEFAULT_GOAL := help
