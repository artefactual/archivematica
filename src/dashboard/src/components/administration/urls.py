from django.conf.urls import url, patterns
from django.conf import settings
from components.administration import views
from components.administration import views_processing

urlpatterns = patterns('',
    url(r'^$', views.administration),
    url(r'reports/failures/delete/(?P<report_id>\w+)/$', views.failure_report_delete),
    url(r'reports/failures/(?P<report_id>\w+)/$', views.failure_report),
    url(r'reports/failures/$', views.failure_report),
    url(r'dips/as/$', views.administration_as_dips),
    url(r'dips/atk/$', views.administration_atk_dips),
    url(r'dips/atom/$', views.atom_dips),
    url(r'dips/atom/edit_levels/$', views.atom_levels_of_description),
    url(r'sources/$', views.sources),
    url(r'storage/$', views.storage),
    url(r'usage/$', views.usage),
    url(r'usage/clear/(?P<dir_id>\w+)/$', views.usage_clear),
    url(r'processing/$', views_processing.list),
    url(r'processing/add/$', views_processing.edit),
    url(r'processing/edit/(?P<name>\w{1,16})/$', views_processing.edit),
    url(r'processing/delete/(?P<name>\w{1,16})$', views_processing.delete),
    url(r'premis/agent/$', views.premis_agent),
    url(r'api/$', views.api),
    url(r'general/$', views.general),
    url(r'version/$', views.version),
    url(r'taxonomy/term/(?P<term_uuid>' + settings.UUID_REGEX + ')/$', views.term_detail),
    url(r'taxonomy/term/(?P<term_uuid>' + settings.UUID_REGEX + ')/delete/$', views.term_delete),
    url(r'taxonomy/(?P<taxonomy_uuid>' + settings.UUID_REGEX + ')/$', views.terms),
    url(r'taxonomy/$', views.taxonomy),
)
