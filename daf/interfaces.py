import arg

from daf import utils


class InterfaceMeta(type):
    """A metaclass for registering interfaces to actions"""

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)

        if cls.action and not cls.action.is_abstract:
            cls.action.interfaces = {**cls.action.interfaces, **{cls.uri: cls}}

        return cls


class Interface(metaclass=InterfaceMeta):
    """
    Provides base properties for any action interface.
    """

    ###
    # Core properties of the interface.
    ###

    # The primary action
    action = None

    # Instrumentation of how the action is run
    wrapper = arg.s()

    @classmethod
    def get_wrapper(cls):
        # A utility so that instance methods can safely access
        # the class wrapper variable. self.wrapper() will use
        # "self" as an argument when calling
        return cls.wrapper

    @utils.classproperty
    def func(cls):
        return cls.get_wrapper()(cls.action.func)

    # The namespace to which the interface belongs. Allows for querying
    # interfaces for a particular type of application such as the admin
    namespace = ''

    # The type of interface
    type = 'interface'

    @utils.classproperty
    def uri(cls):
        """The URI used when registering the interface to an action"""
        return f'{cls.namespace}.{cls.type}' if cls.namespace else cls.type

    @classmethod
    def as_interface(cls, **kwargs):
        cls.check_interface_definition()
        interface = cls.build_interface(**kwargs)
        cls.check_built_interface(interface)
        return interface

    @classmethod
    def build_interface(cls, **kwargs):
        raise NotImplementedError

    ###
    # Mirrored static action properties.
    #
    # Static action properties are automatically mirrored as
    # static properties on interfaces.
    ###

    @utils.classproperty
    def app_label(cls):
        return cls.action.app_label

    @utils.classproperty
    def model(cls):
        return cls.action.model

    @utils.classproperty
    def url_name(cls):
        return f'{cls.action.url_name}_{cls.type}'

    @utils.classproperty
    def url_path(cls):
        return cls.action.url_path

    @utils.classproperty
    def permission_uri(cls):
        return cls.action.permission_uri

    @utils.classproperty
    def display_name(cls):
        return cls.action.display_name

    @utils.classproperty
    def queryset(cls):
        return cls.action.queryset

    ###
    # Mirrored dynamic action properties.
    #
    # The get_ methods for dynamic action properties are automatically
    # mirrored on interfaces.
    ###

    def get_success_message(self, args, results):
        return self.action.get_success_message(args, results)

    ###
    # Runtime properties that change behavior.
    ###

    # True if the action permission should be required
    permission_required = False

    ###
    # Interface class checkers.
    #
    # When interfaces are created, class definitions are checked to ensure
    # they are are set up correctly.
    ###

    @classmethod
    def definition_error(cls, msg):
        raise AttributeError(f'{cls.__name__} - {msg}')

    @classmethod
    def check_interface_definition(cls):
        pass

    @classmethod
    def check_built_interface(cls, interface):
        pass
