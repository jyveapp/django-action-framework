"""A basic action for granting staff access to a user. For integration tests"""
import arg
from django import forms

import daf.actions
import daf.admin
import daf.contrib
import daf.rest_framework
import daf.tests.models as test_models


@arg.defaults(actor=arg.first('actor', arg.val('request').user))
def update_my_model(actor, my_model, my_field, my_extra_field):
    my_model.my_field = my_field
    my_model.my_extra_field = my_extra_field
    my_model.save()
    return my_model


class UpdateMyModel(daf.actions.ObjectAction):
    """Updates MyModel"""

    object_arg = 'my_model'
    callable = update_my_model
    model = test_models.MyModel


class MyFieldForm(forms.Form):
    my_field = forms.CharField(required=True, help_text='help me')


class MyExtraFieldForm(forms.Form):
    my_extra_field = forms.CharField(widget=forms.Textarea)


class UpdateMyModelAdminView(daf.admin.SessionWizardView):
    action = UpdateMyModel
    form_list = (('field', MyFieldForm), ('extra_field', MyExtraFieldForm))

    def get_default_args(self):
        return {
            **super().get_default_args(),
            **{'objects': test_models.MyModel.objects.all()},
        }


class UpdateMyModelObjectAdminView(daf.admin.SessionObjectWizardView):
    action = UpdateMyModel
    form_list = (('field', MyFieldForm), ('extra_field', MyExtraFieldForm))
    fieldsets = {
        'field': [
            (None, {'description': 'Description!', 'fields': ('my_field',)})
        ]
    }


class UpdateMyModelObjectsAdminView(daf.admin.SessionObjectsWizardView):
    action = UpdateMyModel
    form_list = (('field', MyFieldForm), ('extra_field', MyExtraFieldForm))
