from __future__ import unicode_literals

import os

import pytest

from server.processing_config import (
    get_processing_fields,
    processing_configuration_file_exists,
    processing_fields,
    StorageLocationField,
    ChainChoicesField,
    SharedChainChoicesField,
    ReplaceDictField,
)
from server.workflow import load


ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir))), "lib", "assets"
)


@pytest.fixture
def _workflow():
    path = os.path.join(ASSETS_DIR, "workflow.json")
    with open(path) as fp:
        return load(fp)


def test_get_processing_fields(mocker, _workflow):
    mocker.patch("storageService.get_location", return_value=[])

    fields = get_processing_fields(_workflow)

    assert len(fields) == len(processing_fields)


def test_storage_location_field(mocker, _workflow):
    def mocked_get_location(purpose):
        return [
            {
                "resource_uri": "/api/v2/location/e1452470-a51c-4fd7-b2c1-b217b7dbfa11/",
                "relative_path": "mnt/disk1",
                "description": "Description %s" % purpose,
            }
        ]

    mocker.patch("storageService.get_location", side_effect=mocked_get_location)

    mocker.patch(
        "server.processing_config.processing_fields",
        new=[
            StorageLocationField(
                link_id="b320ce81-9982-408a-9502-097d0daa48fa",
                name="store_aip_location",
                purpose="AS",
            ),
            StorageLocationField(
                link_id="cd844b6e-ab3c-4bc6-b34f-7103f88715de",
                name="store_dip_location",
                purpose="DS",
            ),
        ],
    )

    assert get_processing_fields(_workflow) == [
        {
            "choices": [
                {
                    "applies_to": [
                        (
                            "b320ce81-9982-408a-9502-097d0daa48fa",
                            "/api/v2/location/default/AS/",
                            "Default location",
                        )
                    ],
                    "value": "/api/v2/location/default/AS/",
                    "label": "Default location",
                },
                {
                    "applies_to": [
                        (
                            "b320ce81-9982-408a-9502-097d0daa48fa",
                            "/api/v2/location/e1452470-a51c-4fd7-b2c1-b217b7dbfa11/",
                            "Description AS",
                        )
                    ],
                    "value": "/api/v2/location/e1452470-a51c-4fd7-b2c1-b217b7dbfa11/",
                    "label": "Description AS",
                },
            ],
            "id": "b320ce81-9982-408a-9502-097d0daa48fa",
            "name": "store_aip_location",
            "label": "Store AIP location",
        },
        {
            "choices": [
                {
                    "applies_to": [
                        (
                            "cd844b6e-ab3c-4bc6-b34f-7103f88715de",
                            "/api/v2/location/default/DS/",
                            "Default location",
                        )
                    ],
                    "value": "/api/v2/location/default/DS/",
                    "label": "Default location",
                },
                {
                    "applies_to": [
                        (
                            "cd844b6e-ab3c-4bc6-b34f-7103f88715de",
                            "/api/v2/location/e1452470-a51c-4fd7-b2c1-b217b7dbfa11/",
                            "Description DS",
                        )
                    ],
                    "value": "/api/v2/location/e1452470-a51c-4fd7-b2c1-b217b7dbfa11/",
                    "label": "Description DS",
                },
            ],
            "id": "cd844b6e-ab3c-4bc6-b34f-7103f88715de",
            "name": "store_dip_location",
            "label": "Store DIP location",
        },
    ]


