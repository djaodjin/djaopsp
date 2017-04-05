# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from django.contrib import admin
from envconnect.models import (ColumnHeader, ScoreWeight, Consumption,
    Improvement)

admin.site.register(ColumnHeader)
admin.site.register(ScoreWeight)
admin.site.register(Consumption)
admin.site.register(Improvement)

