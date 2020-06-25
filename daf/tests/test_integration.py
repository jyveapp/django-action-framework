"""
A fake app with actions was created under daf/tests. These are integration
tests for the fake app and actions
"""
import arg
import bs4
import ddf
from django import urls
import django.contrib.auth.models as auth_models
import pytest
from rest_framework.test import APIClient

import daf.registry
from daf.tests.actions.grant_staff_access import (
    GrantStaffAccessObjectDRFAction,
)
import daf.tests.models as test_models


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_basic_action(client):
    """
    Tests the basic action and some of the scenarios encountered when
    not using an ObjectAction or ObjectsAction
    """
    basic = daf.registry.get('tests.basic')

    view_url_name = basic.interfaces['view'].url_name
    url = urls.reverse(view_url_name)
    resp = client.get(url)

    # Try performing the action with a badusername
    user = ddf.G(auth_models.User, is_staff=False)
    client.force_login(user)
    resp = client.post(url, data={'user': user.id, 'username': 'list_error'})
    # Throwing a list in a ValidationError results in multiple errors
    assert '<li>list</li><li>error</li>' in resp.content.decode()

    resp = client.post(url, data={'user': user.id, 'username': 'username1'})
    assert list(
        auth_models.User.objects.values_list('username', flat=True)
    ) == ['username1']


@pytest.mark.django_db
def test_grant_staff_access_function():
    """Obtain the GrantStaffAccess action from the registry and run it"""
    user = ddf.G(auth_models.User, is_staff=False)
    actor = ddf.G(auth_models.User, is_superuser=True)

    grant_staff_access = daf.registry.get('tests.grant_staff_access')

    user = grant_staff_access.func.func(user=user, actor=actor, is_staff=True)

    # Verify the return value and the value persisted to the database
    assert user.is_staff
    user.refresh_from_db()
    assert user.is_staff


@pytest.mark.django_db
def test_grant_staff_access_drf_action(api_client, mocker):
    """Run the GrantStaffAccess DRF action"""
    actor = ddf.G(auth_models.User, is_superuser=True)
    actor.set_password('password')
    actor.save()

    user = ddf.G(auth_models.User, is_staff=False)
    grant_staff_access = daf.registry.get('tests.grant_staff_access')

    detail_view_url_name = (
        'user-'
        + grant_staff_access.interfaces[
            'rest_framework.detail_action'
        ].url_name
    )
    url = urls.reverse(detail_view_url_name, kwargs={'pk': user.id})
    api_client.force_login(actor)

    # Perform a run where form validation fails
    resp = api_client.post(url, data={'date_granted': 'invalid'})
    assert resp.status_code == 400
    assert resp.json() == {'date_granted': ['Enter a valid date/time.']}

    # Perform a successful run
    resp = api_client.post(url, data={'is_staff': True})
    assert resp.status_code == 200
    assert resp.json() == {
        'email': user.email,
        'id': user.id,
        'username': user.username,
        'is_staff': True,
    }

    # Make sure refetching for serialization works
    mocker.patch.object(
        GrantStaffAccessObjectDRFAction, 'refetch_for_serialization', False
    )
    resp = api_client.post(url, data={'is_staff': True})
    assert resp.json() == {
        'email': user.email,
        'id': user.id,
        'username': user.username,
        'is_staff': True,
    }

    # Make sure refetching for serialization works even without using
    # a parametrized wrapper
    mocker.patch.object(
        daf.actions.ObjectAction,
        'wrapper',
        arg.defaults(user=arg.val('object')),
    )
    resp = api_client.post(url, data={'is_staff': True})
    assert resp.json() == {
        'email': user.email,
        'id': user.id,
        'username': user.username,
        'is_staff': True,
    }


@pytest.mark.django_db
def test_grant_staff_access_form_view(client):
    """
    Test the form view for the grant_staff_access action.
    """
    grant_staff_access = daf.registry.get('tests.grant_staff_access')

    detail_view_url_name = grant_staff_access.interfaces['view'].url_name
    url = urls.reverse(detail_view_url_name)
    resp = client.get(url)

    # We render the default display name of the action on the form
    assert 'Grant Staff Access' in resp.content.decode()

    # Try performing the action from a non superuser
    actor = ddf.G(auth_models.User, is_superuser=False)
    user = ddf.G(auth_models.User, is_staff=False)
    client.force_login(actor)
    resp = client.post(url, data={'user': user.id, 'is_staff': True})

    assert 'Must be superuser in order to grant staff' in resp.content.decode()

    # Try successfully performing action
    actor.is_superuser = True
    actor.save()

    user.refresh_from_db()
    assert not user.is_staff
    resp = client.post(url, data={'user': user.id, 'is_staff': True})

    user.refresh_from_db()
    assert user.is_staff


