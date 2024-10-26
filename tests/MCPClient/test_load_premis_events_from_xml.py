import os
import pathlib
import sys
import uuid
from unittest import mock

import load_premis_events_from_xml
import pytest
from lxml import etree
from main.models import Agent
from main.models import Event
from main.models import File

THIS_DIR = pathlib.Path(__file__).parent


@pytest.fixture()
def xsd_path():
    return os.path.abspath(
        os.path.join(THIS_DIR, "../../src/MCPClient/lib/assets/premis/premis.xsd")
    )


@pytest.fixture()
def invalid_xsd_path(tmp_path):
    file_path = tmp_path / "invalid.xsd"
    file_path.write_text("""<?xml version="1.0" encoding="UTF-8"?><xsd></xsd>""")
    return file_path


invalid_xml = """
<?xml version="1.0" encoding="UTF-8"?>
<premis:premis xmlns:premis="http://www.loc.gov/premis/v3" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/premis/v3 https://www.loc.gov/standards/premis/premis.xsd" version="3.0">
</premis:premis>
"""
invalid_xsd = """
<?xml version="1.0" encoding="UTF-8"?>
<xsd></xsd>
"""


@pytest.fixture(
    params=[
        {
            "xml": invalid_xml,
            "expected_error": "Element '{http://www.loc.gov/premis/v3}premis': Missing child element(s). Expected is ( {http://www.loc.gov/premis/v3}object )., line 2",
        }
    ],
    ids=["invalid_xml"],
)
def invalid_xml_path(request, tmp_path):
    file_path = tmp_path / "invalid.xml"
    file_path.write_text(request.param["xml"].strip())
    return {"path": file_path, "expected_error": request.param["expected_error"]}


simple_xml = """
<?xml version="1.0" encoding="UTF-8"?>
<premis:premis xmlns:premis="http://www.loc.gov/premis/v3" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/premis/v3 https://www.loc.gov/standards/premis/premis.xsd" version="3.0">
  <premis:object xsi:type="premis:file">
    <premis:objectIdentifier>
      <premis:objectIdentifierType>hdl</premis:objectIdentifierType>
      <premis:objectIdentifierValue>hdl:1</premis:objectIdentifierValue>
    </premis:objectIdentifier>
    <premis:objectCharacteristics>
      <premis:format>
        <premis:formatDesignation>
          <premis:formatName>Exchangeable Image File Format (Compressed)</premis:formatName>
          <premis:formatVersion>2.2.1</premis:formatVersion>
        </premis:formatDesignation>
      </premis:format>
    </premis:objectCharacteristics>
    <premis:originalName>objects/1</premis:originalName>
  </premis:object>
  <premis:event>
    <premis:eventIdentifier>
      <premis:eventIdentifierType>NRI Repository Event ID</premis:eventIdentifierType>
      <premis:eventIdentifierValue>NRI-016</premis:eventIdentifierValue>
    </premis:eventIdentifier>
    <premis:eventType>ingestion</premis:eventType>
    <premis:eventDateTime>2019-07-04T22:46:07.773391+00:00</premis:eventDateTime>
    <premis:linkingAgentIdentifier>
      <premis:linkingAgentIdentifierType>repository code</premis:linkingAgentIdentifierType>
      <premis:linkingAgentIdentifierValue>NRI</premis:linkingAgentIdentifierValue>
    </premis:linkingAgentIdentifier>
  </premis:event>
  <premis:agent>
    <premis:agentIdentifier>
      <premis:agentIdentifierType>repository code</premis:agentIdentifierType>
      <premis:agentIdentifierValue>NRI</premis:agentIdentifierValue>
    </premis:agentIdentifier>
    <premis:agentName>Not a Real Institution</premis:agentName>
    <premis:agentType>organization</premis:agentType>
  </premis:agent>
</premis:premis>
"""


@pytest.fixture()
def simple_xml_path(tmp_path):
    file_path = tmp_path / "simple.xml"
    file_path.write_text(simple_xml.strip())
    return file_path


