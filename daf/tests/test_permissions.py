import django.contrib.auth.models as auth_models
import django.contrib.contenttypes.models as contenttypes_models
from django.core.management import call_command
import pytest

from daf import actions
import daf.models as daf_models


@pytest.mark.django_db
def test_install(mocker):
    """
    Test permissions.install. Ensures that permissions are updated
    and deleted accordingly when actions change.
    """

    def my_func():
        pass

    class ExampleAction1(actions.Action):
        unregistered = True
        app_label = 'tests'
        name = 'example_action1'
        callable = my_func

    class ExampleAction2(actions.Action):
        unregistered = True
        app_label = 'tests'
        name = 'example_action2'
        callable = my_func

    class ExampleAction3(actions.Action):
        unregistered = True
        app_label = 'tests'
        name = 'example_action3'
        callable = my_func

    # Make the action registry return all actions the first time it is
    # called. The second time, it will make it appear as though we deleted
    # an action.
    mocker.patch(
        'daf.registry.actions',
        autospec=True,
        side_effect=[
            [ExampleAction1, ExampleAction2, ExampleAction3],
            [ExampleAction2, ExampleAction3],
        ],
    )

    # Migrations should trigger permissions being installed
    call_command('migrate')

    # We should have three action permissions
    action_permission_ctype = contenttypes_models.ContentType.objects.get_for_model(
        daf_models.ActionPermission
    )
    assert (
        auth_models.Permission.objects.filter(
            content_type=action_permission_ctype
        ).count()
        == 3
    )

    # When we call migrate a second time, we install permissions again.
    # Our mock makes it look like an action was deleted
    call_command('migrate')

    # The removed action should no longer have a permission
    assert (
        auth_models.Permission.objects.filter(
            content_type=action_permission_ctype
        ).count()
        == 2
    )
