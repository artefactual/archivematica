from components.appraisal import views
from django.urls import path

app_name = "appraisal"
urlpatterns = [path("", views.appraisal, name="appraisal_index")]
