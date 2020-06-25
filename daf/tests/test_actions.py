import django.contrib.auth.models as auth_models
import pytest

import daf.actions


def test_base_properties():
    """Test base properties of action objects"""

    def my_func(arg):
        return arg

    class MyAction(daf.actions.Action):
        unregistered = True
        callable = my_func
        app_label = 'app'

    assert MyAction.name == 'my_func'
    assert MyAction.uri == 'app.my_func'
    assert MyAction.url_name == 'app_my_func'
    assert MyAction.url_path == 'app/my-func'
    assert MyAction.permission_codename == 'app_my_func_action'
    assert MyAction.permission_uri == 'daf.app_my_func_action'
    assert MyAction.display_name == 'My Func'
    assert MyAction.success_message == 'Successfully performed "my func"'
    assert MyAction.get_success_message({}, []) == (
        'Successfully performed "my func"'
    )
    assert MyAction.success_url == '.'
    assert MyAction.get_success_url({}, []) == '.'
    assert MyAction()('hi') == 'hi'


def test_action_definitions():
    def my_func(arg1):
        pass

    with pytest.raises(AttributeError, match='provide "callable"'):

        class MyAction0(daf.actions.Action):
            unregistered = True

    with pytest.raises(AttributeError, match='alphanumeric "name"'):

        class MyAction1(daf.actions.Action):
            callable = my_func
            unregistered = True
            name = '***'

    with pytest.raises(AttributeError, match='alphanumeric "app_label"'):

        class MyAction2(daf.actions.Action):
            callable = my_func
            unregistered = True
            name = 'good'

    with pytest.raises(AttributeError, match='exceeds 100 characters'):

        class MyAction3(daf.actions.Action):
            callable = my_func
            unregistered = True
            name = 'good'
            app_label = 'good'
            permission_codename = 'a' * 1000

    with pytest.raises(AttributeError, match='provide "model"'):

        class MyAction4(daf.actions.ModelAction):
            callable = my_func
            unregistered = True
            name = 'good'
            app_label = 'good'

    with pytest.raises(AttributeError, match='provide "object_arg"'):

        class MyAction5(daf.actions.ObjectAction):
            callable = my_func
            unregistered = True
            name = 'good'
            model = auth_models.User

    with pytest.raises(AttributeError, match='not an argument'):

        class MyAction6(daf.actions.ObjectAction):
            callable = my_func
            unregistered = True
            name = 'good'
            model = auth_models.User
            object_arg = 'invalid'

    with pytest.raises(AttributeError, match='provide "objects_arg"'):

        class MyAction7(daf.actions.ObjectsAction):
            callable = my_func
            unregistered = True
            name = 'good'
            model = auth_models.User

    with pytest.raises(AttributeError, match='not an argument'):

        class MyAction8(daf.actions.ObjectsAction):
            callable = my_func
            unregistered = True
            name = 'good'
            model = auth_models.User
            objects_arg = 'invalid'

    class MyAction9(daf.actions.ObjectsAction):
        callable = my_func
        unregistered = True
        name = 'good'
        model = auth_models.User
        objects_arg = 'arg1'
