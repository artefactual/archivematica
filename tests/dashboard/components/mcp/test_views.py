from unittest import mock

import gearman
import pytest
from django.urls import reverse
from lxml import etree

from archivematica.archivematicaCommon.externals import xmltodict
from archivematica.dashboard.components.mcp import views

FILE_FORMAT_IDENTIFICATION_CHOICES = """
<choicesAvailableForUnit>
  <UUID>b8d5dcca-b60e-40fd-b160-32447abbf7f8</UUID>
  <unit>
    <type>Transfer</type>
    <unitXML>
      <UUID>b2b51b27-62e3-4781-bc77-4e7a73b5f0d4</UUID>
      <currentPath>%sharedPath%watchedDirectories/workFlowDecisions/selectFormatIDToolTransfer/bar-b2b51b27-62e3-4781-bc77-4e7a73b5f0d4/</currentPath>
    </unitXML>
  </unit>
  <choices>
    <choice>
      <chainAvailable>0</chainAvailable>
      <description>是</description>
    </choice>
    <choice>
      <chainAvailable>1</chainAvailable>
      <description>不</description>
    </choice>
  </choices>
</choicesAvailableForUnit>
"""
FILE_FORMAT_IDENTIFICATION_CHOICES_DICT = xmltodict.parse(
    etree.tostring(etree.XML(FILE_FORMAT_IDENTIFICATION_CHOICES), encoding="utf8")
)

MCPSERVER_JOBS_AWAITING_APPROVAL_RESULT = f"""
<choicesAvailableForUnits>
  {FILE_FORMAT_IDENTIFICATION_CHOICES}
</choicesAvailableForUnits>
"""


@mock.patch("archivematica.dashboard.contrib.mcp.client.GearmanClient")
@mock.patch(
    "archivematica.dashboard.contrib.mcp.client.gearman.JOB_COMPLETE",
)
def test_list(job_complete, gearman_client, rf, admin_user):
    # Make the Gearman interactions return known values.
    gearman_client.return_value = mock.Mock(
        **{
            "submit_job.return_value": mock.Mock(
                state=job_complete,
                result=MCPSERVER_JOBS_AWAITING_APPROVAL_RESULT,
            )
        }
    )

    # Call the view we are testing.
    request = rf.get(reverse("mcp:list"))
    request.user = admin_user
    response = views.list(request)

    # Check the response is successful and returns XML.
    assert response.status_code == 200
    assert response["Content-Type"] == "text/xml"

    # Convert the data about the only unit in the response into a dictionary.
    response_xml = etree.XML(response.getvalue())
    assert len(response_xml) == 1
    unit_xml = response_xml[0]
    response_unit_dict = xmltodict.parse(etree.tostring(unit_xml, encoding="utf8"))

    # Assert that the unit dictionary matches the original value.
    assert response_unit_dict == FILE_FORMAT_IDENTIFICATION_CHOICES_DICT


@mock.patch("archivematica.dashboard.contrib.mcp.client.GearmanClient")
def test_execute_returns_plaintext_after_approval(
    gearman_client, admin_client, dashboard_uuid
):
    gearman_client.return_value.submit_job.return_value = mock.Mock(
        state=gearman.JOB_COMPLETE, result=["approving: ", "job-id", "chain-id"]
    )

    response = admin_client.post(
        reverse("mcp:execute"), {"uuid": "job-id", "choice": "chain-id"}
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain"
    assert response.content == b"None"
    gearman_client.return_value.shutdown.assert_called_once_with()


@pytest.mark.parametrize(
    "state,payload",
    [
        (gearman.JOB_FAILED, None),
        (gearman.JOB_CREATED, None),
        (gearman.JOB_COMPLETE, {"error": True, "message": "Approval failed"}),
    ],
)
@mock.patch("archivematica.dashboard.contrib.mcp.client.GearmanClient")
def test_execute_returns_unavailable_for_unsuccessful_approval(
    gearman_client, admin_client, dashboard_uuid, state, payload
):
    gearman_client.return_value.submit_job.return_value = mock.Mock(
        state=state, result=payload
    )

    response = admin_client.post(
        reverse("mcp:execute"), {"uuid": "job-id", "choice": "chain-id"}
    )

    assert response.status_code == 503
    assert response["Content-Type"] == "text/plain"
    assert response.content == b"Unable to execute Job choice."
    gearman_client.return_value.shutdown.assert_called_once_with()


@mock.patch("archivematica.dashboard.contrib.mcp.client.GearmanClient")
def test_execute_returns_unavailable_for_transport_error(
    gearman_client, admin_client, dashboard_uuid
):
    gearman_client.return_value.submit_job.side_effect = (
        gearman.errors.ServerUnavailable("gearman:4730")
    )

    response = admin_client.post(
        reverse("mcp:execute"), {"uuid": "job-id", "choice": "chain-id"}
    )

    assert response.status_code == 503
    gearman_client.return_value.shutdown.assert_called_once_with()


@mock.patch("archivematica.dashboard.contrib.mcp.client.GearmanClient")
def test_execute_without_uuid_preserves_empty_response(
    gearman_client, admin_client, dashboard_uuid
):
    response = admin_client.post(reverse("mcp:execute"), {"uuid": ""})

    assert response.status_code == 200
    assert response.content == b""
    gearman_client.assert_not_called()
