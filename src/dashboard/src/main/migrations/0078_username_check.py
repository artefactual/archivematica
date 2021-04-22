# -*- coding: utf-8 -*-
"""Ensures that the username attribute does not exceed maximum expected length.

Column ``auth_user.username`` has a max_length of 150 characters since Django
brought migration  ``auth.0012_alter_user_first_name_max_length``.

Archivematica v1.11 users should have a higher limit (250 characters), brought
by a Django app we used to have installed: ``longerusename``.

In order to avoid potential conflicts down the road, this migration raises an
exception to ensure that the user deals with the situation upfront. If any user
in the system exceed the new limit, we raise an error. The user has two options
at this point:

1. Manually trim the affected users in the database, or
2. Mark the migration as executed using ``manage.py main 0078 --fake``.

The error will not be raised when ``--no-input`` is used, which may be useful
for users that want to deal with the situation later or ignore it entirely.
"""
from __future__ import unicode_literals

import sys

from django.db import migrations
from django.db.models import Max
from django.db.models.functions import Length

# Set in ``auth.0008_alter_user_username_max_length``.
_DJANGO_USERNAME_MAX_LENGTH = 150


def data_migration_up(apps, schema_editor):
    User = apps.get_model("auth", "User")
    result = User.objects.annotate(username_len=Length("username")).aggregate(
        Max("username_len")
    )
    maxlen = result["username_len__max"]
    interactive = "--no-input" not in sys.argv
    if interactive and maxlen is not None and maxlen > _DJANGO_USERNAME_MAX_LENGTH:
        raise Exception(
            "At least one user in the system exceeds the maximum number of"
            " characters expected in the username field."
            " In order to continue, mark this migration as run with"
            ' "manage.py main 0078 --fake" or manually trim the username'
            " attribute where needed before you continue running the remaining"
            " migrations."
        )


def data_migration_down(apps, schema_editor):
    "Reversible migration."
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0077_uuid_fields"),
        ("auth", "0007_alter_validators_add_error_messages"),
    ]

    operations = [migrations.RunPython(data_migration_up, data_migration_down)]
