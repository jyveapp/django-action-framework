from django import urls


def get_url_patterns(
    interfaces, *, path_prefix='', name_prefix='', interface_kwargs=None
):
    """
    Generate URL patterns for interfaces.
    """
    interface_kwargs = interface_kwargs or {}

    return [
        urls.path(
            f'{path_prefix}{interface.url_path}/',
            interface.as_interface(**interface_kwargs),
            name=f'{name_prefix}{interface.url_name}',
        )
        for interface in interfaces
    ]
