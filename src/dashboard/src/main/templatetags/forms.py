from django.template import Library

register = Library()

@register.filter
def is_checkbox(field):
    return field.field.widget.__class__.__name__.lower() == "checkboxinput"

@register.filter
def is_radioselect(field):
    return field.field.widget.__class__.__name__.lower() == "radioselect"
