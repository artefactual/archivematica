from django.conf.urls import url, patterns
from installer import views

urlpatterns = patterns('',
    url(r'welcome/$', views.welcome),
    url(r'fprconnect/$', views.fprconnect),
    url(r'fprupload/$', views.fprupload),
    url(r'fprdownload/$', views.fprdownload),
    url(r'storagesetup/$', views.storagesetup),
)
