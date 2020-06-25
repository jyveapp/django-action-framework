import django.core.exceptions as django_exceptions
import pytest
import rest_framework.exceptions as drf_exceptions

import daf.rest_framework


@pytest.mark.parametrize(
    'error, expected_error_raised',
    [
        (
            drf_exceptions.APIException('bad', code='badd'),
            drf_exceptions.APIException('bad', code='badd'),
        ),
        (ValueError('msg'), daf.rest_framework.APIException('msg')),
        (
            django_exceptions.ValidationError('msg2', code='badd'),
            daf.rest_framework.APIException('msg2', code='badd'),
        ),
        (
            django_exceptions.ValidationError(['msg2'], code='badd'),
            # Codes aren't preserved when raising multi-validation errors
            daf.rest_framework.APIException(['msg2'], code='invalid'),
        ),
        (
            django_exceptions.ValidationError({'field': ['val']}, code='badd'),
            # Codes aren't preserved when raising multi-validation errors
            daf.rest_framework.APIException(
                {'field': ['val']}, code='invalid'
            ),
        ),
    ],
)
def test_raise_drf_error(error, expected_error_raised):
    """
    Tests the rest_framework.raise_drf_error context manager
    that raised DRF exceptions when running actions.
    """
    try:
        with daf.rest_framework.raise_drf_error():
            raise error
    except Exception as exc:
        assert exc.detail == expected_error_raised.detail
    else:
        raise AssertionError('Error wasnt raised')
