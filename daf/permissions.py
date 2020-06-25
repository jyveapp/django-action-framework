from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

import daf.models
import daf.registry


def _get_permission_name(action_class):
    """
    Obtains a human-readable name for a permission
    """
    name = f'Can perform "{action_class.display_name.lower()}" action'
    return name[:255]


def install():
    """
    Installs all permissions associated with actions

    This function is exected automatically at the
    end of every django migration. The signal
    handler is linked in actions/apps.py
    """
    # Start the content types cache from a fresh slate
    # to address issues when running tests.
    ContentType.objects.clear_cache()

    # All action permissions are attached to the ActionPermission
    # content type. This allows the action framework to delete permissions
    # that are no longer attached to actions without risking deleting
    # permissions outside the framework.
    action_permission_ctype = ContentType.objects.get_for_model(
        daf.models.ActionPermission
    )

    # Update action permissions. Delete any permissions that are no longer
    # connected to an action.
    # NOTE - Django's update_or_create is extremely inefficient. Although
    # this could be accomplished in one postgres bulk upsert, we use the naive
    # approach for now to keep this library generic. This operation is
    # only executed during migrations, so we don't have concern for
    # race conditions
    with transaction.atomic():
        permission_ids = []
        for action_class in daf.registry.actions():
            permission = Permission.objects.update_or_create(
                codename=action_class.permission_codename,
                content_type=action_permission_ctype,
                defaults={'name': _get_permission_name(action_class)},
            )[0]
            permission_ids.append(permission.id)

        # Remove any action permissions that no longer exist
        Permission.objects.filter(
            content_type=action_permission_ctype
        ).exclude(id__in=permission_ids).delete()
