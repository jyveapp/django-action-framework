import collections
import importlib

from django.apps import apps


_registry = {}


def _register_action(cls):
    if cls.uri in _registry and _registry[cls.uri] != cls:
        raise RuntimeError(
            f'Action for app {cls.app_label} and name {cls.name}'
            ' has already been defined. Choose a different action name.'
        )

    _registry[cls.uri] = cls


def autodiscover_actions():
    """
    Imports the "actions" module of every installed app
    to discover actions
    """
    for app in apps.get_app_configs():
        actions_module = f'{app.module.__name__}.actions'
        module_spec = importlib.util.find_spec(actions_module)
        if module_spec is not None:
            importlib.import_module(actions_module)


def get(uri):
    """
    Get the action class by uri

    If URI is not a string, assume it is an action class
    that has a URI
    """
    uri = uri if isinstance(uri, str) else uri.uri
    return _registry[uri]


class FilterableObjects(collections.UserList):
    def __init__(self, objects):
        self.data = list(objects)

    def filter(self, **kwargs):
        def _matches(obj, attr_name, val):
            if not hasattr(obj, attr_name):
                return False

            obj_val = getattr(obj, attr_name)
            if isinstance(val, (tuple, list, FilterableObjects)):
                return obj_val in val
            else:
                return obj_val == val

        return self.__class__(
            obj
            for obj in self
            if all(
                _matches(obj, attr_name, attr_val)
                for attr_name, attr_val in kwargs.items()
            )
        )


def actions(actions=None):
    """
    Get all action classes as a filterable list.
    """
    if actions is None:
        actions = _registry.values()

    return FilterableObjects(actions)


def interfaces(interfaces=None):
    """
    Get all action interfaces as a filterable list.
    """
    if interfaces is None:
        interfaces = [
            interface
            for action in actions()
            for interface in action.interfaces.values()
        ]

    return FilterableObjects(interfaces)
