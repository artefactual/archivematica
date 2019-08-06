"""
Unit (or alternatively package) related logic.
"""
from __future__ import unicode_literals

import abc
import ast
import logging
import os

import scandir
from django.conf import settings as django_settings
from django.utils import six
from lxml import etree

from main import models


logger = logging.getLogger("archivematica.mcp.server")


BASE_REPLACEMENTS = {
    r"%tmpDirectory%": os.path.join(django_settings.SHARED_DIRECTORY, "tmp", ""),
    r"%processingDirectory%": django_settings.PROCESSING_DIRECTORY,
    r"%watchDirectoryPath%": django_settings.WATCH_DIRECTORY,
    r"%rejectedDirectory%": django_settings.REJECTED_DIRECTORY,
}


def get_file_replacement_mapping(file_obj, unit_directory):
    mapping = BASE_REPLACEMENTS.copy()
    dirname = os.path.dirname(file_obj.currentlocation)
    name, ext = os.path.splitext(file_obj.currentlocation)
    name = os.path.basename(name)

    absolute_path = file_obj.currentlocation.replace(r"%SIPDirectory%", unit_directory)
    absolute_path = absolute_path.replace(r"%transferDirectory%", unit_directory)

    mapping.update(
        {
            r"%fileUUID%": file_obj.pk,
            r"%originalLocation%": file_obj.originallocation,
            r"%currentLocation%": file_obj.currentlocation,
            r"%fileGrpUse%": file_obj.filegrpuse,
            r"%fileDirectory%": dirname,
            r"%fileName%": name,
            r"%fileExtension%": ext[1:],
            r"%fileExtensionWithDot%": ext,
            r"%relativeLocation%": absolute_path,
            # TODO: standardize duplicates
            r"%inputFile%": absolute_path,
            r"%fileFullName%": absolute_path,
        }
    )

    return mapping


@six.add_metaclass(abc.ABCMeta)
class Unit(object):
    """The end result of a workflow (AIP, SIP, etc.)
    """

    def __init__(self, current_path, uuid):
        self._current_path = current_path.replace(
            r"%sharedPath%", django_settings.SHARED_DIRECTORY
        )
        self.uuid = uuid

    def __repr__(self):
        return '{class_name}("{current_path}", {uuid})'.format(
            class_name=self.__class__.__name__,
            uuid=self.uuid,
            current_path=self.current_path,
        )

    @property
    def current_path(self):
        return self._current_path

    @current_path.setter
    def current_path(self, value):
        """Ensure that we always have a real (no shared dir vars) path.
        """
        self._current_path = value.replace(
            r"%sharedPath%", django_settings.SHARED_DIRECTORY
        )

    @property
    def current_path_for_db(self):
        return self.current_path.replace(
            django_settings.SHARED_DIRECTORY, "%sharedPath%", 1
        )

    @property
    def package_name(self):
        basename = os.path.basename(self.current_path.rstrip("/"))
        return basename.replace("-" + self.uuid, "")

    @property
    def base_queryset(self):
        return models.File.objects.filter(sip_id=self.uuid)

    def reload(self):
        raise NotImplementedError

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = BASE_REPLACEMENTS.copy()
        mapping.update(
            {
                r"%SIPUUID%": self.uuid,
                r"%SIPName%": self.package_name,
                r"%SIPLogsDirectory%": os.path.join(self.current_path, "logs", ""),
                r"%SIPObjectsDirectory%": os.path.join(
                    self.current_path, "objects", ""
                ),
                r"%SIPDirectory%": self.current_path,
                r"%SIPDirectoryBasename": os.path.basename(
                    os.path.abspath(self.current_path)
                ),
                r"%relativeLocation%": self.current_path_for_db,
            }
        )

        return mapping

    def xmlify(self):
        ret = etree.Element("unit")
        etree.SubElement(ret, "type").text = self.__class__.__name__
        unitXML = etree.SubElement(ret, "unitXML")
        etree.SubElement(unitXML, "UUID").text = self.uuid
        etree.SubElement(unitXML, "currentPath").text = self.current_path_for_db

        return ret

    def files(
        self, filter_filename_start=None, filter_filename_end=None, filter_subdir=None
    ):
        """Generator that yields all files associated with the package.
        """
        queryset = self.base_queryset

        if filter_filename_start:
            # TODO: regex filter
            raise NotImplementedError("filter_filename_start is not implemented")
        if filter_filename_end:
            queryset = queryset.filter(currentlocation__endswith=filter_filename_end)
        if filter_subdir:
            filter_path = "".join([self.REPLACEMENT_PATH_STRING, filter_subdir])
            queryset = queryset.filter(currentlocation__startswith=filter_path)

        # If we don't have any matching files in the database, we're in the process of
        # generating file UUIDs, so walk the filesystem.
        # TODO: restructure workflow to remove these cases.
        if not queryset.exists():
            start_path = self.current_path.encode("utf-8")  # use bytes to return bytes
            if filter_subdir:
                start_path = start_path + filter_subdir.encode("utf-8")

            for basedir, subdirs, files in scandir.walk(start_path):
                for file_name in files:
                    if (
                        filter_filename_start
                        and not file_name.startswith(filter_filename_start)
                    ) or (
                        filter_filename_end
                        and not file_name.endswith(filter_filename_end)
                    ):
                        continue

                    file_path = os.path.join(basedir, file_name)
                    yield {
                        r"%relativeLocation%": file_path,
                        r"%fileUUID%": "",
                        r"%fileGrpUse%": "",
                    }
        else:
            for file_obj in queryset.iterator():
                yield get_file_replacement_mapping(file_obj, self.current_path)

    def set_variable(self, key, value, chain_link_id):
        """Sets a UnitVariable, which tracks choices made by users during processing.
        """
        # TODO: refactor this concept
        if not value:
            value = ""

        unit_var, created = models.UnitVariable.objects.update_or_create(
            unittype=self.UNIT_VARIABLE_TYPE,
            unituuid=self.uuid,
            variable=key,
            defaults=dict(variablevalue=value, microservicechainlink=chain_link_id),
        )
        if created:
            message = ("New UnitVariable %s created for %s: %s (MSCL: %s)",)
        else:
            message = ("Existing UnitVariable %s for %s updated to %s (MSCL" " %s)",)

        logger.info(message, key, self.uuid, value, chain_link_id)

    def get_variable_values(self):
        """
        Returns a dict combining all of the replacementDict unit variables for the
        unit.
        """
        unit_vars = dict()

        # TODO: we shouldn't need one UnitVariable per chain, with all the same values
        unit_vars_queryset = models.UnitVariable.objects.filter(
            unituuid=self.uuid, variable="replacementDict"
        )
        # Distinct helps here, at least
        unit_vars_queryset = unit_vars_queryset.values_list("variablevalue").distinct()
        for unit_var_value in unit_vars_queryset:
            # TODO: nope nope nope, fix eval usage
            try:
                unit_var = ast.literal_eval(unit_var_value[0])
            except ValueError:
                logger.exception(
                    "Failed to eval unit variable value %s", unit_var_value[0]
                )
            else:
                unit_vars.update(unit_var)

        return unit_vars


