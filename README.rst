django-action-framework
#######################

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

For examples and a full tutorial of how to use ``django-action-framework``,
check out the `docs <https://django-action-framework.readthedocs.io/>`__.

Documentation
=============

`View the django-action-framework docs here
<https://django-action-framework.readthedocs.io/>`_.

Installation
============

Install django-action-framework with::

    pip3 install django-action-framework

After this, add ``daf`` to the ``INSTALLED_APPS``
setting of your Django project.

Contributing Guide
==================

For information on setting up django-action-framework for development and
contributing changes, view `CONTRIBUTING.rst <CONTRIBUTING.rst>`_.


Primary Authors
===============

- @wesleykendall (Wes Kendall)
- @romansul (Roman Sul)
- @chang-brian (Brian Chang)
