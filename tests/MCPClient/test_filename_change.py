import os
import pathlib
import uuid

import pytest
from django.contrib.auth.models import User

from archivematica.archivematicaCommon.version import get_full_version
from archivematica.dashboard.main.models import SIP
from archivematica.dashboard.main.models import Agent
from archivematica.dashboard.main.models import Directory
from archivematica.dashboard.main.models import Event
from archivematica.dashboard.main.models import File
from archivematica.dashboard.main.models import Transfer
from archivematica.MCPClient.client.job import Job
from archivematica.MCPClient.clientScripts import change_names
from archivematica.MCPClient.clientScripts import change_object_names


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


def event_details(event: Event) -> tuple[str, list[str]]:
    """The detail and the agents of a filename change event."""
    return event.event_detail, sorted(repr(agent) for agent in event.agents.all())


EXPECTED_EVENT_DETAILS = (
    f'prohibited characters removed: program="change_names"; version="{get_full_version()}"',
    [
        '<Agent: Archivematica user; Archivematica user pk: 1; username="kmindelan", first_name="Keladry", last_name="Mindelan">',
        "<Agent: organization; repository code: ORG; Your Organization Name Here>",
    ],
)


@pytest.fixture
def unicode_transfer_agent(
    unicode_transfer: Transfer, user: User, user_agent: Agent
) -> Agent:
    """The agent of the user, set as the active agent of the unicode transfer."""
    unicode_transfer.update_active_agent(user.id)

    return user_agent


@pytest.mark.django_db
def test_change_object_names(
    mcp_job: Job,
    tmp_path: pathlib.Path,
    unicode_transfer: Transfer,
    unicode_transfer_files: list[File],
    unicode_transfer_agent: Agent,
    organization_agent: Agent,
) -> None:
    """Test change_object_names.

    It should change filenames.
    It should change directory names & update the files in it.
    It should handle unicode unit names.
    It should not change a name that is already changed.
    Event and Event Agent details should be written correctly.
    """

    # Create files
    transfer_path = unicode_transfer.currentlocation.replace(
        "%sharedPath%currentlyProcessing", str(tmp_path)
    )
    for file_ in unicode_transfer_files:
        path = file_.currentlocation.decode().replace(
            "%transferDirectory%", transfer_path
        )
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(str(path))

    # Change names
    name_changer = change_object_names.NameChanger(
        mcp_job,
        os.path.join(transfer_path, "objects", "").encode("utf8"),
        str(unicode_transfer.uuid),
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

    assert event_details(event) == EXPECTED_EVENT_DETAILS

    assert os.path.exists(
        os.path.join(transfer_path, "objects", "no_name_change/needed_here/lion.svg")
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
    mcp_job: Job,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    transfer: Transfer,
    subdir_path: pathlib.Path,
    multiple_transfer_file_objs: list[File],
    organization_agent: Agent,
) -> None:
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
    file_uuids = [file_obj.uuid for file_obj in multiple_transfer_file_objs]
    # The prohibited characters are removed from the file names. The directory
    # that contains them is the objects directory, which keeps its name.
    subdir = subdir_path.relative_to(tmp_path).as_posix()
    assert sorted(
        file_obj.currentlocation.decode()
        for file_obj in File.objects.filter(uuid__in=file_uuids)
    ) == sorted(
        f"{transfer.currentlocation}{subdir}/bulk-file{x}"
        for x in range(len(file_uuids))
    )
    assert sorted(
        (event.file_uuid_id, event_details(event))
        for event in Event.objects.filter(
            file_uuid__in=file_uuids, event_type="filename change"
        )
    ) == sorted((file_uuid, EXPECTED_EVENT_DETAILS) for file_uuid in file_uuids)


@pytest.mark.django_db
def test_change_transfer_with_directory_uuids(
    mcp_job: Job,
    tmp_path: pathlib.Path,
    transfer: Transfer,
    subdir_path: pathlib.Path,
    transfer_dir_obj: Directory,
) -> None:
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
def test_change_sip(
    mcp_job: Job,
    tmp_path: pathlib.Path,
    sip: SIP,
    subdir_path: pathlib.Path,
    sip_dir_obj: Directory,
    sip_file_obj: File,
) -> None:
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