@mock.patch("os.path.isfile", return_value=False)
def test_get_premis_schema_with_nonexistent_path(is_file):
    printfn = mock.Mock()
    result = load_premis_events_from_xml.get_premis_schema("mock/xsd/path", printfn)
    printfn.assert_called_once_with(
        "The PREMIS XML schema asset mock/xsd/path is unavailable", file=sys.stderr
    )
    assert result is None


def test_get_premis_schema_with_invalid_schema(invalid_xsd_path):
    printfn = mock.Mock()
    result = load_premis_events_from_xml.get_premis_schema(
        invalid_xsd_path.as_posix(), printfn
    )
    printfn.assert_called_once_with(
        f"Could not parse the PREMIS XML schema {invalid_xsd_path.as_posix()}",
        f"The XML document '{invalid_xsd_path.as_posix()}' is not a schema document.",
        file=sys.stderr,
    )
    assert result is None


def test_get_premis_schema_with_valid_schema(xsd_path):
    result = load_premis_events_from_xml.get_premis_schema(xsd_path)
    assert result is not None


@mock.patch("os.path.isfile", return_value=False)
def test_get_validated_etree_with_nonexistent_path(is_file):
    printfn = mock.Mock()
    result = load_premis_events_from_xml.get_validated_etree(
        "mock/xml/path", None, printfn
    )
    printfn.assert_called_once_with("No events XML file found at path mock/xml/path")
    assert result is None


def test_get_validated_etree_with_invalid_xml(invalid_xml_path, xsd_path):
    printfn = mock.Mock()
    schema = etree.XMLSchema(etree.parse(xsd_path))
    result = load_premis_events_from_xml.get_validated_etree(
        invalid_xml_path["path"].as_posix(), schema, printfn
    )
    printfn.assert_called_once_with(
        "Could not validate the events XML file {} using the PREMIS 3 XML schema".format(
            invalid_xml_path["path"].as_posix()
        ),
        invalid_xml_path["expected_error"],
        file=sys.stderr,
    )
    assert result is None


def test_get_validated_etree_with_valid_xml(simple_xml_path, xsd_path):
    schema = etree.XMLSchema(etree.parse(xsd_path))
    result = load_premis_events_from_xml.get_validated_etree(
        simple_xml_path.as_posix(), schema
    )
    assert result is not None


def test_parse_datetime_with_invalid_value():
    with pytest.raises(ValueError) as excinfo:
        load_premis_events_from_xml.parse_datetime("invalid value")
    assert str(excinfo.value) == "Unable to parse 'invalid value' as a datetime"


def test_parse_datetime_with_valid_date():
    result = load_premis_events_from_xml.parse_datetime("2019-09-24")
    assert (2019, 9, 24) == (result.year, result.month, result.day)
    assert (0, 0, 0) == (result.hour, result.minute, result.second)


def test_parse_datetime_with_valid_datetime_and_no_timezone():
    result = load_premis_events_from_xml.parse_datetime("2019-09-24T16:54:21")
    assert (2019, 9, 24) == (result.year, result.month, result.day)
    assert (16, 54, 21) == (result.hour, result.minute, result.second)
    assert "UTC" == result.tzname()


def test_parse_datetime_with_valid_datetime_and_timezone():
    result = load_premis_events_from_xml.parse_datetime("2019-09-24T16:54:21+04:00")
    assert (2019, 9, 24) == (result.year, result.month, result.day)
    assert (16, 54, 21) == (result.hour, result.minute, result.second)
    assert "UTC+04:00" == result.tzname()


def test_parse_datetime_with_empty_string():
    assert load_premis_events_from_xml.parse_datetime("") is None


def test_get_elements():
    root = mock.Mock(**{"get.return_value": "3.0"})
    element = mock.Mock(**{"get.return_value": None})
    tree = mock.Mock(
        **{"getroot.return_value": root, "findall.return_value": [element]}
    )
    selector = "premis:object"
    element_factory = mock.Mock(return_value={"identifier": "id"})
    result = load_premis_events_from_xml.get_elements(tree, selector, element_factory)
    element.get.assert_called_once_with("version")
    element.set.assert_called_once_with("version", "3.0")
    assert list(result.keys()) == ["id"]
    assert list(result.values()) == [{"identifier": "id"}]


