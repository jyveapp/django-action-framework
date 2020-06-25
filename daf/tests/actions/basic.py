"""
Tests basic actions that dont use any of the ObjectAction or ObjectsAction
interfaces.
"""
import arg
from django import forms
from django.core import exceptions

import daf.actions
import daf.rest_framework
import daf.views


def list_error(username):
    """Helps test strange error messages that are raised in the test suite"""
    if username == 'list_error':
        raise exceptions.ValidationError(['list', 'error'])


@arg.defaults(user=arg.first('user', arg.val('request').user))
@arg.validators(list_error)
def basic(user, username):
    """
    Update a username
    """
    user.username = username
    user.save()
    return user


class Basic(daf.actions.Action):
    """Basic action"""

    app_label = 'tests'
    callable = basic


class BasicForm(forms.Form):
    username = forms.CharField()


class BasicFormView(daf.views.FormView):
    action = Basic
    form_class = BasicForm
    success_url = '.'
    template_name = 'tests/action.html'
