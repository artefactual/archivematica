from django.conf.urls import url, patterns
from django.conf import settings

from components.api import views

urlpatterns = patterns('',
    url(r'transfer/approve', views.approve_transfer),
    url(r'transfer/unapproved', views.unapproved_transfers),
    url(r'transfer/status/(?P<unit_uuid>' + settings.UUID_REGEX + ')', views.status, {'unit_type': 'unitTransfer'}),
    url(r'transfer/start_transfer/', views.start_transfer_api),
    url(r'ingest/status/(?P<unit_uuid>' + settings.UUID_REGEX + ')', views.status, {'unit_type': 'unitSIP'}),
    url(r'ingest/waiting', views.waiting_for_user_input),

    url(r'^ingest/reingest', views.start_reingest),

    url(r'administration/dips/atom/levels/$', views.get_levels_of_description),
    url(r'administration/dips/atom/fetch_levels/$', views.fetch_levels_of_description_from_atom),
    url(r'filesystem/metadata/$', views.path_metadata),

    url(r'processing-configuration/(?P<name>\w{1,16})', views.processing_configuration),
)
