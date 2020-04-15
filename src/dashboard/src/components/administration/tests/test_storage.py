# -*- coding: utf-8 -*-
from __future__ import absolute_import

import mock

from django.test import TestCase

from components import helpers


class TestStorage(TestCase):
    fixtures = ["test_user"]

    def setUp(self):
        self.client.login(username="test", password="test")
        self.url = "/administration/storage/"
        helpers.set_setting("dashboard_uuid", "test-uuid")

    @mock.patch(
        "components.administration.views.storage_service.get_location",
        side_effect=Exception(),
    )
    def test_ss_connection_fail(self, mock_get_location):
        response = self.client.get(self.url)
        self.assertIn("Error retrieving locations", response.content.decode("utf8"))

    @mock.patch("components.administration.views.storage_service.get_location")
    def test_success(self, mock_get_location):
        mock_get_location.return_value = [
            {
                "uuid": "821d8b48-8b19-42ae-9956-df1d749c21a2",
                "pipeline": ["/api/v2/pipeline/fe263021-f1d7-4a25-b691-df80da5ee048/"],
                "used": "0",
                "description": None,
                "space": "/api/v2/space/85a6a5af-8b99-4e04-83da-4d1d712f1115/",
                "enabled": True,
                "quota": None,
                "relative_path": "var/archivematica/sharedDirectory/",
                "purpose": "CP",
                "path": "/var/archivematica/sharedDirectory",
                "resource_uri": "/api/v2/location/821d8b48-8b19-42ae-9956-df1d749c21a2/",
            },
            {
                "uuid": "bad1cfd5-a67a-4791-b4a9-43590727d25f",
                "pipeline": ["/api/v2/pipeline/fe263021-f1d7-4a25-b691-df80da5ee048/"],
                "used": "0",
                "description": "",
                "space": "/api/v2/space/85a6a5af-8b99-4e04-83da-4d1d712f1115/",
                "enabled": True,
                "quota": None,
                "relative_path": "home",
                "purpose": "TS",
                "path": "/home",
                "resource_uri": "/api/v2/location/bad1cfd5-a67a-4791-b4a9-43590727d25f/",
            },
            {
                "uuid": "1232e1d5-a67a-4791-b4a9-4359072747bf",
                "pipeline": ["/api/v2/pipeline/fe263021-f1d7-4a25-b691-df80da5ee048/"],
                "used": "0",
                "description": "",
                "space": "/api/v2/space/85a6a5af-8b99-4e04-83da-4d1d712f1115/",
                "enabled": False,
                "quota": None,
                "relative_path": "home",
                "purpose": "TS",
                "path": "/home",
                "resource_uri": "/api/v2/location/1232e1d5-a67a-4791-b4a9-4359072747bf/",
            },
            {
                "uuid": "817f9ef7-dcf7-450d-bfeb-7dba00abedd5",
                "pipeline": ["/api/v2/pipeline/fe263021-f1d7-4a25-b691-df80da5ee048/"],
                "used": "5368709120",
                "description": "Store AIP in standard Archivematica Directory",
                "space": "/api/v2/space/85a6a5af-8b99-4e04-83da-4d1d712f1115/",
                "enabled": True,
                "quota": "10737418240",
                "relative_path": "var/archivematica/sharedDirectory/www/AIPsStore",
                "purpose": "AS",
                "path": "/var/archivematica/sharedDirectory/www/AIPsStore",
                "resource_uri": "/api/v2/location/817f9ef7-dcf7-450d-bfeb-7dba00abedd5/",
            },
            {
                "uuid": "6e4cf229-e614-436d-9055-839dfe3145a6",
                "pipeline": ["/api/v2/pipeline/fe263021-f1d7-4a25-b691-df80da5ee048/"],
                "used": "0",
                "description": "Store DIP in standard Archivematica Directory",
                "space": "/api/v2/space/85a6a5af-8b99-4e04-83da-4d1d712f1115/",
                "enabled": True,
                "quota": None,
                "relative_path": "var/archivematica/sharedDirectory/www/DIPsStore",
                "purpose": "DS",
                "path": "/var/archivematica/sharedDirectory/www/DIPsStore",
                "resource_uri": "/api/v2/location/6e4cf229-e614-436d-9055-839dfe3145a6/",
            },
            {
                "uuid": "8ace39fe-d52e-4b84-a8ab-3c68fdfea829",
                "pipeline": ["/api/v2/pipeline/fe263021-f1d7-4a25-b691-df80da5ee048/"],
                "used": "0",
                "description": "Default transfer backlog",
                "space": "/api/v2/space/85a6a5af-8b99-4e04-83da-4d1d712f1115/",
                "enabled": True,
                "quota": None,
                "relative_path": "var/archivematica/sharedDirectory/www/AIPsStore/transferBacklog",
                "purpose": "BL",
                "path": "/var/archivematica/sharedDirectory/www/AIPsStore/transferBacklog",
                "resource_uri": "/api/v2/location/8ace39fe-d52e-4b84-a8ab-3c68fdfea829/",
            },
            {
                "uuid": "b3333b2a-5f3d-4c32-86b4-d334ff80c111",
                "pipeline": ["/api/v2/pipeline/fe263021-f1d7-4a25-b691-df80da5ee048/"],
                "used": "0",
                "description": "Default AIP recovery",
                "space": "/api/v2/space/85a6a5af-8b99-4e04-83da-4d1d712f1115/",
                "enabled": True,
                "quota": None,
                "relative_path": "var/archivematica/storage_service/recover",
                "purpose": "AR",
                "path": "/var/archivematica/storage_service/recover",
                "resource_uri": "/api/v2/location/b3333b2a-5f3d-4c32-86b4-d334ff80c111/",
            },
        ]
        response = self.client.get(self.url)
        locations = response.context["locations"]
        # The currently processing and AIP recovery locations are removed
        self.assertFalse([loc for loc in locations if loc["purpose"] == "CP"])
        self.assertFalse([loc for loc in locations if loc["purpose"] == "AR"])
        # Disabled location is removed
        self.assertFalse(
            [
                loc
                for loc in locations
                if loc["uuid"] == "1232e1d5-a67a-4791-b4a9-4359072747bf"
            ]
        )
        # Only two locations show usage
        self.assertEqual(len([loc for loc in locations if loc["show_usage"]]), 2)
        # One of them has an unlimited quota set
        self.assertEqual(
            len([loc for loc in locations if loc["quota"] == "unlimited"]), 1
        )
        # The other, 5 of 10 GB used (formated and in unicode)
        used_loc = [
            loc
            for loc in locations
            if loc["uuid"] == "817f9ef7-dcf7-450d-bfeb-7dba00abedd5"
        ]
        self.assertEqual(used_loc[0]["quota"], u"10.0\xa0GB")
        self.assertEqual(used_loc[0]["used"], u"5.0\xa0GB")
        # Purpose is formatted
        self.assertEqual(used_loc[0]["purpose"], "AIP Storage")
