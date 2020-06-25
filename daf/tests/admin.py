from django.contrib import admin

import daf.admin
from daf.tests.actions import update_my_field
from daf.tests.actions import update_my_model
from daf.tests.models import MyModel


class MyModelAdmin(daf.admin.ActionMixin, admin.ModelAdmin):
    list_filter = ('my_field',)

    fieldsets = [
        (None, {'description': 'Description!', 'fields': ('my_field',)}),
        (
            'Advanced options',
            {'classes': ('collapse',), 'fields': ('my_extra_field',)},
        ),
    ]
    daf_actions = [
        update_my_field.UpdateMyFieldAdminView,
        update_my_field.UpdateMyFieldObjectAdminView,
        update_my_field.UpdateMyFieldObjectsAdminView,
        update_my_model.UpdateMyModelAdminView,
        update_my_model.UpdateMyModelObjectAdminView,
        update_my_model.UpdateMyModelObjectsAdminView,
    ]


admin.site.register(MyModel, MyModelAdmin)
