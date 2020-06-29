django-action-framework
=======================

``django-action-framework`` (``daf``) provides the ability to generate
a number of diverse interfaces from a single action definition. What is
an action? It's a function. By writing a function and providing a few
hints about the characteristics of your function, you can:

1. Generate a form view from the function with proper form validation.
2. Generate an update view on a model object that is passed to the function.
3. Generate a bulk update view on multiple objects. These objects can
   be parametrized over a function expecting one object, meaning your detail
   and bulk views share the same code when desired.
4. Generate wizard views to collect function arguments over multiple steps,
   even if the steps are conditional.
5. Natively integrate these views into the Django admin as model, detail,
   or bulk actions.
6. Generate Django Rest Framework actions on your viewsets.

``daf`` removes the boilerplate and cognitive overhead of maintaining validation
logic, view logic, and update logic spread across Django views, models, admin
interfaces, API endpoints, and other locations in a Django project. ``daf``
allows the engineer to focus on writing one clear and easily-testable piece of
business logic while treating complex UI and APIs as an extension of the
function rather than a piece of intertwined code.

How is one able to write a function and have all validation logic and
parametrization of bulk actions work seamlessly with minimal additional
boilerplate, even if parameters are gathered through a multi-step UI like
a form wizard? The answer lies in the underlying libraries used
by ``daf`` - `python-args <https://github.com/jyveapp/python-args>`__
and `django-args <https://github.com/jyveapp/django-args>`__. While it is
not a requirement to understand these libraries to use the action framework,
we assume some knowledge of ``python-args`` when constructing actions.
For now, we will give a brief quickstart of ``daf`` and then go into
more complex examples in the :ref:`tutorial`.

Quickstart
~~~~~~~~~~

Assuming you have read the installation instructions for installing ``daf``
in your Django project, let's go through an example of creating an action
to grant a user staff access in the database.

Defining the action
-------------------

It is recommended to define or import all of your actions in the ``actions.py``
file of the relevant Django app. ``daf`` automatically searches for actions
in this module and makes all actions accessible via the ``daf`` action
registry. This will be explained more later.

Here, we define the ``GrantStaffAccess`` action in ``examples/actions.py``:

.. code-block:: python

    import daf.actions


    def grant_staff_access(user, is_staff):
        user.is_staff = is_staff
        user.save()
        return user


    class GrantStaffAccess(daf.actions.Action):
        callable = grant_staff_access
        app_label = 'examples'


The purpose of an `Action` class is to primarily serve as
a container of metadata about a function. It is this metadata that is
used to aid in constructing a wide variety of interfaces.

Creating a FormView on the action
---------------------------------

A ``FormView`` can now be created on our action with:

.. code-block:: python

    from django import forms
    import daf.views


    class GrantStaffAccessForm(forms.Form):
        user = forms.ModelChoiceField(queryset=User.objects.all())
        is_staff = forms.BooleanField(required=False)


    class GrantStaffAccessFormView(daf.views.FormView):
        form_class = GrantStaffAccessForm
        template_name = 'examples/grant_staff.html'
        action = GrantStaffAccess


Similar to Django's ``FormView``, we can construct a template using
the ``form`` variable like so::

    {{ form.media }}

    {{ view.display_name }}

    <form action=".?{{ request.GET.urlencode }}" method="post" enctype="multipart/form-data">
      {% csrf_token %}
      {{ form.as_p }}
      <button type="submit">
        Submit
      </button>
    </form>

Every ``daf`` interface and view comes with the ``action`` property on the
view and several other properties of the action mirrored by default. In
the above, we use ``display_name`` to render the title of the action.
We will cover all action and interface attributes in the :ref:`tutorial`.

Two properties, the ``url_name`` and ``url_path`` of the action can
automatically be used to construct a URL to the view in ``urls.py``:

    .. code-block:: python

      import daf.urls

      import examples.actions


      urlpatterns = daf.urls.get_url_patterns(
          [examples.actions.GrantStaffAccessFormView]
      )

