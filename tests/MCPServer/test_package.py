import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

import pytest
from django.core.exceptions import ValidationError
from main import models
from server.packages import DIP
from server.packages import SIP
from server.packages import Package
from server.packages import Transfer
from server.packages import _determine_transfer_paths
from server.packages import _move_to_internal_shared_dir
from server.packages import _pad_destination_filepath_if_it_already_exists
from server.packages import create_package
from server.queues import PackageQueue
from server.workflow import Workflow


@pytest.mark.parametrize(
    "name,path,tmpdir,expected",
    [
        (
            "TransferName",
            "a00a29b6-7530-4f09-b3df-fd88d9e478b1:home/username/archive.zip",
            "/tmp/tmp.WXA9V7LCy1",
            (
                # copy_to
                "/tmp/tmp.WXA9V7LCy1",
                # final_location
                "/tmp/tmp.WXA9V7LCy1/archive.zip",
                # copy_from
                "a00a29b6-7530-4f09-b3df-fd88d9e478b1:home/username/archive.zip",
            ),
        ),
        (
            "TransferName",
            "a00a29b6-7530-4f09-b3df-fd88d9e478b2:home/username/dir",
            "/tmp/tmp.WXA9V7LCy2",
            (
                # copy_to
                "/tmp/tmp.WXA9V7LCy2/TransferName",
                # final_location
                "/tmp/tmp.WXA9V7LCy2/TransferName",
                # copy_from
                "a00a29b6-7530-4f09-b3df-fd88d9e478b2:home/username/dir/.",
            ),
        ),
    ],
)
@pytest.mark.django_db
def test__determine_transfer_paths(name, path, tmpdir, expected):
    results = _determine_transfer_paths(name, path, tmpdir)
    assert results[0] == expected[0], "name mismatch"
    assert results[1] == expected[1], "path mismatch"
    assert results[2] == expected[2], "tmpdir mismatch"


@pytest.mark.django_db(transaction=True)
def test_dip_get_or_create_from_db_path_without_uuid(tmp_path):
    dip_path = tmp_path / "test-dip"

    dip = DIP.get_or_create_from_db_by_path(str(dip_path))

    assert dip.current_path == str(dip_path)
    try:
        models.SIP.objects.get(uuid=dip.uuid)
    except (models.SIP.DoesNotExist, ValidationError):
        pytest.fail("DIP.get_or_create_from_db_by_path didn't create a SIP model")


@pytest.mark.django_db(transaction=True)
def test_dip_get_or_create_from_db_path_with_uuid(tmp_path):
    dip_uuid = uuid.uuid4()
    dip_path = tmp_path / f"test-dip-{dip_uuid}"

    dip = DIP.get_or_create_from_db_by_path(str(dip_path))

    assert dip.uuid == dip_uuid
    assert dip.current_path == str(dip_path)
    try:
        models.SIP.objects.get(uuid=dip_uuid)
    except (models.SIP.DoesNotExist, ValidationError):
        pytest.fail("DIP.get_or_create_from_db_by_path didn't create a SIP model")


@pytest.mark.django_db(transaction=True)
def test_transfer_get_or_create_from_db_path_without_uuid(tmp_path):
    transfer_path = tmp_path / "test-transfer"

    assert not models.Transfer.objects.filter(
        currentlocation=str(transfer_path)
    ).count()

    transfer = Transfer.get_or_create_from_db_by_path(str(transfer_path))

    assert transfer.current_path == str(transfer_path)
    try:
        models.Transfer.objects.get(currentlocation=str(transfer_path))
    except models.Transfer.DoesNotExist:
        pytest.fail(
            "Transfer.get_or_create_from_db_by_path didn't create a Transfer model"
        )


