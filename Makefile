.PHONY: pip-compile
pip-compile:  # Compile pip requirements
	pip-compile --allow-unsafe --output-file requirements.txt requirements.in
	pip-compile --allow-unsafe --output-file requirements-dev.txt requirements-dev.in

.PHONY: pip-compile-py3
pip-compile-py3:  # Compile pip requirements (Python 3)
	pip-compile --allow-unsafe --output-file requirements-py3.txt requirements.in
	pip-compile --allow-unsafe --output-file requirements-dev-py3.txt requirements-dev-py3.in

.PHONY: pip-upgrade
pip-upgrade:  # Upgrade pip requirements
	pip-compile --allow-unsafe --upgrade --output-file requirements.txt requirements.in
	pip-compile --allow-unsafe --upgrade --output-file requirements-dev.txt requirements-dev.in

.PHONY: pip-upgrade-py3
pip-upgrade-py3:  # Upgrade pip requirements
	pip-compile --allow-unsafe --upgrade --output-file requirements-py3.txt requirements.in
	pip-compile --allow-unsafe --upgrade --output-file requirements-dev-py3.txt requirements-dev-py3.in

.PHONY: pip-sync
pip-sync:  # Sync virtualenv
	pip-sync requirements.txt

.PHONY: pip-sync-dev
pip-sync-dev:  # Sync dev virtualenv
	pip-sync requirements-dev.txt
