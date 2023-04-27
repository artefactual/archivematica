from components.appraisal import views
from django.conf.urls import url

app_name = "appraisal"
urlpatterns = [url(r"^$", views.appraisal, name="appraisal_index")]
