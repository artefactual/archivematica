import json
import pathlib
from unittest import mock

import archivematicaFunctions
import pytest
from components import helpers
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from main import models

TEST_USER_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "test_user.json"
ACCESS_FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "access.json"


class TestAccessAPI(TestCase):
    fixtures = [TEST_USER_FIXTURE, ACCESS_FIXTURE]

    def setUp(self):
        self.client = Client()
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_creating_arrange_directory(self):
        record_id = "/repositories/2/archival_objects/2"
        response = self.client.post(
            reverse(
                "access:access_create_directory",
                kwargs={"record_id": record_id.replace("/", "-")},
            ),
            {},
            follow=True,
        )
        assert response.status_code == 201
        response_dict = json.loads(response.content.decode("utf8"))
        assert response_dict["success"] is True
        mapping = models.SIPArrangeAccessMapping.objects.get(
            system=models.SIPArrangeAccessMapping.ARCHIVESSPACE, identifier=record_id
        )
        arrange_path = mapping.arrange_path.encode() + b"/"
        assert models.SIPArrange.objects.get(arrange_path=arrange_path)

    def test_arrange_contents(self):
        record_id = "/repositories/2/archival_objects/1"
        response = self.client.get(
            reverse(
                "access:access_arrange_contents",
                kwargs={"record_id": record_id.replace("/", "-")},
            ),
            follow=True,
        )
        assert response.status_code == 200
        response_dict = json.loads(response.content.decode("utf8"))
        assert "entries" in response_dict
        assert (
            archivematicaFunctions.b64encode_string("evelyn_s_photo.jpg")
            in response_dict["entries"]
        )
        assert len(response_dict["entries"]) == 1


@pytest.mark.django_db
@pytest.fixture
def dashboard_uuid():
    helpers.set_setting("dashboard_uuid", "test-uuid")


def _encode_record_id(record_id):
    return record_id.replace("/", "")


@pytest.mark.django_db
def test_access_arrange_start_sip_fails_if_arrange_mapping_does_not_exist(
    dashboard_uuid, admin_client
):
    record_id = "/repositories/2/archival_objects/1"

    response = admin_client.get(
        reverse(
            "access:access_arrange_start_sip",
            kwargs={"record_id": _encode_record_id(record_id)},
        )
    )
    assert response.status_code == 404

    result = json.loads(response.content.decode())
    assert result == {
        "message": f"No SIP Arrange mapping exists for record {_encode_record_id(record_id)}",
        "success": False,
    }


@pytest.mark.django_db
@mock.patch("components.access.views.get_as_system_client")
def test_access_arrange_start_sip_fails_if_arrange_does_not_exist(
    get_as_system_client, dashboard_uuid, admin_client
):
    record_id = "/repositories/2/archival_objects/1"
    models.SIPArrangeAccessMapping.objects.create(
        arrange_path="/foobar",
        system=models.SIPArrangeAccessMapping.ARCHIVESSPACE,
        identifier=_encode_record_id(record_id),
    )

    response = admin_client.get(
        reverse(
            "access:access_arrange_start_sip",
            kwargs={"record_id": _encode_record_id(record_id)},
        )
    )
    assert response.status_code == 404

    result = json.loads(response.content.decode())
    assert result == {
        "message": f"No SIP Arrange object exists for record {_encode_record_id(record_id)}",
        "success": False,
    }


@pytest.mark.django_db
@mock.patch(
    "components.access.views.get_as_system_client",
    return_value=mock.Mock(
        **{
            "get_record.side_effect": [
                # Archival object.
                {"resource": {"ref": "/repositories/2/resources/10"}},
                # Resource.
                {"linked_agents": []},
            ]
        }
    ),
)
def test_access_arrange_start_sip_fails_if_resource_creators_cannot_be_fetched(
    get_as_system_client, dashboard_uuid, admin_client
):
    record_id = "/repositories/2/archival_objects/1"
    mapping = models.SIPArrangeAccessMapping.objects.create(
        arrange_path="/foobar",
        system=models.SIPArrangeAccessMapping.ARCHIVESSPACE,
        identifier=_encode_record_id(record_id),
    )
    models.SIPArrange.objects.create(
        arrange_path=f"{pathlib.Path(mapping.arrange_path)}/".encode()
    )

    response = admin_client.get(
        reverse(
            "access:access_arrange_start_sip",
            kwargs={"record_id": _encode_record_id(record_id)},
        )
    )
    assert response.status_code == 502

    result = json.loads(response.content.decode())
    assert result == {
        "message": "Unable to fetch ArchivesSpace creator",
        "success": False,
    }


