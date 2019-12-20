from __future__ import print_function
import datetime
import logging
import os
import sys
import uuid

from django.db import transaction
from django.utils import dateparse, timezone
from lxml import etree
import metsrw
import six

from main.models import Agent
from main.models import Event
from main.models import File

logger = logging.getLogger(__name__)
FAILURE = 1
SUCCESS = 0
TRANSFER_ORIGINAL_LOCATION_PREFIX = r"%transferDirectory%"


def log_missing_original_name(file_identifier, printfn=print):
    printfn(
        "The {formatted_object_identifier} does not contain a premis:originalName element".format(
            formatted_object_identifier=format_identifier(
                file_identifier, element_type="object"
            )
        ),
        file=sys.stderr,
    )


def log_filename_mismatch(file_identifier, original_name, printfn=print):
    printfn(
        "The {formatted_object_identifier} contains a premis:originalName value that does not match any filename in this transfer: '{original_name}'".format(
            formatted_object_identifier=format_identifier(
                file_identifier, element_type="object"
            ),
            original_name=original_name,
        ),
        file=sys.stderr,
    )


def log_missing_xsd(path, printfn=print):
    printfn(
        "The PREMIS XML schema asset {} is unavailable".format(path), file=sys.stderr
    )


def log_invalid_xsd(path, exception, printfn=print):
    printfn(
        "Could not parse the PREMIS XML schema {}".format(path),
        str(exception),
        file=sys.stderr,
    )


def log_invalid_events_xml(path, exception, printfn=print):
    printfn(
        "Could not validate the events XML file {} using the PREMIS 3 XML schema".format(
            path
        ),
        str(exception),
        file=sys.stderr,
    )


def log_event_without_files(event_identifier, printfn=print):
    printfn(
        "The {formatted_event_identifier} is not related to any filename in the transfer files".format(
            formatted_event_identifier=format_identifier(
                event_identifier, element_type="event"
            )
        ),
        file=sys.stderr,
    )


def log_event_without_agents(event_identifier, printfn=print):
    printfn(
        "The {formatted_event_identifier} is not related to any agents".format(
            formatted_event_identifier=format_identifier(
                event_identifier, element_type="event"
            )
        ),
        file=sys.stderr,
    )


def log_missing_events_xml(path, printfn=print):
    printfn("No events XML file found at path {}".format(path))


def log_invalid_event_datetime(premis_element, printfn=print):
    printfn(
        "The {formatted_event_identifier} contains a premis:eventDateTime value that could not be parsed: {event_datetime}".format(
            formatted_event_identifier=format_identifier(
                get_identifier(premis_element), element_type="event"
            ),
            event_datetime=premis_element.date_time,
        ),
        file=sys.stderr,
    )


def log_unrelated_file(file_identifier, printfn=print):
    printfn(
        "The {formatted_object_identifier} is not related to any premis:event element".format(
            formatted_object_identifier=format_identifier(
                file_identifier, element_type="object"
            )
        ),
        file=sys.stderr,
    )


def log_unrelated_agent(agent_identifier, printfn=print):
    printfn(
        "The {formatted_agent_identifier} is not related to any premis:event element".format(
            formatted_agent_identifier=format_identifier(
                agent_identifier, element_type="agent"
            )
        ),
        file=sys.stderr,
    )


def log_unrelated_event_to_files(event_identifier, printfn=print):
    printfn(
        "The {formatted_event_identifier} is not related to any premis:object element".format(
            formatted_event_identifier=format_identifier(
                event_identifier, element_type="event"
            )
        ),
        file=sys.stderr,
    )


def log_unrelated_event_to_agents(event_identifier, printfn=print):
    printfn(
        "The {formatted_event_identifier} is not related to any premis:agent element".format(
            formatted_event_identifier=format_identifier(
                event_identifier, element_type="event"
            )
        ),
        file=sys.stderr,
    )


def log_file_related_to_nonexistent_events(
    file_identifier, nonexistent_identifiers, printfn=print
):
    printfn(
        "The {formatted_object_identifier} contains premis:linkingEventIdentifier elements that reference premis:event elements that are not present in this document: {formatted_event_identifiers}".format(
            formatted_object_identifier=format_identifier(
                file_identifier, element_type="object"
            ),
            formatted_event_identifiers=format_as_grouped_identifiers(
                nonexistent_identifiers, element_type="event"
            ),
        ),
        file=sys.stderr,
    )


