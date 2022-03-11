# Copyright (c) 2021, DjaoDjin inc.
# see LICENSE.

from django.db import models

from .compat import python_2_unicode_compatible

@python_2_unicode_compatible
class Account(models.Model):

    slug = models.SlugField(unique=True, db_index=True)
    full_name = models.CharField(max_length=60, blank=True)

    def __str__(self):
        return str(self.slug)

    @property
    def printable_name(self):
        if self.full_name:
            return self.full_name
        return self.slug
