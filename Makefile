UV ?= uv

.PHONY: lock
lock:  # Update the lockfile without upgrading locked dependencies
	$(UV) lock

.PHONY: lock-check
lock-check:  # Verify that the lockfile is up to date
	$(UV) lock --check

.PHONY: upgrade
upgrade:  # Upgrade all locked dependencies
	$(UV) lock --upgrade

.PHONY: sync
sync:  # Sync the project and development dependencies
	$(UV) sync --locked

.PHONY: sync-runtime
sync-runtime:  # Sync only the project and runtime dependencies
	$(UV) sync --locked --no-dev

.PHONY: lint
lint:  # Run all pre-commit checks through Compose
	$(MAKE) -C hack test-linting

.PHONY: check
check: lock-check lint  # Verify the lockfile and run all checks
