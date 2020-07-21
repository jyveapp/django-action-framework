import contextlib
import functools

import arg
from django import forms
from django.conf import settings
from django.core import exceptions
import djarg.forms
import rest_framework.decorators as drf_decorators
import rest_framework.exceptions as drf_exceptions
from rest_framework.response import Response
import rest_framework.status as drf_status

import daf.interfaces


class InstallDAFActions(type):
    """A metaclass that installs DAF actions on DRF viewsets"""

    def __new__(meta, name, bases, class_dict):
        cls = type.__new__(meta, name, bases, class_dict)

        for interface in cls.get_daf_actions().filter(type='detail_action'):
            method_name = f'detail_{interface.action.name}'
            assert not hasattr(cls, method_name)
            setattr(cls, method_name, interface.as_interface())

        return cls


class ActionMixin(metaclass=InstallDAFActions):
    """
    The mixin that must be inherited by a rest framework viewset
    in order to expose actions as endpoints.
    """

    #: The `DetailAction` interfaces to add to the viewset.
    daf_actions = None

    @classmethod
    def get_daf_actions(cls):
        return daf.registry.interfaces(cls.daf_actions or [])


class APIException(drf_exceptions.APIException):
    """
    The base error class raised by `raise_drf_error`.
    """

    @property
    def status_code(self):
        return getattr(
            settings,
            'DAF_DEFAULT_REST_FRAMEWORK_ERROR_STATUS_CODE',
            drf_status.HTTP_400_BAD_REQUEST,
        )

    default_detail = 'Invalid input.'
    default_code = 'invalid'


@contextlib.contextmanager
def raise_drf_error(exception_class=APIException):
    """Re-raise non-DRF errors as APIException classes"""
    assert issubclass(exception_class, drf_exceptions.APIException)
    try:
        yield
    except Exception as exc:
        if not isinstance(exc, drf_exceptions.APIException):
            # For validation errors that serialized lists or dictionaries,
            # load it so that it will be rendered better by DRF
            if hasattr(exc, 'error_dict'):
                msg = dict(exc)
            elif hasattr(exc, 'message'):
                msg = str(exc.message)  # noqa
            elif hasattr(exc, 'error_list'):
                msg = list(exc)
            else:
                msg = str(exc)

            daf_exc = exception_class(msg, code=getattr(exc, 'code', None))
            daf_exc._daf_exc = exc

            raise daf_exc from exc
        else:
            raise


class DetailAction(daf.interfaces.Interface):
    """
    The interface for constructing detail actions in rest framework
    viewsets.
    """

    namespace = 'rest_framework'
    type = 'detail_action'
    exception_class = APIException
    wrapper = arg.contexts(
        functools.partial(raise_drf_error, exception_class=exception_class),
        daf.contrib.raise_contextualized_error,
    )

    #: Define a form class to parse POST parameters through a Django form
    form_class = forms.Form

    #: True if objects should be re-fetched before they are serialized
    #: and returned as a response
    refetch_for_serialization = True

    #: Methods for the action. Defaults to ["post"] if None
    methods = None

    def __init__(self, viewset, request, pk):
        self.viewset = viewset
        self.request = request
        self.pk = pk

    @daf.utils.classproperty
    def url_name(cls):
        return cls.action.name.replace('_', '-') + '-detail-action'

    @daf.utils.classproperty
    def url_path(cls):
        return cls.action.name.replace('_', '-')

    def get_object(self):
        return self.viewset.get_object()

    def get_default_args(self):
        return {'object': self.get_object(), 'request': self.request}

    def run(self):
        request_args = self.request.data
        form = self.form_class(request_args)
        default_args = {**self.get_default_args(), **request_args}
        form = djarg.forms.adapt(
            form, self.action.func, default_args, clean=False
        )
        form.full_clean()

        self.args = {**default_args, **form.cleaned_data}

        def _validate_form():
            if not form.is_valid():
                raise exceptions.ValidationError(form.errors)

        wrapper = arg.s(self.get_wrapper(), arg.validators(_validate_form))
        self.result = wrapper(self.action.func)(**self.args)

        object_to_serialize = self.result

        # Object actions may be parametrized and return a list by default.
        # Return only one object if this is the case
        if (
            isinstance(object_to_serialize, list)
            and len(object_to_serialize) == 1
        ):
            object_to_serialize = object_to_serialize[0]

        if self.refetch_for_serialization:
            object_to_serialize = self.get_object()

        serializer = self.viewset.get_serializer(
            object_to_serialize, context={'request': self.request}
        )
        return Response(serializer.data)

    @classmethod
    def as_interface(
        cls, url_name=None, url_path=None, methods=None, **kwargs
    ):
        """
        Creates a DRF action from a the interface.

        Args:
            url_name (str, default=cls.url_name): The url_name
                argument that is passed to the DRF @action decorator.
            url_path (str, default=cls.url_path): The url_path
                argument that is passed to the DRF @action decorator.
            methods (list, default=[POST]): The list of methods over
                which the action will be available.
            **kwargs: Any additional argument accepted by the drf.action
                decorator.
        """

        def _drf_detail_action(viewset, request, pk, **kwargs):
            """
            The code that is executed in the DRF viewset
            """
            return cls(viewset, request, pk).run()

        url_name = url_name or cls.url_name
        url_path = url_path or cls.url_path
        methods = methods or cls.methods or ['post']

        func = _drf_detail_action
        func.__name__ = 'detail_' + cls.action.name
        func.__doc__ = cls.__doc__

        return drf_decorators.action(
            methods=methods,
            detail=True,
            url_path=url_path,
            url_name=url_name,
            **kwargs,
        )(func)