@pytest.mark.django_db(transaction=True)
def test_transfer_get_or_create_from_db_path_with_uuid(tmp_path):
    transfer_uuid = uuid.uuid4()
    transfer_path = tmp_path / f"test-transfer-{transfer_uuid}"

    transfer = Transfer.get_or_create_from_db_by_path(str(transfer_path))

    assert transfer.uuid == transfer_uuid
    assert transfer.current_path == str(transfer_path)
    try:
        models.Transfer.objects.get(uuid=transfer_uuid)
    except (models.Transfer.DoesNotExist, ValidationError):
        pytest.fail(
            "Transfer.get_or_create_from_db_by_path didn't create a Transfer model"
        )


@pytest.mark.parametrize(
    "package_class, model, loc_attribute",
    [(Transfer, models.Transfer, "currentlocation"), (SIP, models.SIP, "currentpath")],
)
@pytest.mark.django_db(transaction=True)
def test_package_get_or_create_from_db_by_path_updates_model(
    tmp_path, settings, package_class, model, loc_attribute
):
    settings.SHARED_DIRECTORY = "custom-shared-path"
    package_id = uuid.uuid4()
    path_src = tmp_path / r"%sharedPath%" / "src" / f"test-transfer-{package_id}"
    path_dst = tmp_path / r"%sharedPath%" / "dst" / f"test-transfer-{package_id}"

    package_obj_src = package_class.get_or_create_from_db_by_path(str(path_src))
    package_obj_dst = package_class.get_or_create_from_db_by_path(str(path_dst))

    assert package_id == package_obj_src.uuid == package_obj_dst.uuid
    assert package_obj_src.current_path == str(path_src).replace(
        r"%sharedPath%", settings.SHARED_DIRECTORY
    )
    assert package_obj_dst.current_path == str(path_dst).replace(
        r"%sharedPath%", settings.SHARED_DIRECTORY
    )
    try:
        model.objects.get(**{"uuid": package_id, loc_attribute: path_dst})
    except (models.Transfer.DoesNotExist, ValidationError):
        pytest.fail(
            f"Method {package_class.__name__}.get_or_create_from_db_by_path didn't update {model.__name__} model"
        )


