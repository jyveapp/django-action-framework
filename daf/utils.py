import urllib.parse

from django.db import models


def build_objects_url_query_str(
    url_query_arg, objects, additional_query_str=''
):
    return urllib.parse.urlencode(
        {
            **urllib.parse.parse_qs(additional_query_str),
            url_query_arg: [
                getattr(o, url_query_arg) if isinstance(o, models.Model) else o
                for o in list(objects)
            ],
        },
        True,
    )


class classproperty(object):
    """
    A descriptor for a class property

    Adapted from
    https://stackoverflow.com/questions/3203286/how-to-create-a-read-only-class-property-in-python
    Note that this does not handle cases of users overwriting
    the values
    """

    def __init__(self, getter):
        self.getter = getter
        self.__doc__ = getter.__doc__

    def __get__(self, instance, owner):
        return self.getter(owner)
