"""A basic action for granting staff access to a user. For integration tests"""
import arg
from django import forms
import django.contrib.auth.models as auth_models
import djarg
import djarg.views

from daf import actions
from daf import views


@arg.defaults(
    users=djarg.qset('objects', model=auth_models.User),
    actor=arg.first('actor', arg.val('request').user),
)
@arg.parametrize(user=arg.val('users'))
def bulk_grant_staff_access(actor, user, is_staff):
    """
    Grant staff access to a user via an actor.
    """
    user.is_staff = is_staff
    user.save()
    return user


class BulkGrantStaffAccess(actions.ModelAction):
    """Grants staff access to a user"""

    app_label = 'tests'
    name = 'bulk_grant_staff_access'
    callable = bulk_grant_staff_access
    model = auth_models.User


class BulkGrantStaffAccessForm(forms.Form):
    is_staff = forms.BooleanField(required=False)


class BulkGrantStaffAccessView(views.ObjectsFormView):
    action = BulkGrantStaffAccess
    form_class = BulkGrantStaffAccessForm
    success_url = '.'
    template_name = 'tests/action.html'
    permission_required = True
