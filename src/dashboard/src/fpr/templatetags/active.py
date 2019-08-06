# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.template import Library

register = Library()


@register.simple_tag
def active(request, pattern):
    if not request:
        return ""
    elif request.path.startswith(pattern) and pattern != "/":
        return "active"
    elif request.path == pattern == "/":
        return "active"
    else:
        return ""
