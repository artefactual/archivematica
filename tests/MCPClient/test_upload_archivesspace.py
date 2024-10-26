"""Tests for the upload_archivesspace.py client script."""

import uuid
from unittest import mock

import pytest
import upload_archivesspace


def test_recursive_file_gen(tmpdir):
    hello = tmpdir.join("mydir", "hello.txt")
    hello.write("hello!", ensure=True)
    bye = tmpdir.join("mydir", "sub", "bye.txt")
    bye.write("bye!", ensure=True)
    result = list(upload_archivesspace.recursive_file_gen(str(tmpdir / "mydir")))
    assert sorted(result) == [str(hello), str(bye)]


def test_get_files_from_dip_finds_files(tmpdir):
    object1 = tmpdir.join("mydip", "objects", "object1.txt")
    object1.write("object 1", ensure=True)
    object2 = tmpdir.join("mydip", "objects", "subdir", "object2.txt")
    object2.write("object 2", ensure=True)
    result = upload_archivesspace.get_files_from_dip(str(tmpdir / "mydip"))
    assert sorted(result) == [str(object1), str(object2)]


@mock.patch("upload_archivesspace.logger")
def test_get_files_from_dip_with_empty_dip_location(logger, tmpdir):
    dip = tmpdir.mkdir("mydip")
    with pytest.raises(ValueError):
        upload_archivesspace.get_files_from_dip(str(dip))
        pytest.fail("cannot find dip")
    logger.error.assert_called_once_with(f"no files in {str(dip)}/objects")


@mock.patch(
    "upload_archivesspace.ArchivesSpaceDIPObjectResourcePairing.objects.filter",
    return_value=[
        mock.Mock(fileuuid="1", resourceid="myresource"),
        mock.Mock(fileuuid="2", resourceid="myresource"),
    ],
)
def test_get_pairs(filter_mock):
    dip_uuid = "somedipuuid"
    result = upload_archivesspace.get_pairs(dip_uuid)
    assert result == {"1": "myresource", "2": "myresource"}
    filter_mock.assert_called_once_with(dipuuid=dip_uuid)


@mock.patch("upload_archivesspace.ArchivesSpaceDIPObjectResourcePairing.objects.filter")
def test_delete_pairs(filter_mock):
    dip_uuid = "somedipuuid"
    queryset_mock = mock.Mock()
    filter_mock.return_value = queryset_mock
    upload_archivesspace.delete_pairs(dip_uuid)
    filter_mock.assert_called_once_with(dipuuid=dip_uuid)
    queryset_mock.delete.assert_called_once()


@pytest.mark.parametrize(
    "uri",
    ["http://some/uri/", "http://some/uri"],
    ids=["uri_with_trailing_slash", "uri_with_no_trailing_slash"],
)
@mock.patch("upload_archivesspace.mets_file")
@mock.patch("upload_archivesspace.get_pairs")
def test_upload_to_archivesspace_adds_trailing_slash_to_uri(
    get_pairs, mest_file, db, uri
):
    file_uuid = str(uuid.uuid4())
    dip_uuid = str(uuid.uuid4())
    client_mock = mock.Mock()
    get_pairs.return_value = {file_uuid: "myresource"}
    files = [f"file/{file_uuid}-path"]
    success = upload_archivesspace.upload_to_archivesspace(
        files, client_mock, "", "", "", "", uri, dip_uuid, "", "", "", "", ""
    )
    client_mock.add_digital_object.assert_called_once_with(
        **{
            "access_conditions": "",
            "format_name": None,
            "format_version": None,
            "identifier": file_uuid,
            "inherit_notes": "",
            "location_of_originals": dip_uuid,
            "object_type": "",
            "parent_archival_object": "myresource",
            "restricted": False,
            "size": None,
            "title": "",
            # whole point of this test is to check this path is correct
            "uri": f"http://some/uri/{file_uuid}-path",
            "use_conditions": "",
            "use_statement": "",
            "xlink_actuate": "",
            "xlink_show": "",
        }
    )
    assert success


