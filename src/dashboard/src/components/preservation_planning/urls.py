from django.conf.urls.defaults import patterns

urlpatterns = patterns('components.preservation_planning.views',
    (r'$', 'preservation_planning')
)
