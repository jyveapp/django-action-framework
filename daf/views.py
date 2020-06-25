import os.path

import arg
from django.contrib.auth.decorators import permission_required
from django.contrib.humanize.templatetags.humanize import apnumber
import djarg.views

import daf.contrib
import daf.interfaces
import daf.permissions
import daf.utils


class ViewInterface(daf.interfaces.Interface, djarg.views.SuccessMessageMixin):
    """
    Base interface all action views must inherit.

    Automatically wraps the action with
    ``daf.contrib.raise_contextualized_error``, which will raise errors
    contextualized based on various factors.
    """

    type = 'view'
    wrapper = arg.contexts(daf.contrib.raise_contextualized_error)

    @classmethod
    def build_interface(cls, **kwargs):
        view = cls.as_view(**kwargs)
        if cls.permission_required:
            view = permission_required(
                cls.permission_uri, raise_exception=True
            )(view)

        return view


class ModelViewInterface(ViewInterface):
    """
    The base view used by any views that are directly associated with a model.
    Verifies that any action used by the view are subclasses of
    `ModelAction`.
    """

    type = 'model_view'

    @daf.utils.classproperty
    def url_path(cls):
        return os.path.join(
            cls.action.app_label.replace('_', '-'),
            cls.action.model_meta.model_name.replace('_', '-'),
            cls.action.name.replace('_', '-'),
        )

    @classmethod
    def check_interface_definition(cls):
        super().check_interface_definition()

        if not issubclass(cls.action, daf.actions.ModelAction):
            cls.definition_error(
                f'Action "{cls.action.__name__}" is not ModelAction subclass.'
            )


class ObjectViewInterface(ModelViewInterface):
    """
    The base interface for any object-based views.
    """

    type = 'object_view'

    @daf.utils.classproperty
    def url_path(cls):
        # TODO: Implement functionality for slug kwargs as well.
        return os.path.join(
            cls.action.app_label.replace('_', '-'),
            cls.action.model_meta.model_name.replace('_', '-'),
            cls.action.name.replace('_', '-'),
            f'<int:{cls.pk_url_kwarg}>',
        )

    def get_success_message(self, args, results):
        success_msg = super().get_success_message(args, results)
        return success_msg + f' on {self.object}'


class ObjectsViewInterface(ModelViewInterface):
    """
    The base interface for any bulk object views.
    """

    type = 'objects_view'

    def get_successful_and_failed_objects(self, form):
        # Obtain all successful/failed objects and all parametrized objects
        # based on the errors in the form
        failed_objects = set()
        all_objects = set()
        for errors in form.errors.values():
            for error in errors.data:
                # We don't test the "else" of this branch since we currently
                # have no test case for a non-parametrized bulk objects view.
                if (  # pragma: no branch
                    hasattr(error, '_arg_call')
                    and error._arg_call.parametrize_arg_val is not None
                ):
                    failed_objects.add(error._arg_call.parametrize_arg_val)
                    all_objects = set(error._arg_call.parametrize_arg_vals)

        if all_objects:
            successful_objects = all_objects - failed_objects
            ret_val = {
                'successful_objects': list(successful_objects),
                'failed_objects': list(failed_objects),
            }
            if successful_objects and failed_objects:
                ret_val['dismiss_failures_url'] = (
                    f'{self.request.path}?'
                    f'{self.build_url_query_str(successful_objects)}'
                )

            return ret_val
        else:
            return {}

    def get_success_message(self, args, results):
        success_msg = super().get_success_message(args, results)
        model_name = self.action.model_meta.verbose_name
        if len(results) > 1:
            model_name = self.action.model_meta.verbose_name_plural

        return (
            success_msg + f' on {apnumber(len(results))} {model_name.lower()}'
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        return {
            **context_data,
            **self.get_successful_and_failed_objects(context_data['form']),
        }

    def build_url_query_str(self, objects, additional_query_str=''):
        return daf.utils.build_objects_url_query_str(
            self.url_query_arg, objects, additional_query_str
        )


class FormView(ViewInterface, djarg.views.FormView):
    """
    For constructing a ``django-args`` ``FormView`` on an `Action`
    """


class ObjectFormView(ObjectViewInterface, djarg.views.ObjectFormView):
    """
    For constructing a ``django-args`` ``ObjectView`` on an `ObjectAction`
    or `ObjectsAction`
    """


class ObjectsFormView(ObjectsViewInterface, djarg.views.ObjectsFormView):
    """
    For constructing a ``django-args`` ``ObjectsView`` on an `ObjectAction`
    or `ObjectsAction`.
    """


class WizardView(ViewInterface, djarg.views.WizardView):
    """
    For constructing a ``django-args`` ``WizardView`` on an `Action`.
    """


class ObjectWizardView(ObjectViewInterface, djarg.views.ObjectWizardView):
    """
    For constructing a ``django-args`` ``ObjectWizardView`` on an `ObjectAction`
    or `ObjectsAction`.
    """


class ObjectsWizardView(ObjectsViewInterface, djarg.views.ObjectsWizardView):
    """
    For constructing a ``django-args`` ``ObjectsWizardView`` on an
    `ObjectAction` or `ObjectsAction`.
    """


class SessionWizardView(ViewInterface, djarg.views.SessionWizardView):
    """
    For constructing a ``django-args`` ``SessionWizardView`` on an
    `Action`.
    """


class SessionObjectWizardView(
    ObjectViewInterface, djarg.views.SessionObjectWizardView
):
    """
    For constructing a ``django-args`` ``SessionObjectWizardView`` on an
    `ObjectAction` or `ObjectsAction`.
    """


class SessionObjectsWizardView(
    ObjectsViewInterface, djarg.views.SessionObjectsWizardView
):
    """
    For constructing a ``django-args`` ``SessionObjectsWizardView`` on an
    `ObjectAction` or `ObjectsAction`.
    """
