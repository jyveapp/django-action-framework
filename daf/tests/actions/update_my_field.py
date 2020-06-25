"""A basic action for granting staff access to a user. For integration tests"""
import arg
from django import forms

import daf.actions
import daf.admin
import daf.rest_framework
import daf.tests.models as test_models


def cannot_have_aaa_as_my_field(my_model):
    if my_model.my_field == 'aaa':
        raise ValueError('"my_field" is "aaa". Cannot update')


@arg.defaults(actor=arg.first('actor', arg.val('request').user))
@arg.validators(cannot_have_aaa_as_my_field)
def update_my_field(actor, my_model, my_field):
    my_model.my_field = my_field
    my_model.save()
    return my_model


class UpdateMyField(daf.actions.ObjectAction):
    """Updates my_field on MyModel"""

    callable = update_my_field
    object_arg = 'my_model'
    model = test_models.MyModel


class MyFieldForm(forms.Form):
    my_field = forms.CharField(required=True, help_text='help me')
    optional1 = forms.CharField(help_text='help me one', required=False)
    optional2 = forms.CharField(help_text='help me two', required=False)
    optional3 = forms.CharField(help_text='help me three', required=False)
    optional4 = forms.CharField(help_text='help me four', required=False)


class UpdateMyFieldAdminView(daf.admin.FormView):
    action = UpdateMyField
    form_class = MyFieldForm

    def get_default_args(self):
        return {
            **super().get_default_args(),
            **{'objects': test_models.MyModel.objects.all()},
        }


class UpdateMyFieldObjectAdminView(daf.admin.ObjectFormView):
    action = UpdateMyField
    form_class = MyFieldForm
    fieldsets = [
        (None, {'description': 'Description!', 'fields': ('my_field',)}),
        (
            'Advanced options',
            {
                'classes': ('collapse',),
                'fields': ('optional1', 'optional2', 'optional3', 'optional4'),
            },
        ),
    ]


class UpdateMyFieldObjectsAdminView(daf.admin.ObjectsFormView):
    action = UpdateMyField
    form_class = MyFieldForm
