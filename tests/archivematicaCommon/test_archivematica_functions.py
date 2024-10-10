from unittest.mock import patch

import archivematicaFunctions as am
import bagit
import pytest


def test_find_mets_file_match(tmp_path):
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    mets_file = metadata_dir / "METS.1.xml"
    mets_file.touch()
    assert am.find_mets_file(str(tmp_path)) == str(tmp_path / "metadata" / "METS.1.xml")


def test_find_mets_file_ambiguous_mets_file(tmp_path):
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    for i in range(3):
        mets_file = metadata_dir / (f"METS.{i}.xml")
        mets_file.touch()

    with pytest.raises(
        OSError, match=f"Multiple METS files found in {tmp_path}/metadata"
    ):
        am.find_mets_file(str(tmp_path))


def test_find_mets_file_no_mets_file(tmp_path):
    with pytest.raises(OSError, match=f"No METS file found in {tmp_path}/metadata"):
        am.find_mets_file(str(tmp_path))


def test_get_bag_size(tmpdir):
    """Test that get_bag_size uses bag-info Payload-Oxum when present."""
    # Set up test data
    bag_dir = tmpdir.mkdir("bag")
    data_file = bag_dir.join("file.txt")
    data_file.write("Lorem ipsum")
    bag = bagit.make_bag(bag_dir.strpath)
    # Replace Payload-Oxum with incorrect arbitrary value
    size_oxum = "105621.12"
    bag.info["Payload-Oxum"] = size_oxum
    bag.save()
    # Assertions
    with patch("archivematicaFunctions.os") as mock_os:
        # Test returned value against expected
        size = am.get_bag_size(bag, bag_dir.strpath)
        assert size == int(size_oxum.split(".")[0])
        # Verify directory was not walked
        mock_os.path.getsize.assert_not_called()


def test_get_bag_size_bag_missing_oxum(tmpdir):
    """Test that get_bag_size uses walk if bag-info Payload-Oxum is missing."""
    # Set up test data
    bag_dir = tmpdir.mkdir("bag")
    data_file = bag_dir.join("file.txt")
    data_file.write("Lorem ipsum")
    bag = bagit.make_bag(bag_dir.strpath)
    # Remove Payload-Oxum from bag.info
    del bag.info["Payload-Oxum"]
    bag.save()
    # Test returned value against expected)
    size_on_disk = am.walk_dir(bag_dir.strpath)
    size = am.get_bag_size(bag, bag_dir.strpath)
    assert size == size_on_disk
    # Verify directory was walked
    with patch("os.path") as mock_os_path:
        am.get_bag_size(bag, bag_dir.strpath)
        mock_os_path.getsize.assert_called()


def test_package_name_from_path():
    """Test that package_name_from_path returns expected results."""
    test_packages = [
        {
            "current_path": "/dev/null/tar_gz_package-473a9398-0024-4804-81da-38946040c8af.tar.gz",
            "package_name": "tar_gz_package-473a9398-0024-4804-81da-38946040c8af",
            "package_name_without_uuid": "tar_gz_package",
        },
        {
            "current_path": "/dev/null/a.bz2.tricky.7z.package-473a9398-0024-4804-81da-38946040c8af.7z",
            "package_name": "a.bz2.tricky.7z.package-473a9398-0024-4804-81da-38946040c8af",
            "package_name_without_uuid": "a.bz2.tricky.7z.package",
        },
        {
            "current_path": "/dev/null/uncompressed_package-3e0b3093-23ea-4937-9e2a-1fd806bb39b9",
            "package_name": "uncompressed_package-3e0b3093-23ea-4937-9e2a-1fd806bb39b9",
            "package_name_without_uuid": "uncompressed_package",
        },
    ]
    for test_package in test_packages:
        current_path = test_package["current_path"]

        package_name = am.package_name_from_path(current_path)
        assert package_name == test_package["package_name"]

        package_name_with_uuid = am.package_name_from_path(
            current_path, remove_uuid_suffix=False
        )
        assert package_name_with_uuid == test_package["package_name"]

        package_name_without_uuid = am.package_name_from_path(
            current_path, remove_uuid_suffix=True
        )
        assert package_name_without_uuid == test_package["package_name_without_uuid"]