@pytest.mark.django_db
def test_grant_staff_access_object_form_view(client):
    """
    Test the object form view for the grant_staff_access action.
    """
    grant_staff_access = daf.registry.get('tests.grant_staff_access')
    actor = ddf.G(auth_models.User, is_superuser=False)
    user = ddf.G(auth_models.User, is_staff=False)
    client.force_login(actor)

    view_url_name = grant_staff_access.interfaces['object_view'].url_name
    url = urls.reverse(view_url_name, kwargs={'pk': user.id})
    resp = client.get(url)

    # We render the default display name of the action on the form
    assert 'Grant Staff Access' in resp.content.decode()

    # Try performing the action from a non superuser
    resp = client.post(url, data={'user': user.id, 'is_staff': True})

    assert 'Must be superuser in order to grant staff' in resp.content.decode()

    # Try successfully performing action
    actor.is_superuser = True
    actor.save()

    user.refresh_from_db()
    assert not user.is_staff
    resp = client.post(url, data={'user': user.id, 'is_staff': True})
    assert resp.status_code == 302

    # Go to the view again and verify it shows the success message
    resp = client.get(url)
    assert (
        'Successfully performed &quot;grant staff access&quot;'
        in resp.content.decode()
    )

    user.refresh_from_db()
    assert user.is_staff


