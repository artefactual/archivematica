import pytest


@pytest.fixture
def migrate_apps(transactional_db):
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    def _migrate(target):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate([target])
        return executor.loader.project_state([target]).apps

    yield _migrate

    # Always restore the database schema to the latest migration state so
    # migration tests do not leak state into the rest of the suite.
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate(executor.loader.graph.leaf_nodes())
