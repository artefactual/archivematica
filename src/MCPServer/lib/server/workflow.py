# -*- coding: utf-8 -*-

"""Workflow decoder and validator.

The main function to start working with this module is ``load``. It decodes the
JSON-encoded bytes and validates the document against the schema.

    >>> import workflow
    >>> with open("workflow.json") as file_object:
            wf = workflow.load(file_object)

If the document cannot be validated, ``jsonschema.ValidationError`` is raised.
Otherwise, ``load`` will return an instance of ``Workflow`` which is used in
MCPServer to read workflow links that can be instances of three different
classes ``Chain``, ``Link`` and ``WatchedDir``. They have different method
sets.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os

from django.utils.six import text_type, python_2_unicode_compatible
from jsonschema import validate, FormatChecker
from jsonschema.exceptions import ValidationError

from server.jobs import Job
from server.translation import FALLBACK_LANG, TranslationLabel


_LATEST_SCHEMA = "workflow-schema-v1.json"
ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(os.path.join(__file__)))), "assets"
)

DEFAULT_WORKFLOW = os.path.join(ASSETS_DIR, "workflow.json")


def _invert_job_statuses():
    """Return an inverted dict of job statuses, i.e. indexed by labels."""
    statuses = {}
    for status in Job.STATUSES:
        label = text_type(status[1])
        statuses[label] = status[0]

    return statuses


# Job statuses (from ``Job.STATUSES``) indexed by the English labels.
# This is useful when decoding the values used in the JSON-encoded workflow
# where we're using labels instead of IDs.
_STATUSES = _invert_job_statuses()


@python_2_unicode_compatible
class Workflow(object):
    def __init__(self, parsed_obj):
        self._src = parsed_obj
        self._decode_chains()
        self._decode_links()
        self._decode_wdirs()

    def __str__(self):
        return "Chains {}, links {}, watched directories: {}".format(
            len(self.chains), len(self.links), len(self.wdirs)
        )

    def _decode_chains(self):
        self.chains = {}
        for chain_id, chain_obj in self._src["chains"].items():
            self.chains[chain_id] = Chain(chain_id, chain_obj, self)

    def _decode_links(self):
        self.links = {}
        for link_id, link_obj in self._src["links"].items():
            self.links[link_id] = Link(link_id, link_obj, self)

    def _decode_wdirs(self):
        self.wdirs = []
        for wdir_obj in self._src["watched_directories"]:
            self.wdirs.append(WatchedDir(wdir_obj, self))

    def get_chains(self):
        return self.chains

    def get_links(self):
        return self.links

    def get_wdirs(self):
        return self.wdirs

    def get_chain(self, chain_id):
        return self.chains[chain_id]

    def get_link(self, link_id):
        return self.links[link_id]


@python_2_unicode_compatible
class BaseLink(object):
    def __str__(self):
        return self.id

    def get_label(self, key, lang=FALLBACK_LANG, fallback_label=None):
        """Proxy to find translated attributes."""
        try:
            instance = self._src[key]
        except KeyError:
            return None
        return instance.get_label(lang, fallback_label)

    def _decode_translation(self, translation_dict):
        return TranslationLabel(translation_dict)

    @property
    def workflow(self):
        return self._workflow


class Chain(BaseLink):
    def __init__(self, id_, attrs, workflow):
        self.id = id_
        self._src = attrs
        self._workflow = workflow
        self._decode_translations()

    def __repr__(self):
        return "Chain <{}>".format(self.id)

    def __getitem__(self, key):
        return self._src[key]

    def _decode_translations(self):
        self._src["description"] = self._decode_translation(self._src["description"])

    @property
    def link(self):
        return self._workflow.get_link(self._src["link_id"])


class Link(BaseLink):
    def __init__(self, id_, attrs, workflow):
        self.id = id_
        self._src = attrs
        self._workflow = workflow
        self._decode_job_statuses()
        self._decode_translations()

    def __repr__(self):
        return "Link <{}>".format(self.id)

    def __getitem__(self, key):
        return self._src[key]

    def _decode_job_statuses(self):
        """Replace status labels with their IDs.

        In JSON, a job status is encoded using its English label, e.g. "Failed"
        instead of the corresponding value in ``JOB.STATUS_FAILED``. This
        method decodes the statuses so it becomes easier to work with them
        internally.
        """
        self._src["fallback_job_status"] = _STATUSES[self._src["fallback_job_status"]]
        for obj in self._src["exit_codes"].values():
            obj["job_status"] = _STATUSES[obj["job_status"]]

    def _decode_translations(self):
        self._src["description"] = self._decode_translation(self._src["description"])
        self._src["group"] = self._decode_translation(self._src["group"])
        config = self._src["config"]
        if config["@manager"] == "linkTaskManagerReplacementDicFromChoice":
            for item in config["replacements"]:
                item["description"] = self._decode_translation(item["description"])

    @property
    def config(self):
        return self._src["config"]

    @property
    def is_terminal(self):
        """Check if the link is indicated as a terminal link."""
        return self._src.get("end", False)

    def get_next_link(self, code):
        code = text_type(code)
        try:
            link_id = self._src["exit_codes"][code]["link_id"]
        except KeyError:
            link_id = self._src["fallback_link_id"]
        return self._workflow.get_link(link_id)

    def get_status_id(self, code):
        """Return the expected Job status ID given an exit code."""
        code = text_type(code)
        try:
            status_id = self._src["exit_codes"][code]["job_status"]
        except KeyError:
            status_id = self._src["fallback_job_status"]
        return status_id


class WatchedDir(BaseLink):
    def __init__(self, attrs, workflow):
        self.path = attrs["path"]
        self._src = attrs
        self._workflow = workflow

    def __str__(self):
        return self.path

    def __repr__(self):
        return "Watched directory <{}>".format(self.path)

    def __getitem__(self, key):
        return self._src[key]

    @property
    def only_dirs(self):
        return bool(self._src["only_dirs"])

    @property
    def unit_type(self):
        return self._src["unit_type"]

    @property
    def chain(self):
        return self._workflow.get_chain(self._src["chain_id"])


class WorkflowJSONDecoder(json.JSONDecoder):
    def decode(self, foo, **kwargs):
        parsed_json = super(WorkflowJSONDecoder, self).decode(foo, **kwargs)
        return Workflow(parsed_json)


def load(fp):
    """Read JSON document from file-like object, validate and decode it."""
    blob = fp.read()  # Read once, used twice.
    _validate(blob)
    parsed = json.loads(blob, cls=WorkflowJSONDecoder)

    return parsed


def load_default_workflow():
    with open(DEFAULT_WORKFLOW) as default_workflow:
        return load(default_workflow)


class SchemaValidationError(ValidationError):
    """It wraps ``jsonschema.exceptions.ValidationError``."""


def _validate(blob):
    """Decode and validate the JSON document."""
    try:
        validate(json.loads(blob), _get_schema(), format_checker=FormatChecker())
    except ValidationError as err:
        raise SchemaValidationError(**err._contents())


def _get_schema():
    """Decode the default schema and return it."""
    schema = os.path.join(ASSETS_DIR, _LATEST_SCHEMA)
    with open(schema) as fp:
        return json.load(fp)