def test_replace_dict_field(mocker, _workflow):
    mocker.patch(
        "server.processing_config.processing_fields",
        new=[
            ReplaceDictField(
                link_id="f09847c2-ee51-429a-9478-a860477f6b8d",
                name="select_format_id_tool_transfer",
            ),
            ReplaceDictField(
                link_id="f19926dd-8fb5-4c79-8ade-c83f61f55b40", name="delete_packages"
            ),
        ],
    )

    assert get_processing_fields(_workflow) == [
        {
            "choices": [
                {
                    "applies_to": [
                        (
                            "f09847c2-ee51-429a-9478-a860477f6b8d",
                            "d97297c7-2b49-4cfe-8c9f-0613d63ed763",
                            "Yes",
                        )
                    ],
                    "value": "d97297c7-2b49-4cfe-8c9f-0613d63ed763",
                    "label": "Yes",
                },
                {
                    "applies_to": [
                        (
                            "f09847c2-ee51-429a-9478-a860477f6b8d",
                            "1f77af0a-2f7a-468f-af8c-653a9e61ca4f",
                            "No",
                        )
                    ],
                    "value": "1f77af0a-2f7a-468f-af8c-653a9e61ca4f",
                    "label": "No",
                },
            ],
            "id": "f09847c2-ee51-429a-9478-a860477f6b8d",
            "name": "select_format_id_tool_transfer",
            "label": "Do you want to perform file format identification?",
        },
        {
            "choices": [
                {
                    "applies_to": [
                        (
                            "f19926dd-8fb5-4c79-8ade-c83f61f55b40",
                            "85b1e45d-8f98-4cae-8336-72f40e12cbef",
                            "Yes",
                        )
                    ],
                    "value": "85b1e45d-8f98-4cae-8336-72f40e12cbef",
                    "label": "Yes",
                },
                {
                    "applies_to": [
                        (
                            "f19926dd-8fb5-4c79-8ade-c83f61f55b40",
                            "72e8443e-a8eb-49a8-ba5f-76d52f960bde",
                            "No",
                        )
                    ],
                    "value": "72e8443e-a8eb-49a8-ba5f-76d52f960bde",
                    "label": "No",
                },
            ],
            "id": "f19926dd-8fb5-4c79-8ade-c83f61f55b40",
            "name": "delete_packages",
            "label": "Delete package after extraction?",
        },
    ]


def test_chain_choices_field(mocker, _workflow):
    mocker.patch(
        "server.processing_config.processing_fields",
        new=[
            ChainChoicesField(
                link_id="eeb23509-57e2-4529-8857-9d62525db048", name="reminder"
            ),
            ChainChoicesField(
                link_id="cb8e5706-e73f-472f-ad9b-d1236af8095f",
                name="normalize",
                ignored_choices=["Reject SIP"],
                find_duplicates="Normalize",
            ),
        ],
    )

    assert get_processing_fields(_workflow) == [
        {
            "choices": [
                {
                    "applies_to": [
                        (
                            "eeb23509-57e2-4529-8857-9d62525db048",
                            "5727faac-88af-40e8-8c10-268644b0142d",
                            "Continue",
                        )
                    ],
                    "value": "5727faac-88af-40e8-8c10-268644b0142d",
                    "label": "Continue",
                }
            ],
            "id": "eeb23509-57e2-4529-8857-9d62525db048",
            "name": "reminder",
            "label": "Reminder: add metadata if desired",
        },
        {
            "choices": [
                {
                    "applies_to": [
                        (
                            "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                            "b93cecd4-71f2-4e28-bc39-d32fd62c5a94",
                            "Normalize for preservation and access",
                        )
                    ],
                    "value": "b93cecd4-71f2-4e28-bc39-d32fd62c5a94",
                    "label": "Normalize for preservation and access",
                },
                {
                    "applies_to": [
                        (
                            "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                            "612e3609-ce9a-4df6-a9a3-63d634d2d934",
                            "Normalize for preservation",
                        ),
                        (
                            "7509e7dc-1e1b-4dce-8d21-e130515fce73",
                            "612e3609-ce9a-4df6-a9a3-63d634d2d934",
                            "Normalize for preservation",
                        ),
                    ],
                    "value": "612e3609-ce9a-4df6-a9a3-63d634d2d934",
                    "label": "Normalize for preservation",
                },
                {
                    "applies_to": [
                        (
                            "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                            "fb7a326e-1e50-4b48-91b9-4917ff8d0ae8",
                            "Normalize for access",
                        )
                    ],
                    "value": "fb7a326e-1e50-4b48-91b9-4917ff8d0ae8",
                    "label": "Normalize for access",
                },
                {
                    "applies_to": [
                        (
                            "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                            "e600b56d-1a43-4031-9d7c-f64f123e5662",
                            "Normalize service files for access",
                        )
                    ],
                    "value": "e600b56d-1a43-4031-9d7c-f64f123e5662",
                    "label": "Normalize service files for access",
                },
                {
                    "applies_to": [
                        (
                            "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                            "c34bd22a-d077-4180-bf58-01db35bdb644",
                            "Normalize manually",
                        )
                    ],
                    "value": "c34bd22a-d077-4180-bf58-01db35bdb644",
                    "label": "Normalize manually",
                },
                {
                    "applies_to": [
                        (
                            "cb8e5706-e73f-472f-ad9b-d1236af8095f",
                            "89cb80dd-0636-464f-930d-57b61e3928b2",
                            "Do not normalize",
                        ),
                        (
                            "7509e7dc-1e1b-4dce-8d21-e130515fce73",
                            "e8544c5e-9cbb-4b8f-a68b-6d9b4d7f7362",
                            "Do not normalize",
                        ),
                    ],
                    "value": "89cb80dd-0636-464f-930d-57b61e3928b2",
                    "label": "Do not normalize",
                },
            ],
            "id": "cb8e5706-e73f-472f-ad9b-d1236af8095f",
            "name": "normalize",
            "label": "Normalize",
        },
    ]


