# -*- coding: utf8
from __future__ import print_function, unicode_literals

import os
import shutil
import sys
import uuid

import pytest
import six
from django.core.management import call_command
from django.test import TestCase

from job import Job
from main.models import Directory, Event, File, Transfer, SIP

from . import TempDirMixin

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))

import sanitize_names
import sanitize_object_names


@pytest.fixture()
def subdir_path(tmp_path):
    subdir = tmp_path / "subdir1たくさん"
    subdir.mkdir()

    return subdir


@pytest.fixture()
def transfer(db):
    return Transfer.objects.create(
        uuid="f6eb30e3-6ded-4f85-b52e-8653b430f29c",
        currentlocation=r"%transferDirectory%",
        diruuids=True,
    )


@pytest.fixture()
def sip(db):
    return SIP.objects.create(
        uuid=uuid.uuid4(), currentpath=r"%SIPDirectory%", diruuids=True
    )


@pytest.fixture()
def transfer_dir_obj(db, transfer, tmp_path, subdir_path):
    dir_obj_path = "".join(
        [
            transfer.currentlocation,
            six.text_type(subdir_path.relative_to(tmp_path).as_posix(), "utf-8"),
            os.path.sep,
        ]
    )
    dir_obj = Directory.objects.create(
        uuid=uuid.uuid4(),
        transfer=transfer,
        originallocation=dir_obj_path,
        currentlocation=dir_obj_path,
    )

    return dir_obj


@pytest.fixture()
def sip_dir_obj(db, sip, tmp_path, subdir_path):
    dir_obj_path = "".join(
        [
            sip.currentpath,
            six.text_type(subdir_path.relative_to(tmp_path).as_posix(), "utf-8"),
            os.path.sep,
        ]
    )
    dir_obj = Directory.objects.create(
        uuid=uuid.uuid4(),
        sip=sip,
        originallocation=dir_obj_path,
        currentlocation=dir_obj_path,
    )

    return dir_obj


@pytest.fixture()
def sip_file_obj(db, sip, tmp_path, subdir_path):
    file_path = subdir_path / "filé1"
    file_path.write_text("Hello world")
    relative_path = "".join(
        [
            sip.currentpath,
            six.text_type(file_path.relative_to(tmp_path).as_posix(), "utf-8"),
        ]
    )

    return File.objects.create(
        uuid=uuid.uuid4(),
        sip=sip,
        originallocation=relative_path,
        currentlocation=relative_path,
        removedtime=None,
        size=113318,
        checksum="35e0cc683d75704fc5b04fc3633f6c654e10cd3af57471271f370309c7ff9dba",
        checksumtype="sha256",
    )


@pytest.fixture()
def multiple_file_paths(subdir_path):
    paths = [(subdir_path / "bülk-filé{}".format(x)) for x in range(11)]
    for path in paths:
        path.write_text("Hello world")

    return paths


@pytest.fixture()
def multiple_transfer_file_objs(db, transfer, tmp_path, multiple_file_paths):
    relative_paths = [
        "".join(
            [
                transfer.currentlocation,
                six.text_type(path.relative_to(tmp_path).as_posix(), "utf-8"),
            ]
        )
        for path in multiple_file_paths
    ]

    file_objs = [
        File(
            uuid=uuid.uuid4(),
            transfer=transfer,
            originallocation=relative_path,
            currentlocation=relative_path,
            removedtime=None,
            size=113318,
            checksum="35e0cc683d75704fc5b04fc3633f6c654e10cd3af57471271f370309c7ff9dba",
            checksumtype="sha256",
        )
        for relative_path in relative_paths
    ]
    return File.objects.bulk_create(file_objs)


def is_uuid(uuid_):
    """Test for a well-formed UUID string."""
    try:
        uuid.UUID(uuid_, version=4)
    except ValueError:
        return False
    return True


