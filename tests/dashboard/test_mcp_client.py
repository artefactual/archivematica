from unittest import mock

import pytest

from archivematica.dashboard.contrib.mcp import client


@pytest.mark.parametrize("method_name", ("_rpc_sync_call", "execute", "list"))
@mock.patch("archivematica.dashboard.contrib.mcp.client.GearmanClient")
def test_rpc_client_closes_connection_when_submission_fails(
    gearman_client, method_name
):
    gearman_client.return_value.submit_job.side_effect = RuntimeError(
        "Gearman connection lost"
    )
    mcp_client = client.MCPClient(mock.Mock(id=1))

    with pytest.raises(RuntimeError, match="connection lost"):
        if method_name == "_rpc_sync_call":
            mcp_client._rpc_sync_call("getUnitsStatuses")
        elif method_name == "execute":
            mcp_client.execute("job-uuid", "approve")
        else:
            mcp_client.list()

    gearman_client.return_value.shutdown.assert_called_once_with()
