from __future__ import absolute_import, unicode_literals

import csv
import datetime
import logging
import os

import django

django.setup()  # NOQA

from django.db import transaction
from django.utils import dateparse, timezone

from main.models import Agent, Event, File


logger = logging.getLogger(__name__)


DB_BASE_PATH = r"%transferDirectory%"


def _parse_datetime(value):
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


class EventReader(object):

    EVENT_COLUMN_MAP = {
        "eventType": "event_type",
        "eventDetail": "event_detail",
        "eventOutcome": "event_outcome",
        "eventOutcomeDetailNote": "event_outcome_detail",
        # TODO: eventDetailExtension
        # TODO: eventOutcomeDetailExtension
    }
    AGENT_COLUMN_MAP = {
        "agentIdentifierType": "identifiertype",
        "agentIdentifierValue": "identifiervalue",
        "agentName": "name",
        "agentType": "agenttype",
    }

    def __init__(self, file_handle, fieldnames=None, *args, **kwargs):
        self._fieldnames = fieldnames
        self.reader = csv.reader(file_handle, *args, **kwargs)
        self.current_agent = None

    def __iter__(self):
        return self

    @property
    def line_num(self):
        return self.reader.line_num

    @property
    def fieldnames(self):
        if self._fieldnames is None:
            self._fieldnames = next(self.reader, None)

        return self._fieldnames

    @fieldnames.setter
    def fieldnames(self, value):
        self._fieldnames = value

    def next(self):
        if self.line_num == 0:
            self.fieldnames  # Populates fieldnames if empty

        row = self.reader.next()

        # Ignore blank rows
        while row == []:
            row = self.reader.next()

        filename = None
        event = {}
        agent = None
        agents = []

        for column, value in zip(self.fieldnames, row):
            value = value.decode("utf-8")
            if not value:
                continue

            if column == "filename":
                filename = value
            elif column in self.EVENT_COLUMN_MAP:
                event[self.EVENT_COLUMN_MAP[column]] = value
            elif column == "eventDateTime":
                try:
                    event["event_datetime"] = _parse_datetime(value)
                except ValueError:
                    logger.warning(
                        'Error parsing eventDateTime value "%s" on line %s',
                        value,
                        self.line_num,
                    )
            elif column in self.AGENT_COLUMN_MAP:
                if agent is None:
                    agent = {}
                agent[self.AGENT_COLUMN_MAP[column]] = value

            if column == "agentType":
                # agentType marks the end of an agent
                agents.append(agent)
                agent = None

        # If we didn't get as far as the agentType column, include the remainder
        if agent is not None:
            agents.append(agent)

        return filename, event, agents


def parse_events_csv(csv_path, file_queryset):
    with open(csv_path, "rb") as csv_file:
        reader = EventReader(csv_file)

        for filename, event_data, agents in reader:
            if filename is None:
                logger.warning("Row on line %s misssing filename", reader.line_num)
                continue

            original_location = "".join([DB_BASE_PATH, filename])
            try:
                file_obj = file_queryset.get(originallocation=original_location)
            except File.DoesNotExist:
                logger.warning(
                    'Filename "%s" referenced on line %s not found',
                    filename,
                    reader.line_num,
                )
                continue

            agent_objs = []
            for agent_data in agents:
                agent, _ = Agent.objects.get_or_create(**agent_data)
                agent_objs.append(agent)

            event = Event.objects.create(file_uuid=file_obj, **event_data)
            event.agents.add(*agent_objs)

            # The event_datetime field is auto_now, which will ignore what we pass
            # to create. Work around this with another query to update the row :(
            event_datetime = event_data.get("event_datetime", None)
            if event_datetime is not None:

                Event.objects.filter(pk=event.pk).update(event_datetime=event_datetime)

            yield event, reader.line_num


def call(jobs):
    for job in jobs:
        with job.JobContext(logger=logger):
            transfer_uuid = job.args[1]
            csv_path = job.args[2]

            if os.path.isfile(csv_path):
                file_queryset = File.objects.filter(transfer_id=transfer_uuid)
                with transaction.atomic():
                    for event, line_num in parse_events_csv(csv_path, file_queryset):
                        job.pyprint(
                            "Imported PREMIS event and assigned UUID",
                            event.uuid,
                            "(",
                            csv_path,
                            " line ",
                            line_num,
                            ")",
                        )

            else:
                job.pyprint("No events CSV file found at path: ", csv_path)

            job.set_status(0)
