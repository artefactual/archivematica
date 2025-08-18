.PHONY: pip-compile
pip-compile:  # Compile pip requirements
	pip-compile --allow-unsafe --output-file requirements.txt pyproject.toml
	pip-compile --allow-unsafe --extra dev --output-file requirements-dev.txt pyproject.toml

.PHONY: pip-upgrade
pip-upgrade:  # Upgrade pip requirements
	pip-compile --allow-unsafe --upgrade --output-file requirements.txt pyproject.toml
	pip-compile --allow-unsafe --upgrade --extra dev --output-file requirements-dev.txt pyproject.toml

.PHONY: pip-sync
pip-sync:  # Sync virtualenv
	pip-sync requirements.txt

.PHONY: pip-sync-dev
pip-sync-dev:  # Sync dev virtualenv
	pip-sync requirements-dev.txt