def test_shared_choices_field(mocker, _workflow):
    mocker.patch(
        "server.processing_config.processing_fields",
        new=[
            SharedChainChoicesField(
                link_id="856d2d65-cd25-49fa-8da9-cabb78292894",
                name="virus_scanning",
                related_links=[
                    "1dad74a2-95df-4825-bbba-dca8b91d2371",
                    "7e81f94e-6441-4430-a12d-76df09181b66",
                    "390d6507-5029-4dae-bcd4-ce7178c9b560",
                    "97a5ddc0-d4e0-43ac-a571-9722405a0a9b",
                ],
            )
        ],
    )

    assert get_processing_fields(_workflow) == [
        {
            "id": "856d2d65-cd25-49fa-8da9-cabb78292894",
            "label": "Do you want to scan for viruses in metadata?",
            "name": "virus_scanning",
            "choices": [
                {
                    "value": "6e431096-c403-4cbf-a59a-a26e86be54a8",
                    "label": "Yes",
                    "applies_to": [
                        (
                            "856d2d65-cd25-49fa-8da9-cabb78292894",
                            "6e431096-c403-4cbf-a59a-a26e86be54a8",
                            "Yes",
                        ),
                        (
                            "1dad74a2-95df-4825-bbba-dca8b91d2371",
                            "1ac7d792-b63f-46e0-9945-d48d9e5c02c9",
                            "Yes",
                        ),
                        (
                            "7e81f94e-6441-4430-a12d-76df09181b66",
                            "97be337c-ff27-4869-bf63-ef1abc9df15d",
                            "Yes",
                        ),
                        (
                            "390d6507-5029-4dae-bcd4-ce7178c9b560",
                            "34944d4f-762e-4262-8c79-b9fd48521ca0",
                            "Yes",
                        ),
                        (
                            "97a5ddc0-d4e0-43ac-a571-9722405a0a9b",
                            "3e8c0c39-3f30-4c9b-a449-85eef1b2a458",
                            "Yes",
                        ),
                    ],
                },
                {
                    "value": "63767e4b-9ce8-4fe2-8724-65cc1f763de0",
                    "label": "No",
                    "applies_to": [
                        (
                            "856d2d65-cd25-49fa-8da9-cabb78292894",
                            "63767e4b-9ce8-4fe2-8724-65cc1f763de0",
                            "No",
                        ),
                        (
                            "1dad74a2-95df-4825-bbba-dca8b91d2371",
                            "697c0883-798d-4af7-b8b6-101c7f709cd5",
                            "No",
                        ),
                        (
                            "7e81f94e-6441-4430-a12d-76df09181b66",
                            "77355172-b437-4324-9dcc-e2607ad27cb1",
                            "No",
                        ),
                        (
                            "390d6507-5029-4dae-bcd4-ce7178c9b560",
                            "63be6081-bee8-4cf5-a453-91893e31940f",
                            "No",
                        ),
                        (
                            "97a5ddc0-d4e0-43ac-a571-9722405a0a9b",
                            "7f5244fe-590b-4e38-beaf-0cf1ccb9e71b",
                            "No",
                        ),
                    ],
                },
            ],
        }
    ]


def test_processing_configuration_file_exists_with_None():
    assert not processing_configuration_file_exists(None)


def test_processing_configuration_file_exists_with_existent_file(mocker):
    mocker.patch("os.path.isfile", return_value=True)
    assert processing_configuration_file_exists("defaultProcessingMCP.xml")


def test_processing_configuration_file_exists_with_nonexistent_file(mocker):
    mocker.patch("os.path.isfile", return_value=False)
    logger = mocker.patch("server.processing_config.logger")
    assert not processing_configuration_file_exists("bogus.xml")
    logger.debug.assert_called_once_with(
        "Processing configuration file for %s does not exist", "bogus.xml"
    )
