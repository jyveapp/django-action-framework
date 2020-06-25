import collections
import contextlib
import copy

import arg
from django.core import exceptions


class single_list(arg.val):
    """A lazy arg loader that creates a list from a single element"""

    def _call(self, **kwargs):
        return [super()._call(**kwargs)]


class ContextualizedValidationError(exceptions.ValidationError):
    def render_arg_val(self, arg_val):
        return str(arg_val)

    def render_contextualized_error_message(self, arg_val, error):
        return (
            self.render_arg_val(arg_val)
            + ' - '
            + str(exceptions.ValidationError(error).message)
        )

    def contextualize_error_list(self):
        for e in self.error_list:
            if hasattr(e, 'message') and hasattr(e.message, '_arg_call'):
                e = e.message

            if hasattr(e, '_arg_call') and e._arg_call.parametrize_arg:
                self.parametrized_vals = list(e._arg_call.parametrize_arg_vals)
                self.parametrized_errors[
                    e._arg_call.parametrize_arg_val
                ].append(e)
            else:
                self.unparametrized_errors.append(e)

        # Re-organize the errors list and contextualize error messages
        self.error_list = copy.copy(self.unparametrized_errors)
        for arg_val, errors in self.parametrized_errors.items():
            if len(self.parametrized_vals) > 1:
                for error in errors:
                    message = self.render_contextualized_error_message(
                        arg_val, error
                    )
                    contextualized_error = exceptions.ValidationError(message)
                    contextualized_error._arg_call = error._arg_call
                    self.error_list.append(contextualized_error)
            else:
                self.error_list.extend(errors)

    def __init__(self, message, code=None, params=None):
        """
        Initializes a contextual validation error.

        Args:
            message (str): The message for the error. Can be a string,
                or any of the arguments used by Django's ValidationError
            code (str): An optional code for the error.
            params (dict): Parameters used when rendering the message
        """
        # Django's ValidationError allows you to pass an exception
        # as an argument, however, it strips the custom attributes collected
        # by DAF. Maintain these attributes here
        if isinstance(message, Exception) and hasattr(message, '_arg_call'):
            self._arg_call = message._arg_call

        super().__init__(message, code=code, params=params)

        # Organize errors by:
        # 1. Those not raised against a parametrized value
        # 2. Those associated with a parametrized value
        self.unparametrized_errors = []
        self.parametrized_errors = collections.defaultdict(list)
        # All of the values that were parametrized. Defaults to the first
        # parametrized error found
        self.parametrized_vals = []

        if hasattr(self, 'error_list'):
            self.contextualize_error_list()


@contextlib.contextmanager
def raise_contextualized_error(error_class=ContextualizedValidationError):
    """
    Raises a single ContextualizedValidationError where all errors contained
    by it have messages that are contextualized for a parametrized run.
    """
    assert issubclass(error_class, ContextualizedValidationError)
    try:
        yield
    except Exception as exc:
        raise error_class(exc)


@contextlib.contextmanager
def raise_trapped_errors():
    """
    Raises trapped errors as one ValidationError (if multiple errors
    are trapped). Re-raises the single error if one error is trapped.
    """
    trapped_errors = []
    yield trapped_errors
    if len(trapped_errors) > 1:
        raise exceptions.ValidationError(trapped_errors)
    elif len(trapped_errors) == 1:
        raise trapped_errors[0]


@contextlib.contextmanager
def trap_errors(trapped_errors):
    try:
        yield
    except Exception as exc:
        trapped_errors.append(exc)


@contextlib.contextmanager
def attach_error_metadata():
    try:
        yield
    except Exception as exc:
        exc._arg_call = copy.copy(arg.call())
        raise