@pytest.mark.django_db(transaction=True)
def test_reload_file_list(tmp_path):
    # Create a transfer that will be updated through time to simulate
    # Archivematica's processing.
    transfer_uuid = uuid.uuid4()
    transfer_path = tmp_path / f"test-transfer-{transfer_uuid}"
    transfer = Transfer.get_or_create_from_db_by_path(str(transfer_path))

    # Add files to the transfer to simulate a transfer existing on disk.
    transfer_path.mkdir()
    objects_path = transfer_path / "objects"
    objects_path.mkdir()
    first_file = objects_path / "file.txt"
    first_file.touch()

    current_location = Path(transfer.REPLACEMENT_PATH_STRING, "objects", "file.txt")
    kwargs = {
        "uuid": uuid.uuid4(),
        "currentlocation": bytes(current_location),
        "filegrpuse": "original",
        "transfer_id": transfer_uuid,
    }
    models.File.objects.create(**kwargs)
    assert models.File.objects.filter(transfer_id=str(transfer_uuid)).count() == 1

    # Add a new file to the file-system, e.g. to simulate normalization for
    # preservation adding a new object.
    new_file = objects_path / "new_file.txt"
    new_file.touch()

    # One file will be returned from the database  with a UUID, another from
    # the filesystem without a UUID.
    for _file_count, file_info in enumerate(transfer.files(None, "/objects"), 1):
        assert "%fileUUID%" in file_info
        assert "%fileGrpUse%" in file_info
        assert "%relativeLocation%" in file_info
        if file_info.get("%fileUUID%") != "None":
            continue
        assert file_info.get("%relativeLocation%") == str(new_file)
        file_path = Path(
            transfer.REPLACEMENT_PATH_STRING,
            "objects",
            Path(file_info.get("%relativeLocation%")).relative_to(objects_path),
        )
        kwargs = {
            "uuid": uuid.uuid4(),
            "currentlocation": bytes(file_path),
            "filegrpuse": "original",
            "transfer_id": transfer_uuid,
        }
        models.File.objects.create(**kwargs)
    assert (
        _file_count == 2
    ), "Database and file objects were not returned by the generator"
    assert models.File.objects.filter(transfer_id=str(transfer_uuid)).count() == 2

    # Simulate an additional file object being added later on in the transfer
    # in a sub directory of the objects folder, e.g. transcribe contents.
    sub_dir = objects_path / "subdir"
    sub_dir.mkdir()
    new_file = sub_dir / "another_new_file.txt"
    new_file.touch()
    for _file_count, file_info in enumerate(transfer.files(None, "/objects"), 1):
        if file_info.get("%fileUUID%") != "None":
            continue
        file_path = Path(
            transfer.REPLACEMENT_PATH_STRING,
            "objects",
            Path(file_info.get("%relativeLocation%")).relative_to(Path(objects_path)),
        )
        kwargs = {
            "uuid": uuid.uuid4(),
            "currentlocation": bytes(file_path),
            "filegrpuse": "original",
            "transfer_id": transfer_uuid,
        }
        models.File.objects.create(**kwargs)
    assert (
        _file_count == 3
    ), "Database and file objects were not returned by the generator"
    assert models.File.objects.filter(transfer_id=str(transfer_uuid)).count() == 3

    # Now the database is updated, we will still have the same file count, but
    # all objects will be returned from the database and we will have uuids.
    for _file_count, file_info in enumerate(transfer.files(None, "/objects"), 1):
        if file_info.get("%fileUUID%") == "None":
            raise AssertionError(
                f"Non-database entries returned from package.files(): {file_info}"
            )
    assert _file_count == 3

    # Finally, let's just see if the scan works for a slightly larger no.
    # files, i.e. a number with an increment slightly larger than one.
    files = ["f1", "f2", "f3", "f4", "f5"]
    for file_ in files:
        new_file = objects_path / file_
        new_file.touch()
    new_count = 0
    for _file_count, file_info in enumerate(transfer.files(None, "/objects"), 1):
        if file_info.get("%fileUUID%") == "None":
            new_count += 1
    assert new_count == 5
    assert _file_count == 8

    # Clean up state and ensure test doesn't interfere with other transfers
    # expected to be in the database, e.g. in test_queues.py.
    models.File.objects.filter(transfer_id=str(transfer_uuid)).delete()


@pytest.mark.django_db(transaction=True)
def test_package_files_with_non_ascii_names(tmp_path):
    # Create a Transfer package
    transfer_uuid = uuid.uuid4()
    transfer_path = tmp_path / f"test-transfer-{transfer_uuid}"
    transfer = Transfer.get_or_create_from_db_by_path(str(transfer_path))

    # Add a file to the transfer with non-ascii name
    transfer_path.mkdir()
    objects = transfer_path / "objects"
    objects.mkdir()
    file_ = objects / "montréal.txt"
    file_.touch()

    # Create a File model instance for the transfer file
    current_location = Path(transfer.REPLACEMENT_PATH_STRING, "objects", "montréal.txt")
    kwargs = {
        "uuid": uuid.uuid4(),
        "currentlocation": bytes(current_location),
        "filegrpuse": "original",
        "transfer_id": transfer_uuid,
    }
    models.File.objects.create(**kwargs)

    # Assert only one file is returned
    result = list(transfer.files(None, "/objects"))
    assert len(result) == 1

    # And it is the file we just created
    assert result[0]["%fileUUID%"] == str(kwargs["uuid"])
    assert result[0]["%currentLocation%"] == current_location.as_posix()
    assert result[0]["%fileGrpUse%"] == kwargs["filegrpuse"]


