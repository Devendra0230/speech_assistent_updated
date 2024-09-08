from django.db import models


class UserQuery(models.Model):
    query = models.TextField()
    response = models.TextField(blank=True)