def log_agent_related_to_nonexistent_events(
    agent_identifier, nonexistent_identifiers, printfn=print
):
    printfn(
        "The {formatted_agent_identifier} contains premis:linkingEventIdentifier elements that reference premis:event elements that are not present in this document: {formatted_event_identifiers}".format(
            formatted_agent_identifier=format_identifier(
                agent_identifier, element_type="agent"
            ),
            formatted_event_identifiers=format_as_grouped_identifiers(
                nonexistent_identifiers, element_type="event"
            ),
        ),
        file=sys.stderr,
    )


def log_event_related_to_nonexistent_files(
    event_identifier, nonexistent_identifiers, printfn=print
):
    printfn(
        "The {formatted_event_identifier} contains premis:linkingObjectIdentifier elements that reference premis:object elements that are not present in this document: {formatted_object_identifiers}".format(
            formatted_event_identifier=format_identifier(
                event_identifier, element_type="event"
            ),
            formatted_object_identifiers=format_as_grouped_identifiers(
                nonexistent_identifiers, element_type="object"
            ),
        ),
        file=sys.stderr,
    )


def log_event_related_to_nonexistent_agents(
    event_identifier, nonexistent_identifiers, printfn
):
    printfn(
        "The {formatted_event_identifier} contains premis:linkingAgentIdentifier elements that reference premis:agent elements that are not present in this document: {formatted_agent_identifiers}".format(
            formatted_event_identifier=format_identifier(
                event_identifier, element_type="event"
            ),
            formatted_agent_identifiers=format_as_grouped_identifiers(
                nonexistent_identifiers, element_type="agent"
            ),
        ),
        file=sys.stderr,
    )


def log_event_id_change(event_id, new_event_id, printfn=print):
    printfn("Changed event identifier from {} to {}".format(event_id, new_event_id))


def log_event_successfully_created(db_event, printfn=print):
    printfn(
        "Imported PREMIS {} event and assigned identifier {}".format(
            db_event.event_type, db_event.event_id
        )
    )


class PREMISFile(metsrw.plugins.premisrw.PREMISObject):
    """
    Implements the originalName child element used to relate files in a
    transfer to events.
    """

    @property
    def schema(self):
        object_schema = super(PREMISFile, self).schema
        return object_schema + (("original_name",),)


def parse_datetime(value):
    parsed_datetime = dateparse.parse_datetime(value)
    # Check if we got a date
    if parsed_datetime is None:
        parsed_date = dateparse.parse_date(value)
        if parsed_date is not None:
            parsed_datetime = datetime.datetime.combine(
                parsed_date, datetime.datetime.min.time()
            )
    if value and parsed_datetime is None:
        raise ValueError("Unable to parse '{}' as a datetime".format(value))
    # If we didn't get a timezone, use the one configured in Django settings
    if parsed_datetime is not None and parsed_datetime.tzinfo is None:
        parsed_datetime = parsed_datetime.replace(
            tzinfo=timezone.get_default_timezone()
        )
    return parsed_datetime


def get_premis_schema(premis_xsd_path, printfn=print):
    if not os.path.isfile(premis_xsd_path):
        log_missing_xsd(premis_xsd_path, printfn)
        return
    try:
        return etree.XMLSchema(etree.parse(premis_xsd_path))
    except (etree.XMLSyntaxError, etree.XMLSchemaParseError) as exception:
        log_invalid_xsd(premis_xsd_path, exception, printfn)
        return


def get_validated_etree(premis_events_xml_path, premis_schema, printfn=print):
    if not os.path.isfile(premis_events_xml_path):
        # a missing events XML file is not considered an error
        log_missing_events_xml(premis_events_xml_path, printfn)
        return
    try:
        result = etree.parse(premis_events_xml_path)
        premis_schema.assertValid(result)
        return result
    except (etree.XMLSyntaxError, etree.DocumentInvalid) as exception:
        log_invalid_events_xml(premis_events_xml_path, exception, printfn)
        return