def test_get_premis_element_children_identifiers():
    identifier1 = mock.Mock(type="t", value="1")
    identifier2 = mock.Mock(type="t", value="2")
    premis_element = mock.Mock(**{"findall.return_value": [identifier1, identifier2]})
    result = load_premis_events_from_xml.get_premis_element_children_identifiers(
        premis_element, "premis:object"
    )
    assert result == {("t", "1"), ("t", "2")}


@pytest.mark.parametrize(
    "params",
    [
        {"original_name": "name", "expected_original_name": "name"},
        {"original_name": (), "expected_original_name": ""},
    ],
    ids=["original_name_as_string", "original_name_as_empty_string"],
)
@mock.patch("metsrw.plugins.premisrw.premis_to_data")
@mock.patch("load_premis_events_from_xml.PREMISFile")
@mock.patch(
    "load_premis_events_from_xml.get_premis_element_children_identifiers",
    return_value=set(),
)
def test_file_element_factory(
    get_premis_element_children_identifiers, premis_file, premis_to_data, params
):
    premis_file.return_value = mock.Mock(
        identifier_type="f",
        identifier_value="1",
        original_name=params["original_name"],
    )
    result = load_premis_events_from_xml.file_element_factory(None)
    assert result == {
        "identifier": ("f", "1"),
        "original_name": params["expected_original_name"],
        "events": set(),
    }


@mock.patch("metsrw.plugins.premisrw.premis_to_data")
@mock.patch("metsrw.plugins.premisrw.PREMISAgent")
@mock.patch(
    "load_premis_events_from_xml.get_premis_element_children_identifiers",
    return_value=set(),
)
def test_agent_element_factory(
    get_premis_element_children_identifiers, premis_agent, premis_to_data
):
    premis_element = mock.Mock(
        identifier_type="a", identifier_value="1", type="agenttype"
    )
    # a "name" attribute can't be set on a mock at creation time
    premis_element.name = "name"
    premis_agent.return_value = premis_element
    result = load_premis_events_from_xml.agent_element_factory(None)
    assert result == {
        "identifier": ("a", "1"),
        "name": "name",
        "type": "agenttype",
        "events": set(),
    }


@pytest.mark.parametrize(
    "params",
    [
        {"event_outcome_detail_note": None, "expected_event_outcome_detail_note": None},
        {
            "event_outcome_detail_note": "detail note",
            "expected_event_outcome_detail_note": "detail note",
        },
    ],
    ids=["detail_note_as_None", "detail_note_as_string"],
)
@mock.patch("metsrw.plugins.premisrw.premis_to_data")
@mock.patch("metsrw.plugins.premisrw.PREMISEvent")
@mock.patch(
    "load_premis_events_from_xml.get_premis_element_children_identifiers",
    return_value=set(),
)
def test_event_element_factory(
    get_premis_element_children_identifiers, premis_event, premis_to_data, params
):
    event_detail = mock.Mock(event_detail="event detail")
    event_outcome_part1 = mock.Mock(event_outcome="joined")
    event_outcome_part2 = mock.Mock(event_outcome="string")
    event_outcome_detail = mock.Mock(
        event_outcome_detail_note=params["event_outcome_detail_note"]
    )
    premis_element = mock.Mock(
        identifier_type="e",
        identifier_value="1",
        type="ingestion",
        date_time="2019-09-28T00:50",
        **{
            "findall.side_effect": [
                [event_detail],
                [event_outcome_part1, event_outcome_part2],
                [event_outcome_detail],
            ]
        },
    )
    premis_event.return_value = premis_element
    result = load_premis_events_from_xml.event_element_factory(None)
    event_datetime = result.pop("event_datetime")
    if params["event_outcome_detail_note"] is not None:
        assert (
            result.pop("event_outcome_detail")
            == params["expected_event_outcome_detail_note"]
        )
    assert result == {
        "identifier": ("e", "1"),
        "event_id": "1",
        "event_type": "ingestion",
        "event_detail": "event detail",
        "event_outcome": "joined string",
        "files": set(),
        "agents": set(),
    }
    assert (event_datetime.year, event_datetime.month, event_datetime.day) == (
        2019,
        9,
        28,
    )
    assert (event_datetime.hour, event_datetime.minute, event_datetime.second) == (
        0,
        50,
        0,
    )


