# Copyright (c) 2017, DjaoDjin inc.
# see LICENSE.

from django.contrib import admin
from envconnect.models import ColumnHeader, Consumption


admin.site.register(ColumnHeader)
admin.site.register(Consumption)
