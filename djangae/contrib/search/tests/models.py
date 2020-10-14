from django.db import models

from djangae.contrib.search.decorators import (
    ModelDocument,
    searchable,
)


class SearchableModelDocument(ModelDocument):
    class Meta:
        index = "index1"
        fields = (
            "name",
        )


@searchable(SearchableModelDocument)
class SearchableModel1(models.Model):
    name = models.CharField(max_length=128)
