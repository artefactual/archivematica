from collections.abc import Callable
from collections.abc import Iterator
from unittest import mock

import pytest
from django.db.migrations.state import StateApps

from archivematica.search.service import SearchService


@pytest.fixture
def migrate_apps(
    request: pytest.FixtureRequest,
) -> Iterator[Callable[[tuple[str, str]], StateApps]]:
    """Migrate the database to a target and back to the latest migration after
    the test, which must carry django_db(transaction=True): the migrations run
    DDL, which MySQL commits regardless of the test transaction.
    """
    marker = request.node.get_closest_marker("django_db")
    assert marker is not None and marker.kwargs.get("transaction"), (
        "migrate_apps needs the django_db marker with transaction=True"
    )
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    def _migrate(target: tuple[str, str]) -> StateApps:
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