@pytest.mark.parametrize(
    "params",
    [
        {"restrictions": "premis", "access_conditions": "", "use_conditions": ""},
        {
            "restrictions": "",
            "access_conditions": "somecondition",
            "use_conditions": "",
        },
        {
            "restrictions": "",
            "access_conditions": "",
            "use_conditions": "somecondition",
        },
    ],
    ids=["with_restrictions", "with_access_conditions", "with_use_conditions"],
)
@mock.patch("upload_archivesspace.get_pairs")
@mock.patch("upload_archivesspace.logger")
@mock.patch("upload_archivesspace.mets_file")
def test_upload_to_archivesspace_gets_mets_if_needed(
    mets_file_mock, logger, get_pairs, params
):
    upload_archivesspace.upload_to_archivesspace(
        [],
        "",
        "",
        "",
        "",
        "",
        "",
        "dipuuid",
        params["access_conditions"],
        params["use_conditions"],
        params["restrictions"],
        "/dip/location/path",
        "",
    )
    mets_file_mock.assert_called_once_with("/dip/location/path/METS.dipuuid.xml")
    logger.debug.assert_has_calls(
        [
            mock.call("Looking for mets: dipuuid"),
            mock.call("Found mets file at path: /dip/location/path/METS.dipuuid.xml"),
        ]
    )


@mock.patch("upload_archivesspace.get_pairs")
@mock.patch("upload_archivesspace.logger")
@mock.patch("upload_archivesspace.mets_file")
def test_upload_to_archivesspace_logs_files_with_no_pairs(
    mets_file, logger, get_pairs, db
):
    file1_uuid = uuid.uuid4()
    file2_uuid = uuid.uuid4()
    file3_uuid = uuid.uuid4()
    dip_uuid = uuid.uuid4()
    get_pairs.return_value = {
        str(file1_uuid): "myresource",
        str(file3_uuid): "myresource",
    }
    client_mock = mock.Mock()
    files = [
        f"/path/to/{file1_uuid}-image.jpg",
        f"/path/to/{file2_uuid}-video.avi",
        f"/path/to/{file3_uuid}-audio.mp3",
    ]
    success = upload_archivesspace.upload_to_archivesspace(
        files, client_mock, "", "", "", "", "", dip_uuid, "", "", "", "", ""
    )
    logger.error.assert_called_once_with(
        f"Skipping file {files[1]} ({file2_uuid}) - no pairing found"
    )
    assert not success


@mock.patch("upload_archivesspace.get_pairs")
@mock.patch("upload_archivesspace.logger")
@mock.patch("upload_archivesspace.mets_file")
def test_upload_to_archivesspace_when_upload_fails(mets_file, logger, get_pairs, db):
    file1_uuid = uuid.uuid4()
    file2_uuid = uuid.uuid4()
    file3_uuid = uuid.uuid4()
    dip_uuid = uuid.uuid4()
    get_pairs.return_value = {
        str(file1_uuid): "myresource",
        str(file2_uuid): "myresource",
        str(file3_uuid): "myresource",
    }

    def fail_video_upload(*args, **kwargs):
        if kwargs.get("uri").endswith("video.avi"):
            raise upload_archivesspace.ArchivesSpaceError("error with ArchivesSpace")

    client_mock = mock.Mock(**{"add_digital_object.side_effect": fail_video_upload})
    files = [
        f"/path/to/{str(file1_uuid)}-image.jpg",
        f"/path/to/{str(file2_uuid)}-video.avi",
        f"/path/to/{str(file3_uuid)}-audio.mp3",
    ]
    success = upload_archivesspace.upload_to_archivesspace(
        files, client_mock, "", "", "", "", "", dip_uuid, "", "", "", "", ""
    )
    logger.error.assert_called_once_with(
        "Could not upload {} to ArchivesSpace record myresource. Error: {}".format(
            f"{file2_uuid}-video.avi", "error with ArchivesSpace"
        )
    )
    assert not success


