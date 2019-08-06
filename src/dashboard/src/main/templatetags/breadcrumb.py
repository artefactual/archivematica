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
from __future__ import absolute_import

import logging

from django.template import Node, Variable, Library
from django.utils.encoding import smart_text
from django.template.defaulttags import url
from django.template import VariableDoesNotExist
from six.moves import map

logger = logging.getLogger("archivematica.dashboard")
register = Library()


@register.tag
def breadcrumb(parser, token):
    """
    Renders the breadcrumb.
    Examples:
       {% breadcrumb "Title of breadcrumb" url_var %}
       {% breadcrumb context_var  url_var %}
       {% breadcrumb "Just the title" %}
       {% breadcrumb just_context_var %}

    Parameters:
    - First parameter is the title of the crumb,
    - Second (optional) parameter is the url variable to link to, produced by url tag, i.e.:
         {% url person_detail object.id as person_url %}
      then:
         {% breadcrumb person.name person_url %}

    @author Andriy Drozdyuk
    """
    return BreadcrumbNode(token.split_contents()[1:])


@register.tag
def breadcrumb_url(parser, token):
    """
    Same as breadcrumb
    but instead of url context variable takes in all the
    arguments URL tag takes.
        {% breadcrumb "Title of breadcrumb" person_detail person.id %}
        {% breadcrumb person.name person_detail person.id %}
    """

    bits = token.split_contents()
    if len(bits) == 2:
        return breadcrumb(parser, token)

    # Extract our extra title parameter
    title = bits.pop(1)
    token.contents = " ".join(bits)

    url_node = url(parser, token)

    return UrlBreadcrumbNode(title, url_node)


class BreadcrumbNode(Node):
    def __init__(self, vars):
        self.vars = list(map(Variable, vars))

    def render(self, context):
        title = self.vars[0].var

        if title.find("'") == -1 and title.find('"') == -1:
            try:
                val = self.vars[0]
                title = val.resolve(context)
            except:
                title = ""

        else:
            title = title.strip("'").strip('"')
            title = smart_text(title)

        url = None

        if len(self.vars) > 1:
            val = self.vars[1]
            try:
                url = val.resolve(context)
            except VariableDoesNotExist:
                logger.error("URL does not exist: %s", val)
                url = None

        return create_crumb(title, url)


class UrlBreadcrumbNode(Node):
    def __init__(self, title, url_node):
        self.title = Variable(title)
        self.url_node = url_node

    def render(self, context):
        title = self.title.var

        if title.find("'") == -1 and title.find('"') == -1:
            try:
                val = self.title
                title = val.resolve(context)
            except:
                title = ""
        else:
            title = title.strip("'").strip('"')
            title = smart_text(title)

        url = self.url_node.render(context)
        return create_crumb(title, url)


def create_crumb(title, url=None):
    if url:
        return '<li><a href="%s">%s</a>&nbsp;</li>' % (url, title)
    else:
        return "<li>%s</li>" % title
