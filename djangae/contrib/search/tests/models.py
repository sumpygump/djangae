from django.db import models


class SearchableModel1(models.Model):
    name = models.CharField(max_length=128)
