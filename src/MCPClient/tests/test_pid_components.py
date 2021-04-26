#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit tests for the various components associated with PID (persistent
identifier binding and declaration in Archivematica.

The tests in this module cover both the two bind_pid(s) microservice jobs but
also limited unit testing in create_mets_v2 (AIP METS generation).
"""
from __future__ import unicode_literals
from itertools import chain
import os
import sys

from job import Job
from main.models import Directory, File, SIP, DashboardSetting, Transfer

import pytest
import vcr
import six
from six.moves import range
from six.moves import zip


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
sys.path.append(
    os.path.abspath(os.path.join(THIS_DIR, "../../archivematicaCommon/lib"))
)

vcr_cassettes = vcr.VCR(
    cassette_library_dir=os.path.join(THIS_DIR, "fixtures", "vcr_cassettes"),
    path_transformer=vcr.VCR.ensure_suffix(".yaml"),
)

import bind_pid
import bind_pids
import create_mets_v2
import namespaces as ns
from pid_declaration import DeclarePIDs, DeclarePIDsException


PACKAGE_UUID = "cb5ebaf5-beda-40b4-8d0c-fefbd546b8de"
INCOMPLETE_CONFIG_MSG = "A value for parameter"
BOUND_URI = "http://195.169.88.240:8017/12345/"
BOUND_HDL = "12345/"
TRADITIONAL_IDENTIFIERS = ("UUID",)
BOUND_IDENTIFIER_TYPES = ("hdl", "URI")
PID_EXID = "EXÎD"
PID_ULID = "ULID"
DECLARED_IDENTIFIER_TYPES = (PID_EXID, PID_ULID)


@pytest.fixture
def job():
    return Job("stub", "stub", [])


@pytest.fixture
def sip(db):
    return SIP.objects.create(
        uuid=PACKAGE_UUID,
        aip_filename="pid_tests-cb5ebaf5-beda-40b4-8d0c-fefbd546b8de.7z",
        currentpath="%sharedPath%currentlyProcessing/pid_tests-cb5ebaf5-beda-40b4-8d0c-fefbd546b8de/",
        sip_type="SIP",
        createdtime="2015-06-24T17:22:02Z",
    )


@pytest.fixture
def transfer(db):
    return Transfer.objects.create(
        uuid="29460c83-957e-481f-9ca2-873bca42229a",
        type="Standard",
        currentlocation="%sharedPath%watchedDirectories/SIPCreation/completedTransfers/test-3e1e56ed-923b-4b53-84fe-c5c1c0b0cf8e/",
    )


@pytest.fixture
def settings(db):
    settings = [
        DashboardSetting(scope="handle", name=name, value=value)
        for name, value in (
            (
                "resolve_url_template_file_access",
                "https://access.iisg.nl/access/{{ naming_authority }}/{{ pid }}",
            ),
            (
                "resolve_url_template_file_preservation",
                "https://access.iisg.nl/preservation/{{ naming_authority }}/{{ pid }}",
            ),
            (
                "handle_resolver_url",
                "http://195.169.88.240:8017/",
            ),
            (
                "resolve_url_template_file",
                "https://access.iisg.nl/access/{{ naming_authority }}/{{ pid }}",
            ),
            (
                "pid_request_verify_certs",
                False,
            ),
            (
                "resolve_url_template_archive",
                "https://access.iisg.nl/dip/{{ naming_authority }}/{{ pid }}",
            ),
            (
                "resolve_url_template_mets",
                "https://access.iisg.nl/mets/{{ naming_authority }}/{{ pid }}",
            ),
            (
                "pid_web_service_key",
                "84214c59-8694-48d5-89b5-d40a88cd7768",
            ),
            (
                "handle_archive_pid_source",
                "accession_no",
            ),
            (
                "pid_web_service_endpoint",
                "https://pid.socialhistoryservices.org/secure",
            ),
            (
                "resolve_url_template_file_original",
                "https://access.iisg.nl/original/{{ naming_authority }}/{{ pid }}",
            ),
            (
                "naming_authority",
                "12345",
            ),
            (
                "pid_request_body_template",
                "<?xml version='1.0' encoding='UTF-8'?><soapenv:Envelope xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/'\r\n            xmlns:pid='http://pid.socialhistoryservices.org/'>\r\n            <soapenv:Body>\r\n                <pid:UpsertPidRequest>\r\n                    <pid:na>{{ naming_authority }}</pid:na>\r\n                    <pid:handle>\r\n                        <pid:pid>{{ naming_authority }}/{{ pid }}</pid:pid>\r\n                        <pid:locAtt>\r\n                            <pid:location weight='1' href='{{ base_resolve_url }}'/>\r\n                            {% for qrurl in qualified_resolve_urls %}\r\n                                <pid:location\r\n                                    weight='0'\r\n                                    href='{{ qrurl.url }}'\r\n                                    view='{{ qrurl.qualifier }}'/>\r\n                            {% endfor %}\r\n                        </pid:locAtt>\r\n                    </pid:handle>\r\n                </pid:UpsertPidRequest>\r\n            </soapenv:Body>\r\n        </soapenv:Envelope>",
            ),
        )
    ]
    return DashboardSetting.objects.bulk_create(settings)


@pytest.fixture
def files(db):
    return File.objects.bulk_create(
        [
            File(
                uuid="06da9555-dc5b-425c-b967-6f30a740f1c3",
                checksum="012661d0de5ed60973e5cb0f123df74e95118734345b2bdf35432ac7442dd8c8",
                checksumtype="sha256",
                currentlocation="%SIPDirectory%objects/metadata/transfers/pid_tests-29460c83-957e-481f-9ca2-873bca42229a/directory_tree.txt",
                enteredsystem="2019-05-02T11:16:08.195Z",
                filegrpuse="metadata",
                modificationtime="2019-05-02T11:16:08.195Z",
                originallocation="%SIPDirectory%objects/metadata/transfers/pid_tests-29460c83-957e-481f-9ca2-873bca42229a/directory_tree.txt",
                sip_id=PACKAGE_UUID,
                size=233,
            ),
            File(
                uuid="52e4900a-b096-4815-856a-81b3cbe0952d",
                checksum="cd2b6311b1552b32c9bed90209bb219ab8216fd777b12dd36ad06aba959cba6e",
                checksumtype="sha256",
                currentlocation="%SIPDirectory%objects/images/image_001.jpg",
                enteredsystem="2019-05-02T11:15:31.856Z",
                filegrpuse="original",
                modificationtime="2019-04-23T12:25:01Z",
                originallocation="%transferDirectory%objects/images/image_001.jpg",
                sip_id=PACKAGE_UUID,
                size=11,
                transfer_id="29460c83-957e-481f-9ca2-873bca42229a",
            ),
            File(
                uuid="697c407f-7a43-43d2-b7e2-fefc956ea5fd",
                checksum="cd2b6311b1552b32c9bed90209bb219ab8216fd777b12dd36ad06aba959cba6e",
                checksumtype="sha256",
                currentlocation="%SIPDirectory%objects/documents/Document001.doc",
                enteredsystem="2019-05-02T11:15:31.869Z",
                filegrpuse="original",
                modificationtime="2019-04-23T12:26:18Z",
                originallocation="%transferDirectory%objects/documents/Document001.doc",
                sip_id=PACKAGE_UUID,
                size=11,
                transfer_id="29460c83-957e-481f-9ca2-873bca42229a",
            ),
            File(
                uuid="c91d7725-f363-4e8a-bde1-0f5416b4f7f8",
                checksum="e4bdbed4732746727a013431d87126a43e99ee7350c4d7ba27eb4927d8d06f15",
                checksumtype="sha256",
                currentlocation="%SIPDirectory%objects/submissionDocumentation/transfer-pid_tests-29460c83-957e-481f-9ca2-873bca42229a/METS.xml",
                enteredsystem="2019-05-02T11:16:00.917Z",
                filegrpuse="submissionDocumentation",
                modificationtime="2019-05-02T11:16:00.917Z",
                originallocation="%SIPDirectory%objects/submissionDocumentation/transfer-pid_tests-29460c83-957e-481f-9ca2-873bca42229a/METS.xml",
                sip_id=PACKAGE_UUID,
                size=37119,
            ),
            File(
                uuid="d94dbb6b-1082-4747-9d4c-4ddea8ce85b8",
                checksum="28045d295e79a3666bd4c9a09536e2b6c65e2f917972e15c46c6eb2cad1e5700",
                checksumtype="sha256",
                currentlocation="%SIPDirectory%objects/metadata/transfers/pid_tests-29460c83-957e-481f-9ca2-873bca42229a/identifiers.json",
                enteredsystem="2019-05-02T11:16:08.217Z",
                filegrpuse="metadata",
                modificationtime="2019-05-02T11:16:08.217Z",
                originallocation="%SIPDirectory%objects/metadata/transfers/pid_tests-29460c83-957e-481f-9ca2-873bca42229a/identifiers.json",
                sip_id=PACKAGE_UUID,
                size=1768,
            ),
        ]
    )


@pytest.fixture
def directories(db):
    return Directory.objects.bulk_create(
        [
            Directory(
                uuid="3cc124e1-4e5c-433b-8f15-a7831d70145a",
                originallocation="%transferDirectory%metadata/",
                transfer_id="29460c83-957e-481f-9ca2-873bca42229a",
                currentlocation="%transferDirectory%metadata/",
                enteredsystem="2019-04-23T12:45:34.925Z",
            ),
            Directory(
                uuid="41b3fcfd-36ed-4cf7-b5af-56127238b362",
                originallocation="%transferDirectory%logs/",
                transfer_id="29460c83-957e-481f-9ca2-873bca42229a",
                currentlocation="%transferDirectory%logs/",
                enteredsystem="2019-04-23T12:45:34.925Z",
            ),
            Directory(
                uuid="966755bd-0ae3-4f85-b4ec-b359fefeff33",
                sip_id=PACKAGE_UUID,
                originallocation="%transferDirectory%objects/images/",
                transfer_id="29460c83-957e-481f-9ca2-873bca42229a",
                currentlocation="%SIPDirectory%objects/images/",
                enteredsystem="2019-04-23T12:45:34.925Z",
            ),
            Directory(
                uuid="d298dd3f-c5d1-4445-99fe-09123fba8b30",
                sip_id=PACKAGE_UUID,
                originallocation="%transferDirectory%objects/documents/",
                transfer_id="29460c83-957e-481f-9ca2-873bca42229a",
                currentlocation="%SIPDirectory%objects/documents/",
                enteredsystem="2019-04-23T12:45:34.925Z",
            ),
            Directory(
                uuid="e7ae9b01-4c07-4915-a7a0-1833b1078a5b",
                originallocation="%transferDirectory%logs/fileMeta/",
                transfer_id="29460c83-957e-481f-9ca2-873bca42229a",
                currentlocation="%transferDirectory%logs/fileMeta/",
                enteredsystem="2019-04-23T12:45:34.925Z",
            ),
            Directory(
                uuid="f9e8c91a-bfbc-48f0-8ff0-eed210ff6fde",
                originallocation="%transferDirectory%metadata/submissionDocumentation/",
                transfer_id="29460c83-957e-481f-9ca2-873bca42229a",
                currentlocation="%transferDirectory%metadata/submissionDocumentation/",
                enteredsystem="2019-04-23T12:45:34.925Z",
            ),
        ]
    )


@pytest.fixture
def data(db, sip, settings, transfer, files, directories):
    return


@pytest.mark.django_db
def test_bind_pids_no_config(data, caplog, job):
    """Test the output of the code without any args.

    In this instance, we want bind_pids to think that there is some
    configuration available but we haven't provided any other information.
    We should see the microservice job exit without failing for the user.
    An example scenario might be when the user has bind PIDs on in their
    processing configuration but no handle server information configured.
    """
    DashboardSetting.objects.filter(scope="handle").delete()
    assert (
        bind_pids.main(job, None, None) == 1
    ), "Incorrect return value for bind_pids with incomplete configuration."
    assert caplog.records[0].message.startswith(INCOMPLETE_CONFIG_MSG)


@pytest.mark.django_db
def test_bind_pids(data, mocker, job):
    """Test the bind_pids function end-to-end and ensure that the
    result is that which is anticipated.

    The bind_pids module is responsible for binding persistent identifiers
    to the SIP and the SIP's directories so we only test that here.
    """
    # We might want to return a unique accession number, but we can also
    # test here using the package UUID, the function's fallback position.
    mocker.patch.object(bind_pids, "_get_unique_acc_no", return_value=PACKAGE_UUID)
    mocker.patch.object(bind_pids, "_validate_handle_server_config", return_value=None)
    with vcr_cassettes.use_cassette("test_bind_pids_to_sip_and_dirs.yaml") as cassette:
        # Primary entry-point for the bind_pids microservice job.
        bind_pids.main(job, PACKAGE_UUID, "")
    assert cassette.all_played
    sip_mdl = SIP.objects.filter(uuid=PACKAGE_UUID).first()
    assert len(sip_mdl.identifiers.all()) == len(
        BOUND_IDENTIFIER_TYPES
    ), "Number of SIP identifiers is greater than anticipated"
    dirs = Directory.objects.filter(sip=PACKAGE_UUID).all()
    # At time of writing, the Bind PIDs functions only binds to the content
    # folders and the SIP itself, it doesn't bind to the metadata or
    # submissionDocumentation directories in the package.
    package_dirs = ["images/", "documents"]
    assert len(dirs) == len(package_dirs), "Number of directories is incorrect"
    for mdl in chain(dirs, (sip_mdl,)):
        bound = [(idfr.type, idfr.value) for idfr in mdl.identifiers.all()]
        assert len(bound) == len(BOUND_IDENTIFIER_TYPES)
        pid_types = []
        for pid in bound:
            pid_types.append(pid[0])
        assert (
            "hdl" in pid_types
        ), "An expected hdl persistent identifier isn't in the result set"
        assert "URI" in pid_types, "An expected URI isn't in the result set"
        bound_hdl = "{}{}".format(BOUND_HDL, mdl.pk)
        bound_uri = "{}{}".format(BOUND_URI, mdl.pk)
        pids = []
        for pid in bound:
            pids.append(pid[1])
        assert bound_hdl in pids, "Handle PID bound to SIP is incorrect"
        assert bound_uri in pids, "URI PID bound to SIP is incorrect"
        # Once we know we're creating identifiers as expected, test to ensure
        # that those identifiers are output as expected by the METS functions
        # doing that work.
        dir_dmd_sec = create_mets_v2.getDirDmdSec(mdl, "")
        id_type = dir_dmd_sec.xpath(
            "//premis:objectIdentifierType", namespaces={"premis": ns.premisNS}
        )
        id_value = dir_dmd_sec.xpath(
            "//premis:objectIdentifierValue", namespaces={"premis": ns.premisNS}
        )
        id_types = [item.text for item in id_type]
        id_values = [item.text for item in id_value]
        identifiers_dict = dict(list(zip(id_types, id_values)))
        for key in identifiers_dict.keys():
            assert key in chain(TRADITIONAL_IDENTIFIERS, BOUND_IDENTIFIER_TYPES)
        assert bound_hdl in list(identifiers_dict.values())
        assert bound_uri in list(identifiers_dict.values())


@pytest.mark.django_db
def test_bind_pid_no_config(data, caplog, job):
    """Test the output of the code when bind_pids is set to True but there
    are no handle settings in the Dashboard. Conceivably then the dashboard
    settings could be in-between two states, complete and not-complete,
    here we test for the two opposites on the assumption they'll be the
    most visible errors to the user.
    """
    DashboardSetting.objects.filter(scope="handle").delete()
    assert bind_pid.main(job, PACKAGE_UUID) == 1
    assert caplog.records[0].message.startswith(INCOMPLETE_CONFIG_MSG)


@pytest.mark.django_db
def test_bind_pid(data, job):
    """Test the bind_pid function end-to-end and ensure that the
    result is that which is anticipated.

    The bind_pid module is responsible for binding persistent identifiers
    to the SIP's files and so we test for that here.
    """
    files = File.objects.filter(sip=PACKAGE_UUID).all()
    package_files = [
        "directory_tree.txt",
        "image 001.jpg",
        "Dōcumēnt001.doc",
        "METS.xml",
        "identifiers.json",
    ]
    assert len(files) is len(
        package_files
    ), "Number of files returned from package is incorrect"
    for file_ in files:
        with vcr_cassettes.use_cassette("test_bind_pid_to_files.yaml") as cassette:
            bind_pid.main(job, file_.pk)
    assert cassette.all_played
    for file_mdl in files:
        bound = {idfr.type: idfr.value for idfr in file_mdl.identifiers.all()}
        assert (
            "hdl" in bound
        ), "An expected hdl persistent identifier isn't in the result set"
        assert "URI" in bound, "An expected URI isn't in the result set"
        bound_hdl = "{}{}".format(BOUND_HDL, file_mdl.pk)
        bound_uri = "{}{}".format(BOUND_URI, file_mdl.pk)
        assert bound.get("hdl") == bound_hdl
        assert bound.get("URI") == bound_uri
        # Then test to see that the PREMIS objects are created correctly in
        # the AIP METS generation code.
        file_level_premis = create_mets_v2.create_premis_object(file_mdl.pk)
        id_type = file_level_premis.xpath(
            "//premis:objectIdentifierType", namespaces={"premis": ns.premisNS}
        )
        id_value = file_level_premis.xpath(
            "//premis:objectIdentifierValue", namespaces={"premis": ns.premisNS}
        )
        id_types = [item.text for item in id_type]
        id_values = [item.text for item in id_value]
        identifiers_dict = dict(list(zip(id_types, id_values)))
        for key in identifiers_dict.keys():
            assert key in chain(
                TRADITIONAL_IDENTIFIERS, BOUND_IDENTIFIER_TYPES
            ), "Identifier type not in expected schemes list"
        assert bound_hdl in list(identifiers_dict.values())
        assert bound_uri in list(identifiers_dict.values())


@pytest.mark.django_db
def test_bind_pid_no_settings(data, caplog, job):
    """Test the output of the code when bind_pids is set to True but there
    are no handle settings in the Dashboard. Conceivably then the dashboard
    settings could be in-between two states, complete and not-complete,
    here we test for the two opposites on the assumption they'll be the
    most visible errors to the user.
    """
    file_count = 5
    DashboardSetting.objects.filter(scope="handle").delete()
    files = File.objects.filter(sip=PACKAGE_UUID).all()
    assert files is not None, "Files haven't been retrieved from the model as expected"
    for file_ in files:
        bind_pid.main(job, file_.pk)
    for file_number in range(file_count):
        assert caplog.records[file_number].message.startswith(INCOMPLETE_CONFIG_MSG)


@pytest.mark.django_db
def test_pid_declaration(data, mocker, job):
    """Test that the overall functionality of the PID declaration functions
    work as expected.
    """
    example_ulid = "EXAMPLE0RE60SW7SVM2C8EGQAD"
    example_uri = "https://éxample.com/"
    all_identifier_types = (
        TRADITIONAL_IDENTIFIERS + BOUND_IDENTIFIER_TYPES + DECLARED_IDENTIFIER_TYPES
    )
    mocker.patch.object(
        DeclarePIDs,
        "_retrieve_identifiers_path",
        return_value=os.path.join(
            THIS_DIR, "fixtures", "pid_declaration", "identifiers.json"
        ),
    )
    DeclarePIDs(job).pid_declaration(unit_uuid=PACKAGE_UUID, sip_directory="")
    # Declare PIDs allows us to assign PIDs to very specific objects in a
    # transfer.
    sip_mdl = SIP.objects.filter(uuid=PACKAGE_UUID).first()
    files = File.objects.filter(sip=PACKAGE_UUID, filegrpuse="original").all()
    dir_mdl = Directory.objects.filter(
        currentlocation__contains="%SIPDirectory%objects/"
    )
    assert len(files) == 2, "Number of files returned is incorrect"
    assert len(dir_mdl) == 2, "Number of directories returned is incorrect"
    for mdl in chain((sip_mdl,), files, dir_mdl):
        bound = {idfr.type: idfr.value for idfr in mdl.identifiers.all()}
        assert len(bound) == 2, "Number of identifiers is incorrect"
        assert set(bound.keys()) == set(
            DECLARED_IDENTIFIER_TYPES
        ), "Returned keys are not in expected list"
        for key, value in bound.items():
            assert value, "Returned an empty value for an identifier"
            if key == PID_EXID:
                assert example_uri in value, "Example URI type not preserved"
            if key == PID_ULID:
                assert len(example_ulid) == len(value)
    # Use the previous PID binding vcr cassettes to ensure declared PIDs can
    # co-exist with bound ones.
    mocker.patch.object(bind_pids, "_get_unique_acc_no", return_value=PACKAGE_UUID)
    mocker.patch.object(bind_pids, "_validate_handle_server_config", return_value=None)
    with vcr_cassettes.use_cassette("test_bind_pids_to_sip_and_dirs.yaml") as cassette:
        # Primary entry-point for the bind_pids microservice job.
        bind_pids.main(job, PACKAGE_UUID, "")
    for mdl in chain((sip_mdl,), dir_mdl):
        dir_dmd_sec = create_mets_v2.getDirDmdSec(mdl, "")
        id_type = dir_dmd_sec.xpath(
            "//premis:objectIdentifierType", namespaces={"premis": ns.premisNS}
        )
        id_value = dir_dmd_sec.xpath(
            "//premis:objectIdentifierValue", namespaces={"premis": ns.premisNS}
        )
        assert len(id_type) == len(
            all_identifier_types
        ), "Identifier type count is incorrect"
        assert len(id_value) == len(
            all_identifier_types
        ), "Identifier value count is incorrect"
        for key, value in dict(list(zip(id_type, id_value))).items():
            if key == PID_EXID:
                assert example_uri in value, "Example URI not preserved"
            if key == PID_ULID:
                assert len(example_ulid) == len(value)
    for file_ in files:
        with vcr_cassettes.use_cassette("test_bind_pid_to_files.yaml") as cassette:
            bind_pid.main(job, file_.pk)
        assert cassette.all_played
    for file_mdl in files:
        file_level_premis = create_mets_v2.create_premis_object(file_mdl.pk)
        id_type = file_level_premis.xpath(
            "//premis:objectIdentifierType", namespaces={"premis": ns.premisNS}
        )
        id_value = file_level_premis.xpath(
            "//premis:objectIdentifierValue", namespaces={"premis": ns.premisNS}
        )
        assert len(id_type) == len(
            all_identifier_types
        ), "Identifier type count is incorrect"
        assert len(id_value) == len(
            all_identifier_types
        ), "Identifier value count is incorrect"
        for key, value in dict(list(zip(id_type, id_value))).items():
            if key == PID_EXID:
                assert example_uri in value, "Example URI not preserved"
            if key == PID_ULID:
                assert len(example_ulid) == len(value)


@pytest.mark.django_db
def test_pid_declaration_exceptions(data, mocker, job):
    """Ensure that the PID declaration feature exits when the JSOn cannot
    be loaded.
    """
    # Test behavior when there isn't an identifiers.json file, e.g. we
    # simulate this by passing an incorrect Unit UUID.
    DeclarePIDs(job).pid_declaration(
        unit_uuid="eb6b860e-611c-45c8-8d3e-b9396ed6c751", sip_directory=""
    )
    assert (
        "No identifiers.json file found" in job.get_stderr().strip()
    ), "Expecting no identifiers.json file, but got something else"
    # Test behavior when identifiers.json is badly formatted.
    bad_identifiers_loc = os.path.join(
        THIS_DIR, "fixtures", "pid_declaration", "bad_identifiers.json"
    )
    mocker.patch.object(
        DeclarePIDs, "_retrieve_identifiers_path", return_value=bad_identifiers_loc
    )
    try:
        DeclarePIDs(job).pid_declaration(unit_uuid="", sip_directory="")
    except DeclarePIDsException as err:
        json_error = (
            "No JSON object could be decoded"
            if six.PY2
            else "Expecting value: line 15 column 1 (char 336)"
        )
        assert json_error in str(
            err
        ), "Error message something other than anticipated for invalid JSON"
