from unittest import mock

from components.mcp import views
from django.urls import reverse
from externals import xmltodict
from lxml import etree

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


@mock.patch("contrib.mcp.client.GearmanClient")
@mock.patch(
    "contrib.mcp.client.gearman.JOB_COMPLETE",
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