@mock.patch("metsrw.plugins.premisrw.premis_to_data")
@mock.patch(
    "metsrw.plugins.premisrw.PREMISEvent",
    return_value=mock.Mock(
        identifier_type="e",
        identifier_value="1",
        date_time="foobar",
        **{"findall.return_value": []},
    ),
)
@mock.patch(
    "load_premis_events_from_xml.get_premis_element_children_identifiers",
    return_value=set(),
)
def test_event_element_factory_prints_datetime_error(
    get_premis_element_children_identifiers, premis_event, premis_to_data
):
    printfn = mock.Mock()
    load_premis_events_from_xml.event_element_factory(None, printfn)
    printfn.assert_called_once_with(
        "The premis:event element with premis:eventIdentifierType='e' and premis:eventIdentifierValue='1' contains a premis:eventDateTime value that could not be parsed: foobar",
        file=sys.stderr,
    )


no_event_outcome_detail_xml = """
<premis:premis xmlns:premis="http://www.loc.gov/premis/v3" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/premis/v3 https://www.loc.gov/standards/premis/premis.xsd" version="3.0">
  <premis:event>
    <premis:eventIdentifier>
      <premis:eventIdentifierType>NRI Repository Event ID</premis:eventIdentifierType>
      <premis:eventIdentifierValue>NRI-016</premis:eventIdentifierValue>
    </premis:eventIdentifier>
    <premis:eventType>ingestion</premis:eventType>
    <premis:eventDateTime>2019-07-04T22:46:07.773391+00:00</premis:eventDateTime>
    <premis:eventOutcomeInformation>
      <premis:eventOutcome>event outcome</premis:eventOutcome>
    </premis:eventOutcomeInformation>
    <premis:linkingAgentIdentifier>
      <premis:linkingAgentIdentifierType>repository code</premis:linkingAgentIdentifierType>
      <premis:linkingAgentIdentifierValue>NRI</premis:linkingAgentIdentifierValue>
    </premis:linkingAgentIdentifier>
  </premis:event>
</premis:premis>
"""


def test_event_element_factory_with_no_event_outcome_detail():
    premis_element = etree.fromstring(no_event_outcome_detail_xml)
    event_element = premis_element.find("premis:event", premis_element.nsmap)
    event_element.set("version", premis_element.get("version"))
    result = load_premis_events_from_xml.event_element_factory(event_element)
    expected_attributes = [
        "agents",
        "event_datetime",
        "event_id",
        "event_outcome",
        "event_type",
        "files",
        "identifier",
    ]
    assert sorted(result) == expected_attributes
    assert result["agents"] == {("repository code", "NRI")}
    event_datetime = result["event_datetime"]
    assert (event_datetime.year, event_datetime.month, event_datetime.day) == (
        2019,
        7,
        4,
    )
    assert (event_datetime.hour, event_datetime.minute, event_datetime.second) == (
        22,
        46,
        7,
    )
    assert result["event_id"] == "NRI-016"
    assert result["event_outcome"] == "event outcome"
    assert result["event_type"] == "ingestion"
    assert result["files"] == set()
    assert result["identifier"] == ("NRI Repository Event ID", "NRI-016")


def test_get_or_create_agents():
    mock_agent_model = mock.Mock(**{"objects.get_or_create.return_value": (None, None)})
    with mock.patch("load_premis_events_from_xml.Agent", mock_agent_model):
        agents = [
            {"identifier": ("type", "value"), "name": "agent1", "type": "agenttype"}
        ]
        load_premis_events_from_xml.get_or_create_agents(agents)
        mock_agent_model.objects.get_or_create.assert_called_once_with(
            **{
                "identifiertype": "type",
                "identifiervalue": "value",
                "name": "agent1",
                "agenttype": "agenttype",
            }
        )


