from django.conf.urls import url, patterns
from django.conf import settings
from components.backlog import views


urlpatterns = patterns(
    '',
    url(r'^$', views.execute, name='backlog_index'),
    url(r'search/$', views.search, name='backlog_search'),
    url(r'delete/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.delete, name='backlog_delete'),
    url(r'download/(?P<uuid>' + settings.UUID_REGEX + ')/$', views.download, name='backlog_download'),
)
