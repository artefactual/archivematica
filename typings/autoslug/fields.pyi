from django.db.models import Model
from django.db.models.fields import SlugField

__all__: list[str]
SLUG_INDEX_SEPARATOR: str

class AutoSlugField(SlugField[str, str]):
    def __init__(self, *args: object, **kwargs: object) -> None: ...
    def pre_save(self, instance: Model, add: bool) -> str | None: ...
