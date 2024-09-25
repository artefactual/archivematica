import os
import shutil
import tempfile

import store_file_modification_dates
from django.test import TestCase
from django.test import override_settings
from django.utils.timezone import get_current_timezone
from main import models

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestStoreFileModification(TestCase):
    """Test store_file_modification_dates."""

    fixture_files = ["transfer.json", "files-transfer-unicode.json"]
    fixtures = [os.path.join(THIS_DIR, "fixtures", p) for p in fixture_files]

    transfer_uuid = "e95ab50f-9c84-45d5-a3ca-1b0b3f58d9b6"
    temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        transfer = models.Transfer.objects.get(uuid=self.transfer_uuid)
        transfer_path = transfer.currentlocation.replace(
            "%sharedPath%", self.temp_dir + "/"
        )
        shutil.rmtree(transfer_path)

    @override_settings(TIME_ZONE="US/Eastern")
    def test_store_file_modification_dates(self):
        """Test store_file_modification_dates.

        It should store file modification dates.
        """

        # Create files
        transfer = models.Transfer.objects.get(uuid=self.transfer_uuid)
        transfer_path = transfer.currentlocation.replace(
            "%sharedPath%", self.temp_dir + "/"
        )
        transfer.save()

        for f in models.File.objects.filter(transfer_id=self.transfer_uuid):
            path = f.currentlocation.decode().replace(
                "%transferDirectory%", transfer_path
            )
            dirname = os.path.dirname(path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(path, "wb") as f:
                f.write(path.encode("utf8"))
            os.utime(path, (1049597970, 1049597970))

        # Store file modification dates
        store_file_modification_dates.main(
            self.transfer_uuid, self.temp_dir + "/", get_current_timezone()
        )

        # Assert files have expected modification times
        expected_time = "2003-04-06 02:59:30+00:00"
        assert (
            str(
                models.File.objects.get(
                    pk="47813453-6872-442b-9d65-6515be3c5aa1"
                ).modificationtime
            )
            == expected_time
        )
        assert (
            str(
                models.File.objects.get(
                    pk="60e5c61b-14ef-4e92-89ec-9b9201e68adb"
                ).modificationtime
            )
            == expected_time
        )
        assert (
            str(
                models.File.objects.get(
                    pk="791e07ea-ad44-4315-b55b-44ec771e95cf"
                ).modificationtime
            )
            == expected_time
        )
        assert (
            str(
                models.File.objects.get(
                    pk="8a1f0b59-cf94-47ef-8078-647b77c8a147"
                ).modificationtime
            )
            == expected_time
        )
