#!/usr/bin/env python
"""
Tests for CSV metadata management on the METS creation process
"""

from unittest import mock

from archivematicaCreateMETSMetadataCSV import parseMetadataCSV

content_when_value_has_empty_strings = """
filename,dc.title,dc.type,dc.type,Other metadata
objects/foo.jpg,Foo,Photograph,,Taken on a sunny day
objects/bar/,Bar,Photograph,Still Image,All taken on a rainy day
""".strip()


content_with_no_value = """
filename,dc.title,dc.type,dc.type,Other metadata
objects/foo.jpg,Foo,Photograph,,Taken on a sunny day
objects/bar/,,Photograph,Still Image,All taken on a rainy day
""".strip()


def test_parseMetadataCSV_with_null_values(tmp_path):
    """Applying testcases in parseMetadataCSV function"""
    job = mock.Mock()
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "metadata.csv"
    p.write_text(content_when_value_has_empty_strings)
    result = parseMetadataCSV(job, p)
    assert (result["objects/foo.jpg"]["dc.type"]) == ["Photograph"]
    assert (result["objects/bar"]["dc.type"]) == ["Photograph", "Still Image"]


def test_parseMetadataCSV_with_column_has_no_values(tmp_path):
    """Applying testcases in parseMetadataCSV function"""
    job = mock.Mock()
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "metadata.csv"
    p.write_text(content_with_no_value)
    result = parseMetadataCSV(job, p)
    assert "dc.title" not in result["objects/bar"]
