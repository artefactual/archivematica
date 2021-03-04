# -*- coding: utf-8 -*-
from __future__ import absolute_import

import bagit
from mock import patch

import archivematicaFunctions as am


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
    # Test returned value against expected
    size_on_disk = am.walk_dir(bag_dir.strpath)
    size = am.get_bag_size(bag, bag_dir.strpath)
    assert size == size_on_disk
    # Verify directory was walked
    with patch("archivematicaFunctions.os") as mock_os:
        am.get_bag_size(bag, bag_dir.strpath)
        mock_os.path.getsize.assert_called()


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