And *voila*, you have now written an entire form view on top of a function.

``daf`` is not opinionated on where views and interfaces should be defined.
Users can continue to define these in ``views.py`` or wherever they see fit.
``daf``, however, is opinionated in the sense of defining functions and
business logic completely separate from the interface.

A more advanced use case
------------------------

The advantages of ``daf`` are not going to be seen in defining one trivial
action with a single interface, however, we can extend this example just a bit
more to highlight where ``daf`` starts to shine.

One common pattern in complex Django forms and views is validation. Users
typically have the option to override form and field ``clean`` methods in
order to display nice error messages to the user. Django provides several
ways to make this process easier, some of which include using
`validators <https://docs.djangoproject.com/en/3.0/ref/validators/>`__ on
form fields.

One pattern ``daf`` aims to prevent is the intertwining of UI logic with
core business logic and code. Not only does this make testing code more
involved, but it can create a web of complexity in trying to perform the action
safely and understand what is going on.

For example, what if we really need to perform the validation logic on our
model only after a ``select_for_update`` to ensure there are no race conditions?
What if we want to make sure this ``select_for_update`` only happens during
the run of the action (after the entire form is validated)? It's these
types of situations that can quickly make a simple form into a very complex
one.

``daf`` is build completely on top of
`python-args <https://github.com/jyveapp/python-args>`__
and `django-args <https://github.com/jyveapp/django-args>`__. This means
that we can decorate our main function with ``python-args`` decorators
and have our functions work seamlessly with Django form validation.

For example, let's extend our example and pass the person that's granting
the user staff access. Let's also make sure the granter is also a staff
member.


.. code-block:: python

  import arg


  def is_granter_valid(granter):
      if not granter.is_staff:
          raise ValueError(f'Granter {granter} is not staff')


  @arg.validators(is_granter_staff)
  def grant_staff_access(granter, user, is_staff):
      user.is_staff = is_staff
      user.save()

      logging.info(f'Granted staff access to {user} from {granter}')
      return user


When we use ``python-args`` ``@arg.validators`` decorator on our function,
the validation routines will automatically be bound to our form based on
the function arguments. This means you can always keep your validation logic
close to your function and keep it away from your form. It also means that
you can more easily test individual validators
(by running ``is_granter_valid``) or only test the core business logic
(by running ``grant_staff_access.func(...)`` since it's a ``python-args``
function now).

We still need to update our view to pass in the ``granter`` parameter.
We do this by overridding ``get_default_args`` since we are not going to
collect the granter from the form:


.. code-block:: python

  class GrantStaffAccessFormView(daf.views.FormView):
      form_class = GrantStaffAccessForm
      template_name = 'examples/grant_staff.html'
      action = GrantStaffAccess

      def get_default_args(self):
          return {
              **super().get_default_args(),
              'granter': self.request.user
          }

Submitting this form results in a form error message if the authenticated
user is not a staff member. Although one could solve the specific problem
of permissions and object access with different mechanisms, this serves
as an example of how one can write clear and concise validation logic
that is not intertwined with a UI.

Next Steps
~~~~~~~~~~

As we will show in the :ref:`tutorial`, the use of other utilities
like `daf.actions.ObjectAction` and the combination of other ``python-args``
decorators for action wrappers can cut down on even more of the boilerplate
of writing:

1. Single and multiple object actions.
2. Wizards that collect data across multiple steps.
3. Rest framework viewsets that run actions.
4. Admin actions that run on single or multiple objects across single or
   multiple steps.

Before continuing to the :ref:`tutorial`, it is highly recommended to read about
`python-args <https://github.com/jyveapp/python-args>`__
and `django-args <https://github.com/jyveapp/django-args>`__ to understand
the full expressiveness of what one can do. The action framework is really
just a wrapper on top of these libraries.