@pytest.mark.django_db
@mock.patch("components.filesystem_ajax.views.copy_from_arrange_to_completed_common")
@mock.patch("components.access.views.get_as_system_client")
def test_access_arrange_start_sip(
    get_as_system_client,
    copy_from_arrange_to_completed_common,
    dashboard_uuid,
    admin_client,
    caplog,
):
    # Mock expected responses from ArchivesSpace.
    archival_object = {
        "resource": {"ref": "/repositories/2/resources/10"},
        "notes": [{"type": "odd", "subnotes": [{"content": "A note"}]}],
        "display_string": "Object, 2024",
        "parent": {"ref": "/repositories/2/resources/1"},
    }
    resource = {"linked_agents": [{"ref": "/agents/people/3", "role": "creator"}]}
    creator = {"display_name": {"sort_name": "Foo, Bar"}}
    parent = {"title": "Parent resource"}
    digital_object = {"id": "do"}
    get_as_system_client.return_value = mock.Mock(
        **{
            "get_record.side_effect": [archival_object, resource, creator, parent],
            "add_digital_object.side_effect": [
                digital_object,
            ],
        }
    )

    # Mock interaction with copy_from_arrange_to_completed_common.
    sip = models.SIP.objects.create()
    expected_status_code = 201
    expected_response_content = {"message": "SIP created.", "sip_uuid": str(sip.uuid)}
    copy_from_arrange_to_completed_common.return_value = (
        expected_status_code,
        expected_response_content,
    )

    # Set database fixtures.
    record_id = "/repositories/2/archival_objects/1"
    mapping = models.SIPArrangeAccessMapping.objects.create(
        arrange_path="/foobar",
        system=models.SIPArrangeAccessMapping.ARCHIVESSPACE,
        identifier=_encode_record_id(record_id),
    )
    models.SIPArrange.objects.create(
        arrange_path=f"{pathlib.Path(mapping.arrange_path)}/".encode()
    )
    models.ArchivesSpaceDigitalObject.objects.create(
        resourceid=_encode_record_id(record_id), started=False
    )

    response = admin_client.post(
        reverse(
            "access:access_arrange_start_sip",
            kwargs={"record_id": _encode_record_id(record_id)},
        ),
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == expected_status_code

    result = json.loads(response.content.decode())
    assert result == expected_response_content

    assert models.DublinCore.objects.count() == 1
    assert (
        models.DublinCore.objects.filter(
            metadataappliestotype_id=models.MetadataAppliesToType.SIP_TYPE,
            metadataappliestoidentifier=sip.uuid,
            title=archival_object["display_string"],
            creator=creator["display_name"]["sort_name"],
            description=archival_object["notes"][0]["subnotes"][0]["content"],
            rights=" ".join(
                [
                    "This content may be under copyright.",
                    "Researchers are responsible for determining the",
                    "appropriate use or reuse of materials.",
                ]
            ),
            relation=parent["title"],
        ).count()
        == 1
    )

    assert models.ArchivesSpaceDigitalObject.objects.count() == 1
    assert (
        models.ArchivesSpaceDigitalObject.objects.filter(
            resourceid=_encode_record_id(record_id),
            started=True,
            remoteid=digital_object["id"],
            sip_id=expected_response_content["sip_uuid"],
        ).count()
        == 1
    )

    assert [r.message for r in caplog.records] == [
        f"archival object {archival_object}",
        f"resource {resource}",
        f"creator {creator}",
        f"New SIP UUID {sip.uuid}",
    ]
