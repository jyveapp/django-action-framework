"""A basic action for granting staff access to a user. For integration tests"""
import arg
from django import forms
import django.contrib.auth.models as auth_models

import daf.actions
import daf.rest_framework
import daf.views


def actor_must_be_superuser(actor):
    if not actor.is_superuser:
        raise ValueError('Must be superuser in order to grant staff access.')


@arg.defaults(actor=arg.first('actor', arg.val('request').user))
@arg.validators(actor_must_be_superuser)
def grant_staff_access(actor, user, is_staff):
    """
    Grant staff access to a user via an actor.
    """
    user.is_staff = is_staff
    user.save()
    return user


class GrantStaffAccess(daf.actions.ObjectAction):
    """Grants staff access to a user"""

    app_label = 'tests'
    name = 'grant_staff_access'
    callable = grant_staff_access
    model = auth_models.User
    object_arg = 'user'


class GrantStaffAccessForm(forms.Form):
    user = forms.ModelChoiceField(queryset=auth_models.User.objects.all())
    is_staff = forms.BooleanField(required=False)


class GrantStaffAccessFormView(daf.views.FormView):
    action = GrantStaffAccess
    form_class = GrantStaffAccessForm
    success_url = '.'
    template_name = 'tests/action.html'


class GrantStaffAccessObjectForm(forms.Form):
    is_staff = forms.BooleanField(required=False)
    date_granted = forms.DateTimeField(required=False)


class GrantStaffAccessObjectFormView(daf.views.ObjectFormView):
    action = GrantStaffAccess
    form_class = GrantStaffAccessObjectForm
    success_url = '.'
    template_name = 'tests/action.html'


class GrantStaffAccessObjectDRFAction(daf.rest_framework.DetailAction):
    action = GrantStaffAccess
    form_class = GrantStaffAccessObjectForm