def test_get_oidc_secondary_providers_ignores_provider_if_client_id_and_secret_are_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OIDC_RP_CLIENT_ID_FOO", "foo-client-id")
    monkeypatch.setenv("OIDC_RP_CLIENT_SECRET_FOO", "foo-client-secret")
    monkeypatch.setenv("OIDC_RP_CLIENT_ID_BAR", "bar-client-id")
    monkeypatch.setenv("OIDC_RP_CLIENT_SECRET_BAZ", "foo-secret")

    assert am.get_oidc_secondary_providers(["FOO", "BAR", "BAZ"]) == {
        "FOO": {
            "OIDC_OP_AUTHORIZATION_ENDPOINT": "",
            "OIDC_OP_JWKS_ENDPOINT": "",
            "OIDC_OP_LOGOUT_ENDPOINT": "",
            "OIDC_OP_TOKEN_ENDPOINT": "",
            "OIDC_OP_USER_ENDPOINT": "",
            "OIDC_RP_CLIENT_ID": "foo-client-id",
            "OIDC_RP_CLIENT_SECRET": "foo-client-secret",
        }
    }


def test_get_oidc_secondary_providers_strips_provider_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OIDC_RP_CLIENT_ID_FOO", "foo-client-id")
    monkeypatch.setenv("OIDC_RP_CLIENT_SECRET_FOO", "foo-client-secret")
    monkeypatch.setenv("OIDC_RP_CLIENT_ID_BAR", "bar-client-id")
    monkeypatch.setenv("OIDC_RP_CLIENT_SECRET_BAR", "bar-client-secret")

    assert am.get_oidc_secondary_providers(["  FOO", " BAR  "]) == {
        "FOO": {
            "OIDC_OP_AUTHORIZATION_ENDPOINT": "",
            "OIDC_OP_JWKS_ENDPOINT": "",
            "OIDC_OP_LOGOUT_ENDPOINT": "",
            "OIDC_OP_TOKEN_ENDPOINT": "",
            "OIDC_OP_USER_ENDPOINT": "",
            "OIDC_RP_CLIENT_ID": "foo-client-id",
            "OIDC_RP_CLIENT_SECRET": "foo-client-secret",
        },
        "BAR": {
            "OIDC_OP_AUTHORIZATION_ENDPOINT": "",
            "OIDC_OP_JWKS_ENDPOINT": "",
            "OIDC_OP_LOGOUT_ENDPOINT": "",
            "OIDC_OP_TOKEN_ENDPOINT": "",
            "OIDC_OP_USER_ENDPOINT": "",
            "OIDC_RP_CLIENT_ID": "bar-client-id",
            "OIDC_RP_CLIENT_SECRET": "bar-client-secret",
        },
    }


def test_get_oidc_secondary_providers_capitalizes_provider_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OIDC_RP_CLIENT_ID_FOO", "foo-client-id")
    monkeypatch.setenv("OIDC_RP_CLIENT_SECRET_FOO", "foo-client-secret")
    monkeypatch.setenv("OIDC_RP_CLIENT_ID_BAR", "bar-client-id")
    monkeypatch.setenv("OIDC_RP_CLIENT_SECRET_BAR", "bar-client-secret")

    assert am.get_oidc_secondary_providers(["fOo", "bar"]) == {
        "FOO": {
            "OIDC_OP_AUTHORIZATION_ENDPOINT": "",
            "OIDC_OP_JWKS_ENDPOINT": "",
            "OIDC_OP_LOGOUT_ENDPOINT": "",
            "OIDC_OP_TOKEN_ENDPOINT": "",
            "OIDC_OP_USER_ENDPOINT": "",
            "OIDC_RP_CLIENT_ID": "foo-client-id",
            "OIDC_RP_CLIENT_SECRET": "foo-client-secret",
        },
        "BAR": {
            "OIDC_OP_AUTHORIZATION_ENDPOINT": "",
            "OIDC_OP_JWKS_ENDPOINT": "",
            "OIDC_OP_LOGOUT_ENDPOINT": "",
            "OIDC_OP_TOKEN_ENDPOINT": "",
            "OIDC_OP_USER_ENDPOINT": "",
            "OIDC_RP_CLIENT_ID": "bar-client-id",
            "OIDC_RP_CLIENT_SECRET": "bar-client-secret",
        },
    }
