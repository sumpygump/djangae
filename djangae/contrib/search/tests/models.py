from django.db import models


class SearchableModel1(models.Model):
    name = models.CharField(max_length=128)
    other_thing = models.CharField(max_length=128, default="1")
