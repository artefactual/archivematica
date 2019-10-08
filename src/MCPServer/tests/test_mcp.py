from __future__ import absolute_import, division, print_function, unicode_literals

import threading


from server.mcp import main


def test_mcp_main(mocker):
    """Test spin up with immediate shutdown.

    This test has limited utility because everything is mocked, but it should
    help catch basic errors.
    """
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
