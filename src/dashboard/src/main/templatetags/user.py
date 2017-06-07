from django import template
from django.utils.translation import ugettext as _
from tastypie.models import ApiKey

register = template.Library()


@register.filter
def api_key(user):
    try:
        return user.api_key.key
    except ApiKey.DoesNotExist:
        return _('<no API key generated>')
