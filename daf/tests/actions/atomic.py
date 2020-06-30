"""For integration tests of atomicity"""
from django import forms
import django.contrib.auth.models as auth_models

import daf.actions
import daf.rest_framework
import daf.views


def atomic_check(user, username, first_name):
    """
    For verifying atomicity of actions
    """
    user.first_name = first_name
    user.save()
    user.username = username
    user.save()


class AtomicCheck(daf.actions.ObjectAction):
    """
    Updates first_name and a field with a unique constraint to test atomicity
    """

    app_label = 'tests'
    name = 'atomic_check'
    callable = atomic_check
    model = auth_models.User
    object_arg = 'user'


class AtomicCheckObjectForm(forms.Form):
    username = forms.CharField()
    first_name = forms.CharField()


class AtomicCheckObjectFormView(daf.views.ObjectFormView):
    action = AtomicCheck
    form_class = AtomicCheckObjectForm
    success_url = '.'
    template_name = 'tests/action.html'