class DIP(Unit):
    REPLACEMENT_PATH_STRING = r"%SIPDirectory%"
    UNIT_VARIABLE_TYPE = "DIP"
    JOB_UNIT_TYPE = "unitDIP"

    def reload(self):
        """Reload is called for all unit types, but is a no-op for DIPs.
        """
        pass

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = super(DIP, self).get_replacement_mapping(
            filter_subdir_path=filter_subdir_path
        )
        mapping[r"%unitType%"] = "DIP"

        if filter_subdir_path:
            relative_location = filter_subdir_path.replace(
                django_settings.SHARED_DIRECTORY, "%sharedPath%", 1
            )
            mapping[r"%relativeLocation%"] = relative_location

        return mapping


class Transfer(Unit):
    REPLACEMENT_PATH_STRING = r"%transferDirectory%"
    UNIT_VARIABLE_TYPE = "Transfer"
    JOB_UNIT_TYPE = "unitTransfer"

    @property
    def base_queryset(self):
        return models.File.objects.filter(transfer_id=self.uuid)

    def reload(self):
        transfer = models.Transfer.objects.get(uuid=self.uuid)
        self.current_path = transfer.currentlocation

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = super(Transfer, self).get_replacement_mapping(
            filter_subdir_path=filter_subdir_path
        )

        mapping.update(
            {self.REPLACEMENT_PATH_STRING: self.current_path, r"%unitType%": "Transfer"}
        )

        return mapping


class SIP(Unit):
    REPLACEMENT_PATH_STRING = r"%SIPDirectory%"
    UNIT_VARIABLE_TYPE = "SIP"
    JOB_UNIT_TYPE = "unitSIP"

    def __init__(self, *args, **kwargs):
        super(SIP, self).__init__(*args, **kwargs)

        self.aip_filename = None
        self.sip_type = None

    def reload(self):
        sip = models.SIP.objects.get(uuid=self.uuid)
        self.current_path = sip.currentpath
        self.aip_filename = sip.aip_filename or ""
        self.sip_type = sip.sip_type

    def get_replacement_mapping(self, filter_subdir_path=None):
        mapping = super(SIP, self).get_replacement_mapping(
            filter_subdir_path=filter_subdir_path
        )

        mapping.update(
            {
                r"%unitType%": "SIP",
                r"%AIPFilename%": self.aip_filename,
                r"%SIPType%": self.sip_type,
            }
        )

        return mapping
