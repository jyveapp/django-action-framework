import django.contrib.auth.models as auth_models
import pytest

import daf.actions
import daf.registry


@pytest.fixture(autouse=True)
def mock_registry(mocker):
    # Always patch out the global registry so that it doesnt leak
    # into other tests
    yield mocker.patch.dict('daf.registry._registry', {}, clear=True)


def test_duplicate_registration():
    class Action0(daf.actions.Action):
        callable = test_duplicate_registration
        app_label = 'hi'

    with pytest.raises(RuntimeError):

        class Action1(daf.actions.Action):
            callable = test_duplicate_registration
            app_label = 'hi'


def test_registry_filtering():
    """Tests various ways of filtering action registry"""

    class Action0(daf.actions.Action):
        callable = test_duplicate_registration
        app_label = 'hi'

    class Action1(daf.actions.Action):
        callable = test_registry_filtering
        app_label = 'hello'

    class Action2(daf.actions.ModelAction):
        callable = test_duplicate_registration
        model = auth_models.User

    class Action3(daf.actions.ModelAction):
        callable = test_registry_filtering
        model = auth_models.User

    assert set(daf.registry.actions()) == {Action0, Action1, Action2, Action3}
    assert set(daf.registry.actions().filter(model=auth_models.User)) == {
        Action2,
        Action3,
    }

    assert daf.registry.actions(
        [
            daf.registry.get('hi.test_duplicate_registration'),
            daf.registry.get('auth.test_registry_filtering'),
        ]
    ).filter(app_label='hi') == [Action0]
    assert set(daf.registry.actions().filter(app_label=['hi', 'auth'])) == {
        Action0,
        Action2,
        Action3,
    }
