from unittest import mock

import gearman
import pytest

from archivematica.dashboard.contrib.mcp import client


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
