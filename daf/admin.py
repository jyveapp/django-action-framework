import functools
import os

from django import shortcuts
from django import urls
from django.conf import settings
import django.contrib.admin.helpers as admin_helpers
import django.contrib.admin.options as admin_options
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
import djarg.views

import daf.actions
import daf.registry
import daf.views


class ActionMixin:
    """
    All admins that use actions from ``daf`` must inherit this mixin.

    Attributes:

        daf_actions (List[`Interface`]): The list of action interfaces
            to be rendered on the admin.
    """

    change_form_template = 'daf/admin/change_form.html'
    change_list_template = 'daf/admin/change_list.html'
    daf_actions = None

    @classmethod
    def get_daf_actions(cls):
        return daf.registry.interfaces(cls.daf_actions or [])

    def get_urls(self):
        return [
            urls.path(
                interface.url_path + '/',
                interface.as_interface(admin=self),
                name=interface.url_name,
            )
            for interface in self.get_daf_actions().filter(model=self.model)
        ] + super().get_urls()

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['daf_actions'] = [
            (
                interface.display_name,
                urls.reverse(
                    f'admin:{interface.url_name}',
                    kwargs={interface.pk_url_kwarg: object_id},
                ),
            )
            for interface in self.get_daf_actions().filter(type='object_view')
            if interface.is_visible(request)
        ]

        return super().change_view(
            request, object_id, extra_context=extra_context
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['daf_actions'] = [
            (
                interface.action.display_name,
                urls.reverse(f'admin:{interface.url_name}'),
            )
            for interface in self.get_daf_actions().filter(type='model_view')
            if interface.is_visible(request)
        ]

        return super().changelist_view(request, extra_context)

    def get_actions(self, request):
        def _view(self, request, queryset, *, interface):
            preserved_filters = self.get_preserved_filters(request)
            url = (
                urls.reverse(f'admin:{interface.url_name}')
                + '?'
                + daf.utils.build_objects_url_query_str(
                    interface.url_query_arg, queryset, preserved_filters
                )
            )

            return shortcuts.redirect(url)

        return {
            **super().get_actions(request),
            **{
                f'_daf_{interface.action.name}': (
                    functools.partial(_view, interface=interface),
                    f'_daf_{interface.action.name}',
                    interface.action.display_name,
                )
                for interface in self.get_daf_actions().filter(
                    type='objects_view'
                )
                if interface.is_visible(request)
            },
        }


class AdminViewInterfaceMixin:
    """
    The base view used for any interface that is rendered in the Django
    admin.

    Similar to the Django admin, users can also define ``fieldsets``
    for rendering fields from forms and
    ``readonly_fields`` declarations. Interfaces also have access to the
    ``admin`` attribute, which holds the instance of the Django admin
    class.

    Attributes:

        permission_required (bool): ``True`` if the permission associated
            with the `Action` class should be required to view and perform
            the action. Defaults to ``True`` or
            ``settings.DAF_ADMIN_ACTION_PERMISSIONS_REQUIRED``.
    """

    namespace = 'admin'
    admin = None
    fieldsets = ()
    readonly_fields = ()
    template_name = 'daf/admin/action.html'
    hide_inline_formsets = True
    hide_object_tools = True

    @daf.utils.classproperty
    def permission_required(cls):
        return getattr(settings, 'DAF_ADMIN_ACTION_PERMISSIONS_REQUIRED', True)

    @classmethod
    def is_visible(cls, request):
        """True if the interface is visible from the admin

        By default, returns False if permissions are required and the user does
        not have permission.
        """
        if cls.permission_required:
            return request.user.has_perm(cls.permission_uri)
        else:
            return True

    @classmethod
    def build_interface(self, *, admin, **kwargs):
        # The Django admin wraps all view functions in this decorator.
        # Unfortunately the code is buried in their admin and must
        # be copied here
        def wrap(view):
            def wrapper(*args, **kwargs):
                return admin.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = admin

            return functools.update_wrapper(wrapper, view)

        return wrap(super().build_interface(admin=admin, **kwargs))

    @daf.utils.classproperty
    def changelist_url_name(cls):
        return f'admin:{cls.app_label}_{cls.model._meta.model_name}_changelist'

    @daf.utils.classproperty
    def change_url_name(cls):
        return f'admin:{cls.app_label}_{cls.model._meta.model_name}_change'

    def add_preserved_filters(self, url):
        preserved_filters = self.admin.get_preserved_filters(self.request)
        return add_preserved_filters(
            {
                'opts': self.admin.model._meta,
                'preserved_filters': preserved_filters,
            },
            url,
        )

    def get_success_url(self):
        changelist_url = urls.reverse(self.changelist_url_name)
        return self.add_preserved_filters(changelist_url)

    def get_fieldsets(self):
        return self.fieldsets or [
            (None, {'fields': list(self.get_form().fields)})
        ]

    def get_readonly_fields(self):
        return self.readonly_fields or []

    def get_form_url(self, context):
        return '?' + self.admin.get_preserved_filters(self.request)

    @property
    def save_as(self):
        return self.admin.save_as

    @property
    def save_on_top(self):
        return self.admin.save_on_top

    def get_change_form_context(self, context):
        """
        This methods attempts to gather the same context the admin site
        gathers when it renders a changeform. The Django admin
        doesn't have a pretty way of getting this data since it is
        so tightly coupled with template rendering.
        """
        form = context['form']
        request = self.request
        model = self.admin.model
        opts = model._meta
        app_label = opts.app_label
        obj = context.get('object', None)
        form_url = self.get_form_url(context)

        view_on_site_url = self.admin.get_view_on_site_url(obj)
        fieldsets = self.get_fieldsets()
        formsets, inline_instances = self.admin._create_formsets(
            request, obj, change=not self.hide_inline_formsets
        )
        readonly_fields = self.get_readonly_fields()
        admin_form = admin_helpers.AdminForm(
            form,
            list(fieldsets),
            self.admin.get_prepopulated_fields(request, obj),
            readonly_fields,
            model_admin=self.admin,
        )
        media = self.admin.media + admin_form.media

        # The inline formset code is copied from django's code. It has
        # not been used in practice yet and has no tests
        inline_formsets = self.admin.get_inline_formsets(
            request, formsets, inline_instances, obj
        )
        for inline_formset in inline_formsets:  # pragma: no cover
            media = media + inline_formset.media

        has_editable_inline_admin_formsets = True if inline_formsets else False
        has_file_field = admin_form.form.is_multipart() or any(
            admin_formset.formset.is_multipart()
            for admin_formset in inline_formsets
        )

        # The admin admin also sets this variable
        request.current_app = self.admin.admin_site.name

        return {
            **self.admin.admin_site.each_context(request),
            'title': self.display_name,
            'adminform': admin_form,
            'original': obj,
            'is_popup': False,
            'to_field': None,
            'media': media,
            'inline_admin_formsets': inline_formsets,
            'errors': admin_helpers.AdminErrorList(form, formsets),
            'preserved_filters': self.admin.get_preserved_filters(request),
            'add': False,
            'change': bool(obj),
            'has_view_permission': self.admin.has_view_permission(
                request, obj
            ),
            'has_add_permission': self.admin.has_add_permission(request),
            'has_change_permission': self.admin.has_change_permission(
                request, obj
            ),
            'has_delete_permission': self.admin.has_delete_permission(
                request, obj
            ),
            'has_editable_inline_admin_formsets': (
                has_editable_inline_admin_formsets
            ),
            'has_file_field': has_file_field,
            'has_absolute_url': view_on_site_url is not None,
            'absolute_url': view_on_site_url,
            'form_url': form_url,
            'opts': opts,
            'content_type_id': (
                admin_options.get_content_type_for_model(self.admin.model).pk
            ),
            'save_as': self.save_as,
            'save_on_top': self.save_on_top,
            'to_field_var': admin_options.TO_FIELD_VAR,
            'is_popup_var': admin_options.IS_POPUP_VAR,
            'app_label': app_label,
            'hide_object_tools': self.hide_object_tools,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return {
            **context,
            **self.get_change_form_context(context),
            'is_daf_action': True,
        }


class ModelViewInterface(
    AdminViewInterfaceMixin, daf.views.ModelViewInterface
):
    """
    The base interface used by any admin views that require a model.

    Currently all admin views require a model, so this needs to be
    the parent class for every admin view.

    If this is the base class, the action is rendered in the toolbar
    on the model change list page.
    """

    @daf.utils.classproperty
    def url_path(cls):
        return os.path.join('action', cls.action.name.replace('_', '-'))

    @daf.utils.classproperty
    def url_name(cls):
        return (
            f'{cls.app_label}_{cls.action.model_meta.model_name}_'
            f'{cls.action.name}_action'
        )


class ObjectViewInterface(
    AdminViewInterfaceMixin, daf.views.ObjectViewInterface
):
    """
    The base interface for object views in the admin. These are rendered
    in the toolbar of the object detail page.
    """

    @daf.utils.classproperty
    def url_path(cls):
        return os.path.join(
            f'<path:{cls.pk_url_kwarg}>',
            'object-action',
            cls.action.name.replace('_', '-'),
        )

    @daf.utils.classproperty
    def url_name(cls):
        return (
            f'{cls.app_label}_{cls.action.model_meta.model_name}_'
            f'{cls.action.name}_object_action'
        )

    def get_success_url(self):
        # If the user selects "submit and continue editing", redirect them
        # back to the detail page.
        if '_continue_editing' in self.request.POST:
            change_url = urls.reverse(
                self.change_url_name,
                kwargs={'object_id': self.kwargs[self.pk_url_kwarg]},
            )
            return self.add_preserved_filters(change_url)
        else:
            return super().get_success_url()


class ObjectsViewInterface(
    AdminViewInterfaceMixin, daf.views.ObjectsViewInterface
):
    """
    The base interface for objects views in the admin. These are rendered
    in the dropdown menu of the change list page.
    """

    @daf.utils.classproperty
    def url_path(cls):
        return os.path.join(
            'objects-action', cls.action.name.replace('_', '-')
        )

    @daf.utils.classproperty
    def url_name(cls):
        return (
            f'{cls.app_label}_{cls.action.model_meta.model_name}_'
            f'{cls.action.name}_objects_action'
        )

    def get_form_url(self, context):
        return '?' + self.build_url_query_str(context['objects'])

    def build_url_query_str(self, objects, additional_query_str=''):
        return super().build_url_query_str(
            objects, self.admin.get_preserved_filters(self.request)
        )


class FormView(ModelViewInterface, djarg.views.FormView):
    """
    For constructing form views in the admin. Using this as the
    base class for an admin view will render it in the toolbar
    on the change list admin page for the model.
    """


class ObjectFormView(ObjectViewInterface, djarg.views.ObjectFormView):
    """
    For constructing object form views in the admin. Using this as the
    base class for an admin view will render it in the toolbar
    on the detail admin page for the model object.
    """


class ObjectsFormView(ObjectsViewInterface, djarg.views.ObjectsFormView):
    """
    For constructing objects form views in the admin. Using this as the
    base class for an admin view will render it in the dropdown menu
    of bulk actions on the change list admin page for the model.
    """


class WizardAdminViewInterfaceMixin:
    """
    Overrides fieldset getters for wizards so that fieldsets can be
    defined for each step in Django admin views.
    """

    def get_fieldsets(self):
        fieldsets = self.fieldsets or {}
        return fieldsets.get(
            self.steps.current,
            [
                (
                    None,
                    {'fields': list(self.get_form(self.steps.current).fields)},
                )
            ],
        )


class WizardViewInterface(WizardAdminViewInterfaceMixin, ModelViewInterface):
    """The base interface required by any admin wizard view.

    Renders buttons in the same location as `ModelViewInterface`.
    """


class ObjectWizardViewInterface(
    WizardAdminViewInterfaceMixin, ObjectViewInterface
):
    """The base interface required by any admin object wizard view.

    Renders buttons in the same location as `ObjectViewInterface`.
    """


class ObjectsWizardViewInterface(
    WizardAdminViewInterfaceMixin, ObjectsViewInterface
):
    """The base interface required by any admin objects wizard view.

    Renders buttons in the same location as `ObjectsViewInterface`.
    """


class WizardView(WizardViewInterface, djarg.views.WizardView):
    """
    The base view class for making wizard views in the Django
    admin. Using this view as the base class renders a wizard view
    in the toolbar for the main change list page on the model admin.
    """


class ObjectWizardView(
    ObjectWizardViewInterface, djarg.views.ObjectWizardView
):
    """
    The base view class for making object wizard views in the Django
    admin. Using this view as the base class renders a wizard view
    in the toolbar for the main detail page on the model object admin.
    """


class ObjectsWizardView(
    ObjectsWizardViewInterface, djarg.views.ObjectsWizardView
):
    """
    The base view class for making wizard objects views in the Django
    admin. Using this view as the base class renders a wizard view
    in the dropdown menu alongside other bulk actions on the change list
    page in the model admin.
    """


class SessionWizardView(WizardViewInterface, djarg.views.SessionWizardView):
    """
    Same as `daf.admin.WizardView`, but uses a session backend by default.
    """


class SessionObjectWizardView(
    ObjectWizardViewInterface, djarg.views.SessionObjectWizardView
):
    """
    Same as `daf.admin.ObjectWizardView`, but uses a session backend by
    default.
    """


class SessionObjectsWizardView(
    ObjectsWizardViewInterface, djarg.views.SessionObjectsWizardView
):
    """
    Same as `daf.admin.ObjectsWizardView`, but uses a session backend by
    default.
    """
