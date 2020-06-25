import pytest

import daf.actions
import daf.views


def test_view_definitions():
    """Tests scenarios that result in views raising view definition errors"""

    def my_func():
        pass

    class NonModelAction(daf.actions.Action):
        unregistered = True
        name = 'name'
        app_label = 'label'
        callable = my_func

    class MyModelViewInterface(daf.views.ModelViewInterface):
        action = NonModelAction

    with pytest.raises(AttributeError):
        MyModelViewInterface.check_interface_definition()
