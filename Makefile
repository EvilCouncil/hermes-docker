IMAGE   := hermes-docker
TAG     := local

.DEFAULT_GOAL := help

.PHONY: help
help: ## 📖 Show this help
	@echo "🐳 hermes-docker — dev tasks"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: build
build: ## 🔨 Build the image locally
	docker build -t $(IMAGE):$(TAG) .

.PHONY: shell
shell: ## 🐚 Shell into the running hermes-agent container
	docker exec -it hermes-agent bash

.PHONY: test
test: ## 🧪 Run the version-bump script's unit tests
	pytest test_update_versions.py

.PHONY: update-versions
update-versions: ## ⬆️  Check Docker Hub + npm for newer versions → rewrite Dockerfile + VERSION
	python3 update_versions.py

.PHONY: clean
clean: ## 🧹 Remove local image and Python cache
	docker rmi $(IMAGE):$(TAG) 2>/dev/null || true
	rm -rf __pycache__ .pytest_cache

.PHONY: check-build
check-build: ## 🔍 Check GHCR tag + CI build status (TAG=v0.23.1 to check a specific tag)
	python3 check_build.py $(if $(filter-out local,$(TAG)),$(TAG))