def get_xml_tree(xsd_path, xml_path, printfn=print):
    schema = get_premis_schema(xsd_path, printfn)
    if schema is None:
        return None
    return get_validated_etree(xml_path, schema, printfn)


def get_elements(tree, selector, element_factory, printfn=print):
    """
    Looks for PREMISElements based on a selector and builds a dictionary
    keyed by identifier that contains element attributes.
    """
    result = {}
    root = tree.getroot()
    premis_version = root.get("version", metsrw.plugins.premisrw.PREMIS_VERSION)
    elements = tree.findall(
        selector,
        metsrw.plugins.premisrw.PREMIS_VERSIONS_MAP[premis_version]["namespaces"],
    )
    # metsrw.plugins.premisrw.premis_to_data (used later) expects the PREMISElements
    # to have their own version attribute, so we set it if they don't
    for element in elements:
        if element.get("version") is None:
            element.set("version", premis_version)
        attributes = element_factory(element, printfn)
        result[attributes["identifier"]] = attributes
    return result


def format_identifier_details(identifier, element_type):
    identifier_type = identifier[0]
    identifier_value = identifier[1]
    return "premis:{element_type}IdentifierType='{identifier_type}' and premis:{element_type}IdentifierValue='{identifier_value}'".format(
        identifier_type=identifier_type,
        identifier_value=identifier_value,
        element_type=element_type,
    )


def format_identifier(identifier, element_type):
    return "premis:{element_type} element with {formatted_identifier_details}".format(
        element_type=element_type,
        formatted_identifier_details=format_identifier_details(
            identifier, element_type=element_type
        ),
    )


def format_as_grouped_identifiers(identifiers, element_type):
    return ",".join(
        [
            "({formatted_identifier_details})".format(
                formatted_identifier_details=format_identifier_details(
                    identifier, element_type=element_type
                )
            )
            for identifier in identifiers
        ]
    )


def get_premis_element_children_identifiers(premis_element, selector):
    result = set()
    for identifier in premis_element.findall(selector):
        result.add((identifier.type, identifier.value))
    return result


def get_premis_element_children_text_attribute(
    premis_element, selector, attribute_name
):
    """
    Get children of a PREMISElement based on a selector. If the children contain
    text, they're joined as a single string.
    """
    return (
        " ".join(
            [
                getattr(e, attribute_name)
                for e in premis_element.findall(selector)
                if isinstance(getattr(e, attribute_name), six.string_types)
            ]
        )
        or None
    )


def get_identifier(premis_element):
    return (premis_element.identifier_type, premis_element.identifier_value)


def file_element_factory(element, printfn=print):
    premis_element = PREMISFile(data=metsrw.plugins.premisrw.premis_to_data(element))
    result = {"identifier": get_identifier(premis_element)}
    if isinstance(premis_element.original_name, six.string_types):
        result["original_name"] = premis_element.original_name.strip()
    else:
        result["original_name"] = ""
    result["events"] = get_premis_element_children_identifiers(
        premis_element, "linking_event_identifier"
    )
    return result


def agent_element_factory(element, printfn=print):
    premis_element = metsrw.plugins.premisrw.PREMISAgent(
        data=metsrw.plugins.premisrw.premis_to_data(element)
    )
    result = {
        "identifier": get_identifier(premis_element),
        "name": premis_element.name,
        "type": premis_element.type,
    }
    result["events"] = get_premis_element_children_identifiers(
        premis_element, "linking_event_identifier"
    )
    return result


def event_element_factory(element, printfn=print):
    premis_element = metsrw.plugins.premisrw.PREMISEvent(
        data=metsrw.plugins.premisrw.premis_to_data(element)
    )
    result = {
        "identifier": get_identifier(premis_element),
        "event_id": premis_element.identifier_value,
        "event_type": premis_element.type,
    }
    event_datetime = None
    if premis_element.date_time:
        try:
            event_datetime = parse_datetime(premis_element.date_time)
        except ValueError:
            log_invalid_event_datetime(premis_element, printfn)
    if event_datetime is not None:
        result["event_datetime"] = event_datetime
    event_detail = get_premis_element_children_text_attribute(
        premis_element, "event_detail_information", "event_detail"
    )
    if event_detail:
        result["event_detail"] = event_detail
    event_outcome = get_premis_element_children_text_attribute(
        premis_element, "event_outcome_information", "event_outcome"
    )
    if event_outcome:
        result["event_outcome"] = event_outcome
    event_outcome_detail = get_premis_element_children_text_attribute(
        premis_element,
        "event_outcome_information/event_outcome_detail",
        "event_outcome_detail_note",
    )
    if event_outcome_detail:
        result["event_outcome_detail"] = event_outcome_detail
    result["files"] = get_premis_element_children_identifiers(
        premis_element, "linking_object_identifier"
    )
    result["agents"] = get_premis_element_children_identifiers(
        premis_element, "linking_agent_identifier"
    )
    return result