class TestPadDestinationFilePath:
    def test_zipfile_is_not_padded_if_does_not_exist(self, tmp_path):
        transfer_path = tmp_path / "transfer.zip"
        padded_path = _pad_destination_filepath_if_it_already_exists(transfer_path)
        assert padded_path == transfer_path

    def test_zipfile_is_padded_if_exists(self, tmp_path):
        transfer_path = tmp_path / "transfer.zip"
        transfer_path.touch()
        padded_path = _pad_destination_filepath_if_it_already_exists(transfer_path)
        assert padded_path == tmp_path / "transfer_1.zip"

    def test_dir_is_not_padded_if_does_not_exist(self, tmp_path):
        transfer_path = tmp_path / "transfer/"
        padded_path = _pad_destination_filepath_if_it_already_exists(transfer_path)
        assert padded_path == transfer_path

    def test_dir_is_padded_if_exists(self, tmp_path):
        transfer_path = tmp_path / "transfer/"
        transfer_path.mkdir()
        padded_path = _pad_destination_filepath_if_it_already_exists(transfer_path)
        assert padded_path == tmp_path / "transfer_1"


@pytest.fixture
def transfer():
    return models.Transfer.objects.create()


@pytest.fixture
def processing_dir(tmp_path):
    proc_dir = tmp_path / "processing"
    proc_dir.mkdir()
    return proc_dir


@pytest.mark.django_db(transaction=True)
class TestMoveToInternalSharedDir:
    def test_move_dir(self, tmp_path, processing_dir, transfer):
        filepath = tmp_path / "transfer"
        filepath.mkdir()

        _move_to_internal_shared_dir(str(filepath), str(processing_dir), transfer)

        transfer.refresh_from_db()
        dest_path = processing_dir / "transfer"
        assert dest_path.is_dir()
        assert Path(transfer.currentlocation) == dest_path

    def test_move_file(self, tmp_path, processing_dir, transfer):
        filepath = tmp_path / "transfer.zip"
        filepath.touch()

        _move_to_internal_shared_dir(str(filepath), str(processing_dir), transfer)

        dest_path = processing_dir / "transfer.zip"
        assert dest_path.is_file()

        transfer.refresh_from_db()
        assert Path(transfer.currentlocation) == dest_path


@pytest.mark.parametrize(
    "package_class,model_class",
    [
        (
            Transfer,
            models.Transfer,
        ),
        (
            SIP,
            models.SIP,
        ),
        (
            DIP,
            models.SIP,
        ),
    ],
)
@pytest.mark.django_db(transaction=True)
def test_package_statuses(tmp_path, package_class, model_class):
    package_id = uuid.uuid4()
    model_class.objects.create(pk=package_id)
    package = package_class(str(tmp_path), package_id)

    package.mark_as_done()

    assert model_class.objects.get(pk=package_id).status == models.PACKAGE_STATUS_DONE

    package.mark_as_processing()

    assert (
        model_class.objects.get(pk=package_id).status
        == models.PACKAGE_STATUS_PROCESSING
    )

    Package.cleanup_old_db_entries()

    assert model_class.objects.get(pk=package_id).status == models.PACKAGE_STATUS_FAILED


@pytest.mark.django_db(transaction=True)
def test_create_package(tmp_path, admin_user, settings):
    package_queue = mock.Mock(spec=PackageQueue)
    executor = mock.Mock(spec=ThreadPoolExecutor)
    workflow = mock.Mock(spec=Workflow)

    d = tmp_path / "sub"
    d.mkdir()
    (d / "tmp").mkdir()
    settings.SHARED_DIRECTORY = str(d)

    # Verify there are no existing transfers.
    assert models.Transfer.objects.count() == 0

    create_package(
        package_queue,
        executor,
        "foobar",
        "standard",
        "",
        "",
        d.as_posix(),
        "",
        admin_user.pk,
        workflow,
        auto_approve=True,
        processing_config="automated",
    )

    # Verify a transfer was added.
    assert models.Transfer.objects.count() == 1
