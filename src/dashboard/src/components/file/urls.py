from components.file import views
from django.urls import path

app_name = "file"
urlpatterns = [
    path(
        "<uuid:fileuuid>/",
        views.file_details,
        name="file_details",
    ),
    path(
        "<uuid:fileuuid>/tags/",
        views.TransferFileTags.as_view(),
        name="transfer_file_tags",
    ),
    path(
        "<uuid:fileuuid>/bulk_extractor/",
        views.bulk_extractor,
        name="bulk_extractor",
    ),
]
