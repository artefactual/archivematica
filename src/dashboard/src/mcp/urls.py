from django.conf.urls.defaults import patterns

urlpatterns = patterns('mcp.views',
    (r'execute/$', 'execute'),
    (r'list/$', 'list'),
)
