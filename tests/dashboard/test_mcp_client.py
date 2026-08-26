from unittest import mock

import gearman
import pytest

from archivematica.dashboard.contrib.mcp import client


def test_execute_waits_for_approval_acknowledgement(settings):
    settings.GEARMAN_SERVER = "gearman:4730"
    user = mock.Mock(id=1)
    gearman_client = mock.Mock()
    gearman_client.submit_job.return_value = mock.Mock(
        state=gearman.JOB_COMPLETE, result=["approving: ", "job-id", "chain-id"]
    )

    with mock.patch.object(client, "GearmanClient", return_value=gearman_client):
        result = client.MCPClient(user).execute("job-id", "chain-id")

    assert result is None
    gearman_client.submit_job.assert_called_once_with(
        b"approveJob",
        {"jobUUID": "job-id", "chain": "chain-id", "user_id": 1},
        background=False,
        wait_until_complete=True,
        poll_timeout=client.INFLIGHT_POLL_TIMEOUT,
    )
    gearman_client.shutdown.assert_called_once_with()


@pytest.mark.parametrize(
    "state,payload,error",
    [
        (gearman.JOB_FAILED, None, client.RPCError),
        (gearman.JOB_CREATED, None, client.TimeoutError),
        (
            gearman.JOB_COMPLETE,
            {"error": True, "message": "Approval failed"},
            client.RPCServerError,
        ),
    ],
)
def test_execute_rejects_unsuccessful_approvals(settings, state, payload, error):
    settings.GEARMAN_SERVER = "gearman:4730"
    gearman_client = mock.Mock()
    gearman_client.submit_job.return_value = mock.Mock(state=state, result=payload)

    with (
        mock.patch.object(client, "GearmanClient", return_value=gearman_client),
        pytest.raises(error),
    ):
        client.MCPClient(mock.Mock(id=1)).execute("job-id", "chain-id")

    gearman_client.shutdown.assert_called_once_with()


def test_execute_translates_transport_errors_and_closes_connection(settings):
    settings.GEARMAN_SERVER = "gearman:4730"
    gearman_client = mock.Mock()
    gearman_client.submit_job.side_effect = gearman.errors.ServerUnavailable(
        "gearman:4730"
    )

    with (
        mock.patch.object(client, "GearmanClient", return_value=gearman_client),
        pytest.raises(client.RPCError, match="approveJob failed"),
    ):
        client.MCPClient(mock.Mock(id=1)).execute("job-id", "chain-id")

    gearman_client.shutdown.assert_called_once_with()


def test_rpc_sync_call_translates_gearman_transport_errors(settings):
    settings.GEARMAN_SERVER = "gearman:4730"
    user = mock.Mock(id=1)
    gearman_client = mock.Mock()
    gearman_client.submit_job.side_effect = gearman.errors.ServerUnavailable(
        "gearman:4730"
    )

    with (
        mock.patch.object(client, "GearmanClient", return_value=gearman_client),
        pytest.raises(client.RPCError) as exc_info,
    ):
        client.MCPClient(user)._rpc_sync_call("getUnitsSummary")

    assert str(exc_info.value) == "getUnitsSummary failed (check the logs)"
    gearman_client.shutdown.assert_called_once_with()