@mock.patch(
    "upload_archivesspace.get_parser",
    return_value=mock.Mock(
        **{
            "parse_args.return_value": mock.Mock(
                **{
                    "base_url": "some_base_url",
                    "user": "some_user",
                    "passwd": "some_passwd",
                    "dip_location": "some_dip_location",
                    "dip_name": "some_dip_name",
                    "dip_uuid": "some_dip_uuid",
                    "xlink_show": "some_xlink_show",
                    "xlink_actuate": "some_xlink_actuate",
                    "object_type": "some_object_type",
                    "use_statement": "some_use_statement",
                    "uri_prefix": "some_uri_prefix",
                    "access_conditions": "some_access_conditions",
                    "use_conditions": "some_use_conditions",
                    "restrictions": "some_restrictions",
                    "inherit_notes": "some_inherit_notes",
                }
            )
        }
    ),
)
@mock.patch("upload_archivesspace.ArchivesSpaceClient")
@mock.patch("upload_archivesspace.get_files_from_dip", return_value=[])
@mock.patch("upload_archivesspace.upload_to_archivesspace")
def test_call(
    upload_to_archivesspace,
    get_files_from_dip_mock,
    client_factory_mock,
    get_parser,
    db,
):
    client_mock = mock.Mock()
    client_factory_mock.return_value = client_mock
    job = mock.Mock(args=[])
    job.JobContext = mock.MagicMock()
    upload_archivesspace.call([job])
    client_factory_mock.assert_called_once_with(
        host="some_base_url", user="some_user", passwd="some_passwd"
    )
    get_files_from_dip_mock.assert_called_once_with("some_dip_location")
    upload_to_archivesspace.assert_called_once_with(
        [],
        client_mock,
        "some_xlink_show",
        "some_xlink_actuate",
        "some_object_type",
        "some_use_statement",
        "some_uri_prefix",
        "some_dip_uuid",
        "some_access_conditions",
        "some_use_conditions",
        "some_restrictions",
        "some_dip_location",
        False,
    )
    job.set_status.assert_called_once_with(0)


@pytest.mark.parametrize(
    "params",
    [
        {"exception": ValueError("cannot find dip"), "expected_job_status": 2},
        {"exception": Exception("unknown error"), "expected_job_status": 3},
    ],
    ids=["no_files_found", "unknown_error_raised"],
)
@mock.patch("upload_archivesspace.get_parser")
@mock.patch("upload_archivesspace.ArchivesSpaceClient")
@mock.patch("upload_archivesspace.get_files_from_dip")
@mock.patch("upload_archivesspace.upload_to_archivesspace")
def test_call_when_files_from_dip_cant_be_retrieved(
    upload_to_archivesspace,
    get_files_from_dip,
    client_factory,
    get_parser,
    db,
    params,
):
    get_files_from_dip.side_effect = params["exception"]

    job = mock.Mock(args=[])
    job.JobContext = mock.MagicMock()
    upload_archivesspace.call([job])
    job.set_status.assert_called_once_with(params["expected_job_status"])
    upload_to_archivesspace.assert_not_called()


@mock.patch("upload_archivesspace.get_parser")
@mock.patch("upload_archivesspace.ArchivesSpaceClient")
@mock.patch("upload_archivesspace.get_files_from_dip")
@mock.patch("upload_archivesspace.upload_to_archivesspace", return_value=False)
def test_call_when_not_all_files_can_be_paired(
    upload_to_archivesspace, get_files_from_dip, client_factory, get_parser, db
):
    job = mock.Mock(args=[])
    job.JobContext = mock.MagicMock()
    upload_archivesspace.call([job])
    job.set_status.assert_called_once_with(2)