def test_premis_file_class():
    premis_element = load_premis_events_from_xml.PREMISFile()
    default = object()
    assert getattr(premis_element, "original_name", default) is not default


def test_get_invalid_file_identifiers():
    printfn = mock.Mock()
    prefix = load_premis_events_from_xml.TRANSFER_ORIGINAL_LOCATION_PREFIX
    valid_filenames = ["".join([prefix, "object1"]), "".join([prefix, "object2"])]

    def mock_filter(originallocation):
        return_value = originallocation.decode() in valid_filenames
        return mock.Mock(**{"exists.return_value": return_value})

    file_queryset = mock.Mock(**{"filter.side_effect": mock_filter})
    files = {
        ("f", "valid"): {"original_name": "object1"},
        ("f", "no-original-name"): {"original_name": ""},
        ("f", "nonexistent-name"): {"original_name": "object3"},
    }
    result = load_premis_events_from_xml.get_invalid_file_identifiers(
        files, file_queryset, printfn
    )
    assert result == {("f", "no-original-name"), ("f", "nonexistent-name")}
    calls = [
        mock.call(
            "The premis:object element with premis:objectIdentifierType='f' and premis:objectIdentifierValue='no-original-name' does not contain a premis:originalName element",
            file=sys.stderr,
        ),
        mock.call(
            "The premis:object element with premis:objectIdentifierType='f' and premis:objectIdentifierValue='nonexistent-name' contains a premis:originalName value that does not match any filename in this transfer: 'object3'",
            file=sys.stderr,
        ),
    ]
    printfn.assert_has_calls(calls, any_order=True)


def test_print_unrelated_files():
    printfn = mock.Mock()
    files = {
        ("f", "1"): {"identifier": ("f", "1")},
        ("f", "2"): {"identifier": ("f", "2")},
        ("f", "3"): {"identifier": ("f", "3")},
        ("f", "4"): {"identifier": ("f", "4")},
    }
    events = {
        ("e", "1"): {"files": {("f", "1"), ("f", "2")}},
        ("e", "2"): {"files": {("f", "1"), ("f", "4")}},
    }
    load_premis_events_from_xml.print_unrelated_files(files, events, printfn)
    printfn.assert_called_once_with(
        "The premis:object element with premis:objectIdentifierType='f' and premis:objectIdentifierValue='3' is not related to any premis:event element",
        file=sys.stderr,
    )


def test_print_unrelated_agents():
    printfn = mock.Mock()
    agents = {
        ("a", "1"): {"identifier": ("a", "1")},
        ("a", "2"): {"identifier": ("a", "2")},
        ("a", "3"): {"identifier": ("a", "3")},
        ("a", "4"): {"identifier": ("a", "4")},
    }
    events = {
        ("e", "1"): {"agents": {("a", "1"), ("a", "2")}},
        ("e", "2"): {"agents": {("a", "1"), ("a", "4")}},
    }
    load_premis_events_from_xml.print_unrelated_agents(agents, events, printfn)
    printfn.assert_called_once_with(
        "The premis:agent element with premis:agentIdentifierType='a' and premis:agentIdentifierValue='3' is not related to any premis:event element",
        file=sys.stderr,
    )


def test_print_unrelated_events():
    printfn = mock.Mock()
    events = {
        ("e", "1"): {"files": {"f1"}, "agents": set()},
        ("e", "2"): {"files": {"f1"}, "agents": {"a1"}},
        ("e", "3"): {"files": set(), "agents": {"a1"}},
        ("e", "4"): {"files": set(), "agents": set()},
    }
    load_premis_events_from_xml.print_unrelated_events(events, printfn)
    calls = [
        mock.call(
            "The premis:event element with premis:eventIdentifierType='e' and premis:eventIdentifierValue='1' is not related to any premis:agent element",
            file=sys.stderr,
        ),
        mock.call(
            "The premis:event element with premis:eventIdentifierType='e' and premis:eventIdentifierValue='3' is not related to any premis:object element",
            file=sys.stderr,
        ),
        mock.call(
            "The premis:event element with premis:eventIdentifierType='e' and premis:eventIdentifierValue='4' is not related to any premis:object element",
            file=sys.stderr,
        ),
        mock.call(
            "The premis:event element with premis:eventIdentifierType='e' and premis:eventIdentifierValue='4' is not related to any premis:agent element",
            file=sys.stderr,
        ),
    ]
    printfn.assert_has_calls(calls, any_order=True)


