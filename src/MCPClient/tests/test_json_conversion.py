import json
import os
import sys

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))
from job import Job
import json_metadata_to_csv


JSON = '[{"dc.title": "This is a test item", "filename": "objects/test.txt"}]'
CSV = "filename,dc.title\nobjects/test.txt,This is a test item\n"

JSON_MULTICOLUMN = '[{"filename": "objects/test.txt", "dc.subject": ["foo", "bar", "baz"], "dc.title": "This is a test item"}]'
CSV_MULTICOLUMN = "filename,dc.subject,dc.subject,dc.subject,dc.title\nobjects/test.txt,foo,bar,baz,This is a test item\n"

JSON_NULL = '[{"dc.title": "This is a test item", "filename": "objects/test.txt", "spurious metadata": null}]'
CSV_NULL = (
    "filename,dc.title,spurious metadata\nobjects/test.txt,This is a test item,\n"
)

JSON_NESTED_NULL = '[{"dc.title": "This is a test item", "filename": "objects/test.txt", "sublist": ["first", null]}]'
CSV_NESTED_NULL = (
    "filename,dc.title,sublist,sublist\nobjects/test.txt,This is a test item,first,\n"
)

JSON_INT_VAL = '[{"dc.title": 2, "filename": "objects/test.txt"}]'
CSV_INT_VAL = "filename,dc.title\nobjects/test.txt,2\n"

JSON_KEYS_VALS_VARY = json.dumps(
    [
        {
            "dc.creator": ["Jim Bob"],
            "parts": "objects/",
            "dc.contributor": ["Sally Bean", "Nancy Pumpkin", "Mary Pea"],
            "dc.title": "A thing",
        },
        {  # note: no title
            "dc.creator": ["Frank Mills", "Sunny McRainbow"],  # one more creator
            "parts": "objects/filezilla.mfo",
            "dc.contributor": "Lucifer",  # string correlates to 3-ary list above
        },
    ]
)
KEYS_VALS_VARY_HEADERS = [
    "parts",
    "dc.contributor",
    "dc.contributor",
    "dc.contributor",
    "dc.creator",
    "dc.creator",
    "dc.title",
]
KEYS_VALS_VARY_FIRST_ROW = [
    "objects/",
    "Sally Bean",
    "Nancy Pumpkin",
    "Mary Pea",
    "Jim Bob",
    None,
    "A thing",
]
KEYS_VALS_VARY_SECOND_ROW = [
    "objects/filezilla.mfo",
    "Lucifer",
    None,
    None,
    "Frank Mills",
    "Sunny McRainbow",
    None,
]


def _list2csvrow(list_):
    return ",".join([e or "" for e in list_]) + "\n"


CSV_KEYS_VALS_VARY = "".join(
    [
        _list2csvrow(KEYS_VALS_VARY_HEADERS),
        _list2csvrow(KEYS_VALS_VARY_FIRST_ROW),
        _list2csvrow(KEYS_VALS_VARY_SECOND_ROW),
    ]
)


def test_json_csv_conversion(tmpdir):
    json_path = os.path.join(str(tmpdir), "metadata.json")
    csv_path = os.path.join(str(tmpdir), "metadata.csv")
    with open(json_path, "w") as jsonfile:
        jsonfile.write(JSON)
    job = Job("stub", "stub", ["", json_path])
    json_metadata_to_csv.call([job])
    with open(csv_path, "rU") as csvfile:
        csvdata = csvfile.read()

    assert csvdata == CSV


def test_json_csv_conversion_with_int_val(tmpdir):
    json_path = os.path.join(str(tmpdir), "metadata.json")
    csv_path = os.path.join(str(tmpdir), "metadata.csv")
    with open(json_path, "w") as jsonfile:
        jsonfile.write(JSON_INT_VAL)
    job = Job("stub", "stub", ["", json_path])
    json_metadata_to_csv.call([job])
    with open(csv_path, "rU") as csvfile:
        csvdata = csvfile.read()
    assert csvdata == CSV_INT_VAL


def test_json_csv_conversion_with_repeated_columns(tmpdir):
    json_path = os.path.join(str(tmpdir), "metadata.json")
    csv_path = os.path.join(str(tmpdir), "metadata.csv")
    with open(json_path, "w") as jsonfile:
        jsonfile.write(JSON_MULTICOLUMN)
    job = Job("stub", "stub", ["", json_path])
    json_metadata_to_csv.call([job])
    with open(csv_path, "rU") as csvfile:
        csvdata = csvfile.read()

    assert csvdata == CSV_MULTICOLUMN


def test_json_csv_with_null_data(tmpdir):
    json_path = os.path.join(str(tmpdir), "metadata.json")
    csv_path = os.path.join(str(tmpdir), "metadata.csv")
    with open(json_path, "w") as jsonfile:
        jsonfile.write(JSON_NULL)
    job = Job("stub", "stub", ["", json_path])
    json_metadata_to_csv.call([job])
    with open(csv_path, "rU") as csvfile:
        csvdata = csvfile.read()

    assert csvdata == CSV_NULL


def test_json_csv_with_nested_null_data(tmpdir):
    json_path = os.path.join(str(tmpdir), "metadata.json")
    csv_path = os.path.join(str(tmpdir), "metadata.csv")
    with open(json_path, "w") as jsonfile:
        jsonfile.write(JSON_NESTED_NULL)
    job = Job("stub", "stub", ["", json_path])
    json_metadata_to_csv.call([job])
    with open(csv_path, "rU") as csvfile:
        csvdata = csvfile.read()

    assert csvdata == CSV_NESTED_NULL


def test_json_csv_keys_vals_vary(tmpdir):
    """Test that a JSON array of objects with varying keys and varying value
    types works as expected, i.e.:

    - the headers of the CSV are the union of all attributes of all objects in
      the JSON array: ``[{'a': ...}, {'b': ...}]`` yields ``'a,b\n'``;
    - the order of the JSON object attributes does not matter;
    - a JSON object value may be an array or a string:
      ``[{'a': ['x', 'y']}, {'a': 'z'}]`` yields ``'a,a\nx,y\nz,\n'``.
    """
    json_array = json.loads(JSON_KEYS_VALS_VARY)
    headers = json_metadata_to_csv.fetch_keys(json_array)
    assert headers == KEYS_VALS_VARY_HEADERS
    first_json_obj, second_json_obj = json_array
    first_row = json_metadata_to_csv.object_to_row(
        json_metadata_to_csv.fix_encoding(first_json_obj), headers
    )
    assert first_row == KEYS_VALS_VARY_FIRST_ROW
    second_row = json_metadata_to_csv.object_to_row(
        json_metadata_to_csv.fix_encoding(second_json_obj), headers
    )
    assert second_row == KEYS_VALS_VARY_SECOND_ROW
    json_path = os.path.join(str(tmpdir), "metadata.json")
    csv_path = os.path.join(str(tmpdir), "metadata.csv")
    with open(json_path, "w") as jsonfile:
        jsonfile.write(JSON_KEYS_VALS_VARY)
    job = Job("stub", "stub", ["", json_path])
    json_metadata_to_csv.call([job])
    with open(csv_path, "rU") as csvfile:
        csvdata = csvfile.read()
    assert CSV_KEYS_VALS_VARY == csvdata
