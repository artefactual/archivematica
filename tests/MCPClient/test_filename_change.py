import os
import shutil
import uuid

import change_names
import change_object_names
import pytest
from client.job import Job
from django.test import TestCase
from main.models import Agent
from main.models import Directory
from main.models import Event
from main.models import File
from main.models import Transfer
from main.models import UnitVariable
from pytest_django.asserts import assertQuerysetEqual

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# This uses the same name as the pytest fixture in conftest and it can be
# removed when these TestCase subclasses are converted into pytest tests.
mcp_job = Job("stub", "stub", [])


@pytest.fixture()
def subdir_path(tmp_path):
    subdir = tmp_path / "subdir1たくさん"
    subdir.mkdir()

    return subdir


@pytest.fixture()
def transfer_dir_obj(db, transfer, tmp_path, subdir_path):
    dir_obj_path = "".join(
        [
            transfer.currentlocation,
            subdir_path.relative_to(tmp_path).as_posix(),
            os.path.sep,
        ]
    )
    dir_obj = Directory.objects.create(
        uuid=uuid.uuid4(),
        transfer=transfer,
        originallocation=dir_obj_path.encode(),
        currentlocation=dir_obj_path.encode(),
    )

    return dir_obj


@pytest.fixture()
def sip_dir_obj(db, sip, tmp_path, subdir_path):
    dir_obj_path = "".join(
        [
            sip.currentpath,
            subdir_path.relative_to(tmp_path).as_posix(),
            os.path.sep,
        ]
    )
    dir_obj = Directory.objects.create(
        uuid=uuid.uuid4(),
        sip=sip,
        originallocation=dir_obj_path.encode(),
        currentlocation=dir_obj_path.encode(),
    )

    return dir_obj


@pytest.fixture()
def sip_file_obj(db, sip, tmp_path, subdir_path):
    file_path = subdir_path / "filé1"
    file_path.write_text("Hello world")
    relative_path = "".join(
        [
            sip.currentpath,
            file_path.relative_to(tmp_path).as_posix(),
        ]
    )

    return File.objects.create(
        uuid=uuid.uuid4(),
        sip=sip,
        originallocation=relative_path.encode(),
        currentlocation=relative_path.encode(),
        removedtime=None,
        size=113318,
        checksum="35e0cc683d75704fc5b04fc3633f6c654e10cd3af57471271f370309c7ff9dba",
        checksumtype="sha256",
    )


@pytest.fixture()
def multiple_file_paths(subdir_path):
    paths = [(subdir_path / f"bülk-filé{x}") for x in range(11)]
    for path in paths:
        path.write_text("Hello world")

    return paths


