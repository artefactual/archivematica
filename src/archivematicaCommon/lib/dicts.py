# -*- coding: utf-8 -*-
# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage MCPServer
# @author Joseph Perry <joseph@artefactual.com>
from __future__ import absolute_import

import ast
import os
import re

import six

from archivematicaFunctions import unicodeToStr

from main import models


config = {}


def setup(shared_directory, processing_directory, watch_directory, rejected_directory):
    config["shared_directory"] = shared_directory
    config["processing_directory"] = processing_directory
    config["watch_directory"] = watch_directory
    config["rejected_directory"] = rejected_directory


def replace_string_values(string, **kwargs):
    """
    Replace standard Archivematica variables in a string given data from
    the database to use to populate them.

    This function is just a wrapper around ReplacementDict.frommodel().replace(string)[0].
    The keyword arguments to this function are identical to the keyword
    arguments to ReplacementDict.frommodel.
    """
    rd = ReplacementDict.frommodel(**kwargs)
    return rd.replace(string)[0]


class ReplacementDict(dict):
    @staticmethod
    def fromstring(s):
        """
        Create a new ReplacementDict given a string representing a
        serialized Python dict. This is commonly used within the
        MCPServer, where unit variables are frequently dicts stored
        in the database.
        """
        return ReplacementDict(ast.literal_eval(s))

    @staticmethod
    def frommodel(type_="file", sip=None, file_=None, expand_path=True):
        """
        Creates a new ReplacementDict option with the standard variables
        populated based on values taken from the models passed in.
        SIP and File instances can be passed as arguments, using the sip
        and file_ keyword arguments respectively. sip accepts both SIP
        and Transfer objects.

        By default, path strings returned via this constructor are not
        absolute, but include the %sharedPath% variable in place of the
        actual path to the Archivematica shared path. This matches the
        behaviour previously used by the ReplacementDict construction code
        in the Unit classes, and is suitable for passing paths to the
        MCPClient. If the expand_path keyword argument is set to True,
        then true absolute paths will be returned instead. This is useful
        when creating ReplacementDicts within MCPClient scripts.

        If both sip and file_ are passed in, values from both will be
        included. Since there is some overlap in variable naming, the
        type_ keyword argument must be used to indicate the context
        in which the dict is being created. Supported values are 'file',
        'sip', and 'transfer'. The default is 'file'.
        """

        # Currently, MCPServer does not use the Django ORM.
        # In order to make this code accessible to MCPServer,
        # we need to support passing in UUID strings instead
        # of models.
        if isinstance(file_, six.string_types):
            file_ = models.File.objects.get(uuid=file_)
        if isinstance(sip, six.string_types):
            # sip can be a SIP or Transfer
            try:
                sip = models.SIP.objects.get(uuid=sip)
            except:
                sip = models.Transfer.objects.get(uuid=sip)

        shared_path = config["shared_directory"]

        # We still want to set SIP variables, even if no SIP or Transfer
        # was passed in, so try to fetch it from the file
        if file_ and not sip:
            try:
                sip = file_.sip
            except:
                sip = file_.transfer

        rd = ReplacementDict()
        sipdir = None
        if sip:
            if isinstance(sip, models.Transfer):
                relative_location = sip.currentlocation
            else:
                relative_location = sip.currentpath
            if expand_path:
                sipdir = relative_location.replace("%sharedPath%", shared_path)
            else:
                sipdir = relative_location

            rd["%SIPUUID%"] = sip.uuid
            sip_name = os.path.basename(sipdir.rstrip("/")).replace("-" + sip.uuid, "")
            rd["%SIPName%"] = sip_name
            rd["%currentPath%"] = sipdir
            rd["%SIPDirectory%"] = sipdir
            rd["%SIPDirectoryBasename%"] = os.path.basename(os.path.abspath(sipdir))
            rd["%SIPLogsDirectory%"] = os.path.join(sipdir, "logs", "")
            rd["%SIPObjectsDirectory%"] = os.path.join(sipdir, "objects", "")
            if type_ == "sip":
                rd["%relativeLocation%"] = relative_location
            elif type_ == "transfer":
                rd["%transferDirectory%"] = sipdir
                rd["%relativeLocation%"] = relative_location

        if file_:
            rd["%fileUUID%"] = file_.uuid
            try:
                base_location = file_.sip.currentpath
            except:
                base_location = file_.transfer.currentlocation

            if expand_path and sipdir is not None:
                base_location = base_location.replace("%sharedPath%", shared_path)
                origin = file_.originallocation.replace(
                    "%transferDirectory%", base_location
                )
                current_location = file_.currentlocation.replace(
                    "%transferDirectory%", base_location
                )
                current_location = current_location.replace("%SIPDirectory%", sipdir)
            else:
                origin = file_.originallocation
                current_location = file_.currentlocation
            rd["%originalLocation%"] = origin
            rd["%currentLocation%"] = current_location
            rd["%fileDirectory%"] = os.path.dirname(current_location)
            rd["%fileGrpUse%"] = file_.filegrpuse
            if type_ == "file":
                rd["%relativeLocation%"] = current_location

            # These synonyms were originally defined by the Normalize microservice
            rd["%inputFile%"] = current_location
            rd["%fileFullName%"] = current_location
            name, ext = os.path.splitext(current_location)
            rd["%fileName%"] = os.path.basename(name)
            rd["%fileExtension%"] = ext[1:]
            rd["%fileExtensionWithDot%"] = ext

        rd["%tmpDirectory%"] = os.path.join(config["shared_directory"], "tmp", "")
        rd["%processingDirectory%"] = config["processing_directory"]
        rd["%watchDirectoryPath%"] = config["watch_directory"]
        rd["%rejectedDirectory%"] = config["rejected_directory"]

        return rd

    def replace(self, *strings):
        """
        Iterates over a set of strings. Any keys in self found within
        the string will be replaced with their respective values.
        Returns an array of strings, regardless of the number of parameters
        pased in. For example:

        >>> rd = ReplacementDict({"$foo": "bar"})
        >>> rd.replace('The value of the foo variable is: $foo')
        ['The value of the foo variable is: bar']

        IMPORTANT NOTE: Any unicode strings present as dictionary values will
        be converted into bytestrings. All returned strings will also be
        bytestrings, regardless of the type of the original strings.
        Returned strings may or may not be valid Unicode, depending on the
        contents of data fetched from the database. (%originalLocation%,
        for instance, may contain arbitrary non-Unicode characters of
        nonspecific encoding.)

        Note that, within, Archivematica, the only value that typically
        contains Unicode characters is "%originalLocation%", and Archivematica
        does not use this variable in any place where precise fidelity of the
        original string is required.
        """
        ret = []
        for orig in strings:
            if orig is not None:
                orig = unicodeToStr(orig)
                for key, value in self.items():
                    orig = orig.replace(key, unicodeToStr(value))
            ret.append(orig)
        return ret

    def to_gnu_options(self):
        """
        Returns the replacement dict's values as an array of GNU-style
        long options. This is primarily useful for passing options to
        FPR commands. For example:

        >>> rd = ReplacementDict({'%foo%': 'bar'})
        >>> rd.to_gnu_options()
        ['--foo=bar']
        """
        args = []
        for key, value in self.items():
            optname = re.sub(r"([A-Z]+)", r"-\1", key[1:-1]).lower()
            opt = "--{k}={v}".format(k=optname, v=value)
            args.append(opt)

        return args


class ChoicesDict(ReplacementDict):
    @staticmethod
    def fromstring(s):
        """
        See ReplacementDict.fromstring.
        """
        return ChoicesDict(ast.literal_eval(s))
