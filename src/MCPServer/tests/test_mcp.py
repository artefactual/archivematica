from __future__ import absolute_import, division, print_function, unicode_literals

import threading
import uuid

import pytest

from server.mcp import main
from server.mcp import watched_dir_handler


@pytest.mark.django_db(transaction=True)
def test_watched_dir_handler_creates_transfer_if_it_does_not_exist(mocker, tmpdir):
    """Test that a models.Transfer object exists for an unknown path.

    This for example simulates the case when a user drops a directory
    in `watchedDirectories/activeTransfers/standardTransfer`, and a
    transfer UUID cannot be infered from the path because the transfer
    does not exist yet in the database.

    The database transfer is created with a new UUID and the path as
    its current location.
    """
    # We're not interested in the package queue or the link chaining logics here,
    # so we mock very limited implementations for those.
    job_chain_mock = mocker.MagicMock()
    job_chain_mock.return_value = iter(["some_chain_link"])
    mocker.patch("server.mcp.JobChain", job_chain_mock)
    package_queue = mocker.Mock()
    watched_dir = mocker.MagicMock(**{"__getitem__.return_value": "Transfer"})

    # Mock a known UUID for the new transfer.
    transfer_uuid = uuid.uuid4()
    mocker.patch("server.packages.uuid4", return_value=transfer_uuid)

    # Mock the Django manager for the Transfer model. This is mocked from the
    # `server.packages` module since its path from the Dashboard is not available.
    transfer_mock = mocker.Mock(uuid=transfer_uuid)
    create_mock = mocker.patch(
        "server.packages.models.Transfer.objects.create", return_value=transfer_mock
    )

    # The new/unknown path for creating the transfer.
    path = tmpdir.mkdir("some_transfer")

    # Call the function under test.
    watched_dir_handler(package_queue, str(path), watched_dir)

    # The Transfer manager should have been called with the right arguments.
    create_mock.assert_called_once_with(
        uuid=transfer_uuid, currentlocation="{}/".format(path)
    )


@pytest.mark.django_db(transaction=True)
def test_watched_dir_handler_creates_transfer_for_file(mocker, tmpdir):
    """Test that a models.Transfer object exists for a file path."""
    # We're not interested in the package queue or the link chaining logics here,
    # so we mock very limited implementations for those.
    job_chain_mock = mocker.MagicMock()
    job_chain_mock.return_value = iter(["some_chain_link"])
    mocker.patch("server.mcp.JobChain", job_chain_mock)
    package_queue = mocker.Mock()
    watched_dir = mocker.MagicMock(**{"__getitem__.return_value": "Transfer"})

    # Mock a known UUID for the new transfer.
    transfer_uuid = uuid.uuid4()
    mocker.patch("server.packages.uuid4", return_value=transfer_uuid)

    # Mock the Django manager for the Transfer model. This is mocked from the
    # `server.packages` module since its path from the Dashboard is not available.
    transfer_mock = mocker.Mock(uuid=transfer_uuid)
    create_mock = mocker.patch(
        "server.packages.models.Transfer.objects.create", return_value=transfer_mock
    )

    # The new/unknown path of a file for creating the transfer.
    path = tmpdir.join("file.txt")
    path.write("a file!")

    # Call the function under test.
    watched_dir_handler(package_queue, str(path), watched_dir)

    # The Transfer manager should have been called with the right arguments.
    create_mock.assert_called_once_with(uuid=transfer_uuid, currentlocation=str(path))


def test_mcp_main(mocker, settings):
    """Test spin up with immediate shutdown.

    This test has limited utility because everything is mocked, but it should
    help catch basic errors.
    """
    # Don't bother starting many threads
    settings.RPC_THREADS = 1
    settings.WORKER_THREADS = 1
    settings.PROMETHEUS_ENABLED = True

    mock_load_default_workflow = mocker.patch("server.mcp.load_default_workflow")
    mock_shared_dirs = mocker.patch("server.mcp.shared_dirs")
    mock_job = mocker.patch("server.mcp.Job")
    mock_task = mocker.patch("server.mcp.Task")
    mock_metrics = mocker.patch("server.mcp.metrics")

    shutdown_event = threading.Event()
    shutdown_event.set()

    main(shutdown_event=shutdown_event)

    mock_load_default_workflow.assert_called_once()
    mock_shared_dirs.create.assert_called_once()
    mock_job.cleanup_old_db_entries.assert_called_once()
    mock_task.cleanup_old_db_entries.assert_called_once()
    mock_metrics.start_prometheus_server.assert_called_once()
