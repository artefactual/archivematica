# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django import template
import django.template.base as base
from django.urls import reverse


register = template.Library()


@register.tag(name="revisions_link")
def revisions_link(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, revision_type, object_uuid = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires two arguments" % token.contents.split()[0]
        )

    return RevisionLinkNode(revision_type, object_uuid)


class RevisionLinkNode(template.Node):
    def __init__(self, revision_type, object_uuid):
        self.revision_type = self._convert_to_template_variable_if_not_in_quotes(
            revision_type
        )
        self.object_uuid = self._convert_to_template_variable_if_not_in_quotes(
            object_uuid
        )

    def render(self, context):
        revision_type = self._resolve_if_template_variable(self.revision_type, context)
        object_uuid = self._resolve_if_template_variable(self.object_uuid, context)

        return '<a class="revisions_link" href="{}">Revision history</a>'.format(
            reverse(
                "fpr:revision_list",
                kwargs={"entity_name": revision_type, "uuid": object_uuid},
            )
        )

    def _convert_to_template_variable_if_not_in_quotes(self, value):
        if self._in_quotes(value):
            return value[1:-1]
        else:
            return template.Variable(value)

    def _in_quotes(self, value):
        return value[0] == '"' or value[0] == "'"

    def _resolve_if_template_variable(self, value, context):
        if value.__class__ == base.Variable:
            return value.resolve(context)
        else:
            return value
