# -*- coding: utf-8 -*-
"""Validation of transfer documents.

Usage example::

    >> validator = get_validator("avalon")
    >> validator.validate(b"...")
    True

Expect the ``validate`` method to raise ``ValidationError`` when validation
does not pass. The exception may include a message with more details.

New validators must be added to the `` _VALIDATORS`` registry.
"""
from __future__ import absolute_import

import collections
import csv
from io import BytesIO
from six import PY2, StringIO


class ValidationError(Exception):
    """Validators should raise this exception when the input is invalid."""


class BaseValidator(object):
    def validate(self, string):
        """Validator must implement this method.

        Raise ``ValidationError`` when a validation error occurs. Otherwise,
        return ``True``."""
        raise NotImplementedError


class AvalonValidator(BaseValidator):
    @staticmethod
    def _check_admin_data(row):
        """Raise if the administrative data line in an Avalon CSV is missing."""
        err = ValidationError(
            "Administrative data must include reference name and author."
        )
        if len(row) < 2:
            raise err
        name = row[0]
        author = row[1]
        if not bool(name and author):
            raise err

    @staticmethod
    def _check_header_data(row):
        """Validate header data line in an Avalon CSV.

        :param row: list: metadata fields
        """
        all_headers = [
            "Bibliographic ID",
            "Bibliographic ID Label",
            "Other Identifier",
            "Other Identifier Type",
            "Title",
            "Creator",
            "Contributor",
            "Genre",
            "Publisher",
            "Date Created",
            "Date Issued",
            "Abstract",
            "Language",
            "Physical Description",
            "Related Item URL",
            "Related Item Label",
            "Topical Subject",
            "Geographic Subject",
            "Temporal Subject",
            "Terms of Use",
            "Table of Contents",
            "Statement of Responsibility",
            "Note",
            "Note Type",
            "Publish",
            "Hidden",
            "File",
            "Label",
            "Offset",
            "Skip Transcoding",
            "Absolute Location",
            "Date Ingested",
        ]
        req_headers = ["Title", "Date Issued", "File"]
        unique_headers = [
            "Bibliographic ID",
            "Bibliographic ID Label",
            "Title",
            "Date Created",
            "Date Issued",
            "Abstract",
            "Physical Description",
            "Terms of Use",
        ]
        collected_headers = list(collections.Counter(row).items())
        repeated_headers = [k for k, v in collected_headers if v > 1]

        for x in row:
            while "" in row:
                row.remove("")
            if x[0] == " " or x[-1] == " ":
                raise ValidationError(
                    (
                        "Header fields cannot have leading or trailing blanks. Invalid field: "
                        + str(x)
                    )
                )

        if not (set(row).issubset(set(all_headers))):
            raise ValidationError(
                "Manifest includes invalid metadata field(s). Invalid field(s): "
                + ",".join(list(set(row) - set(all_headers)))
            )

        if any(x in repeated_headers for x in unique_headers):
            raise ValidationError(
                "A non-repeatable header field is repeated. Repeating field(s): "
                + ",".join(repeated_headers)
            )

        if not (all(x in row for x in req_headers)):
            if "Bibliographic ID" not in row:
                raise ValidationError(
                    (
                        "One of the required headers is missing: Title, Date Issued, File."
                    )
                )
        return True

    @staticmethod
    def _get_file_columns(row):
        """Identify columns containing file data.

        :param row: list: metadata fields
        """
        columns = []
        for i, field in enumerate(row):
            if field == "File":
                columns.append(i)
        return columns

    @staticmethod
    def _get_op_columns(row):
        """Identify columns containing file data.

        :param row: list: metadata fields
        """
        columns = []
        for i, field in enumerate(row):
            if field == "Publish" or field == "Hidden":
                columns.append(i)
        return columns

    @staticmethod
    def _check_field_pairs(row):
        """Checks paired fields have associated pair.

        :param row: list: metadata fields
        """
        for i, field in enumerate(row):
            if field == "Other Identifier Type":
                if not all(
                    f in row for f in ["Other Identifier", "Other Identifier Type"]
                ):
                    raise ValidationError(
                        ("Other Identifier Type field missing its required pair.")
                    )
            if field == "Related Item Label":
                if not all(
                    f in row for f in ["Related Item URL", "Related Item Label"]
                ):
                    raise ValidationError(
                        ("Related Item Label field missing its required pair.")
                    )
            if field == "Note Type":
                if not all(f in row for f in ["Note", "Note Type"]):
                    raise ValidationError(
                        ("Note Type field missing its required pair.")
                    )

    @staticmethod
    def _check_file_exts(row, file_cols):
        """Checks for only one period in filepath, unless specifying transcoded
        video quality.

        :param row: list: metadata fields
        :param file_cols: list: columns holding file data
        """
        for c in file_cols:
            if row[c].count(".") > 1 and not any(
                q in row[c] for q in [".high.", ".medium.", ".low"]
            ):
                raise ValidationError(
                    ("Filepath " + row[c] + " contains" " more than one period.")
                )

    @staticmethod
    def _check_op_fields(row, op_cols):
        """Checks that operational fields are marked only as "yes" or "no".

        :param row: list: metadata fields
        :param op_cols: list: columns holding operational field data
        """
        for c in op_cols:
            if row[c]:
                if not (row[c].lower() == "yes" or row[c].lower() == "no"):
                    raise ValidationError(
                        (
                            "Publish/Hidden fields must have boolean value (yes or no). Value is "
                            + str(row[c])
                        )
                    )

    def validate(self, string):
        if PY2:
            csvfile = BytesIO(string)
        else:
            csvfile = StringIO(string.decode("utf8"))
        csvr = csv.reader(csvfile)
        for i, row in enumerate(csvr):
            if i == 0:
                self._check_admin_data(row)
            if i == 1:
                self._check_header_data(row)
                file_cols = self._get_file_columns(row)
                op_cols = self._get_op_columns(row)
                self._check_field_pairs(row)
            if i >= 2:
                self._check_file_exts(row, file_cols)
                self._check_op_fields(row, op_cols)
        try:
            i
        except NameError:
            raise ValidationError("The document is empty.")
        else:
            if i < 2:
                raise ValidationError("The document is incomplete.")
        return True


_VALIDATORS = {"avalon": AvalonValidator}


class ValidatorNotAvailableError(ValueError):
    default = "Unknown validator. Accepted values: {}".format(
        ",".join(list(_VALIDATORS.keys()))
    )

    def __init__(self, *args, **kwargs):
        if not (args or kwargs):
            args = (self.default,)
        super(ValidatorNotAvailableError, self).__init__(*args, **kwargs)


def get_validator(name):
    try:
        klass = _VALIDATORS[name]
    except KeyError:
        raise ValidatorNotAvailableError
    return klass()
