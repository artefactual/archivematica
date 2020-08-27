# -*- coding: utf-8 -*-

"""FSEntriesTree

Taken from Cole's transfer METS code completed for SFU...
"""

import logging
from lxml import etree
import os
import scandir

from django.db.models import Prefetch

import metsrw

from main.models import Derivation, Directory, File, FPCommandOutput

from archivematicaFunctions import escape


PREMIS_META = metsrw.plugins.premisrw.PREMIS_3_0_META
FILE_PREMIS_META = PREMIS_META.copy()
FILE_PREMIS_META["xsi:type"] = "premis:file"
IE_PREMIS_META = PREMIS_META.copy()
IE_PREMIS_META["xsi:type"] = "premis:intellectualEntity"


FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("fs_entries_tree")


class FSEntriesTree(object):
    """
    Builds a tree of FSEntry objects from the path given, and looks up required data
    from the database.
    """

    QUERY_BATCH_SIZE = 2000
    TRANSFER_RIGHTS_LOOKUP_UUID = "45696327-44c5-4e78-849b-e027a189bf4d"
    FILE_RIGHTS_LOOKUP_UUID = "7f04d9d4-92c2-44a5-93dc-b7bfdf0c1f17"

    file_queryset_prefetches = [
        "identifiers",
        "event_set",
        "event_set__agents",
        "fileid_set",
        Prefetch(
            "original_file_set",
            queryset=Derivation.objects.filter(event__isnull=False),
            to_attr="related_has_source",
        ),
        Prefetch(
            "derived_file_set",
            queryset=Derivation.objects.filter(event__isnull=False),
            to_attr="related_is_source_of",
        ),
        Prefetch(
            "fpcommandoutput_set",
            queryset=FPCommandOutput.objects.filter(
                rule__purpose__in=["characterization", "default_characterization"]
            ),
            to_attr="characterization_documents",
        ),
    ]
    file_queryset = File.objects.prefetch_related(*file_queryset_prefetches).order_by(
        "currentlocation"
    )

    def __init__(self, root_path, db_base_path, transfer):
        """FSEntriesTree Constructor

        :param string root_path: The path to find out files at.
        :param string db_base_path: Template string, e.g. %SIPDirectory%
        :param transfer ORM object: Transfer or SIP entries from db.
        :param structure_only bool: Elect for just a fileSec and StructMap.
        """
        self.root_path = root_path
        self.db_base_path = db_base_path
        self.transfer = transfer

        root_path = root_path.replace("aips/", "").replace("/", "")

        self.root_node = metsrw.FSEntry(
            path=os.path.basename(root_path), type="Directory"
        )
        self.file_index = {}
        self.dir_index = {}

    def scan(self):
        self.build_tree(self.root_path, parent=self.root_node)
        self.load_file_data_from_db()
        self.load_dir_uuids_from_db()
        self.check_for_missing_file_uuids()

    def get_relative_path(self, path):
        return os.path.relpath(path, start=self.root_path)

    def build_tree(self, path, parent=None):
        dir_entries = sorted(scandir.scandir(path), key=lambda d: d.name)
        for dir_entry in dir_entries:
            entry_relative_path = os.path.relpath(dir_entry.path, start=self.root_path)
            if dir_entry.is_dir():
                fsentry = metsrw.FSEntry(
                    path=entry_relative_path, label=dir_entry.name, type="Directory"
                )
                db_path = "".join([self.db_base_path, entry_relative_path, os.path.sep])
                self.dir_index[db_path] = fsentry
                self.build_tree(dir_entry.path, parent=fsentry)
            else:
                fsentry = metsrw.FSEntry(
                    path=entry_relative_path, label=dir_entry.name, type="Item"
                )
                db_path = "".join([self.db_base_path, entry_relative_path])
                self.file_index[db_path] = fsentry

            parent.add_child(fsentry)

    def _batch_query(self, queryset):
        offset, limit = 0, self.QUERY_BATCH_SIZE
        total_count = queryset.count()

        while offset < total_count:
            batch = queryset[offset:limit]
            for item in batch:
                yield item
            offset += self.QUERY_BATCH_SIZE
            limit += self.QUERY_BATCH_SIZE

    def load_file_data_from_db(self):
        file_objs = self.file_queryset.filter(
            sip=self.transfer, removedtime__isnull=True
        )

        for file_obj in self._batch_query(file_objs):
            try:
                fsentry = self.file_index[file_obj.currentlocation]
            except KeyError:
                logger.info(
                    "File is no longer present on the filesystem: %s",
                    file_obj.currentlocation,
                )
                continue

            fsentry.file_uuid = file_obj.uuid
            fsentry.checksum = file_obj.checksum
            fsentry.checksumtype = convert_to_premis_hash_function(
                file_obj.checksumtype
            )
            fsentry.use = file_obj.filegrpuse
            premis_object = file_obj_to_premis(file_obj)
            if premis_object is not None:
                fsentry.add_premis_object(premis_object)

    def load_dir_uuids_from_db(self):
        dir_objs = Directory.objects.prefetch_related("identifiers").filter(
            sip=self.transfer
        )

        for dir_obj in self._batch_query(dir_objs):
            try:
                fsentry = self.dir_index[dir_obj.currentlocation]
            except KeyError:
                logger.info(
                    "Directory is no longer present on the filesystem: %s",
                    dir_obj.currentlocation,
                )
            else:
                premis_intellectual_entity = dir_obj_to_premis(dir_obj)
                fsentry.add_premis_object(premis_intellectual_entity)

    def check_for_missing_file_uuids(self):
        missing = []
        for path, fsentry in self.file_index.iteritems():
            if fsentry.file_uuid is None:
                logger.info("No record in database for file: %s", path)
                missing.append(path)

        # update our index after, so we don't modify the dict during iteration
        for path in missing:
            fsentry = self.file_index[path]
            fsentry.parent.remove_child(fsentry)
            del self.file_index[path]