def get_invalid_file_identifiers(files, file_queryset, printfn=print):
    """
    File dictionaries are considered invalid if their `original_name` is
    empty or if its filename is not found in the transfer's file queryset.
    """
    result = set()
    for file_identifier, file_ in six.iteritems(files):
        original_name = file_["original_name"]
        if not original_name:
            log_missing_original_name(file_identifier, printfn)
            result.add(file_identifier)
            continue
        original_location = "".join([TRANSFER_ORIGINAL_LOCATION_PREFIX, original_name])
        if not file_queryset.filter(originallocation=original_location).exists():
            log_filename_mismatch(file_identifier, original_name, printfn)
            result.add(file_identifier)
    return result


def print_unrelated_files(files, events, printfn=print):
    """
    A file dictionary is considered unrelated if its key that corresponds to
    its identifier doesn't appear in the `files` set of any event.

    Return a boolean indicating if there are unrelated file elements.
    """
    result = False
    related_files = set()
    for event in six.itervalues(events):
        related_files.update(event["files"])
    for file_identifier in files:
        if file_identifier not in related_files:
            log_unrelated_file(file_identifier, printfn)
            result = True
    return result


def print_unrelated_agents(agents, events, printfn=print):
    """
    An agent dictionary is considered unrelated if its key that corresponds to
    its identifier doesn't appear in the `agents` set of any event.

    Return a boolean indicating if there are unrelated agent elements.
    """
    result = False
    related_agents = set()
    for event in six.itervalues(events):
        related_agents.update(event["agents"])
    for agent_identifier in agents:
        if agent_identifier not in related_agents:
            log_unrelated_agent(agent_identifier, printfn)
            result = True
    return result


def print_unrelated_events(events, printfn=print):
    """
    An event dictionary is considered unrelated if it doesn't have any identifiers
    in its `files` or `agents` sets.

    Return a boolean indicating if there are unrelated event elements.
    """
    result = False
    for event_identifier, event in six.iteritems(events):
        if not event["files"]:
            log_unrelated_event_to_files(event_identifier, printfn)
            result = True
        if not event["agents"]:
            log_unrelated_event_to_agents(event_identifier, printfn)
            result = True
    return result


def print_unrelated_elements(files, agents, events, printfn=print):
    """
    Go through each relationship and return a boolean indicating if any unrelated
    element exists.
    """
    return (
        print_unrelated_files(files, events, printfn)
        or print_unrelated_agents(agents, events, printfn)
        or print_unrelated_events(events, printfn)
    )


def print_files_related_to_nonexistent_events(files, events, printfn=print):
    """
    Search the events set of each file and print event identifiers that don't
    exist in the events collection.

    Return a boolean indicating if there are any file elements referencing
    nonexistent events.
    """
    result = False
    event_identifiers = set(events)
    for file_identifier, file_ in six.iteritems(files):
        nonexistent_identifiers = file_["events"].difference(event_identifiers)
        if nonexistent_identifiers:
            log_file_related_to_nonexistent_events(
                file_identifier, nonexistent_identifiers, printfn
            )
            result = True
    return result


def print_agents_related_to_nonexistent_events(agents, events, printfn=print):
    """
    Search the events set of each agent and print event identifiers that don't
    exist in the events collection.

    Return a boolean indicating if there are any agent elements referencing
    nonexistent events.
    """
    result = False
    event_identifiers = set(events)
    for agent_identifier, agent in six.iteritems(agents):
        nonexistent_identifiers = agent["events"].difference(event_identifiers)
        if nonexistent_identifiers:
            log_agent_related_to_nonexistent_events(
                agent_identifier, nonexistent_identifiers, printfn
            )
            result = True
    return result


