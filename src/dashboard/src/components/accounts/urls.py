from django.conf.urls import url, patterns
import django.contrib.auth.views
from components.accounts import views

urlpatterns = patterns('',
    url(r'^$', views.list),
    url(r'add/$', views.add),
    url(r'(?P<id>\d+)/delete/$', views.delete),
    url(r'(?P<id>\d+)/edit/$', views.edit),
    url(r'profile/$', views.edit),
    url(r'list/$', views.list)
)

urlpatterns += patterns('',
    url(r'login/$', django.contrib.auth.views.login, { 'template_name': 'accounts/login.html' }),
    url(r'logout/$', django.contrib.auth.views.logout_then_login)
)