@pytest.mark.django_db
def test_bulk_grant_staff_access(client):
    """
    Test the bulk object view for the bulk_grant_staff_access action
    """
    bulk_grant_staff_access = daf.registry.get('tests.bulk_grant_staff_access')
    actor = ddf.G(auth_models.User, is_superuser=True)
    user = ddf.G(auth_models.User, is_staff=False)
    client.force_login(actor)

    view = bulk_grant_staff_access.interfaces['objects_view']
    url = urls.reverse(view.url_name)
    resp = client.get(url)
    assert resp.status_code == 404

    url = urls.reverse(view.url_name) + f'?pk={user.pk}'
    resp = client.get(url)
    assert resp.status_code == 200
    assert 'Bulk Grant Staff Access' in resp.content.decode()

    # Try performing the bulk action
    resp = client.post(url, data={'is_staff': True})

    user.refresh_from_db()
    assert user.is_staff

    # Try to access the view without permissions
    actor.is_superuser = False
    actor.save()
    resp = client.get(url)
    assert resp.status_code == 403

    actor.user_permissions.add(
        auth_models.Permission.objects.get(
            codename=view.action.permission_codename
        )
    )
    resp = client.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_my_model_list_and_change_views(client):
    """Verify MyModel actions are rendered on all admin views"""
    my_models = ddf.G(test_models.MyModel, n=3, my_field='hi')
    actor = ddf.G(auth_models.User, is_superuser=True, is_staff=True)
    client.force_login(actor)

    url = urls.reverse('admin:tests_mymodel_changelist')
    resp = client.get(url)
    assert resp.status_code == 200

    # Verify action toolbar is rendered
    toolbar_actions = {
        element.attrs['data-tool-name']
        for element in bs4.BeautifulSoup(
            resp.content.decode(), features='html.parser'
        ).select('.daf-action-item')
    }
    assert toolbar_actions == {'Update My Field', 'Update My Model'}

    # Verify bulk actions are rendered
    bulk_actions = {
        element.string
        for element in bs4.BeautifulSoup(
            resp.content.decode(), features='html.parser'
        ).select('option')
    }
    assert bulk_actions == {
        'Update My Field',
        'Update My Model',
        'Delete selected my models',
        '---------',
    }

    # Get a detail page and verify object actions
    url = urls.reverse(
        'admin:tests_mymodel_change', kwargs={'object_id': my_models[0].id}
    )
    resp = client.get(url)
    assert resp.status_code == 200

    # Verify action toolbar is rendered
    toolbar_actions = {
        element.attrs['data-tool-name']
        for element in bs4.BeautifulSoup(
            resp.content.decode(), features='html.parser'
        ).select('.daf-action-item')
    }
    assert toolbar_actions == {'Update My Field', 'Update My Model'}

    # Render the changelist page with filters
    url = urls.reverse('admin:tests_mymodel_changelist')
    resp = client.get(url + f'?my_field={my_models[0].my_field}')
    assert resp.status_code == 200

    # Go to one of the bulk actions
    resp = client.post(
        url + f'?my_field={my_models[0].my_field}',
        {
            'action': '_daf_update_my_field',
            '_selected_action': my_models[0].id,
        },
    )
    assert resp.status_code == 302
    assert resp.url == (
        '/admin/tests/mymodel/objects-action/update-my-field/'
        f'?_changelist_filters=my_field%3Dhi&pk={my_models[0].id}'
    )
    resp = client.post(resp.url, data={'my_field': 'other_value'})
    assert resp.status_code == 302
    assert resp.url == '/admin/tests/mymodel/?my_field=hi'

    resp = client.get(resp.url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_dynamic_button_rendering(client, mocker):
    """Verify admin actions are rendered based on permissions"""
    update_my_field = daf.registry.get('tests.update_my_field')
    admin_interface = update_my_field.interfaces['admin.model_view']
    my_models = ddf.G(test_models.MyModel, n=3, my_field='hi')
    actor = ddf.G(auth_models.User, is_superuser=False, is_staff=True)
    actor.user_permissions.add(
        auth_models.Permission.objects.get(codename='view_mymodel'),
        auth_models.Permission.objects.get(
            codename='tests_update_my_field_action'
        ),
    )
    client.force_login(actor)

    url = urls.reverse(admin_interface.changelist_url_name)
    resp = client.get(url)
    assert resp.status_code == 200

    # Verify action toolbar is rendered
    toolbar_actions = {
        element.attrs['data-tool-name']
        for element in bs4.BeautifulSoup(
            resp.content.decode(), features='html.parser'
        ).select('.daf-action-item')
    }
    assert toolbar_actions == {'Update My Field'}

    # Verify bulk actions are rendered
    bulk_actions = {
        element.string
        for element in bs4.BeautifulSoup(
            resp.content.decode(), features='html.parser'
        ).select('option')
    }
    assert bulk_actions == {'Update My Field', '---------'}

    # Get a detail page and verify object actions
    url = urls.reverse(
        admin_interface.change_url_name, kwargs={'object_id': my_models[0].id}
    )
    resp = client.get(url)
    assert resp.status_code == 200

    # Verify action toolbar is rendered
    toolbar_actions = {
        element.attrs['data-tool-name']
        for element in bs4.BeautifulSoup(
            resp.content.decode(), features='html.parser'
        ).select('.daf-action-item')
    }
    assert toolbar_actions == {'Update My Field'}

    # When no permissions are required, all buttons are rendered
    mocker.patch(
        'daf.admin.AdminViewInterfaceMixin.permission_required', False
    )
    resp = client.get(url)
    assert resp.status_code == 200
    toolbar_actions = {
        element.attrs['data-tool-name']
        for element in bs4.BeautifulSoup(
            resp.content.decode(), features='html.parser'
        ).select('.daf-action-item')
    }
    assert toolbar_actions == {'Update My Field', 'Update My Model'}


@pytest.mark.django_db
def test_update_my_field_admin_view(client):
    """
    Test the "update_my_field" main admin view.
    """
    ddf.G(test_models.MyModel, n=2, my_field='value')
    update_my_field = daf.registry.get('tests.update_my_field')

    view_url_name = update_my_field.interfaces['admin.model_view'].url_name
    url = urls.reverse(f'admin:{view_url_name}')
    resp = client.get(url)
    # We should be redirected to the login page
    assert resp.status_code == 302
    assert 'admin/login' in resp.url

    # Try performing the action that results in an error
    actor = ddf.G(auth_models.User, is_superuser=True, is_staff=True)
    client.force_login(actor)
    resp = client.post(url)
    content = resp.content.decode()

    # Ensure page rendering and some expected help text
    assert 'Django administration' in content
    assert 'help me one' in content
    assert 'Please correct the error below' in content
    assert 'Update My Field' in content

    # Try successfully performing action and test success message
    resp = client.post(url, data={'my_field': 'other_value'})
    assert resp.status_code == 302
    resp = client.get(resp.url)
    assert (
        'Successfully performed &quot;update my field&quot;'
        in resp.content.decode()
    )

    assert list(
        test_models.MyModel.objects.values_list(
            'my_field', flat=True
        ).distinct()
    ) == ['other_value']


@pytest.mark.django_db
def test_update_my_field_admin_object_view(client):
    """
    Test the "update_my_field" object view.
    """
    actor = ddf.G(auth_models.User, is_superuser=True, is_staff=True)
    client.force_login(actor)

    my_model = ddf.G(test_models.MyModel, my_field='value')
    update_my_field = daf.registry.get('tests.update_my_field')
    view_url_name = update_my_field.interfaces['admin.object_view'].url_name
    url = urls.reverse(f'admin:{view_url_name}', kwargs={'pk': my_model.id})

    # Try successfully performing action and test success message
    resp = client.post(url, data={'my_field': 'other_value'})
    assert resp.status_code == 302
    assert resp.url == '/admin/tests/mymodel/'
    resp = client.get(resp.url)
    assert (
        'Successfully performed &quot;update my field&quot;'
        in resp.content.decode()
    )

    # Successfully perfom the action, but hit the "submit and continue"
    # button. You should be redirected elsewhere
    resp = client.post(
        url, data={'my_field': 'other_value', '_continue_editing': 'True'}
    )
    assert resp.status_code == 302
    assert resp.url == f'/admin/tests/mymodel/{my_model.id}/change/'

    assert list(
        test_models.MyModel.objects.values_list(
            'my_field', flat=True
        ).distinct()
    ) == ['other_value']


@pytest.mark.django_db
def test_update_my_model_admin_view(client):
    """
    Test the "update_my_model" main admin wizard view.
    """
    actor = ddf.G(auth_models.User, is_superuser=True, is_staff=True)
    client.force_login(actor)

    ddf.G(test_models.MyModel, n=3, my_field='value')
    update_my_model = daf.registry.get('tests.update_my_model')
    view_url_name = update_my_model.interfaces['admin.model_view'].url_name
    url = urls.reverse(f'admin:{view_url_name}')
    resp = client.post(
        url,
        data={
            'update_my_model_admin_view-current_step': 'field',
            'field-my_field': 'other_value',
        },
    )
    assert resp.status_code == 200
    assert 'My extra field' in resp.content.decode()

    resp = client.post(
        url,
        data={
            'update_my_model_admin_view-current_step': 'extra_field',
            'extra_field-my_extra_field': 'extra_value',
        },
    )
    assert resp.status_code == 302

    assert resp.url == '/admin/tests/mymodel/'
    resp = client.get(resp.url)
    assert (
        'Successfully performed &quot;update my model&quot;'
        in resp.content.decode()
    )

    assert list(
        test_models.MyModel.objects.values_list(
            'my_field', flat=True
        ).distinct()
    ) == ['other_value']


@pytest.mark.django_db
def test_update_my_model_admin_object_view(client):
    """
    Test the "update_my_model" object wizard view.
    """
    actor = ddf.G(auth_models.User, is_superuser=True, is_staff=True)
    client.force_login(actor)

    my_model = ddf.G(test_models.MyModel, my_field='value')
    update_my_model = daf.registry.get('tests.update_my_model')
    view_url_name = update_my_model.interfaces['admin.object_view'].url_name
    url = urls.reverse(f'admin:{view_url_name}', kwargs={'pk': my_model.id})
    resp = client.get(url)
    # Verify the fieldset renders
    assert 'Description!' in resp.content.decode()

    # Try successfully performing action and test success message
    resp = client.post(
        url,
        data={
            'update_my_model_object_admin_view-current_step': 'field',
            'field-my_field': 'other_value',
        },
    )
    assert resp.status_code == 200
    assert 'My extra field' in resp.content.decode()

    resp = client.post(
        url,
        data={
            'update_my_model_object_admin_view-current_step': 'extra_field',
            'extra_field-my_extra_field': 'extra_value',
        },
    )
    assert resp.status_code == 302

    assert resp.url == '/admin/tests/mymodel/'
    resp = client.get(resp.url)
    assert (
        'Successfully performed &quot;update my model&quot;'
        in resp.content.decode()
    )

    assert list(
        test_models.MyModel.objects.values_list(
            'my_field', flat=True
        ).distinct()
    ) == ['other_value']


@pytest.mark.django_db
def test_update_my_field_admin_objects_view(client):
    """
    Test the "update_my_field" objects view.

    Test the flow of dismissing failing objects
    """
    actor = ddf.G(auth_models.User, is_superuser=True, is_staff=True)
    client.force_login(actor)

    my_models = ddf.G(test_models.MyModel, n=3, my_field='value')
    update_my_field = daf.registry.get('tests.update_my_field')
    view_url_name = update_my_field.interfaces['admin.objects_view'].url_name
    url = urls.reverse(f'admin:{view_url_name}')
    # No objects should result in 404
    assert client.get(url).status_code == 404

    url += f'?pk={my_models[0].id}&pk={my_models[1].id}&pk={my_models[2].id}'
    resp = client.get(url)
    assert resp.status_code == 200
    assert 'Update My Field' in resp.content.decode()
    assert ' - Three My Models' in resp.content.decode()

    # Make all objects fail
    test_models.MyModel.objects.update(my_field='aaa')
    resp = client.post(url, data={'my_field': 'other_value'})
    assert resp.status_code == 200
    content = resp.content.decode()
    assert (
        f'{my_models[0]} - &quot;my_field&quot; is &quot;aaa&quot;. Cannot update'
        in content
    )
    assert (
        f'{my_models[1]} - &quot;my_field&quot; is &quot;aaa&quot;. Cannot update'
        in content
    )
    assert (
        f'{my_models[2]} - &quot;my_field&quot; is &quot;aaa&quot;. Cannot update'
        in content
    )

    # Try successfully performing action and test success message
    test_models.MyModel.objects.update(my_field='valid')
    resp = client.post(url, data={'my_field': 'other_value'})
    assert resp.status_code == 302
    resp = client.get(resp.url)
    assert (
        'Successfully performed &quot;update my field&quot; on three my models'
        in resp.content.decode()
    )

    assert list(
        test_models.MyModel.objects.values_list(
            'my_field', flat=True
        ).distinct()
    ) == ['other_value']


@pytest.mark.django_db
def test_update_my_field_admin_objects_dismissal_flow(client):
    """
    Test the flow of dismissing failing objects with the "update_my_field"
    admin objects view.
    """
    actor = ddf.G(auth_models.User, is_superuser=True, is_staff=True)
    client.force_login(actor)

    my_models = ddf.G(test_models.MyModel, n=3, my_field='value')
    update_my_field = daf.registry.get('tests.update_my_field')
    view_url_name = update_my_field.interfaces['admin.objects_view'].url_name
    url = urls.reverse(f'admin:{view_url_name}')
    url += f'?pk={my_models[0].id}&pk={my_models[1].id}&pk={my_models[2].id}'
    resp = client.get(url)
    assert resp.status_code == 200
    assert 'Update My Field' in resp.content.decode()
    assert ' - Three My Models' in resp.content.decode()

    # Make the second my_model fail validation by using "aaa" as the value
    my_models[1].my_field = 'aaa'
    my_models[1].save()
    resp = client.post(url, data={'my_field': 'other_value2'})
    assert resp.status_code == 200
    content = resp.content.decode()

    # Verify we have a contextualized error and a dismiss button
    assert (
        f'MyModel object ({my_models[1].id}) - &quot;my_field&quot;'
        ' is &quot;aaa&quot;. Cannot update'
    ) in content
    assert 'Dismiss One Failing' in content

    # Go to the dismissal link
    dismiss_url = (
        bs4.BeautifulSoup(content, features='html.parser')
        .select('#dismiss-failed-objects')[0]
        .attrs['href']
    )
    resp = client.get(dismiss_url)
    assert resp.status_code == 200
    assert 'Update My Field' in resp.content.decode()
    assert ' - Two My Models' in resp.content.decode()
    resp = client.post(dismiss_url, data={'my_field': 'other_value2'})
    assert resp.status_code == 302

    assert set(
        test_models.MyModel.objects.values_list(
            'my_field', flat=True
        ).distinct()
    ) == {'aaa', 'other_value2'}