def verify_event_details(event):
    """Verify event detail and event agent information is written correctly"""
    NUMBER_OF_EXPECTED_AGENTS = 3
    # Agent values we can test against. Three agents, which should be,
    # preservation system, repository, and user.
    AGENT_IDENTIFIER_VALUES = [
        "Archivematica-1.10",
        "エズメレルダ",
        "Atefactual Systems Inc.",
    ]
    AGENT_IDENTIFIER_TYPES = [
        "preservation system",
        "repository code",
        "Archivematica user pk",
    ]
    AGENT_NAMES = [
        "Archivematica",
        "Artefactual Systems Corporate Archive",
        'username="\u30a8\u30ba\u30e1\u30ec\u30eb\u30c0", first_name="\u3053\u3093\u306b\u3061\u306f", last_name="\u4e16\u754c"',
    ]
    AGENT_TYPES = ["software", "organization", "Archivematica user"]

    EVENT_DETAIL = (
        'prohibited characters removed: program="sanitize_names"; version="1.10.'
    )
    assert event.event_id is not None, "Event ID is None"
    assert is_uuid(event.event_id), "UUID is invalid"
    assert EVENT_DETAIL in event.event_detail, "Event detail written incorrectly"
    # Verify the all Event agents are written as expected in standard workflow.
    agents = list(event.agents.all())
    assert len(agents) == NUMBER_OF_EXPECTED_AGENTS, "Agents not all written for Event"
    for agent in agents:
        # Assert True, then remove from the list to simulate set-like
        # functionality.
        assert (
            agent.identifiervalue in AGENT_IDENTIFIER_VALUES
        ), "Agent identifier value not written"
        assert (
            agent.identifiertype in AGENT_IDENTIFIER_TYPES
        ), "Agent identifier type not written"
        assert agent.name in AGENT_NAMES, "Agent name not written"
        assert agent.agenttype in AGENT_TYPES, "Agent type not written"
        agents.remove(agent)


