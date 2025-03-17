from django.urls import path

from archivematica.dashboard.components.appraisal import views

app_name = "appraisal"
urlpatterns = [path("", views.appraisal, name="appraisal_index")]
