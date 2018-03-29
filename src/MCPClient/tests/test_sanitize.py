# -*- coding: utf8
from __future__ import print_function

import os
import shutil
import sys

from django.test import TestCase

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, '../lib/clientScripts')))

from main.models import Event, File, Transfer

from job import Job
import sanitize_object_names


class TestSanitize(TestCase):
    """Test sanitizeNames, sanitize_object_names & sanitizeSipName."""

    fixture_files = ['transfer.json', 'files-transfer-unicode.json']
    fixtures = [os.path.join(THIS_DIR, 'fixtures', p) for p in fixture_files]

    transfer_uuid = 'e95ab50f-9c84-45d5-a3ca-1b0b3f58d9b6'

    def test_sanitize_object_names(self):
        """Test sanitize_object_names.

        It should sanitize files.
        It should sanitize a directory & update the files in it.
        It should handle unicode unit names.
        It should not change a name that is already sanitized.
        """
        # Create files
        transfer = Transfer.objects.get(uuid=self.transfer_uuid)
        transfer_path = transfer.currentlocation.replace('%sharedPath%currentlyProcessing', THIS_DIR)
        for f in File.objects.filter(transfer_id=self.transfer_uuid):
            path = f.currentlocation.replace('%transferDirectory%', transfer_path)
            dirname = os.path.dirname(path)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(path, 'w') as f:
                f.write(path.encode('utf8'))

        try:
            # Sanitize
            sanitize_object_names.sanitize_object_names(
                Job("stub", "stub", []),
                objectsDirectory=os.path.join(transfer_path, 'objects', '').encode('utf8'),
                sipUUID=self.transfer_uuid,
                date='2017-01-04 19:35:22',
                groupType='%transferDirectory%',
                groupSQL='transfer_id',
                sipPath=os.path.join(transfer_path, '').encode('utf8'),
            )

            # Assert files have expected name
            # Assert DB has been updated
            # Assert events created
            assert os.path.exists(os.path.join(transfer_path, 'objects', 'takusan_directories', 'need_sanitization', 'checking_here', 'evelyn_s_photo.jpg'))
            assert File.objects.get(currentlocation='%transferDirectory%objects/takusan_directories/need_sanitization/checking_here/evelyn_s_photo.jpg')
            assert Event.objects.filter(file_uuid='47813453-6872-442b-9d65-6515be3c5aa1', event_type='name cleanup').exists()

            assert os.path.exists(os.path.join(transfer_path, 'objects', 'no_sanitization/needed_here/lion.svg'))
            assert File.objects.get(currentlocation='%transferDirectory%objects/no_sanitization/needed_here/lion.svg')
            assert not Event.objects.filter(file_uuid='60e5c61b-14ef-4e92-89ec-9b9201e68adb', event_type='name cleanup').exists()

            assert os.path.exists(os.path.join(transfer_path, 'objects', 'takusan_directories', 'need_sanitization', 'checking_here', 'lionXie_Zhen_.svg'))
            assert File.objects.get(currentlocation='%transferDirectory%objects/takusan_directories/need_sanitization/checking_here/lionXie_Zhen_.svg')
            assert Event.objects.filter(file_uuid='791e07ea-ad44-4315-b55b-44ec771e95cf', event_type='name cleanup').exists()

            assert os.path.exists(os.path.join(transfer_path, 'objects', 'has_space', 'lion.svg'))
            assert File.objects.get(currentlocation='%transferDirectory%objects/has_space/lion.svg')
            assert Event.objects.filter(file_uuid='8a1f0b59-cf94-47ef-8078-647b77c8a147', event_type='name cleanup').exists()
        finally:
            # Delete files
            shutil.rmtree(transfer_path)
