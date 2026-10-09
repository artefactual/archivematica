from collections.abc import Iterator
from unittest import mock

import pytest

from archivematica.search.service import SearchService


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
def mock_search_service() -> Iterator[mock.Mock]:
    """The search service as set up by the views and commands that use it."""
    service = mock.Mock(spec=SearchService)
    with (
        mock.patch(
            "archivematica.dashboard.components.archival_storage.views.setup_search_service_from_conf",
            return_value=service,
        ),
        mock.patch(
            "archivematica.dashboard.main.management.commands.purge_transient_processing_data.setup_search_service_from_conf",
            return_value=service,
        ),
    ):
        yield service


@pytest.fixture
def mets_hdr() -> str:
    """A METS document with a header only, as streamed from the Storage Service."""
    return """<?xml version='1.0' encoding='UTF-8'?>
    <mets:mets xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/version1121/mets.xsd">
        <mets:metsHdr CREATEDATE="2020-01-20T15:22:15"/>
    </mets:mets>
    """
