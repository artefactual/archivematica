from django.template import Node, Library

register = Library()

@register.filter
def keyvalue(d, key):
    return d.get(key)
