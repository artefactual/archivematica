from django.conf.urls import url
from django.conf import settings
from components.file import views

urlpatterns = [
    url(r"(?P<fileuuid>" + settings.UUID_REGEX + ")/$", views.file_details),
    url(
        r"(?P<fileuuid>" + settings.UUID_REGEX + ")/tags/$",
        views.TransferFileTags.as_view(),
    ),
    url(
        r"(?P<fileuuid>" + settings.UUID_REGEX + ")/bulk_extractor/$",
        views.bulk_extractor,
    ),
]
