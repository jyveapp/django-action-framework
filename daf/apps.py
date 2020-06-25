from django.apps import AppConfig
from django.db.models.signals import post_migrate

from daf import registry


def install_permissions_handler(**kwargs):
    # Nest this import since we can only import models
    # when Django is loaded
    from . import permissions

    permissions.install()


class DjangoActionFrameworkConfig(AppConfig):
    name = 'daf'

    def ready(self):
        """
        Load action classes into the registry and install
        permissions for actions post migrate.
        """
        # Try to discover any action classes by importing
        # the "actions" module of every app
        registry.autodiscover_actions()

        # NOTE(@wesleykendall) - Installing permissions at the
        # end of migrations makes it more difficult to write data
        # migrations that assign new action permissions to groups.
        # However, Django already uses this pattern for their
        # permissions, and we should ideally be defining initial
        # application data outside of data migrations
        post_migrate.connect(install_permissions_handler, sender=self)
