import inspect
import os
import re

import arg
from django.db import transaction
import djarg

import daf.contrib
import daf.registry
import daf.utils


class ActionMeta(type):
    """A metaclass for validating and registering actions"""

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)

        if not cls.is_abstract:
            cls.check_class_definition()

        if not cls.is_abstract and not cls.unregistered:
            daf.registry._register_action(cls)

        return cls


class Action(metaclass=ActionMeta):
    """
    The core Action class.

    Given an ``app_label`` and ``callable``, the Action class automatically
    generates attributes that can be overridden by a user. These attributes
    influence every interface built directly from the Action. Change attributes
    on the Action object to affect every interface.
    """

    ###
    # Static action properties.
    #
    # Static action properties can only be set directly on the class.
    # These properties are all queryable in the action registry.
    ###

    @daf.utils.classproperty
    def name(cls):
        """The identifying name of the action"""
        return arg.s()(cls.func).func.__name__

    #: The app to which the action belongs.
    app_label = ''

    @daf.utils.classproperty
    def uri(cls):
        """The URI is the unique identifier for the action."""
        return f'{cls.app_label}.{cls.name}'

    @daf.utils.classproperty
    def url_name(cls):
        """The default URL name for URL-based interfaces"""
        return f'{cls.app_label}_{cls.name}'

    @daf.utils.classproperty
    def url_path(cls):
        """The default URL name for URL-based interfaces"""
        return os.path.join(
            cls.app_label.replace('_', '-'), cls.name.replace('_', '-')
        )

    @daf.utils.classproperty
    def permission_codename(cls):
        """
        Returns the name of the permission associate with the action
        """
        return f'{cls.app_label}_{cls.name}_action'

    @daf.utils.classproperty
    def permission_uri(cls):
        """
        The full permission URI, which includes the "daf" app label
        under which all DAF permissions are saved
        """
        return f'daf.{cls.permission_codename}'

    ###
    # Dynamic action properties
    #
    # Dynamic action properties can be set on the class or dynamically
    # determined with an associated get_{property_name} function.
    # Some dynamic properties will take different arguments depending on
    # the context of how they are called. For example, the success URL
    # is only obtained after a successful action run, so it contains
    # all returned values.
    ###

    @daf.utils.classproperty
    def display_name(cls):
        """The display name is used to render UI headings and other elements"""
        return cls.name.replace('_', ' ').title()

    @daf.utils.classproperty
    def success_message(cls):
        """The success message displayed after successful action runs"""
        return f'Successfully performed "{cls.display_name.lower()}"'

    @classmethod
    def get_success_message(cls, args, results):
        """Obtains a success message based on callable args and results"""
        return cls.success_message

    #: The URL one goes to after a successful action
    success_url = '.'

    @classmethod
    def get_success_url(cls, args, results):
        """Obtain a success url based on callable args and results"""
        return cls.success_url

    ###
    # Action running.
    #
    # The wrapper around the action function in constructed, and the
    # action itself can be executed with __call__.
    ###

    #: The main action callable
    callable = None

    #: The wrapper around the callable. Attach exception metadata
    #: by default for interoperability with other tools
    wrapper = arg.contexts(daf.contrib.attach_error_metadata)

    @classmethod
    def get_wrapper(cls):
        # A utility so that instance methods can safely access
        # the class wrapper variable. self.wrapper() will use
        # "self" as an argument when calling
        return cls.wrapper

    @daf.utils.classproperty
    def func(cls):
        """The function called by the action"""
        return cls.get_wrapper()(cls.callable)

    def __call__(self, *args, **kwargs):
        """
        A utility for calling the main action. Note that this is not
        used
        """
        return self.func(*args, **kwargs)

    ###
    # Action interfaces.
    #
    # These properties are not meant to be overridden. They are
    # determined as interface classes are created for an action.
    ###

    # The interfaces registered to the action
    interfaces = {}

    ###
    # Abstract properties.
    #
    # These properties help in creating abstract actions. Abstract
    # actions are not registered and are used to build other actions.
    ###

    # True if the class is abstract. Note this property must be
    # overridden in each child class to declare it as abstract.
    abstract = True

    @daf.utils.classproperty
    def is_abstract(cls):
        """
        True if the action is an abstract action, False otherwise
        Do not override this helper, otherwise actual abstract
        actions could appear as concrete
        """
        return cls.__dict__.get('abstract', False)

    # True if the action should not populate the registry
    unregistered = False

    ###
    # Action class checkers.
    #
    # When actions are registered, class definitions are checked to ensure
    # actions are set up correctly.
    ###

    @classmethod
    def definition_error(cls, msg):
        raise AttributeError(f'{cls.__name__} - {msg}')

    @classmethod
    def check_class_definition(cls):
        """
        Verifies all properties have been filled out properly for the action
        class. Called by the metaclass only on concrete actions
        """
        if not cls.callable:
            cls.definition_error('Must provide "callable" attribute.')

        if not re.match(r'\w+', cls.name):
            cls.definition_error('Must provide alphanumeric "name" attribute.')

        if not re.match(r'\w+', cls.app_label):
            cls.definition_error(
                'Must provide alphanumeric "app_label" attribute.'
            )

        if len(cls.permission_codename) > 100:
            cls.definition_error(
                f'The permission_codename "{cls.permission_codename}"'
                ' exceeds 100 characters. Try making a shorter action name'
                ' or manually overridding the permission_codename attribute.'
            )


