from django.db import models


class ActionPermission(models.Model):
    """
    This model only serves to provide a content type for action permissions.

    When this table is created, Django makes a content type for the model.
    We associate all auto-generated action permissions with this content type
    in order to ensure that action permissions dont accidentally override
    other Django permissions.
    """

    class Meta:
        default_permissions = ()