def test_print_files_related_to_nonexistent_events():
    printfn = mock.Mock()
    files = {
        ("f", "1"): {"events": set()},
        ("f", "2"): {"events": {("e", "1"), ("e", "2"), ("e", "3")}},
        ("f", "3"): {"events": {("e", "2")}},
        ("f", "4"): {"events": {("e", "1")}},
    }
    events = {("e", "1"): {}, ("e", "2"): {}}
    load_premis_events_from_xml.print_files_related_to_nonexistent_events(
        files, events, printfn
    )
    printfn.assert_called_once_with(
        "The premis:object element with premis:objectIdentifierType='f' and premis:objectIdentifierValue='2' contains premis:linkingEventIdentifier elements that reference premis:event elements that are not present in this document: (premis:eventIdentifierType='e' and premis:eventIdentifierValue='3')",
        file=sys.stderr,
    )


def test_print_agents_related_to_nonexistent_events():
    printfn = mock.Mock()
    agents = {
        ("a", "1"): {"events": set()},
        ("a", "2"): {"events": {("e", "1"), ("e", "2"), ("e", "3")}},
        ("a", "3"): {"events": {("e", "2")}},
        ("a", "4"): {"events": {("e", "1")}},
    }
    events = {("e", "1"): {}, ("e", "2"): {}}
    load_premis_events_from_xml.print_agents_related_to_nonexistent_events(
        agents, events, printfn
    )
    printfn.assert_called_once_with(
        "The premis:agent element with premis:agentIdentifierType='a' and premis:agentIdentifierValue='2' contains premis:linkingEventIdentifier elements that reference premis:event elements that are not present in this document: (premis:eventIdentifierType='e' and premis:eventIdentifierValue='3')",
        file=sys.stderr,
    )


def test_print_events_related_to_nonexistent_files():
    printfn = mock.Mock()
    files = {("f", "1"): {}, ("f", "2"): {}}
    events = {
        ("e", "1"): {"files": set()},
        ("e", "2"): {"files": {("f", "1"), ("f", "2"), ("f", "3")}},
        ("e", "3"): {"files": {("f", "2")}},
        ("e", "4"): {"files": {("f", "1")}},
    }
    load_premis_events_from_xml.print_events_related_to_nonexistent_files(
        events, files, printfn
    )
    printfn.assert_called_once_with(
        "The premis:event element with premis:eventIdentifierType='e' and premis:eventIdentifierValue='2' contains premis:linkingObjectIdentifier elements that reference premis:object elements that are not present in this document: (premis:objectIdentifierType='f' and premis:objectIdentifierValue='3')",
        file=sys.stderr,
    )


def test_print_events_related_to_nonexistent_agents():
    printfn = mock.Mock()
    agents = {("a", "1"): {}, ("a", "2"): {}}
    events = {
        ("e", "1"): {"agents": set()},
        ("e", "2"): {"agents": {("a", "1"), ("a", "2"), ("a", "3")}},
        ("e", "3"): {"agents": {("a", "2")}},
        ("e", "4"): {"agents": {("a", "1")}},
    }
    load_premis_events_from_xml.print_events_related_to_nonexistent_agents(
        events, agents, printfn
    )
    printfn.assert_called_once_with(
        "The premis:event element with premis:eventIdentifierType='e' and premis:eventIdentifierValue='2' contains premis:linkingAgentIdentifier elements that reference premis:agent elements that are not present in this document: (premis:agentIdentifierType='a' and premis:agentIdentifierValue='3')",
        file=sys.stderr,
    )