# TODO: FSEntryTree Helper functions... (Let's move these out of here...)


def convert_to_premis_hash_function(hash_type):
    """
    Returns a PREMIS valid hash function name, if possible.
    """
    if hash_type.lower().startswith("sha") and "-" not in hash_type:
        hash_type = "SHA-" + hash_type.upper()[3:]
    elif hash_type.lower() == "md5":
        return "MD5"

    return hash_type


def file_obj_to_premis(file_obj):
    """
    Converts an File model object to a PREMIS event object via metsrw.

    Returns:
        lxml.etree._Element
    """

    # premis_digest_algorithm = convert_to_premis_hash_function(file_obj.checksumtype)
    format_data = get_premis_format_data(file_obj.fileid_set.all())
    original_name = escape(file_obj.originallocation)
    object_identifiers = get_premis_object_identifiers(
        file_obj.uuid, file_obj.identifiers.all()
    )
    object_characteristics_extensions = get_premis_object_characteristics_extension(
        file_obj.characterization_documents
    )

    # WELLCOME TODO: For Wellcome's purpose we only care about these if
    # there is information to care about.
    if len(object_characteristics_extensions) == 0:
        return None

    object_characteristics = (
        "object_characteristics",
        format_data,
        (
            "creating_application",
            (
                "date_created_by_application",
                file_obj.modificationtime.strftime("%Y-%m-%d"),
            ),
        ),
    )

    if object_characteristics_extensions:
        object_characteristics += object_characteristics_extensions

    premis_data = (
        ("object", FILE_PREMIS_META)
        + object_identifiers
        + (object_characteristics, ("original_name", original_name))
    )

    return metsrw.plugins.premisrw.data_to_premis(
        premis_data, premis_version=FILE_PREMIS_META["version"]
    )


def get_premis_format_data(file_ids):
    format_data = ()

    for file_id in file_ids:
        format_data += (
            "format",
            (
                "format_designation",
                ("format_name", file_id.format_name),
                ("format_version", file_id.format_version),
            ),
        )
    if not format_data:
        # default to unknown
        format_data = ("format", ("format_designation", ("format_name", "Unknown")))

    return format_data


def get_premis_object_identifiers(uuid, additional_identifiers):
    object_identifiers = (
        (
            "object_identifier",
            ("object_identifier_type", "UUID"),
            ("object_identifier_value", uuid),
        ),
    )
    return object_identifiers


def get_premis_object_characteristics_extension(documents):
    extensions = ()

    for document in documents:
        # lxml will complain if we pass unicode, even if the XML
        # is UTF-8 encoded.
        # See https://lxml.de/parsing.html#python-unicode-strings
        # This only covers the UTF-8 and ASCII cases.
        xml_element = etree.fromstring(document.content.encode("utf-8"))

        extensions += (("object_characteristics_extension", xml_element),)

    return extensions


def clean_date(date_string):
    if date_string is None:
        return ""

    # Legacy dates may be slash seperated
    return date_string.replace("/", "-")


def dir_obj_to_premis(dir_obj, relative_dir_path=""):
    """
    Converts an Directory model object to a PREMIS object via metsrw.

    Returns:
        lxml.etree._Element
    """
    try:
        original_name = escape(dir_obj.originallocation)
    except AttributeError:
        # We are working with an AIP.
        original_name = escape(relative_dir_path)

    object_identifiers = get_premis_object_identifiers(
        dir_obj.uuid, dir_obj.identifiers.all()
    )

    premis_data = (
        ("object", IE_PREMIS_META)
        + object_identifiers
        + (("original_name", original_name),)
    )

    return metsrw.plugins.premisrw.data_to_premis(
        premis_data, premis_version=IE_PREMIS_META["version"]
    )