@pytest.fixture()
def multiple_transfer_file_objs(db, transfer, tmp_path, multiple_file_paths):
    relative_paths = [
        "".join(
            [
                transfer.currentlocation,
                path.relative_to(tmp_path).as_posix(),
            ]
        )
        for path in multiple_file_paths
    ]

    file_objs = [
        File(
            uuid=uuid.uuid4(),
            transfer=transfer,
            originallocation=relative_path.encode(),
            currentlocation=relative_path.encode(),
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
    assert (
        'prohibited characters removed: program="change_names"; ' 'version="1.10.'
    ) in event.event_detail
    assertQuerysetEqual(
        event.agents.all(),
        [
            "<Agent: organization; repository code: ORG; Your Organization Name Here>",
            '<Agent: Archivematica user; Archivematica user pk: 1; username="kmindelan", first_name="Keladry", last_name="Mindelan">',
        ],
        transform=repr,
        ordered=False,
    )


class TestFilenameChange(TestCase):
    """Test change_names, change_object_names & change_sip_name."""

    fixture_files = [
        "transfer.json",
        "files-transfer-unicode.json",
    ]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    transfer_uuid = "e95ab50f-9c84-45d5-a3ca-1b0b3f58d9b6"

    @pytest.fixture(autouse=True)
    def tmp_dir(self, tmp_path):
        tmpdir = tmp_path / "tmp"
        tmpdir.mkdir()
        self.tmpdir = tmpdir

    @pytest.fixture(autouse=True)
    def admin_agent(self, user):
        return Agent.objects.create(
            agenttype="Archivematica user",
            identifiervalue=str(user.pk),
            name=f'username="{user.username}", first_name="{user.first_name}", last_name="{user.last_name}"',
            identifiertype="Archivematica user pk",
        )

    @pytest.fixture(autouse=True)
    def microservice_unitvars(self, admin_agent):
        UnitVariable.objects.create(
            unituuid=self.transfer_uuid,
            unittype="Transfer",
            variablevalue=str(admin_agent.pk),
            variable="activeAgent",
        )

    def test_change_object_names(self):
        """Test change_object_names.

        It should change filenames.
        It should change directory names & update the files in it.
        It should handle unicode unit names.
        It should not change a name that is already changed.
        Event and Event Agent details should be written correctly.
        """

        # Create files
        transfer = Transfer.objects.get(uuid=self.transfer_uuid)
        transfer_path = transfer.currentlocation.replace(
            "%sharedPath%currentlyProcessing", str(self.tmpdir)
        )
        for f in File.objects.filter(transfer_id=self.transfer_uuid):
            path = f.currentlocation.decode().replace(
                "%transferDirectory%", transfer_path
            )
            dirname = os.path.dirname(path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(path, "w") as f:
                f.write(str(path))

        try:
            # Change names
            name_changer = change_object_names.NameChanger(
                mcp_job,
                os.path.join(transfer_path, "objects", "").encode("utf8"),
                self.transfer_uuid,
                "2017-01-04 19:35:22",
                "%transferDirectory%",
                "transfer_id",
                os.path.join(transfer_path, "").encode("utf8"),
            )
            name_changer.change_objects()
            # Assert files have expected name
            # Assert DB has been updated
            # Assert events created
            assert os.path.exists(
                os.path.join(
                    transfer_path,
                    "objects",
                    "takusan_directories",
                    "need_name_change",
                    "checking_here",
                    "evelyn_s_photo.jpg",
                )
            )
            assert File.objects.get(
                currentlocation=b"%transferDirectory%objects/takusan_directories/need_name_change/checking_here/evelyn_s_photo.jpg"
            )
            event = Event.objects.get(
                file_uuid="47813453-6872-442b-9d65-6515be3c5aa1",
                event_type="filename change",
            )

            verify_event_details(event)

            assert os.path.exists(
                os.path.join(
                    transfer_path, "objects", "no_name_change/needed_here/lion.svg"
                )
            )
            assert File.objects.get(
                currentlocation=b"%transferDirectory%objects/no_name_change/needed_here/lion.svg"
            )
            assert not Event.objects.filter(
                file_uuid="60e5c61b-14ef-4e92-89ec-9b9201e68adb",
                event_type="filename change",
            ).exists()

            assert os.path.exists(
                os.path.join(
                    transfer_path,
                    "objects",
                    "takusan_directories",
                    "need_name_change",
                    "checking_here",
                    "lionXie_Zhen_.svg",
                )
            )
            assert File.objects.get(
                currentlocation=b"%transferDirectory%objects/takusan_directories/need_name_change/checking_here/lionXie_Zhen_.svg"
            )
            assert Event.objects.filter(
                file_uuid="791e07ea-ad44-4315-b55b-44ec771e95cf",
                event_type="filename change",
            ).exists()

            assert os.path.exists(
                os.path.join(transfer_path, "objects", "has_space", "lion.svg")
            )
            assert File.objects.get(
                currentlocation=b"%transferDirectory%objects/has_space/lion.svg"
            )
            assert Event.objects.filter(
                file_uuid="8a1f0b59-cf94-47ef-8078-647b77c8a147",
                event_type="filename change",
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
def test_change_name(basename, expected_name):
    assert change_names.change_name(basename) == expected_name


def test_change_name_raises_valueerror_on_empty_string():
    with pytest.raises(ValueError):
        change_names.change_name("")


@pytest.mark.django_db
def test_change_transfer_with_multiple_files(
    monkeypatch, tmp_path, transfer, subdir_path, multiple_transfer_file_objs
):
    monkeypatch.setattr(change_object_names.NameChanger, "BATCH_SIZE", 10)

    name_changer = change_object_names.NameChanger(
        mcp_job,
        subdir_path.as_posix(),
        transfer.uuid,
        "2017-01-04 19:35:22",
        "%transferDirectory%",
        "transfer_id",
        os.path.join(tmp_path.as_posix(), ""),
    )
    name_changer.change_objects()

    assert multiple_transfer_file_objs, "File objects structure is empty"
    for file_obj in multiple_transfer_file_objs:
        original_location = file_obj.currentlocation
        file_obj.refresh_from_db()

        assert file_obj.currentlocation.decode() != original_location
        assert subdir_path.as_posix() not in file_obj.currentlocation.decode()
        assert "bulk-file" in file_obj.currentlocation.decode()
        verify_event_details(
            Event.objects.get(file_uuid=file_obj.uuid, event_type="filename change")
        )


@pytest.mark.django_db
def test_change_transfer_with_directory_uuids(
    tmp_path, transfer, subdir_path, transfer_dir_obj
):
    name_changer = change_object_names.NameChanger(
        mcp_job,
        os.path.join(tmp_path.as_posix(), ""),
        transfer.uuid,
        "2017-01-04 19:35:22",
        "%transferDirectory%",
        "transfer_id",
        os.path.join(tmp_path.as_posix(), ""),
    )
    name_changer.change_objects()

    original_location = transfer_dir_obj.currentlocation
    transfer_dir_obj.refresh_from_db()

    assert transfer_dir_obj.currentlocation != original_location
    assert subdir_path.as_posix() not in transfer_dir_obj.currentlocation.decode()


@pytest.mark.django_db
def test_change_sip(tmp_path, sip, subdir_path, sip_dir_obj, sip_file_obj):
    name_changer = change_object_names.NameChanger(
        mcp_job,
        os.path.join(tmp_path.as_posix(), ""),
        sip.uuid,
        "2017-01-04 19:35:22",
        r"%SIPDirectory%",
        "sip_id",
        os.path.join(tmp_path.as_posix(), ""),
    )
    name_changer.change_objects()

    original_dir_location = sip_dir_obj.currentlocation
    sip_dir_obj.refresh_from_db()

    assert sip_dir_obj.currentlocation != original_dir_location
    assert subdir_path.as_posix() not in sip_dir_obj.currentlocation.decode()

    original_file_location = sip_file_obj.currentlocation
    sip_file_obj.refresh_from_db()

    assert sip_file_obj.currentlocation != original_file_location
    assert subdir_path.as_posix() not in sip_file_obj.currentlocation.decode()
    assert "file" in sip_file_obj.currentlocation.decode()