def print_events_related_to_nonexistent_files(events, files, printfn=print):
    """
    Search the files set of each event and print event identifiers that don't
    exist in the events collection.

    Return a boolean indicating if there are any event elements referencing
    nonexistent files.
    """
    result = False
    file_identifiers = set(files)
    for event_identifier, event in six.iteritems(events):
        nonexistent_identifiers = event["files"].difference(file_identifiers)
        if nonexistent_identifiers:
            log_event_related_to_nonexistent_files(
                event_identifier, nonexistent_identifiers, printfn
            )
            result = True
    return result


def print_events_related_to_nonexistent_agents(events, agents, printfn=print):
    """
    Search the agents set of each event and print event identifiers that don't
    exist in the events collection.

    Return a boolean indicating if there are any event elements referencing
    nonexistent agents.
    """
    result = False
    agent_identifiers = set(agents)
    for event_identifier, event in six.iteritems(events):
        nonexistent_identifiers = event["agents"].difference(agent_identifiers)
        if nonexistent_identifiers:
            log_event_related_to_nonexistent_agents(
                event_identifier, nonexistent_identifiers, printfn
            )
            result = True
    return result


def print_nonexistent_references(files, agents, events, printfn=print):
    """
    Go through each relationship and return a boolean indicating if an element
    references any nonexistent element.
    """
    return (
        print_files_related_to_nonexistent_events(files, events, printfn)
        or print_agents_related_to_nonexistent_events(agents, events, printfn)
        or print_events_related_to_nonexistent_files(events, files, printfn)
        or print_events_related_to_nonexistent_agents(events, agents, printfn)
    )


def get_or_create_agents(agents):
    """
    Get a list of Agent model instances from each agent dictionary.
    """
    result = []
    for agent in agents:
        db_agent, _ = Agent.objects.get_or_create(
            identifiertype=agent["identifier"][0],
            identifiervalue=agent["identifier"][1],
            name=agent["name"],
            agenttype=agent["type"],
        )
        result.append(db_agent)
    return result


def get_event_agents(event, agents, agent_identifiers, printfn=print):
    """
    Get agents for the event ensuring that they exist in the agents collection.

    A message identifying the event is logged if no agents can be returned.
    """
    # get only agent identifiers that exist in the agents collection
    existent_agent_identifiers = event["agents"].intersection(agent_identifiers)
    return [agents[agent_identifier] for agent_identifier in existent_agent_identifiers]


def get_event_files(
    event, files, file_identifiers, file_identifiers_to_ignore, printfn=print
):
    """
    Get files for the event ensuring that they exist in the files collection.
    Invalid files are ignored.

    A message identifying the event is logged if no events can be returned.
    """
    # get only file identifiers that exist in the files collection
    event_file_identifiers = event["files"].intersection(file_identifiers)
    # and ignore invalid files
    event_file_identifiers = event_file_identifiers.difference(
        file_identifiers_to_ignore
    )
    return [files[file_identifier] for file_identifier in event_file_identifiers]


def ensure_event_id_is_uuid(event_id, printfn=print):
    try:
        uuid.UUID(event_id, version=4)
        if Event.objects.filter(event_id=event_id).exists():
            raise ValueError(
                "There is already an event with this event_id {}".format(event_id)
            )
    except ValueError:
        new_event_id = uuid.uuid4()
        log_event_id_change(event_id, new_event_id, printfn)
        event_id = new_event_id
    return event_id


def save_events(valid_events, file_queryset, printfn=print):

    for valid_event in valid_events:

        event = valid_event["event"]

        db_agents = get_or_create_agents(valid_event["event_agents"])

        for file_ in valid_event["event_files"]:

            # get database file from originalName
            db_file = file_queryset.get(
                originallocation="".join(
                    [TRANSFER_ORIGINAL_LOCATION_PREFIX, file_["original_name"]]
                )
            )

            # ensure the event identifier is uuid
            event["event_id"] = ensure_event_id_is_uuid(event["event_id"], printfn)

            # get only attributes suitable for the database model
            event_attributes = event.copy()
            del event_attributes["identifier"]
            del event_attributes["files"]
            del event_attributes["agents"]

            # create database event
            db_event = Event.objects.create(file_uuid=db_file, **event_attributes)
            db_event.agents.add(*db_agents)

            # The event_datetime field is auto_now, which will ignore what we pass
            # to create. Work around this with another query to update the row :(
            if event_attributes.get("event_datetime") is not None:
                Event.objects.filter(pk=db_event.pk).update(
                    event_datetime=event_attributes["event_datetime"]
                )

            # print success message
            log_event_successfully_created(db_event, printfn)


