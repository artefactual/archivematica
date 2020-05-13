# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django import template
from django.urls import reverse
from django.utils.translation import ugettext as _
from tastypie.models import ApiKey

register = template.Library()


@register.filter
def api_key(user):
    try:
        return user.api_key.key
    except ApiKey.DoesNotExist:
        return _("<no API key generated>")


@register.simple_tag(takes_context=True)
def logout_link(context):
    if context.get("logout_link"):
        return context["logout_link"]
    else:
        return reverse("accounts:logout")
