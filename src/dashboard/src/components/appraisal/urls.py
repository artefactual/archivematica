from django.conf.urls import url
from components.appraisal import views

urlpatterns = [
    url(r'^$', views.appraisal, name='appraisal_index')
]
