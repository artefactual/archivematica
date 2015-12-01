from django.template import Node, Library
import math

register = Library()

@register.filter
def math(lopr, expr):
    if lopr:
        return eval(expr.replace('$1', str(lopr)), {"__builtins__": None})
    return ''
