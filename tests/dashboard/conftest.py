import pytest

from archivematica.dashboard.main.models import MetadataAppliesToType


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


@pytest.fixture
def metadata_applies_to_types(db):
    sip_type, _ = MetadataAppliesToType.objects.get_or_create(description="SIP")
    transfer_type, _ = MetadataAppliesToType.objects.get_or_create(
        description="Transfer"
    )
    file_type, _ = MetadataAppliesToType.objects.get_or_create(description="File")
    return {"sip": sip_type, "transfer": transfer_type, "file": file_type}
