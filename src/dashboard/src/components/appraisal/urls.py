from django.conf.urls import url, patterns
from components.appraisal import views

urlpatterns = patterns('',
    url(r'^$', views.appraisal, name='appraisal_index')
)
