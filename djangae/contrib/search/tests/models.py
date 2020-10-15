from django.db import models

from djangae.contrib.search import (
    ModelDocument,
    register,
)


class SearchableModelDocument(ModelDocument):
    class Meta:
        index = "index1"
        fields = (
            "name",
        )


class SearchableModel1(models.Model):
    name = models.CharField(max_length=128)


register(SearchableModel1, SearchableModelDocument)