def test_relate_files_to_events():
    files = {
        "f1": {"events": {"e1", "e3"}},
        "f2": {"events": {"e2"}},
        "f3": {"events": set()},
    }
    events = {
        "e1": {"files": set()},
        "e2": {"files": {"f3", "f4"}},
        "e3": {"files": {"f1"}},
    }
    load_premis_events_from_xml.relate_files_to_events(files, events)
    assert events == {
        "e1": {"files": {"f1"}},
        "e2": {"files": {"f2", "f3", "f4"}},
        "e3": {"files": {"f1"}},
    }


def test_relate_agents_to_events():
    agents = {
        "a1": {"events": {"e1", "e3"}},
        "a2": {"events": {"e2"}},
        "a3": {"events": set()},
    }
    events = {
        "e1": {"agents": set()},
        "e2": {"agents": {"a3", "a4"}},
        "e3": {"agents": {"a1"}},
    }
    load_premis_events_from_xml.relate_agents_to_events(agents, events)
    assert events == {
        "e1": {"agents": {"a1"}},
        "e2": {"agents": {"a2", "a3", "a4"}},
        "e3": {"agents": {"a1"}},
    }


def test_get_event_agents():
    printfn = mock.Mock()
    event = {"agents": {"a2", "a3"}}
    agents = {"a1": {"identifier": "a1"}, "a2": {"identifier": "a2"}}
    agent_identifiers = set(agents)
    result = load_premis_events_from_xml.get_event_agents(
        event, agents, agent_identifiers, printfn
    )
    assert result == [{"identifier": "a2"}]
    printfn.assert_not_called()


@pytest.mark.parametrize(
    "params",
    [
        {
            "file_identifiers_to_ignore": set(),
            "expected_result": [{"identifier": "f1"}, {"identifier": "f2"}],
        },
        {
            "file_identifiers_to_ignore": {"f2"},
            "expected_result": [{"identifier": "f1"}],
        },
    ],
    ids=["no_file_identifiers_to_ignore", "with_file_identifiers_to_ignore"],
)
def test_get_event_files(params):
    printfn = mock.Mock()
    event = {"files": {"f1", "f2", "f3"}}
    files = {"f1": {"identifier": "f1"}, "f2": {"identifier": "f2"}}
    file_identifiers = set(files)
    result = load_premis_events_from_xml.get_event_files(
        event, files, file_identifiers, params["file_identifiers_to_ignore"], printfn
    )
    assert sorted(result, key=lambda f: f["identifier"]) == params["expected_result"]
    printfn.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "params",
    [
        {"event_id": "7e3330fe-0d7c-4c11-8a42-05964192425a", "message_logged": None},
        {
            "event_id": "foobar",
            "message_logged": "Changed event identifier from foobar to f4eea76b-1921-4152-b1b4-a93dbbfeaaef",
        },
    ],
)
@mock.patch("uuid.uuid4")
def test_ensure_event_id_is_uuid(uuid4, params):
    if params["message_logged"]:
        uuid4.return_value = uuid.UUID("f4eea76b-1921-4152-b1b4-a93dbbfeaaef")
    printfn = mock.Mock()
    result = load_premis_events_from_xml.ensure_event_id_is_uuid(
        params["event_id"], printfn
    )
    assert isinstance(result, str)
    if not params["message_logged"]:
        assert result == params["event_id"]
        printfn.assert_not_called()
    else:
        assert result != params["event_id"]
        printfn.assert_called_once_with(params["message_logged"])


@pytest.fixture()
def existent_event_id(transfer_file):
    event = Event.objects.create(event_type="ingest", file_uuid=transfer_file)
    return str(event.event_id)


@pytest.mark.django_db
@mock.patch("uuid.uuid4")
def test_ensure_event_id_is_uuid_with_existent_event(uuid4, existent_event_id):
    expected_uuid = uuid.uuid4()
    uuid4.return_value = expected_uuid
    printfn = mock.Mock()
    result = load_premis_events_from_xml.ensure_event_id_is_uuid(
        existent_event_id, printfn
    )
    assert result != existent_event_id
    assert isinstance(result, str)
    printfn.assert_called_once_with(
        f"Changed event identifier from {existent_event_id} to {expected_uuid}"
    )


