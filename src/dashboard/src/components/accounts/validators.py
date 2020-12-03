# -*- coding: utf-8 -*-
from __future__ import absolute_import
import six

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _


class PasswordComplexityValidator(object):
    """Custom password complexity validator.

    To pass validation, passwords must contain at least three of:
    - uppercase characters
    - lowercase characters
    - numbers
    - special characters
    """

    HELP_TEXT = _(
        "Your password must contain at least 3 of: uppercase characters, "
        "lowercase characters, numbers, and special characters (symbols or "
        "non-alphanumeric Unicode characters)."
    )

    def validate(self, password, user=None):
        type_count = 0

        has_lower = False
        has_upper = False
        has_number = False
        has_special = False

        unicode_password = six.ensure_text(password, errors="ignore")
        for char in unicode_password:
            if char.islower():
                has_lower = True
            elif char.isupper():
                has_upper = True
            elif char.isdigit():
                has_number = True
            else:
                has_special = True

        CHARACTER_TYPES = (has_lower, has_upper, has_number, has_special)
        type_count = sum(val is True for val in CHARACTER_TYPES)

        if type_count < 3:
            raise ValidationError(self.HELP_TEXT, code="notcomplex")

    def get_help_text(self):
        return self.HELP_TEXT