class TestSanitize(TempDirMixin, TestCase):
    """Test sanitizeNames, sanitize_object_names & sanitizeSipName."""

    transfer_uuid = "e95ab50f-9c84-45d5-a3ca-1b0b3f58d9b6"

    def setUp(self):
        super(TestSanitize, self).setUp()

    @staticmethod
    @pytest.fixture(scope="class")
    def django_db_setup(self, django_db_blocker):
        """Load the various database fixtures required for our tests."""
        agents_fixtures_dir = "microservice_agents"
        agents = os.path.join(agents_fixtures_dir, "microservice_agents.json")
        agent_unitvars = os.path.join(agents_fixtures_dir, "microservice_unitvars.json")
        fixture_files = [
            "transfer.json",
            "files-transfer-unicode.json",
            agents,
            agent_unitvars,
        ]
        fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]
        with django_db_blocker.unblock():
            for fixture in fixtures:
                call_command("loaddata", fixture)

    def test_sanitize_object_names(self):
        """Test sanitize_object_names.

        It should sanitize files.
        It should sanitize a directory & update the files in it.
        It should handle unicode unit names.
        It should not change a name that is already sanitized.
        Event and Event Agent details should be written correctly.
        """

        # Create files
        transfer = Transfer.objects.get(uuid=self.transfer_uuid)
        transfer_path = transfer.currentlocation.replace(
            "%sharedPath%currentlyProcessing", str(self.tmpdir)
        )
        for f in File.objects.filter(transfer_id=self.transfer_uuid):
            path = f.currentlocation.replace("%transferDirectory%", transfer_path)
            dirname = os.path.dirname(path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(path, "w") as f:
                f.write(path.encode("utf8"))

        try:
            # Sanitize
            sanitizer = sanitize_object_names.NameSanitizer(
                Job("stub", "stub", []),
                os.path.join(transfer_path, "objects", "").encode("utf8"),
                self.transfer_uuid,
                "2017-01-04 19:35:22",
                "%transferDirectory%",
                "transfer_id",
                os.path.join(transfer_path, "").encode("utf8"),
            )
            sanitizer.sanitize_objects()
            # Assert files have expected name
            # Assert DB has been updated
            # Assert events created
            assert os.path.exists(
                os.path.join(
                    transfer_path,
                    "objects",
                    "takusan_directories",
                    "need_sanitization",
                    "checking_here",
                    "evelyn_s_photo.jpg",
                )
            )
            assert File.objects.get(
                currentlocation="%transferDirectory%objects/takusan_directories/need_sanitization/checking_here/evelyn_s_photo.jpg"
            )
            event = Event.objects.get(
                file_uuid="47813453-6872-442b-9d65-6515be3c5aa1",
                event_type="name cleanup",
            )

            verify_event_details(event)

            assert os.path.exists(
                os.path.join(
                    transfer_path, "objects", "no_sanitization/needed_here/lion.svg"
                )
            )
            assert File.objects.get(
                currentlocation="%transferDirectory%objects/no_sanitization/needed_here/lion.svg"
            )
            assert not Event.objects.filter(
                file_uuid="60e5c61b-14ef-4e92-89ec-9b9201e68adb",
                event_type="name cleanup",
            ).exists()

            assert os.path.exists(
                os.path.join(
                    transfer_path,
                    "objects",
                    "takusan_directories",
                    "need_sanitization",
                    "checking_here",
                    "lionXie_Zhen_.svg",
                )
            )
            assert File.objects.get(
                currentlocation="%transferDirectory%objects/takusan_directories/need_sanitization/checking_here/lionXie_Zhen_.svg"
            )
            assert Event.objects.filter(
                file_uuid="791e07ea-ad44-4315-b55b-44ec771e95cf",
                event_type="name cleanup",
            ).exists()

            assert os.path.exists(
                os.path.join(transfer_path, "objects", "has_space", "lion.svg")
            )
            assert File.objects.get(
                currentlocation="%transferDirectory%objects/has_space/lion.svg"
            )
            assert Event.objects.filter(
                file_uuid="8a1f0b59-cf94-47ef-8078-647b77c8a147",
                event_type="name cleanup",
            ).exists()
        finally:
            # Delete files
            shutil.rmtree(transfer_path)


@pytest.mark.parametrize(
    "basename, expected_name",
    [
        ("helloworld", "helloworld"),
        ("a\x80b", "ab"),
        ("Smörgåsbord.txt", "Smorgasbord.txt"),
        ("🚀", "_"),
    ],
)
def test_sanitize_name(basename, expected_name):
    assert sanitize_names.sanitize_name(basename) == expected_name


def test_sanitize_name_raises_valueerror_on_empty_string():
    with pytest.raises(ValueError):
        sanitize_names.sanitize_name("")


@pytest.mark.django_db
def test_sanitize_transfer_with_multiple_files(
    monkeypatch, tmp_path, transfer, subdir_path, multiple_transfer_file_objs
):
    monkeypatch.setattr(sanitize_object_names.NameSanitizer, "BATCH_SIZE", 10)

    sanitizer = sanitize_object_names.NameSanitizer(
        Job("stub", "stub", []),
        subdir_path.as_posix(),
        transfer.uuid,
        "2017-01-04 19:35:22",
        "%transferDirectory%",
        "transfer_id",
        os.path.join(tmp_path.as_posix(), ""),
    )
    sanitizer.sanitize_objects()

    assert multiple_transfer_file_objs, "File objects structure is empty"
    for file_obj in multiple_transfer_file_objs:
        original_location = file_obj.currentlocation
        file_obj.refresh_from_db()

        assert file_obj.currentlocation != original_location
        assert (
            six.text_type(subdir_path.as_posix(), "utf-8")
            not in file_obj.currentlocation
        )
        assert "bulk-file" in file_obj.currentlocation
        # Test the event details were written correctly for our object.
        event = Event.objects.get(file_uuid=file_obj.uuid, event_type="name cleanup")
        verify_event_details(event)


@pytest.mark.django_db
def test_sanitize_transfer_with_directory_uuids(
    tmp_path, transfer, subdir_path, transfer_dir_obj
):
    sanitizer = sanitize_object_names.NameSanitizer(
        Job("stub", "stub", []),
        os.path.join(tmp_path.as_posix(), ""),
        transfer.uuid,
        "2017-01-04 19:35:22",
        "%transferDirectory%",
        "transfer_id",
        os.path.join(tmp_path.as_posix(), ""),
    )
    sanitizer.sanitize_objects()

    original_location = transfer_dir_obj.currentlocation
    transfer_dir_obj.refresh_from_db()

    assert transfer_dir_obj.currentlocation != original_location
    assert (
        six.text_type(subdir_path.as_posix(), "utf-8")
        not in transfer_dir_obj.currentlocation
    )


@pytest.mark.django_db
def test_sanitize_sip(tmp_path, sip, subdir_path, sip_dir_obj, sip_file_obj):
    sanitizer = sanitize_object_names.NameSanitizer(
        Job("stub", "stub", []),
        os.path.join(tmp_path.as_posix(), ""),
        sip.uuid,
        "2017-01-04 19:35:22",
        r"%SIPDirectory%",
        "sip_id",
        os.path.join(tmp_path.as_posix(), ""),
    )
    sanitizer.sanitize_objects()

    original_dir_location = sip_dir_obj.currentlocation
    sip_dir_obj.refresh_from_db()

    assert sip_dir_obj.currentlocation != original_dir_location
    assert (
        six.text_type(subdir_path.as_posix(), "utf-8")
        not in sip_dir_obj.currentlocation
    )

    original_file_location = sip_file_obj.currentlocation
    sip_file_obj.refresh_from_db()

    assert sip_file_obj.currentlocation != original_file_location
    assert (
        six.text_type(subdir_path.as_posix(), "utf-8")
        not in sip_file_obj.currentlocation
    )
    assert "file" in sip_file_obj.currentlocation
