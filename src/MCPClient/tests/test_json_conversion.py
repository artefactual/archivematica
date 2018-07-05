import os
import sys

JSON = '[{"dc.title": "This is a test item", "filename": "objects/test.txt"}]'
CSV = 'filename,dc.title\r\nobjects/test.txt,This is a test item\r\n'

JSON_MULTICOLUMN = '[{"filename": "objects/test.txt", "dc.subject": ["foo", "bar", "baz"], "dc.title": "This is a test item"}]'
CSV_MULTICOLUMN = 'filename,dc.subject,dc.subject,dc.subject,dc.title\r\nobjects/test.txt,foo,bar,baz,This is a test item\r\n'

JSON_NULL = '[{"dc.title": "This is a test item", "filename": "objects/test.txt", "spurious metadata": null}]'
CSV_NULL = 'filename,dc.title,spurious metadata\r\nobjects/test.txt,This is a test item,\r\n'

JSON_NESTED_NULL = '[{"dc.title": "This is a test item", "filename": "objects/test.txt", "sublist": ["first", null]}]'
CSV_NESTED_NULL = 'filename,dc.title,sublist,sublist\r\nobjects/test.txt,This is a test item,first,\r\n'

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(
    os.path.abspath(os.path.join(THIS_DIR, '../lib/clientScripts')))

from job import Job
import json_metadata_to_csv


def test_json_csv_conversion(tmpdir):
    json_path = os.path.join(str(tmpdir), 'metadata.json')
    csv_path = os.path.join(str(tmpdir), 'metadata.csv')
    with open(json_path, 'w') as jsonfile:
        jsonfile.write(JSON)
    job = Job("stub", "stub", ["", json_path])
    json_metadata_to_csv.call([job])
    with open(csv_path) as csvfile:
        csvdata = csvfile.read()

    assert csvdata == CSV


def test_json_csv_conversion_with_repeated_columns(tmpdir):
    json_path = os.path.join(str(tmpdir), 'metadata.json')
    csv_path = os.path.join(str(tmpdir), 'metadata.csv')
    with open(json_path, 'w') as jsonfile:
        jsonfile.write(JSON_MULTICOLUMN)
    job = Job("stub", "stub", ["", json_path])
    json_metadata_to_csv.call([job])
    with open(csv_path) as csvfile:
        csvdata = csvfile.read()

    assert csvdata == CSV_MULTICOLUMN


def test_json_csv_with_null_data(tmpdir):
    json_path = os.path.join(str(tmpdir), 'metadata.json')
    csv_path = os.path.join(str(tmpdir), 'metadata.csv')
    with open(json_path, 'w') as jsonfile:
        jsonfile.write(JSON_NULL)
    job = Job("stub", "stub", ["", json_path])
    json_metadata_to_csv.call([job])
    with open(csv_path) as csvfile:
        csvdata = csvfile.read()

    assert csvdata == CSV_NULL


def test_json_csv_with_nested_null_data(tmpdir):
    json_path = os.path.join(str(tmpdir), 'metadata.json')
    csv_path = os.path.join(str(tmpdir), 'metadata.csv')
    with open(json_path, 'w') as jsonfile:
        jsonfile.write(JSON_NESTED_NULL)
    job = Job("stub", "stub", ["", json_path])
    json_metadata_to_csv.call([job])
    with open(csv_path) as csvfile:
        csvdata = csvfile.read()

    assert csvdata == CSV_NESTED_NULL
