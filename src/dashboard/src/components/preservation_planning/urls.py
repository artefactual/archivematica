from django.conf.urls.defaults import patterns

urlpatterns = patterns('components.preservation_planning.views',
    #(r'fpr/(?P<current_page_number>\d+)/$', 'preservation_planning_fpr_data'),
    #(r'fpr/$', 'preservation_planning_fpr_data'),
    #(r'fpr/search/$', 'preservation_planning_fpr_search'),
    #(r'fpr/search/(?P<current_page_number>\d+)/$', 'preservation_planning_fpr_search'),
    #(r'$', 'preservation_planning')
    (r'old/$', 'preservation_planning'),

    (r'(?P<current_page_number>\d+)/$', 'preservation_planning_fpr_data'),
    (r'$', 'preservation_planning_fpr_data'),
    (r'search/$', 'preservation_planning_fpr_search'),
    (r'search/(?P<current_page_number>\d+)/$', 'preservation_planning_fpr_search'),
)
