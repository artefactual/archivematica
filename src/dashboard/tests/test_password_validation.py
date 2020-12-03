# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pytest

from django.contrib.auth.password_validation import (
    get_password_validators,
    validate_password,
)
from django.core.exceptions import ValidationError


@pytest.mark.parametrize(
    "password,raises_exception",
    [
        # Passwords with only one type raise ValidationError.
        ("abcdefghijk", True),
        ("ABCDEFGHIJK", True),
        ("12345678", True),
        ("@#!_-=^$", True),
        # Passwords with only two types raise ValidationError. Accented upper
        # and lower case letters are treated as their ASCII equivalents and do
        # not count as a special character.
        ("abcdeFGHIJK", True),
        ("ABÇDEF1234", True),
        ("àbcdef!$@", True),
        # Passwords with three types pass validation.
        ("abcdef123!@#", False),
        ("ABCdef12345", False),
        ("#@!abcdefGHIJK", False),
        # Passwords with all four types pass validation.
        ("abcDEF123!@#", False),
        ("#l33t#PASSWORD!", False),
    ],
)
def test_password_complexity_validator(password, raises_exception):
    VALIDATOR_CONFIG = [
        {"NAME": "components.accounts.validators.PasswordComplexityValidator"}
    ]
    validators = get_password_validators(VALIDATOR_CONFIG)

    if raises_exception:
        with pytest.raises(ValidationError):
            _ = validate_password(password, password_validators=validators)
    else:
        _ = validate_password(password, password_validators=validators)