def relate_files_to_events(files, events):
    """
    Ensure the identifier of a file is included in the events collection
    for all its related events.
    """
    for file_identifier, file_ in six.iteritems(files):
        for event_identifier in file_["events"]:
            if event_identifier in events:
                events[event_identifier]["files"].add(file_identifier)


def relate_agents_to_events(agents, events):
    """
    Ensure the identifier of an agent is included in the events collection
    for all its related events.
    """
    for agent_identifier, agent in six.iteritems(agents):
        for event_identifier in agent["events"]:
            if event_identifier in events:
                events[event_identifier]["agents"].add(agent_identifier)


def get_valid_events(files, agents, events, file_identifiers_to_ignore, printfn=print):
    """
    Get the events that are related to valid files and agents. These can
    be stored in the database.

    Return also a boolean indicating if there are incomplete (invalid) events.
    """

    result = []
    invalid_events_exist = False

    # cache the identifiers and use them for several events
    file_identifiers = set(files)
    agent_identifiers = set(agents)

    for event in six.itervalues(events):
        # get the agents for this event
        event_agents = get_event_agents(event, agents, agent_identifiers, printfn)
        if not event_agents:
            log_event_without_agents(event["identifier"], printfn)
            invalid_events_exist = True
            continue

        # get the files for this event
        event_files = get_event_files(
            event, files, file_identifiers, file_identifiers_to_ignore, printfn
        )
        if not event_files:
            log_event_without_files(event["identifier"], printfn)
            invalid_events_exist = True
            continue

        result.append(
            {"event_agents": event_agents, "event_files": event_files, "event": event}
        )

    return result, invalid_events_exist


def main(job):

    # extract arguments from job
    transfer_uuid, xsd_path, xml_path = job.args[1:4]

    # a missing events XML file is not considered an error
    if not os.path.isfile(xml_path):
        log_missing_events_xml(xml_path, job.pyprint)
        return SUCCESS

    file_queryset = File.objects.filter(transfer_id=transfer_uuid)

    # validate the xml
    tree = get_xml_tree(xsd_path, xml_path, job.pyprint)
    if tree is None:
        return FAILURE

    # get dictionary of dictionaries with file attributes
    files = get_elements(
        tree, 'premis:object[@xsi:type="premis:file"]', file_element_factory
    )

    # get dictionary of dictionaries with agent attributes
    agents = get_elements(tree, "premis:agent", agent_element_factory)

    # get dictionary of dictionaries with event attributes
    events = get_elements(tree, "premis:event", event_element_factory, job.pyprint)

    # look for files that do not contain a premis:originalName element or do not
    # point to a filename in this transfer. we only care about their identifiers
    invalid_file_identifiers = get_invalid_file_identifiers(
        files, file_queryset, job.pyprint
    )

    # iterate files and relate them to their events
    relate_files_to_events(files, events)

    # iterate agents and relate them to their events
    relate_agents_to_events(agents, events)

    # log elements that are not related to any other element
    unrelated_elements_exist = print_unrelated_elements(
        files, agents, events, job.pyprint
    )

    # log elements that are related to nonexistent elements
    invalid_relationships_exist = print_nonexistent_references(
        files, agents, events, job.pyprint
    )

    # get events that can be saved
    valid_events, invalid_events_exist = get_valid_events(
        files, agents, events, invalid_file_identifiers, job.pyprint
    )

    if any(
        [unrelated_elements_exist, invalid_relationships_exist, invalid_events_exist]
    ):
        return FAILURE

    # save events
    save_events(valid_events, file_queryset, job.pyprint)

    return SUCCESS


def call(jobs):
    for job in jobs:
        with job.JobContext(logger=logger):
            with transaction.atomic():
                job.set_status(main(job))
