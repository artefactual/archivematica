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

from __future__ import unicode_literals

import importlib
import json
import os
import pprint

from django.utils.six import text_type, python_2_unicode_compatible
from jsonschema import validate, FormatChecker
from jsonschema.exceptions import ValidationError

from main.models import Job


_LATEST_SCHEMA = "workflow-schema-v1.json"

_UNKNOWN_TRANSLATION_LABEL = "<unknown>"

_FALLBACK_LANG = "en"


def _load_job_statuses():
    """Return an inverted dict of job statuses, i.e. indexed by labels."""
    ret = {}
    for id_, proxy in dict(Job.STATUS).items():
        label = getattr(proxy, "_proxy____args")[0]
        ret[label] = id_
    return ret


# Job statuses (from ``main.models.Job.STATUS``) indexed by the English labels.
# This is useful when decoding the values used in the JSON-encoded workflow
# where we're using labels instead of IDs.
_STATUSES = _load_job_statuses()


@python_2_unicode_compatible
class TranslationLabel(object):
    """Mixin for easy access to translated messages.

    The JSON-encoded workflow uses ``object`` (mapping type) to associate
    messages for a particular property to language codes, e.g.::

        {
            "en": "cat",
            "es": "gato"
        }

    ``json`` decodes it as a ``dict``. This class wraps the dictionary so it is
    easier to access the translations. Usage example::

        >>> message = {"en": "cat", "es": "gato"}
        >>> tr = TranslationLabel(message)
        >>> tr
        TranslationLabel <{'en': 'cat', 'es': 'gato'}>
        >>> str(tr)
        'cat'
        >>> tr["es"]
        'gato'
        >>> tr["foobar"]
        'cat'
        >>> tr.get_label(lang="es")
        'gato'
        >>> tr.get_label(lang="is", "köttur")
        'köttur'

    """

    def __init__(self, translations):
        if not isinstance(translations, dict):
            translations = {_FALLBACK_LANG: text_type(translations)}
        self._src = translations

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, pprint.saferepr(self._src))

    def __str__(self):
        return self.get_label()

    def __getitem__(self, lang):
        return self.get_label(lang)

    def _prepare_lang(self, lang):
        parts = lang.partition("-")
        if parts[1] == "-":
            return "{}_{}".format(parts[0], parts[2].upper())
        return lang

    def get_label(self, lang=_FALLBACK_LANG, fallback_label=None):
        """Get the translation of a message.

        It defaults to ``_FALLBACK_LANG`` unless ``lang`` is used.
        It accepts a ``fallback_label``,  used when the message is not
        available in the language given. As a last resort, it returns
        ``_UNKNOWN_TRANSLATION_LABEL``.
        """
        lang = self._prepare_lang(lang)
        if lang in self._src:
            return self._src[lang]
        if fallback_label is not None:
            return fallback_label
        return self._src.get(_FALLBACK_LANG, _UNKNOWN_TRANSLATION_LABEL)


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

    def get_label(self, key, lang=_FALLBACK_LANG, fallback_label=None):
        """Proxy to find translated attributes."""
        try:
            instance = self._src[key]
        except KeyError:
            return None
        return instance.get_label(lang, fallback_label)

    def _decode_translation(self, translation_dict):
        return TranslationLabel(translation_dict)


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
    def manager(self):
        name = self._src["config"]["@manager"]
        module = importlib.import_module(name)
        return getattr(module, name)

    @property
    def config(self):
        return self._src["config"]

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
    return json.loads(blob, cls=WorkflowJSONDecoder)


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
    dirname = os.path.dirname(os.path.realpath(__file__))
    schema = os.path.join(dirname, "assets", _LATEST_SCHEMA)
    with open(schema) as fp:
        return json.load(fp)
