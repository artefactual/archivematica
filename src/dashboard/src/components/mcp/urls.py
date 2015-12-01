from django.conf.urls import url, patterns
from components.mcp import views

urlpatterns = patterns('',
    url(r'execute/$', views.execute),
    url(r'list/$', views.list),
)