def test_get_valid_events():
    printfn = mock.Mock()
    files = {"f1": {"identifier": "f1"}, "f2": {"identifier": "f2"}}
    agents = {"a1": {"identifier": "a1"}, "a2": {"identifier": "a2"}}
    events = {
        "e1": {"identifier": "e1", "files": {"f1"}, "agents": {"a1"}},
        "e2": {"identifier": "e2", "files": set(), "agents": {"a2"}},
        "e3": {"identifier": "e3", "files": {"f2"}, "agents": set()},
        "e4": {"identifier": "e4", "files": {"f3"}, "agents": set()},
    }
    file_identifiers_to_ignore = {"f3"}

    valid_events, invalid_events_exist = load_premis_events_from_xml.get_valid_events(
        files, agents, events, file_identifiers_to_ignore, printfn
    )

    assert invalid_events_exist
    assert valid_events == [
        {
            "event": {"identifier": "e1", "files": {"f1"}, "agents": {"a1"}},
            "event_agents": [{"identifier": "a1"}],
            "event_files": [{"identifier": "f1"}],
        }
    ]

    calls = [
        mock.call(
            "The premis:event element with premis:eventIdentifierType='e' and premis:eventIdentifierValue='2' is not related to any filename in the transfer files",
            file=sys.stderr,
        ),
        mock.call(
            "The premis:event element with premis:eventIdentifierType='e' and premis:eventIdentifierValue='3' is not related to any agents",
            file=sys.stderr,
        ),
        mock.call(
            "The premis:event element with premis:eventIdentifierType='e' and premis:eventIdentifierValue='4' is not related to any agents",
            file=sys.stderr,
        ),
    ]
    printfn.assert_has_calls(calls, any_order=True)


@pytest.mark.django_db
def test_save_events(transfer, transfer_file):
    # check there are no events initially
    assert not Event.objects.count()

    # set up valid events
    valid_events = [
        {
            "event": {
                "identifier": ("e", "f4eea76b-1921-4152-b1b4-a93dbbfeaa11"),
                "event_id": "f4eea76b-1921-4152-b1b4-a93dbbfeaa11",
                "event_type": "ingestion",
                "event_datetime": load_premis_events_from_xml.parse_datetime(
                    "2019-09-28T00:50"
                ),
                "event_detail": "the event detail",
                "event_outcome": "the event outcome",
                "event_outcome_detail": "the event outcome detail",
                "files": {("f", "1")},
                "agents": {("a", "1")},
            },
            "event_files": [
                {
                    "identifier": ("f", "1"),
                    "original_name": transfer_file.originallocation.decode().replace(
                        "%transferDirectory%", "", 1
                    ),
                    "events": set(),
                }
            ],
            "event_agents": [
                {
                    "identifier": ("a", "1"),
                    "name": "an agent",
                    "type": "agent type",
                    "events": set(),
                }
            ],
        }
    ]

    file_queryset = File.objects.filter(transfer=transfer)
    printfn = mock.Mock()

    # save the event
    load_premis_events_from_xml.save_events(valid_events, file_queryset, printfn)

    printfn.assert_called_once_with(
        "Imported PREMIS ingestion event and assigned identifier f4eea76b-1921-4152-b1b4-a93dbbfeaa11"
    )

    # a new agent was also created
    assert Agent.objects.filter(name="an agent", agenttype="agent type").exists()

    # check the saved event
    assert Event.objects.count() == 1
    event = Event.objects.get(
        event_id="f4eea76b-1921-4152-b1b4-a93dbbfeaa11", file_uuid=transfer_file
    )
    assert event.event_type == "ingestion"
    assert event.event_detail == "the event detail"
    assert event.event_outcome == "the event outcome"
    assert event.event_outcome_detail == "the event outcome detail"
    event_datetime = event.event_datetime
    assert (event_datetime.year, event_datetime.month, event_datetime.day) == (
        2019,
        9,
        28,
    )
    assert (event_datetime.hour, event_datetime.minute, event_datetime.second) == (
        0,
        50,
        0,
    )