class ModelAction(Action):
    """
    An action associated with a model.

    Requires that the ``model`` attribute point to the
    Django ``Model`` class associated with the action.

    Includes all of the core properties of `Action`, but also defines
    other properties and creates automatic default values for others:
    """

    abstract = True

    #: The model the action is associated with
    model = None

    @daf.utils.classproperty
    def app_label(cls):
        """The app label to which this action belongs"""
        return cls.model_meta.app_label

    @daf.utils.classproperty
    def model_meta(cls):
        """The model._meta instance"""
        return cls.model._meta

    @daf.utils.classproperty
    def queryset(cls):
        """The main queryset, if any, the action is associated with"""
        return cls.model._default_manager.all()

    @classmethod
    def check_class_definition(cls):
        """
        Verifies all properties have been filled out properly for the action
        class. Called by the metaclass only on concrete actions
        """
        super().check_class_definition()

        if not cls.model:
            cls.definition_error('Must provide "model" attribute.')


class ObjectAction(ModelAction):
    """
    An action associated with a single model object.

    Similar to `ModelAction`, an `ObjectAction` updates a single model
    object. It requires an ``object_arg`` attribute which specifies which
    argument of ``callable`` is the model object.

    `ObjectAction` exposes an ``object`` variable that is automatically
    included as a default argument when running the wrapped callable.
    Allowing your function to take an ``object`` parameter will make it
    work seamlessly with object actions.

    By default, the ``wrapper`` for `ObjectAction` automatically:

    1. Parametrizes the run of the individual callable over multiple
       objects if the ``objects`` parameter is passed to the callable.
    2. Traps errors on each parametrized run of the callable and raises
       all trapped errors as one ``django.core.exceptions.ValidationError``
       if more than one error is trapped in a parameterized run.
    3. Automatically maps the ``object`` argument to the argument identified
       by the ``object_arg`` attribute.
    4. Wraps everything in a transaction and applies a select_for_update to
       the queryset if select_for_update is supplied.
    """

    abstract = True

    #: The name of the object arg for the action callable
    object_arg = None

    #: Select_for_update parameters if the action is atomic
    select_for_update = ['self']

    # Object actions default to operating on "object" or "objects"
    # arguments. Object actions also trap individual errors and raise
    # aggregate errors by default
    @daf.utils.classproperty
    def wrapper(cls):
        arg_decs = []
        if cls.select_for_update is not None:  # pragma: no branch
            arg_decs = [arg.contexts(transaction.atomic)]

        arg_decs += [
            arg.contexts(trapped_errors=daf.contrib.raise_trapped_errors),
            arg.defaults(
                objects=arg.first(
                    'objects',
                    daf.contrib.single_list('object'),
                    daf.contrib.single_list(cls.object_arg),
                )
            ),
            arg.defaults(
                objects=djarg.qset(
                    'objects',
                    qset=cls.queryset,
                    select_for_update=cls.select_for_update,
                )
            ),
            arg.parametrize(**{cls.object_arg: arg.val('objects')}),
            arg.contexts(daf.contrib.trap_errors),
            super().wrapper,
        ]

        return arg.s(*arg_decs)

    @classmethod
    def check_class_definition(cls):
        """
        Verifies all properties have been filled out properly for the action
        class. Called by the metaclass only on concrete actions
        """
        super().check_class_definition()

        if not cls.object_arg:
            cls.definition_error('Must provide "object_arg" attribute.')

        func_parameters = inspect.signature(arg.s()(cls.func).func).parameters
        if cls.object_arg not in func_parameters:
            cls.definition_error(
                f'object_arg "{cls.object_arg}" not an argument to callable.'
                f' Possible parameters={func_parameters}'
            )


class ObjectsAction(ModelAction):
    """An action associated with multiple model objects.

    The action is similar to `ObjectAction` except one
    must define an ``objects_arg`` attribute that tells ``daf`` which
    parameter to ``callable`` takes the list of objects. The callable must
    work with a list of objects at once.

    By default, the ``wrapper`` attribute ensures passing an ``object``
    argument will be automatically expanded into a single-element list
    (ensuring interoperability with object views). In contrast to
    `ObjectAction`, `ObjectsAction` cannot trap and re-raise multiple
    errors since it is up to the author of the bulk callable to handle
    raising multiple failures at once. `ObjectsAction` is intended to
    provide engineers the flexibility to optimize bulk routines if
    the automatic parametrization of `ObjectAction` is insufficient for
    their needs.
    """

    abstract = True

    #: The name of the objects arg for the action callable
    objects_arg = None

    #: Select_for_update parameters if the action is atomic
    select_for_update = ['self']

    # Objects actions default to operating on "object" or "objects"
    # arguments.
    @daf.utils.classproperty
    def wrapper(cls):
        arg_decs = []
        if cls.select_for_update is not None:  # pragma: no branch
            arg_decs = [arg.contexts(transaction.atomic)]

        arg_decs += [
            arg.defaults(
                **{
                    cls.objects_arg: arg.first(
                        'objects',
                        daf.contrib.single_list('object'),
                        cls.objects_arg,
                    )
                }
            ),
            arg.defaults(
                **{
                    cls.objects_arg: djarg.qset(
                        cls.objects_arg,
                        qset=cls.queryset,
                        select_for_update=cls.select_for_update,
                    )
                }
            ),
            super().wrapper,
        ]

        return arg.s(*arg_decs)

    @classmethod
    def check_class_definition(cls):
        """
        Verifies all properties have been filled out properly for the action
        class. Called by the metaclass only on concrete actions
        """
        super().check_class_definition()

        if not cls.objects_arg:
            cls.definition_error('Must provide "objects_arg" attribute.')

        func_parameters = inspect.signature(arg.s()(cls.func).func).parameters
        if cls.objects_arg not in func_parameters:
            cls.definition_error(
                f'objects_arg "{cls.objects_arg}" not an argument to callable.'
                f' Possible parameters={func_parameters}'
            )
