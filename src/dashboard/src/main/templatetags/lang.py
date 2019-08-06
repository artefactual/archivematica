# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django import template

register = template.Library()


@register.filter
def standardize_lang_code(language_code):
    """Django uses language codes like es-es or pt-br. This will convert them
    into es_ES and pt_BR."""
    head, sep, tail = language_code.partition("-")
    if sep == "":
        return head
    return "{}_{}".format(head, tail.upper())
